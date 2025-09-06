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
        self.customers_file = "data/customers.json"
        self.products_file = "data/products.json"
        self.orders_file = "data/orders.json"
    
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
        
        # Initialize session ID - use a default for now since session might not be available yet
        self.session_id = self.conversation_manager.generate_session_id("default_user")
        
        # Check if this is a returning customer
        session_info = self.conversation_manager.get_session_info(self.session_id)
        
        if session_info.get('message_count', 0) > 0:
            # Returning customer
            logger.info(f"Returning customer session: {self.session_id}")
            greeting = ("Welcome back! I'm Sarah from customer support. "
                       "I have our previous conversation history, so I can pick up right where we left off. "
                       "How can I assist you today?")
        else:
            # New customer
            greeting = ("Hello! I'm Sarah, your customer support specialist. "
                       "I'm here to help with any questions about products, orders, or account information. "
                       "What can I assist you with today?")
        
        # Add system message to conversation history
        self.conversation_manager.add_message(
            self.session_id, 
            "system", 
            f"Session started. Agent greeting: {greeting}"
        )
        
        # Use the session from the agent session if available
        if hasattr(self, '_agent_session') and self._agent_session:
            await self._agent_session.say(greeting)
        else:
            logger.warning("Session not available for greeting")

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
            if hasattr(self, '_agent_session') and self._agent_session:
                await self._agent_session.say(response)
            else:
                logger.warning("Session not available for response")
            
        except asyncio.CancelledError:
            logger.info("🚫 Response cancelled due to interruption")
        except Exception as e:
            logger.error(f"Error in human flow processing: {e}")
            error_response = "I apologize, could you repeat that?"
            if hasattr(self, '_agent_session') and self._agent_session:
                await self._agent_session.say(error_response)
            else:
                logger.warning("Session not available for error response")
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
            if hasattr(self, '_agent_session') and self._agent_session:
                await self._agent_session.say(response)
            else:
                logger.warning("Session not available for response")
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            error_response = "I apologize, but I encountered an error. Could you please repeat your question?"
            self.conversation_manager.add_message(self.session_id, "assistant", error_response)
            if hasattr(self, '_agent_session') and self._agent_session:
                await self._agent_session.say(error_response)
            else:
                logger.warning("Session not available for error response")
        finally:
            self.processing_query = False
    
    async def process_customer_query(self, query: str, conversation_context: str = "") -> str:
        """Process customer queries using LLM with intelligent context and data access."""
        try:
            logger.info(f"🔄 Processing query: {query[:50]}...")
            
            # For now, use super simple approach to test LLM
            simple_prompt = f"You are Sarah, a customer support agent. Respond helpfully to: {query}"
            
            # Try direct LLM call
            if hasattr(self, '_agent_session') and self._agent_session and hasattr(self._agent_session, 'llm'):
                try:
                    llm = self._agent_session.llm
                    response = await llm.agenerate(simple_prompt)
                    
                    if response and hasattr(response, 'choices') and len(response.choices) > 0:
                        content = response.choices[0].message.content.strip()
                        logger.info(f"✅ Simple LLM response: {content[:50]}...")
                        return content
                    else:
                        logger.error("No valid response from LLM")
                        return "Hello! I'm Sarah from customer support. How can I help you today?"
                        
                except Exception as llm_error:
                    logger.error(f"LLM error: {llm_error}")
                    return "Hello! I'm Sarah from customer support. How can I help you today?"
            else:
                logger.error("LLM not available")
                return "Hello! I'm Sarah from customer support. How can I help you today?"
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "Hello! I'm Sarah from customer support. How can I help you today?"
    
    async def _gather_context_data(self, query: str, conversation_context: str, customer_name: str = None) -> Dict:
        """Gather all relevant data for the query."""
        context_data = {
            "query_type": self._determine_query_type(query),
            "customer_data": None,
            "product_data": None,
            "order_data": None,
            "available_actions": []
        }
        
        # Get customer data if name is provided or found in context
        if customer_name:
            context_data["customer_data"] = await self._find_customer_by_name(customer_name)
            if not context_data["customer_data"]:
                # Create new customer
                context_data["customer_data"] = await self._create_new_customer(customer_name)
                context_data["new_customer_created"] = True
        else:
            # Try to extract customer ID from context
            customer_id = await self._get_customer_from_context(conversation_context)
            if customer_id:
                customers = self.data_manager.get_customers()
                context_data["customer_data"] = next((c for c in customers if c['customer_id'] == customer_id), None)
        
        # Get product data if query mentions products
        if any(word in query.lower() for word in ['product', 'item', 'buy', 'purchase', 'headphones', 'watch', 'keyboard']):
            context_data["product_data"] = self._find_relevant_products(query)
        
        # Get order data if query mentions orders
        if any(word in query.lower() for word in ['order', 'tracking', 'delivery', 'cancel']):
            context_data["order_data"] = self._find_relevant_orders(query, context_data.get("customer_data"))
        
        return context_data
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of query to help LLM understand intent."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['my name is', 'i am', 'call me', 'i\'m']):
            return "name_introduction"
        elif any(word in query_lower for word in ['buy', 'purchase', 'want to buy', 'place order']):
            return "order_placement"
        elif any(word in query_lower for word in ['order status', 'tracking', 'delivery', 'my order']):
            return "order_inquiry"
        elif any(word in query_lower for word in ['cancel', 'refund', 'return']):
            return "cancellation"
        elif any(word in query_lower for word in ['product', 'item', 'what is', 'tell me about']):
            return "product_inquiry"
        elif any(word in query_lower for word in ['cart', 'add to cart']):
            return "cart_management"
        elif any(word in query_lower for word in ['hello', 'hi', 'hey']):
            return "greeting"
        else:
            return "general_inquiry"
    
    def _find_relevant_products(self, query: str) -> List[Dict]:
        """Find products relevant to the query."""
        products = self.data_manager.get_products()
        query_lower = query.lower()
        relevant_products = []
        
        for product in products:
            # Check product name, brand, category
            if (product['name'].lower() in query_lower or 
                product['brand'].lower() in query_lower or
                product['category'].lower() in query_lower or
                any(word in query_lower for word in product['name'].lower().split())):
                relevant_products.append(product)
        
        return relevant_products[:5]  # Limit to 5 most relevant
    
    def _find_relevant_orders(self, query: str, customer_data: Dict = None) -> List[Dict]:
        """Find orders relevant to the query."""
        orders = self.data_manager.get_orders()
        relevant_orders = []
        
        # Extract order ID from query
        import re
        order_id_match = re.search(r'ord\s*(\d+)', query.lower())
        if order_id_match:
            order_id = f"ORD{order_id_match.group(1).zfill(3)}"
            order = next((o for o in orders if o['order_id'] == order_id), None)
            if order:
                relevant_orders.append(order)
        
        # If customer data available, get their recent orders
        elif customer_data:
            customer_orders = [o for o in orders if o['customer_id'] == customer_data['customer_id']]
            relevant_orders.extend(customer_orders[-3:])  # Last 3 orders
        
        return relevant_orders
    
    async def _generate_llm_response_with_data(self, query: str, context_data: Dict, conversation_context: str) -> str:
        """Generate LLM response with all available data and context."""
        try:
            logger.info(f"🤖 Generating LLM response for query: {query[:50]}...")
            
            # Build very simple system prompt for fast processing
            system_prompt = "You are Sarah, a friendly customer support agent."
            
            # Add only essential customer info if available
            if context_data.get('customer_data'):
                customer = context_data['customer_data']
                system_prompt += f" Customer: {customer['name']} (ID: {customer['customer_id']})."
            
            # Add basic product info if available
            if context_data.get('product_data') and len(context_data['product_data']) > 0:
                product = context_data['product_data'][0]
                system_prompt += f" Product discussed: {product['name']} (${product['price']:.2f})."
            
            system_prompt += " Be helpful and concise."
            
            # Get LLM response with debugging
            logger.info(f"🔄 Calling LLM with system prompt length: {len(system_prompt)}")
            response = await self._get_llm_response(system_prompt, query)
            logger.info(f"✅ LLM response received: {response[:100]}...")
            
            # Handle specific actions based on query type
            if context_data['query_type'] == 'order_placement' and context_data.get('customer_data') and context_data.get('product_data'):
                # If we have enough info, actually place the order
                response = await self._handle_order_placement_with_llm(query, context_data, response)
            elif context_data['query_type'] == 'cancellation' and context_data.get('order_data'):
                # If we have order info, handle cancellation
                response = await self._handle_cancellation_with_llm(query, context_data, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating LLM response with data: {e}")
            return "I'm here to help! What can I do for you?"
    
    async def _handle_order_placement_with_llm(self, query: str, context_data: Dict, llm_response: str) -> str:
        """Handle actual order placement when LLM indicates it should happen."""
        try:
            # Check if we have enough information
            customer = context_data['customer_data']
            products = context_data['product_data']
            
            if not customer or not products:
                return llm_response
            
            # Extract quantity from query (default to 1)
            import re
            quantity = 1
            quantity_match = re.search(r'(\d+)', query.lower())
            if quantity_match:
                quantity = int(quantity_match.group(1))
            
            # Use the first relevant product
            product = products[0]
            
            # Check if LLM response indicates we should place the order
            if any(phrase in llm_response.lower() for phrase in ['placing your order', 'order placed', 'processing your order']):
                # Actually place the order
                order_result = await self.process_order_placement(product, f"{query} customer id {customer['customer_id']}")
                return order_result
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Error handling order placement with LLM: {e}")
            return llm_response
    
    async def _handle_cancellation_with_llm(self, query: str, context_data: Dict, llm_response: str) -> str:
        """Handle actual order cancellation when LLM indicates it should happen."""
        try:
            orders = context_data['order_data']
            if not orders:
                return llm_response
            
            # Check if LLM response indicates we should cancel the order
            if any(phrase in llm_response.lower() for phrase in ['cancelling your order', 'order cancelled', 'processing cancellation']):
                # Actually cancel the order
                order = orders[0]  # Use first relevant order
                cancel_result = await self.process_order_cancellation(order['order_id'])
                return cancel_result
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Error handling cancellation with LLM: {e}")
            return llm_response
    
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
        """Generate natural response using LLM based on context."""
        try:
            # Create a comprehensive prompt for the LLM
            system_context = f"""
            You are Sarah, a professional customer support specialist. 
            
            CONTEXT: {context}
            
            Based on this context and the customer's query, provide a natural, helpful response.
            Keep it conversational, warm, and professional. Ask for specific information you need.
            Be concise but thorough - typically 1-3 sentences unless detailed info is needed.
            """
            
            # Use the LLM to generate a natural response
            response = await self._get_llm_response(system_context, user_query)
            return response
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Simple fallback without predefined responses
            return "I'm here to help! What can I do for you?"

    async def _get_llm_response(self, system_context: str, user_query: str) -> str:
        """Get response from LLM with proper error handling."""
        try:
            # Get the LLM from the session
            if hasattr(self, '_agent_session') and self._agent_session and hasattr(self._agent_session, 'llm'):
                llm = self._agent_session.llm
                
                # Create the chat completion request with simplified approach
                try:
                    # Use a simpler approach - combine system and user message
                    combined_prompt = f"{system_context}\n\nUser: {user_query}\nAssistant:"
                    
                    # Try direct LLM call without complex message structure
                    response = await llm.agenerate(combined_prompt)
                    
                    if response and hasattr(response, 'choices') and len(response.choices) > 0:
                        content = response.choices[0].message.content.strip()
                        logger.info(f"✅ LLM responded successfully: {content[:50]}...")
                        return content
                    else:
                        logger.error("Empty or invalid response from LLM")
                        return "I understand you're asking something. Could you please rephrase that?"
                        
                except Exception as llm_error:
                    logger.error(f"LLM chat error: {llm_error}")
                    # Try even simpler approach
                    try:
                        simple_response = await llm.agenerate(f"You are Sarah, a customer support agent. Respond to: {user_query}")
                        if simple_response and hasattr(simple_response, 'choices') and len(simple_response.choices) > 0:
                            return simple_response.choices[0].message.content.strip()
                    except Exception as e2:
                        logger.error(f"Simple LLM call also failed: {e2}")
                    
                    return "I'm having trouble processing that right now. Could you try asking in a different way?"
            else:
                logger.warning("LLM not available, using fallback")
                return "I'm here to help! What can I do for you?"
                
        except Exception as e:
            logger.error(f"Error in LLM response: {e}")
            return "I'm here to help! What can I do for you?"
    
    
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
                try:
                    self._agent_session.interrupt()  # This is synchronous
                except Exception as e:
                    logger.error(f"Error interrupting session: {e}")
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
    
    # Connect to the room with optimized settings for stability
    await ctx.connect(
        auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY,
        # Add connection options for better stability
    )
    
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
        
        # Voice Activity Detection: Optimized Silero with minimal processing
        vad=silero.VAD.load(
            min_speech_duration=0.1,   # Ultra-fast speech detection (100ms)
            min_silence_duration=0.2,  # Ultra-short silence detection (200ms)
            max_buffered_speech=3.0,   # Limit buffer to reduce processing load
        ),
        
        # Turn Detection: Use server VAD for better performance
        turn_detection="server_vad",
    )

    # Store session reference in agent for interruption handling
    agent._agent_session = session
    
    # Start the session with optimized audio settings
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # Disable noise cancellation to reduce processing overhead
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    # Give an immediate voice greeting to test TTS
    logger.info("🔊 Testing voice output with initial greeting...")
    await asyncio.sleep(1)  # Let session initialize

    # Simplified turn processing for better performance
    async def simple_turn_processing():
        """Lightweight turn processing for optimal performance."""
        await asyncio.sleep(1)  # Wait for session to be ready
        
        while True:
            try:
                # Simple turn commit without complex logic
                if not agent.processing_query:
                    session.commit_user_turn()
                    
                await asyncio.sleep(0.5)  # Less frequent checks to reduce overhead
            except Exception as e:
                logger.debug(f"Turn processing: {e}")
                await asyncio.sleep(0.5)
    
    # Start simplified turn processing
    asyncio.create_task(simple_turn_processing())
    
    logger.info("✅ Customer Support Agent ready with intelligent query processing!")

    # Event handlers for connection management
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Customer connected: {participant.identity}")
    
    @ctx.room.on("participant_disconnected") 
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Customer disconnected: {participant.identity}")

    # Keep the session running with proper error handling
    try:
        logger.info("✅ Customer Support Agent ready and running!")
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Agent error: {e}")
    finally:
        logger.info("Customer Support Agent shutting down...")
        try:
            if hasattr(session, 'acclose'):
                await session.acclose()
            elif hasattr(session, 'close'):
                await session.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
