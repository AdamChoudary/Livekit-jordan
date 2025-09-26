import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import google.generativeai as genai

from conversation_manager import ConversationManager
from system_prompt import build_context_prompt

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


class TextChatAgent:
    """
    Text-only Customer Support Agent with intelligent query processing using Google Gemini.
    Handles customer inquiries, product information, and order management via text chat.
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
        
        # Initialize Gemini AI
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("✅ Gemini AI initialized successfully")
        else:
            self.model = None
            logger.warning("⚠️ GEMINI_API_KEY not found. Using rule-based responses only.")
        
        # Chat-specific settings
        self.last_processed_input = ""
        self.processing_query = False
        self.conversation_flow = {
            'last_topic': None,
            'context': {}
        }
        
        logger.info("TextChatAgent initialized successfully")

    async def start_chat_session(self, user_id: str = None) -> str:
        """Start a new chat session and return greeting."""
        # Generate session ID
        self.session_id = self.conversation_manager.generate_session_id(user_id or "text_user")
        
        # Check if this is a returning customer
        session_info = self.conversation_manager.get_session_info(self.session_id)
        
        if session_info.get('message_count', 0) > 0:
            # Returning customer
            logger.info(f"Returning customer session: {self.session_id}")
            greeting = "Welcome back! How can I help you today?"
        else:
            # New customer
            greeting = "Hello! I'm your AI customer support assistant. How can I help you today?"
        
        # Add system message to conversation history
        self.conversation_manager.add_message(
            self.session_id, 
            "system", 
            f"Session started. Agent greeting: {greeting}"
        )
        
        return greeting

    async def process_message(self, user_message: str) -> str:
        """Process user message and return response."""
        if not user_message or not user_message.strip():
            return "I didn't receive your message. Please try again."
        
        user_text = user_message.strip()
        if user_text == self.last_processed_input:
            return "You just sent the same message. Is there anything else I can help you with?"
        
        self.last_processed_input = user_text
        logger.info(f"💬 User: {user_text}")
        
        try:
            self.processing_query = True
            
            # Add user message to conversation history
            self.conversation_manager.add_message(self.session_id, "user", user_text)
            
            # Get conversation context
            conversation_context = self.conversation_manager.get_conversation_context(self.session_id)
            
            # Process the query
            response = await self.process_customer_query(user_text, conversation_context)
            
            # Add agent response to conversation history
            self.conversation_manager.add_message(self.session_id, "assistant", response)
            
            logger.info(f"🤖 Agent: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "I apologize, but I encountered an error. Could you please try again?"
            self.conversation_manager.add_message(self.session_id, "assistant", error_response)
            return error_response
        finally:
            self.processing_query = False

    async def process_customer_query(self, query: str, conversation_context: str = "") -> str:
        """Process customer queries using intelligent context and data access."""
        try:
            logger.info(f"🔄 Processing query: {query[:50]}...")
            
            # Gather context data
            context_data = await self._gather_context_data(query, conversation_context)
            
            # Generate response based on query type
            response = await self._generate_intelligent_response(query, context_data, conversation_context)
            
            return response
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "I'm here to help! What can I do for you?"

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
        """Determine the type of query to help understand intent."""
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

    async def _get_customer_from_context(self, conversation_context: str) -> Optional[str]:
        """Extract customer ID from conversation context."""
        import re
        customer_ids = re.findall(r'CUST\d+', conversation_context)
        return customer_ids[-1] if customer_ids else None

    async def _find_customer_by_name(self, name: str) -> Optional[Dict]:
        """Find customer by name in the database."""
        customers = self.data_manager.get_customers()
        name_lower = name.lower()
        
        for customer in customers:
            if customer['name'].lower() == name_lower:
                return customer
        
        return None

    async def _create_new_customer(self, name: str) -> Optional[Dict]:
        """Create a new customer account."""
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

    def _extract_customer_name(self, query: str) -> str:
        """Extract customer name from query."""
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

    async def _generate_gemini_response(self, query: str, context_data: Dict, conversation_context: str) -> str:
        """Generate response using Google Gemini AI."""
        try:
            # Build system prompt with context
            system_prompt = build_context_prompt(
                products_data=self.data_manager.get_products(),
                customer_data=context_data.get('customer_data'),
                product_discussion=context_data.get('product_data', []),
                order_discussion=context_data.get('order_data', []),
                conversation_history=conversation_context
            )
            
            # Create the prompt
            full_prompt = f"{system_prompt}\n\nCustomer Query: {query}"
            
            # Generate response using Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(full_prompt)
            )
            
            if response and response.text:
                logger.info(f"✅ Gemini response generated: {response.text[:100]}...")
                return response.text.strip()
            else:
                logger.warning("Gemini returned empty response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return None


    async def _generate_intelligent_response(self, query: str, context_data: Dict, conversation_context: str) -> str:
        """Generate intelligent response using Gemini AI with comprehensive system prompt."""
        if not self.model:
            return "I'm sorry, but I'm not able to process your request right now. Please try again later."
        
        try:
            response = await self._generate_gemini_response(query, context_data, conversation_context)
            if response:
                return response
            else:
                return "I'm having trouble processing your request. Could you please rephrase your question?"
        except Exception as e:
            logger.error(f"Gemini AI error: {e}")
            return "I apologize, but I encountered an error. Please try again."






    async def get_conversation_history(self) -> List[Dict]:
        """Get conversation history for current session."""
        if not self.session_id:
            return []
        
        return self.conversation_manager.get_conversation_history(self.session_id)

    async def clear_conversation(self) -> bool:
        """Clear conversation history for current session."""
        if not self.session_id:
            return False
        
        return self.conversation_manager.clear_session(self.session_id)

    async def end_chat_session(self) -> str:
        """End the chat session."""
        if self.session_id:
            self.conversation_manager.add_message(
                self.session_id,
                "system",
                "Chat session ended"
            )
            self.session_id = None
        
        return "Thank you for chatting with us! Have a great day!"


# Example usage and testing
async def main():
    """Example usage of the TextChatAgent."""
    agent = TextChatAgent()
    
    # Start a chat session
    greeting = await agent.start_chat_session("test_user")
    print(f"Agent: {greeting}")
    
    # Simulate a conversation
    test_messages = [
        "Hello!",
        "My name is John",
        "I want to buy wireless headphones",
        "My customer ID is CUST001",
        "What's my order status?",
        "Thank you!"
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = await agent.process_message(message)
        print(f"Agent: {response}")
    
    # End the session
    goodbye = await agent.end_chat_session()
    print(f"\nAgent: {goodbye}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
