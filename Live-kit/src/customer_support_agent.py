import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    deepgram,
    elevenlabs,
    noise_cancellation,
    silero,
)

from conversation_manager import ConversationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManager:
    """Manages JSON data files for customers, products, and orders."""
    
    def __init__(self):
        self.customers_file = "../data/customers.json"
        self.products_file = "../data/products.json"
        self.orders_file = "../data/orders.json"
    
    def load_json(self, file_path: str) -> Dict:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {file_path}")
            return {}
    
    def save_json(self, file_path: str, data: Dict) -> bool:
        """Save JSON data to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {e}")
            return False
    
    def get_customers(self) -> List[Dict]:
        """Get all customers."""
        data = self.load_json(self.customers_file)
        return data.get('customers', [])
    
    def get_products(self) -> List[Dict]:
        """Get all products."""
        data = self.load_json(self.products_file)
        return data.get('products', [])
    
    def get_orders(self) -> List[Dict]:
        """Get all orders."""
        data = self.load_json(self.orders_file)
        return data.get('orders', [])
    
    def add_order(self, order: Dict) -> bool:
        """Add a new order."""
        data = self.load_json(self.orders_file)
        if 'orders' not in data:
            data['orders'] = []
        data['orders'].append(order)
        return self.save_json(self.orders_file, data)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by updating its status."""
        data = self.load_json(self.orders_file)
        orders = data.get('orders', [])
        
        for order in orders:
            if order['order_id'] == order_id:
                if order['status'] in ['pending', 'processing']:
                    order['status'] = 'cancelled'
                    order['cancelled_date'] = datetime.now().isoformat()
                    return self.save_json(self.orders_file, data)
                else:
                    return False  # Cannot cancel shipped/delivered orders
        return False  # Order not found


class CustomerSupportAgent(Agent):
    """
    Advanced Customer Support Agent with intelligent query processing.
    Handles customer inquiries, product information, and order management.
    """
    
    def __init__(self) -> None:
        # Initialize data manager and conversation manager
        self.data_manager = DataManager()
        self.conversation_manager = ConversationManager(
            redis_url=os.getenv("REDIS_URL"),
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600")),
            max_history=int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
        )
        self.session_id = None
        
        super().__init__(
            instructions=(
                "You are a professional, warm, and intelligent customer support specialist with access to comprehensive customer, product, and order information. "
                "You have conversation memory and build genuine relationships with customers. "
                "PERSONALITY & BEHAVIOR: "
                "- Be genuinely warm, professional, and personable - like a skilled human agent "
                "- Use the customer's name naturally throughout the conversation when you know it "
                "- Speak conversationally and naturally - avoid robotic or scripted language "
                "- Show genuine interest in helping and ask thoughtful follow-up questions "
                "- Remember and reference previous conversations to build rapport "
                "- Be proactive in offering relevant suggestions based on customer history "
                "- Express empathy and understanding when customers have issues "
                "COMMUNICATION STYLE: "
                "- Speak naturally like a real human - vary your responses and avoid repetitive phrases "
                "- Use conversational fillers and natural speech patterns: 'Well...', 'Let me see...', 'Actually...' "
                "- Keep responses concise but warm (2-4 sentences unless detailed info is needed) "
                "- Use different ways to express the same ideas - never sound robotic or scripted "
                "- Show genuine interest with varied questions and acknowledgments "
                "- Adapt your tone based on the customer's mood and context "
                "INTERRUPTION HANDLING: "
                "- You can be interrupted at ANY time while speaking - STOP immediately and listen "
                "- When interrupted, acknowledge naturally and professionally: 'Of course!', 'Yes, please go ahead!', or 'I'm listening!' "
                "- Never repeat what you were saying before the interruption "
                "- Seamlessly respond to the new input as if it's a natural conversation flow "
                "- Show that you're actively listening and engaged "
                "PROFESSIONAL EXCELLENCE: "
                "- Always confirm important actions before executing them "
                "- Provide clear, accurate information with confidence "
                "- Offer additional help proactively "
                "- Use conversation history to provide personalized recommendations "
                "\n\nSCENARIO HANDLING (be natural, not scripted): "
                "CUSTOMER IDENTIFICATION: When you need to identify someone, ask casually: 'What's your name?' or 'Who am I talking to?' or 'What's your customer ID or email?' "
                "ACCOUNT CREATION: When creating accounts, mention it briefly and move on: 'Got you set up with account XYZ' then ask what they need "
                "MISSING INFO: When you need details, ask naturally: 'Which product?' or 'How many?' or 'What's your email?' - don't give long lists "
                "ORDERS: For orders, ask for what you need conversationally: 'What do you want to order?' then 'Your customer ID?' "
                "CLARIFICATION: If something's unclear, ask simply: 'What do you mean?' or 'Can you tell me more about that?' "
                "\n\nYou can help with: "
                "1. Customer information lookup (by email, phone, or customer ID) "
                "2. Product information and search "
                "3. Order status and tracking "
                "4. Placing new orders "
                "5. Cancelling orders "
                "6. General product questions "
                "7. Returns, shipping, and warranty information "
                "\n\nRespond naturally based on context - don't use templated phrases. Ask for what you need when you need it."
            )
        )
        self.last_processed_input = ""
        self.processing_query = False
        self.is_speaking = False
        self._agent_session = None
        self.current_response_task = None
        self.conversation_flow = {
            'last_topic': None,
            'interruption_count': 0,
            'acknowledgments': [
                "Of course!", "Yes, go ahead!", "I'm listening!", "Please continue!",
                "What can I help with?", "Yes?", "I'm here!", "Tell me more!"
            ]
        }

    async def on_enter(self) -> None:
        """Called when the agent is first activated."""
        logger.info("CustomerSupportAgent activated")
        
        # Initialize session ID
        participant_identity = getattr(self.session, 'participant_identity', None)
        self.session_id = self.conversation_manager.generate_session_id(participant_identity)
        
        # Check if this is a returning customer
        session_info = self.conversation_manager.get_session_info(self.session_id)
        
        if session_info.get('message_count', 0) > 0:
            # Returning customer
            logger.info(f"Returning customer session: {self.session_id}")
            greeting = ("Welcome back! I'm Sarah from customer support. "
                       "I have our previous conversation history, so I can pick up right where we left off. "
                       "How can I assist you today?")
        
        # Add system message to conversation history
        self.conversation_manager.add_message(
            self.session_id, 
            "system", 
            f"Session started. Agent greeting: {greeting}"
        )
        
        await self.session.say(greeting)

    async def on_user_turn_completed(self, chat_ctx, new_message) -> None:
        """Process user input with smooth, human-like interaction."""
        if not new_message.text_content or len(new_message.text_content) == 0:
            return

        user_text = new_message.text_content.strip()
        if not user_text or user_text == self.last_processed_input:
            return

        self.last_processed_input = user_text
        logger.info(f"🎤 Customer: {user_text}")

        # Cancel any current response to avoid overlap
        if self.current_response_task and not self.current_response_task.done():
            self.current_response_task.cancel()
            logger.info("🚫 Cancelled previous response for new input")

        # Process with smooth human-like flow
        self.current_response_task = asyncio.create_task(
            self._process_with_human_flow(user_text)
        )
    
    async def _process_with_human_flow(self, user_text: str) -> None:
        """Process user input with natural, human-like conversation flow."""
        try:
            if self.processing_query:
                return
                
            self.processing_query = True
            
            # Handle interruption acknowledgment naturally (only if truly needed)
            response_prefix = ""
            if self.conversation_flow['interruption_count'] > 0 and self.is_speaking:
                # Brief, natural acknowledgment
                ack_responses = ["Yes?", "Go ahead!", "I'm listening!"]
                import random
                response_prefix = random.choice(ack_responses) + " "
                self.conversation_flow['interruption_count'] = 0
            
            # Add to conversation history (optimized)
            self.conversation_manager.add_message(self.session_id, "user", user_text)
            
            # Get conversation context (cached for performance)
            conversation_context = self.conversation_manager.get_conversation_context(self.session_id)
            
            # Process the query with optimized routing
            response = await self.process_customer_query(user_text, conversation_context)
            
            # Add natural prefix if interrupted
            if response_prefix:
                response = response_prefix + response
            
            # Store response in conversation history
            self.conversation_manager.add_message(self.session_id, "assistant", response)
            
            # Speak naturally with minimal delay
            logger.info(f"🗣️ Sarah: {response}")
            await self.session.say(response)
            
        except asyncio.CancelledError:
            logger.info("🚫 Response cancelled due to interruption")
        except Exception as e:
            logger.error(f"Error in human flow processing: {e}")
            error_response = "I apologize, could you repeat that?"
            await self.session.say(error_response)
        finally:
            self.processing_query = False
    
    async def process_customer_query_direct(self, query: str) -> None:
        """Process customer query directly without buffering for better interruption handling."""
        if self.processing_query:
            logger.info("Already processing a query, skipping...")
            return
            
        self.processing_query = True
        
        try:
            # Add user message to conversation history
            self.conversation_manager.add_message(self.session_id, "user", query)

            # Get conversation context for better responses
            conversation_context = self.conversation_manager.get_conversation_context(self.session_id)

            # Analyze the query and provide intelligent response
            response = await self.process_customer_query(query, conversation_context)

            # Add agent response to conversation history
            self.conversation_manager.add_message(self.session_id, "assistant", response)

            # Use session.say for voice output
            await self.session.say(response)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            error_response = "I apologize, but I encountered an error. Could you please repeat your question?"
            self.conversation_manager.add_message(self.session_id, "assistant", error_response)
            await self.session.say(error_response)
        finally:
            self.processing_query = False
    
    async def process_customer_query(self, query: str, conversation_context: str = "") -> str:
        """Process customer queries intelligently with conversation context."""
        query_lower = query.lower()
        
        # Log conversation context for debugging
        if conversation_context:
            logger.debug(f"Using conversation context: {conversation_context[:200]}...")
        
        # Extract customer name if provided
        customer_name = self._extract_customer_name(query)
        if customer_name:
            # Store customer name in conversation metadata
            self.conversation_manager.add_message(
                self.session_id,
                "system",
                f"Customer name: {customer_name}",
                metadata={"customer_name": customer_name}
            )
        
        # Enhanced query processing with context awareness
        if conversation_context:
            # Check if query references previous conversation
            if any(word in query_lower for word in ['that order', 'my order', 'the product', 'it', 'that']):
                # Extract relevant information from context
                context_info = self._extract_context_info(conversation_context)
                if context_info:
                    query = f"{query} (Context: {context_info})"
        
        # Name Introduction / Personal Information
        if customer_name or any(word in query_lower for word in ['my name is', 'i am', 'call me', 'i\'m']):
            return await self.handle_name_introduction(query, customer_name, conversation_context)
        
        # Customer Information Queries
        elif any(word in query_lower for word in ['my account', 'my info', 'customer info', 'my details']):
            return await self.handle_customer_info_query(query)
        
        # Product Information Queries
        elif any(word in query_lower for word in ['product', 'item', 'what is', 'tell me about', 'price of']):
            return await self.handle_product_query(query)
        
        # Order Placement (check first - more specific)
        elif any(word in query_lower for word in ['buy', 'purchase', 'want to buy', 'place order', 'i want to order', 'order for']):
            return await self.handle_order_placement_query(query)
        
        # Order Queries (check after placement)
        elif any(word in query_lower for word in ['check order', 'order status', 'tracking', 'delivery', 'shipped', 'my order']):
            return await self.handle_order_query(query)
        
        # Cart Management (add to cart, cart operations)
        elif any(word in query_lower for word in ['add to cart', 'add this', 'add it', 'put in cart', 'cart']):
            return await self.handle_cart_management(query, conversation_context)
        
        # Order Cancellation
        elif any(word in query_lower for word in ['cancel', 'refund', 'return']):
            return await self.handle_cancellation_query(query)
        
        # Product Search
        elif any(word in query_lower for word in ['search', 'find', 'looking for', 'show me']):
            return await self.handle_product_search_query(query)
        
        # General Support
        elif any(word in query_lower for word in ['help', 'support', 'question', 'policy']):
            return await self.handle_general_query(query)
        
        else:
            return await self.handle_general_query(query)
    
    def _extract_context_info(self, conversation_context: str) -> str:
        """Extract relevant information from conversation context."""
        context_info = []
        
        # Extract order IDs
        import re
        order_ids = re.findall(r'ORD\d+', conversation_context)
        if order_ids:
            context_info.append(f"Recent orders: {', '.join(set(order_ids))}")
        
        # Extract customer IDs
        customer_ids = re.findall(r'CUST\d+', conversation_context)
        if customer_ids:
            context_info.append(f"Customer ID: {customer_ids[-1]}")
        
        # Extract product mentions
        product_keywords = ['headphones', 'watch', 'keyboard', 'shirt', 'coffee', 'book', 'yoga', 'cream']
        mentioned_products = [word for word in product_keywords if word in conversation_context.lower()]
        if mentioned_products:
            context_info.append(f"Discussed products: {', '.join(set(mentioned_products))}")
        
        return '; '.join(context_info) if context_info else ""
    
    def _extract_customer_name(self, query: str) -> str:
        """Extract customer name from query with better filtering."""
        import re
        
        # Patterns to extract names
        name_patterns = [
            r'my name is ([A-Za-z\s]{2,30})',
            r'i am ([A-Za-z\s]{2,30})',
            r'i\'m ([A-Za-z\s]{2,30})',
            r'name is ([A-Za-z\s]{2,30})',
            r'call me ([A-Za-z\s]{2,30})'
        ]
        
        # Words that are definitely not names
        non_names = [
            'looking', 'for', 'a', 'wireless', 'bluetooth', 'headphones', 'headset',
            'new', 'customer', 'user', 'the', 'an', 'this', 'that', 'here', 'there',
            'good', 'bad', 'nice', 'great', 'awesome', 'product', 'item', 'thing'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query.lower())
            if match:
                name = match.group(1).strip().title()
                # Check if it's a valid name (not product-related words)
                name_words = name.lower().split()
                if (name and len(name_words) <= 3 and 
                    not any(word in non_names for word in name_words)):
                    return name
        
        return ""
    
    async def _find_customer_by_name(self, name: str) -> Optional[Dict]:
        """Find customer by name in the database."""
        customers = self.data_manager.get_customers()
        name_lower = name.lower()
        
        for customer in customers:
            if customer['name'].lower() == name_lower:
                return customer
        
        return None
    
    async def _create_new_customer(self, name: str) -> Optional[Dict]:
        """Create a new customer account in real-time."""
        try:
            customers_data = self.data_manager.load_json(self.data_manager.customers_file)
            customers = customers_data.get('customers', [])
            
            # Generate new customer ID
            existing_ids = [int(c['customer_id'].replace('CUST', '')) for c in customers if c['customer_id'].startswith('CUST')]
            new_id_num = max(existing_ids) + 1 if existing_ids else 1
            new_customer_id = f"CUST{new_id_num:03d}"
            
            # Create new customer record
            new_customer = {
                "customer_id": new_customer_id,
                "name": name,
                "email": f"{name.lower().replace(' ', '.')}@email.com",  # Placeholder email
                "phone": "+1-XXX-XXX-XXXX",  # Placeholder phone
                "address": "Address to be updated",
                "loyalty_tier": "Bronze",
                "total_orders": 0,
                "total_spent": 0.0,
                "join_date": datetime.now().strftime("%Y-%m-%d"),
                "cart": []  # Initialize empty cart
            }
            
            # Add to customers list
            customers.append(new_customer)
            customers_data['customers'] = customers
            
            # Save to file
            if self.data_manager.save_json(self.data_manager.customers_file, customers_data):
                logger.info(f"✅ Created new customer: {name} (ID: {new_customer_id})")
                return new_customer
            else:
                logger.error(f"❌ Failed to save new customer: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating customer {name}: {e}")
            return None
    
    async def _get_customer_from_context(self, conversation_context: str) -> Optional[str]:
        """Extract customer ID from conversation context."""
        import re
        customer_ids = re.findall(r'CUST\d+', conversation_context)
        return customer_ids[-1] if customer_ids else None
    
    async def handle_cart_management(self, query: str, conversation_context: str) -> str:
        """Handle cart operations like add to cart."""
        # Get customer ID from context
        customer_id = await self._get_customer_from_context(conversation_context)
        
        if not customer_id:
            context = "Customer asking about cart operations - need customer identification first"
            return await self._generate_natural_response(query, context)
        
        # Check if this is an "add to cart" request
        if any(word in query.lower() for word in ['add', 'put']):
            # Try to identify the product from recent conversation
            product = await self._identify_product_from_context(conversation_context)
            
            if product:
                # Add product to customer's cart
                success = await self._add_to_cart(customer_id, product['product_id'])
                
                if success:
                    context = f"Successfully added {product['name']} (${product['price']:.2f}) to cart - ask about continuing shopping or checkout"
                    return await self._generate_natural_response(query, context)
                else:
                    context = "Failed to add item to cart - ask customer to try again"
                    return await self._generate_natural_response(query, context)
            else:
                context = "Customer wants to add to cart but no product specified - ask which product"
                return await self._generate_natural_response(query, context)
        
        # Show cart contents
        elif 'cart' in query.lower():
            cart_items = await self._get_cart_contents(customer_id)
            if cart_items:
                return self._format_cart_contents(cart_items)
            else:
                context = "Customer's cart is empty - suggest browsing products"
                return await self._generate_natural_response(query, context)
        
        context = "Customer asking about cart operations - ask what they want to do"
        return await self._generate_natural_response(query, context)
    
    async def _generate_natural_response(self, user_query: str, context: str) -> str:
        """Generate natural response based on context - always returns a valid response."""
        try:
            # For now, use intelligent fallback responses that sound natural
            # This ensures the voice agent always responds appropriately
            return self._get_context_fallback(context, user_query)
                
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            return "How can I help you today?"

    
    def _get_context_fallback(self, context: str, user_query: str) -> str:
        """Get natural fallback response based on context with variation."""
        import random
        
        context_lower = context.lower()
        
        if "need customer identification" in context_lower:
            responses = ["What's your name?", "Who am I talking to?", "What should I call you?"]
            return random.choice(responses)
            
        elif "created new customer account" in context_lower:
            # Extract customer ID if available
            import re
            id_match = re.search(r'ID: (CUST\d+)', context)
            if id_match:
                customer_id = id_match.group(1)
                responses = [
                    f"Got you set up with account {customer_id}! What can I help you with?",
                    f"Perfect! Your account {customer_id} is ready. What are you looking for?",
                    f"All set with {customer_id}! How can I help?"
                ]
            else:
                responses = [
                    "Got you set up! What can I help you with?",
                    "You're all set! What are you looking for?",
                    "Perfect! How can I help you?"
                ]
            return random.choice(responses)
            
        elif "found existing customer" in context_lower:
            # Extract customer name if available
            import re
            name_match = re.search(r'customer: ([^(]+)', context)
            name = name_match.group(1).strip() if name_match else ""
            
            if name:
                responses = [
                    f"Hey {name}! Great to see you again. How can I help?",
                    f"Hi {name}! What can I do for you today?",
                    f"Good to see you again, {name}! What do you need?"
                ]
            else:
                responses = [
                    "Great to see you again! How can I help?",
                    "Welcome back! What can I do for you?",
                    "Nice to see you again! How can I help?"
                ]
            return random.choice(responses)
            
        elif "greeting" in context_lower:
            responses = [
                "Hi! How can I help you?",
                "Hello! What can I do for you?",
                "Hey there! How can I help?",
                "Hi! What do you need help with?"
            ]
            return random.choice(responses)
            
        elif "product" in context_lower and "looking for" in context_lower:
            responses = [
                "What product are you looking for?",
                "What can I help you find?",
                "What do you have in mind?",
                "Tell me what you're looking for!"
            ]
            return random.choice(responses)
            
        elif "order" in context_lower and "status" in context_lower:
            responses = [
                "I can help with your order. What's your order ID?",
                "Let me check your order. Do you have the order number?",
                "I'll look up your order. What's the order ID?"
            ]
            return random.choice(responses)
            
        elif "cart" in context_lower and "empty" in context_lower:
            responses = [
                "Your cart is empty. Want to browse some products?",
                "Nothing in your cart yet. What are you looking for?",
                "Cart's empty! Let me show you some great products."
            ]
            return random.choice(responses)
            
        else:
            responses = [
                "How can I help you today?",
                "What can I do for you?",
                "What do you need help with?",
                "How can I help?",
                "What can I help you find?"
            ]
            return random.choice(responses)

    async def _identify_product_from_context(self, conversation_context: str) -> Optional[Dict]:
        """Identify the most recently discussed product from conversation context."""
        # Look for product mentions in the conversation
        products = self.data_manager.get_products()
        
        # Check for specific product names or IDs in context
        context_lower = conversation_context.lower()
        
        # Look for recently mentioned products
        for product in products:
            if (product['name'].lower() in context_lower or 
                product['product_id'].lower() in context_lower):
                return product
        
        # Look for category-based matches
        if 'headphones' in context_lower or 'bluetooth' in context_lower:
            for product in products:
                if 'headphones' in product['name'].lower():
                    return product
        
        return None
    
    async def _add_to_cart(self, customer_id: str, product_id: str, quantity: int = 1) -> bool:
        """Add product to customer's cart in real-time."""
        try:
            customers_data = self.data_manager.load_json(self.data_manager.customers_file)
            customers = customers_data.get('customers', [])
            
            # Find the customer
            for customer in customers:
                if customer['customer_id'] == customer_id:
                    # Initialize cart if it doesn't exist
                    if 'cart' not in customer:
                        customer['cart'] = []
                    
                    # Check if product already in cart
                    for cart_item in customer['cart']:
                        if cart_item['product_id'] == product_id:
                            cart_item['quantity'] += quantity
                            break
                    else:
                        # Add new item to cart
                        customer['cart'].append({
                            'product_id': product_id,
                            'quantity': quantity,
                            'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    
                    # Save updated data
                    if self.data_manager.save_json(self.data_manager.customers_file, customers_data):
                        logger.info(f"✅ Added product {product_id} to cart for customer {customer_id}")
                        return True
                    break
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return False
    
    async def _get_cart_contents(self, customer_id: str) -> List[Dict]:
        """Get customer's cart contents."""
        try:
            customers = self.data_manager.get_customers()
            products = self.data_manager.get_products()
            
            for customer in customers:
                if customer['customer_id'] == customer_id:
                    cart = customer.get('cart', [])
                    cart_with_details = []
                    
                    for cart_item in cart:
                        # Find product details
                        for product in products:
                            if product['product_id'] == cart_item['product_id']:
                                cart_with_details.append({
                                    **cart_item,
                                    'name': product['name'],
                                    'price': product['price'],
                                    'total': product['price'] * cart_item['quantity']
                                })
                                break
                    
                    return cart_with_details
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting cart contents: {e}")
            return []
    
    def _format_cart_contents(self, cart_items: List[Dict]) -> str:
        """Format cart contents for display."""
        if not cart_items:
            return "Your cart is empty."
        
        cart_text = "🛒 Your Cart:\n"
        total = 0
        
        for item in cart_items:
            cart_text += f"• {item['name']} - Qty: {item['quantity']} - ${item['total']:.2f}\n"
            total += item['total']
        
        cart_text += f"\nTotal: ${total:.2f}"
        cart_text += "\n\nWould you like to proceed to checkout or continue shopping?"
        
        return cart_text
    
    async def handle_name_introduction(self, query: str, customer_name: str, conversation_context: str) -> str:
        """Handle customer name introductions with professional onboarding."""
        if customer_name:
            # Check if customer exists in database
            existing_customer = await self._find_customer_by_name(customer_name)
            
            if existing_customer:
                # Existing customer found
                logger.info(f"Found existing customer: {existing_customer['name']} (ID: {existing_customer['customer_id']})")
                
                # Store customer info in conversation metadata
                self.conversation_manager.add_message(
                    self.session_id,
                    "system",
                    f"Customer identified: {existing_customer['name']} (ID: {existing_customer['customer_id']})",
                    metadata={"customer_id": existing_customer['customer_id'], "customer_name": existing_customer['name']}
                )
                
                # Generate natural response about finding existing customer
                context = f"Found existing customer: {customer_name} (ID: {existing_customer['customer_id']}, {existing_customer['loyalty_tier']} tier)"
                return await self._generate_natural_response(query, context)
            else:
                # New customer - create account
                new_customer = await self._create_new_customer(customer_name)
                
                if new_customer:
                    logger.info(f"Created new customer: {new_customer['name']} (ID: {new_customer['customer_id']})")
                    
                    # Store customer info in conversation metadata
                    self.conversation_manager.add_message(
                        self.session_id,
                        "system",
                        f"New customer created: {new_customer['name']} (ID: {new_customer['customer_id']})",
                        metadata={"customer_id": new_customer['customer_id'], "customer_name": new_customer['name']}
                    )
                    
                    # Generate natural response about creating new customer
                    context = f"Created new customer account for {customer_name} (ID: {new_customer['customer_id']})"
                    return await self._generate_natural_response(query, context)
                else:
                    # Generate natural greeting for new customer (account creation failed)
                    context = f"Meeting new customer {customer_name} for the first time"
                    return await self._generate_natural_response(query, context)
        else:
            # No clear name provided
            context = "Need customer identification - no name provided"
            return await self._generate_natural_response(query, context)
    
    async def handle_customer_info_query(self, query: str) -> str:
        """Handle customer information queries."""
        context = "Customer asking for account information - need customer ID, email, or phone number"
        return await self._generate_natural_response(query, context)
    
    async def handle_product_query(self, query: str) -> str:
        """Handle product information queries with enhanced matching."""
        query_lower = query.lower()
        products = self.data_manager.get_products()
        
        # Enhanced product matching - check for product names, brands, and keywords
        matching_products = []
        
        for product in products:
            # Check product name
            product_words = product['name'].lower().split()
            if any(word in query_lower for word in product_words):
                matching_products.append(product)
                continue
            
            # Check brand
            if product['brand'].lower() in query_lower:
                matching_products.append(product)
                continue
            
            # Check product ID
            if product['product_id'].lower() in query_lower:
                matching_products.append(product)
                continue
            
            # Check tags
            if 'tags' in product:
                if any(tag.lower() in query_lower for tag in product['tags']):
                    matching_products.append(product)
        
        # Remove duplicates
        seen_ids = set()
        unique_products = []
        for product in matching_products:
            if product['product_id'] not in seen_ids:
                unique_products.append(product)
                seen_ids.add(product['product_id'])
        
        if unique_products:
            if len(unique_products) == 1:
                return self.format_product_info(unique_products[0])
            else:
                return f"I found {len(unique_products)} matching products:\n" + self.format_detailed_product_list(unique_products[:3])
        
        # If no direct matches, try category-based search
        return await self.handle_product_search_query(query)
    
    async def handle_order_query(self, query: str) -> str:
        """Handle order status and tracking queries with real data lookup."""
        query_lower = query.lower()
        
        # Look for order ID in the query
        import re
        order_id = None
        customer_id = None
        
        # Order ID patterns
        order_patterns = [
            r'ord\s*(\d+)',
            r'order\s*id\s*(\d+)',
            r'o\s*r\s*d\s*(\d+)',
            r'order\s*(\d+)'
        ]
        
        for pattern in order_patterns:
            match = re.search(pattern, query_lower)
            if match:
                order_num = match.group(1).zfill(3)  # Pad with zeros
                order_id = f"ORD{order_num}"
                break
        
        # Customer ID patterns
        cust_patterns = [
            r'cust\s*(\d+)',
            r'customer\s*id\s*(\d+)',
            r'c\s*u\s*s\s*t\s*(\d+)',
            r'customer\s*(\d+)'
        ]
        
        for pattern in cust_patterns:
            match = re.search(pattern, query_lower)
            if match:
                cust_num = match.group(1).zfill(3)  # Pad with zeros
                customer_id = f"CUST{cust_num}"
                break
        
        if order_id:
            return await self.get_order_details(order_id=order_id)
        elif customer_id:
            return await self.get_order_details(customer_id=customer_id)
        else:
            context = "Customer wants order status - need either order ID or customer ID to look up orders"
            return await self._generate_natural_response(query, context)
    
    async def get_order_details(self, order_id: str = None, customer_id: str = None) -> str:
        """Get real order details from JSON data."""
        orders = self.data_manager.get_orders()
        
        if order_id:
            order = next((o for o in orders if o["order_id"] == order_id), None)
            if order:
                return self.format_order_info(order)
            else:
                return f"I couldn't find order {order_id}. Please check the order ID and try again."
        
        elif customer_id:
            customer_orders = [order for order in orders if order["customer_id"] == customer_id]
            if customer_orders:
                # Sort by date (newest first)
                customer_orders.sort(key=lambda x: x['order_date'], reverse=True)
                
                if len(customer_orders) == 1:
                    return f"Here's your order:\n\n" + self.format_order_info(customer_orders[0])
                else:
                    return f"Here are your {len(customer_orders)} orders:\n\n" + self.format_multiple_orders(customer_orders)
            else:
                return f"No orders found for customer {customer_id}."
        
        return "Please provide either an order ID or customer ID to look up orders."
    
    async def handle_order_placement_query(self, query: str) -> str:
        """Handle order placement queries with real order processing."""
        query_lower = query.lower()
        
        # Check if they mentioned specific products
        products = self.data_manager.get_products()
        mentioned_products = []
        
        for product in products:
            # Check for product name mentions
            product_words = product['name'].lower().split()
            if any(word in query_lower for word in product_words):
                mentioned_products.append(product)
                continue
            
            # Check for product ID mentions (handle "o r d" format)
            product_id_formatted = product['product_id'].lower().replace('prod', 'p r o d')
            if product_id_formatted in query_lower or product['product_id'].lower() in query_lower:
                mentioned_products.append(product)
                continue
        
        # Remove duplicates
        unique_products = []
        seen_ids = set()
        for product in mentioned_products:
            if product['product_id'] not in seen_ids:
                unique_products.append(product)
                seen_ids.add(product['product_id'])
        
        if unique_products:
            if len(unique_products) == 1:
                product = unique_products[0]
                # Try to place order for this product
                return await self.process_order_placement(product, query)
            else:
                # Multiple products mentioned
                product_list = "\n".join([f"• {p['name']} - ${p['price']:.2f}" for p in unique_products[:3]])
                return (f"I found {len(unique_products)} products you mentioned:\n{product_list}\n\n"
                        "Which specific product would you like to order? "
                        "Also, I'll need your customer ID to process the order.")
        
        # No specific products mentioned
        context = "Customer wants to place an order - need product name, customer ID, and quantity"
        return await self._generate_natural_response(query, context)
    
    async def process_order_placement(self, product: Dict, query: str) -> str:
        """Process actual order placement with real JSON updates."""
        query_lower = query.lower()
        
        # Extract customer ID from query
        customer_id = None
        customers = self.data_manager.get_customers()
        
        # Look for customer ID patterns
        import re
        cust_patterns = [
            r'cust\s*(\d+)',
            r'customer\s*id\s*(\d+)',
            r'c\s*u\s*s\s*t\s*(\d+)',
            r'customer\s*(\d+)'
        ]
        
        for pattern in cust_patterns:
            match = re.search(pattern, query_lower)
            if match:
                cust_num = match.group(1).zfill(3)  # Pad with zeros
                customer_id = f"CUST{cust_num}"
                break
        
        # Check if customer exists
        customer = None
        if customer_id:
            customer = next((c for c in customers if c['customer_id'] == customer_id), None)
        
        if not customer:
            return (f"I found the product: {product['name']} - ${product['price']:.2f}\n\n"
                    "To place this order, I need your customer ID. "
                    "Please provide your customer ID (like CUST001, CUST002, etc.) "
                    "If you're a new customer, please say 'I'm a new customer' and I'll help you get set up.")
        
        # Extract quantity (default to 1)
        quantity = 1
        quantity_patterns = [
            r'(\d+)\s*(?:piece|pieces|item|items|unit|units)?',
            r'(?:quantity|qty)\s*(\d+)',
            r'(\d+)\s*of'
        ]
        
        for pattern in quantity_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                try:
                    quantity = int(matches[0])
                    break
                except ValueError:
                    continue
        
        # Check stock availability
        if product['stock_quantity'] < quantity:
            return (f"Sorry, we only have {product['stock_quantity']} units of {product['name']} in stock. "
                    f"You requested {quantity} units. "
                    "Would you like to order the available quantity instead?")
        
        # Generate new order ID
        existing_orders = self.data_manager.get_orders()
        order_number = len(existing_orders) + 1
        order_id = f"ORD{order_number:03d}"
        
        # Calculate totals
        unit_price = product['price']
        total_price = unit_price * quantity
        
        # Create order
        new_order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": datetime.now().isoformat()[:10],
            "status": "pending",
            "total_amount": round(total_price, 2),
            "shipping_address": customer["address"],
            "items": [{
                "product_id": product["product_id"],
                "product_name": product["name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price
            }],
            "payment_method": "credit_card",  # Default payment method
            "tracking_number": None,
            "estimated_delivery": (datetime.now() + timedelta(days=5)).isoformat()[:10],
            "actual_delivery": None
        }
        
        # Save order to JSON
        if self.data_manager.add_order(new_order):
            # Update product stock
            self.update_product_stock(product['product_id'], quantity)
            
            # Store order metadata in conversation history
            order_metadata = {
                "action": "order_placed",
                "order_id": order_id,
                "customer_id": customer_id,
                "product_id": product['product_id'],
                "product_name": product['name'],
                "quantity": quantity,
                "total_amount": total_price
            }
            
            self.conversation_manager.add_message(
                self.session_id,
                "system",
                f"Order {order_id} placed successfully for {customer['name']}",
                metadata=order_metadata
            )
            
            return (f"🎉 Order placed successfully!\n\n"
                    f"Order ID: {order_id}\n"
                    f"Product: {product['name']}\n"
                    f"Quantity: {quantity}\n"
                    f"Unit Price: ${unit_price:.2f}\n"
                    f"Total Amount: ${total_price:.2f}\n"
                    f"Customer: {customer['name']}\n"
                    f"Estimated Delivery: {new_order['estimated_delivery']}\n\n"
                    f"Your order has been added to our system and will be processed shortly. "
                    f"You can track your order using Order ID: {order_id}")
        else:
            return "Sorry, there was an error processing your order. Please try again."
    
    def update_product_stock(self, product_id: str, quantity_ordered: int) -> bool:
        """Update product stock after order placement."""
        try:
            data = self.data_manager.load_json(self.data_manager.products_file)
            products = data.get('products', [])
            
            for product in products:
                if product['product_id'] == product_id:
                    product['stock_quantity'] -= quantity_ordered
                    break
            
            return self.data_manager.save_json(self.data_manager.products_file, data)
        except Exception as e:
            logger.error(f"Error updating product stock: {e}")
            return False
    
    async def handle_cancellation_query(self, query: str) -> str:
        """Handle order cancellation queries with real processing."""
        query_lower = query.lower()
        
        # Look for order ID in the query
        import re
        order_id = None
        
        # Order ID patterns
        order_patterns = [
            r'ord\s*(\d+)',
            r'order\s*id\s*(\d+)',
            r'o\s*r\s*d\s*(\d+)',
            r'order\s*(\d+)'
        ]
        
        for pattern in order_patterns:
            match = re.search(pattern, query_lower)
            if match:
                order_num = match.group(1).zfill(3)  # Pad with zeros
                order_id = f"ORD{order_num}"
                break
        
        if order_id:
            return await self.process_order_cancellation(order_id)
        else:
            context = "Customer wants to cancel order - need order ID to proceed, explain cancellation policy"
            return await self._generate_natural_response(query, context)
    
    async def process_order_cancellation(self, order_id: str) -> str:
        """Process actual order cancellation with real JSON updates."""
        orders = self.data_manager.get_orders()
        order = next((o for o in orders if o["order_id"] == order_id), None)
        
        if not order:
            return f"I couldn't find order {order_id}. Please check the order ID and try again."
        
        # Check if order can be cancelled
        if order["status"] in ["shipped", "delivered"]:
            return (f"Sorry, order {order_id} cannot be cancelled because it has already been {order['status']}. "
                    f"For returns on delivered items, please contact our returns department.")
        
        if order["status"] == "cancelled":
            return f"Order {order_id} has already been cancelled."
        
        # Cancel the order
        if self.data_manager.cancel_order(order_id):
            # Restore product stock
            for item in order['items']:
                self.restore_product_stock(item['product_id'], item['quantity'])
            
            # Store cancellation metadata in conversation history
            cancel_metadata = {
                "action": "order_cancelled",
                "order_id": order_id,
                "customer_id": order['customer_id'],
                "refund_amount": order['total_amount'],
                "cancelled_items": [item['product_name'] for item in order['items']]
            }
            
            self.conversation_manager.add_message(
                self.session_id,
                "system",
                f"Order {order_id} cancelled successfully, refund ${order['total_amount']:.2f}",
                metadata=cancel_metadata
            )
            
            return (f"✅ Order {order_id} has been successfully cancelled!\n\n"
                    f"Cancelled Order Details:\n"
                    f"Product: {order['items'][0]['product_name']}\n"
                    f"Quantity: {order['items'][0]['quantity']}\n"
                    f"Amount: ${order['total_amount']:.2f}\n\n"
                    f"Your refund of ${order['total_amount']:.2f} will be processed within 3-5 business days. "
                    f"The product stock has been restored to our inventory. "
                    f"Is there anything else I can help you with?")
        else:
            return f"There was an error cancelling order {order_id}. Please try again or contact support."
    
    def restore_product_stock(self, product_id: str, quantity_to_restore: int) -> bool:
        """Restore product stock after order cancellation."""
        try:
            data = self.data_manager.load_json(self.data_manager.products_file)
            products = data.get('products', [])
            
            for product in products:
                if product['product_id'] == product_id:
                    product['stock_quantity'] += quantity_to_restore
                    break
            
            return self.data_manager.save_json(self.data_manager.products_file, data)
        except Exception as e:
            logger.error(f"Error restoring product stock: {e}")
            return False
    
    async def handle_product_search_query(self, query: str) -> str:
        """Handle product search queries with enhanced category support."""
        query_lower = query.lower()
        
        # Enhanced category detection with more keywords
        category_keywords = {
            'electronics': ['electronics', 'electronic', 'tech', 'gadget', 'device', 'headphones', 'watch', 'keyboard', 'computer'],
            'clothing': ['clothing', 'clothes', 'shirt', 'dress', 'wear', 'fashion', 'apparel'],
            'home': ['home', 'house', 'kitchen', 'coffee', 'maker', 'appliance'],
            'books': ['book', 'novel', 'read', 'story', 'literature'],
            'sports': ['sports', 'fitness', 'exercise', 'yoga', 'workout', 'gym'],
            'beauty': ['beauty', 'cosmetic', 'skincare', 'cream', 'makeup']
        }
        
        # Find mentioned categories
        mentioned_categories = []
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                mentioned_categories.append(category)
        
        # Remove duplicates and get the first match
        mentioned_categories = list(set(mentioned_categories))
        
        if mentioned_categories:
            products = self.data_manager.get_products()
            
            # If multiple categories, show all
            if len(mentioned_categories) > 1:
                all_products = []
                for category in mentioned_categories:
                    category_products = [p for p in products if p['category'] == category]
                    all_products.extend(category_products)
                
                if all_products:
                    return f"Here are products from {', '.join(mentioned_categories)}:\n" + self.format_detailed_product_list(all_products[:5])
            else:
                category = mentioned_categories[0]
                category_products = [p for p in products if p['category'] == category]
                
                if category_products:
                    return f"Here are our {category} products:\n" + self.format_detailed_product_list(category_products)
                else:
                    return f"I don't have any {category} products available right now."
        
        # Check for buying intent
        if any(word in query_lower for word in ['buy', 'purchase', 'want', 'need', 'looking for']):
            context = "Customer showing buying intent - show available product categories and ask what they're interested in"
            return await self._generate_natural_response(query, context)
        
        context = "Customer asking about products - explain available categories and ask what they're looking for"
        return await self._generate_natural_response(query, context)
    
    async def handle_general_query(self, query: str) -> str:
        """Handle general support queries with context awareness."""
        query_lower = query.lower()
        
        # Check if this is a greeting/introduction (avoid repetitive welcomes)
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            # Generate natural greeting response
            context = "Customer greeting - respond naturally and ask how to help"
            return await self._generate_natural_response(query, context)
        
        elif any(word in query_lower for word in ['return', 'refund']):
            context = "Customer asking about returns/refunds - explain policy and offer help with specific return"
            return await self._generate_natural_response(query, context)
        
        elif any(word in query_lower for word in ['shipping', 'delivery']):
            context = "Customer asking about shipping/delivery - explain options and offer to track specific order"
            return await self._generate_natural_response(query, context)
        
        elif any(word in query_lower for word in ['warranty', 'guarantee']):
            context = "Customer asking about warranty - explain typical warranty terms and offer specific product warranty info"
            return await self._generate_natural_response(query, context)
        
        elif any(word in query_lower for word in ['payment', 'credit card', 'paypal']):
            context = "Customer asking about payment methods - explain accepted payment options and offer help with payment issues"
            return await self._generate_natural_response(query, context)
        
        else:
            # Generate natural response for unclear queries
            context = "Customer query unclear - ask naturally what they need help with"
            return await self._generate_natural_response(query, context)
    
    # Formatting Helper Methods
    def format_product_info(self, product: Dict) -> str:
        """Format product information for display."""
        return (f"{product['name']} - ${product['price']:.2f}\n"
                f"Brand: {product['brand']} | Category: {product['category']}\n"
                f"Rating: {product['rating']}/5 ({product['reviews_count']} reviews)\n"
                f"Stock: {product['stock_quantity']} available\n"
                f"{product['description']}")
    
    def format_product_list(self, products: List[Dict]) -> str:
        """Format a list of products for display."""
        products_text = []
        for product in products:
            products_text.append(f"• {product['name']} - ${product['price']:.2f} (Rating: {product['rating']}/5)")
        
        return "\n".join(products_text)
    
    def format_detailed_product_list(self, products: List[Dict]) -> str:
        """Format a detailed list of products with more information."""
        if not products:
            return "No products found."
            
        products_text = []
        for i, product in enumerate(products, 1):
            stock_status = "In Stock" if product['stock_quantity'] > 0 else "Out of Stock"
            products_text.append(
                f"{i}. {product['name']} - ${product['price']:.2f}\n"
                f"   Brand: {product['brand']} | Rating: {product['rating']}/5 | {stock_status}\n"
                f"   {product['description'][:100]}{'...' if len(product['description']) > 100 else ''}"
            )
        
        return "\n\n".join(products_text)
    
    def format_customer_info(self, customer: Dict) -> str:
        """Format customer information for display."""
        return (f"Customer: {customer['name']} (ID: {customer['customer_id']})\n"
                f"Email: {customer['email']} | Phone: {customer['phone']}\n"
                f"Loyalty Tier: {customer['loyalty_tier']}\n"
                f"Total Orders: {customer['total_orders']} | Total Spent: ${customer['total_spent']:.2f}")
    
    def format_order_info(self, order: Dict) -> str:
        """Format order information for display."""
        items_text = ", ".join([f"{item['product_name']} (x{item['quantity']})" for item in order['items']])
        
        return (f"Order {order['order_id']} - {order['status'].title()}\n"
                f"Date: {order['order_date']} | Total: ${order['total_amount']:.2f}\n"
                f"Items: {items_text}\n"
                f"Estimated Delivery: {order['estimated_delivery']}")

    async def on_user_start_speaking(self) -> None:
        """Called when user starts speaking - SMOOTH HUMAN-LIKE INTERRUPTION."""
        logger.info("🎤 Customer interrupting - listening now!")
        
        # Increment interruption counter for natural acknowledgment (but limit it)
        if self.conversation_flow['interruption_count'] < 2:  # Prevent excessive acknowledgments
            self.conversation_flow['interruption_count'] += 1
        
        # Immediately stop current speech with minimal delay
        if self.is_speaking:
            logger.info("⚡ Stopping speech smoothly for customer")
            if self._agent_session:
                await self._agent_session.interrupt()  # Make it async for faster response
            self.is_speaking = False
            
        # Cancel current response generation gracefully
        if self.current_response_task and not self.current_response_task.done():
            self.current_response_task.cancel()
            logger.info("🚫 Gracefully cancelled current response")
        
    async def on_user_stop_speaking(self) -> None:
        """Called when user stops speaking - ready to respond."""
        logger.info("🔇 Customer stopped speaking - ready to process")
    
    async def on_agent_start_speaking(self) -> None:
        """Called when agent starts speaking."""
        logger.info("🗣️ Agent started speaking")
        self.is_speaking = True
        
    async def on_agent_stop_speaking(self) -> None:
        """Called when agent stops speaking."""
        logger.info("🔇 Agent finished speaking")
        self.is_speaking = False


async def entrypoint(ctx: agents.JobContext):
    """
    Main entrypoint for the customer support agent.
    """
    logger.info("Starting Customer Support Agent...")
    
    # Connect to the room first with AUDIO subscription
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    # Create the customer support agent
    agent = CustomerSupportAgent()
    
    # Configure the agent session with optimal settings
    session = AgentSession(
        # Speech-to-Text: Deepgram for accurate transcription
        stt=deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY")),
        
        # Large Language Model: OpenAI GPT-4 for intelligent responses
        llm=openai.LLM(api_key=os.getenv("OPENAI_API_KEY")),
        
        # Text-to-Speech: Deepgram for natural voice (female Asian accent)
        tts=deepgram.TTS(
            model="aura-luna-en",  # Female voice with warm, professional tone
            api_key=os.getenv("DEEPGRAM_API_KEY")
        ),
        
        # Voice Activity Detection: Silero with optimized settings for performance
        vad=silero.VAD.load(
            min_speech_duration=0.15,  # Even faster speech detection (150ms)
            min_silence_duration=0.3,  # Much shorter silence detection for responsiveness (300ms)
        ),
        
        # Turn Detection: Use manual with custom processing for reliability
        turn_detection="manual",
    )

    # Store session reference in agent for interruption handling
    agent._agent_session = session
    
    # Start the session (audio output is handled automatically by AgentSession)
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    # Give an immediate voice greeting to test TTS
    logger.info("🔊 Testing voice output with initial greeting...")
    await asyncio.sleep(1)  # Let session initialize
    await session.say("Hello! I'm your customer support agent. I can hear you and I'm ready to help. Please speak to me now!")
    
    # Smart turn processing that actually works
    async def smart_turn_processing():
        """Smart turn processing that ensures queries get processed."""
        await asyncio.sleep(2)  # Wait for session to be ready
        last_transcript_time = 0
        
        while True:
            try:
                # Only commit turns when not processing and not speaking
                if not agent.processing_query and not agent.is_speaking:
                    session.commit_user_turn()
                    
                await asyncio.sleep(0.3)  # Check frequently for responsiveness
            except Exception as e:
                logger.debug(f"Smart turn processing: {e}")
                await asyncio.sleep(0.3)
    
    # Start smart turn processing
    asyncio.create_task(smart_turn_processing())
    
    logger.info("✅ Customer Support Agent ready with intelligent query processing!")

    # Event handlers for connection management
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Customer connected: {participant.identity}")
    
    @ctx.room.on("participant_disconnected") 
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Customer disconnected: {participant.identity}")

    # Keep the session running
    try:
        await asyncio.Future()  # Run forever
    finally:
        logger.info("Customer Support Agent shutting down...")
        if hasattr(session, 'acclose'):
            await session.acclose()
        elif hasattr(session, 'close'):
            await session.close()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
