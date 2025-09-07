"""
Payment and Subscription System for Word Counter Pro
Handles Stripe integration, subscription management, and billing
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

@dataclass
class SubscriptionPlan:
    """Subscription plan data structure"""
    plan_id: str
    name: str
    price: float
    currency: str
    interval: str  # monthly, yearly
    features: List[str]
    max_users: int
    max_storage: int  # MB
    
@dataclass
class Customer:
    """Customer data structure"""
    customer_id: str
    email: str
    name: str
    subscription_status: str
    current_plan: Optional[str]
    trial_end: Optional[datetime]
    created_at: datetime

class StripePaymentProcessor:
    """Handles Stripe payment processing"""
    
    def __init__(self, api_key: str, webhook_secret: str):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.base_url = "https://api.stripe.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def create_customer(self, email: str, name: str) -> Optional[str]:
        """Create a new Stripe customer"""
        try:
            data = {
                "email": email,
                "name": name,
                "metadata": {
                    "source": "wordcounter_pro"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/customers",
                headers=self.headers,
                data=data
            )
            
            if response.status_code == 200:
                customer_data = response.json()
                return customer_data["id"]
            else:
                logging.error(f"Failed to create customer: {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error creating customer: {e}")
            return None
    
    def create_subscription(self, customer_id: str, price_id: str, 
                          trial_days: int = 14) -> Optional[str]:
        """Create a subscription for a customer"""
        try:
            data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "trial_period_days": trial_days,
                "metadata": {
                    "source": "wordcounter_pro"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/subscriptions",
                headers=self.headers,
                data=data
            )
            
            if response.status_code == 200:
                subscription_data = response.json()
                return subscription_data["id"]
            else:
                logging.error(f"Failed to create subscription: {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error creating subscription: {e}")
            return None
    
    def create_checkout_session(self, customer_id: str, price_id: str, 
                               success_url: str, cancel_url: str) -> Optional[str]:
        """Create a Stripe checkout session"""
        try:
            data = {
                "customer": customer_id,
                "payment_method_types[]": "card",
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": 1,
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "source": "wordcounter_pro"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/checkout/sessions",
                headers=self.headers,
                data=data
            )
            
            if response.status_code == 200:
                session_data = response.json()
                return session_data["url"]
            else:
                logging.error(f"Failed to create checkout session: {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error creating checkout session: {e}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details"""
        try:
            response = requests.get(
                f"{self.base_url}/subscriptions/{subscription_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Failed to get subscription: {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error getting subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        try:
            response = requests.delete(
                f"{self.base_url}/subscriptions/{subscription_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return True
            else:
                logging.error(f"Failed to cancel subscription: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error canceling subscription: {e}")
            return False

class SubscriptionManager:
    """Manages subscriptions and billing"""
    
    def __init__(self, stripe_processor: StripePaymentProcessor):
        self.stripe = stripe_processor
        self.plans = self._initialize_plans()
    
    def _initialize_plans(self) -> Dict[str, SubscriptionPlan]:
        """Initialize subscription plans"""
        return {
            "free": SubscriptionPlan(
                plan_id="free",
                name="Free",
                price=0.0,
                currency="usd",
                interval="monthly",
                features=[
                    "Basic word counting",
                    "Daily goal tracking",
                    "7-day history",
                    "Local data storage"
                ],
                max_users=1,
                max_storage=100
            ),
            "pro": SubscriptionPlan(
                plan_id="pro",
                name="Pro",
                price=9.99,
                currency="usd",
                interval="monthly",
                features=[
                    "Everything in Free",
                    "Cloud sync across devices",
                    "Unlimited history",
                    "Advanced analytics",
                    "Achievement system",
                    "Goal templates",
                    "Priority support"
                ],
                max_users=1,
                max_storage=1000
            ),
            "team": SubscriptionPlan(
                plan_id="team",
                name="Team",
                price=19.99,
                currency="usd",
                interval="monthly",
                features=[
                    "Everything in Pro",
                    "Team collaboration",
                    "Shared goals",
                    "Team analytics",
                    "Admin dashboard",
                    "Custom branding",
                    "24/7 support"
                ],
                max_users=10,
                max_storage=5000
            )
        }
    
    def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get a subscription plan by ID"""
        return self.plans.get(plan_id)
    
    def get_all_plans(self) -> List[SubscriptionPlan]:
        """Get all available plans"""
        return list(self.plans.values())
    
    def create_customer_subscription(self, email: str, name: str, 
                                   plan_id: str) -> Optional[Dict[str, Any]]:
        """Create a customer and subscription"""
        try:
            # Create Stripe customer
            customer_id = self.stripe.create_customer(email, name)
            if not customer_id:
                return None
            
            # Get plan
            plan = self.get_plan(plan_id)
            if not plan:
                return None
            
            # Create subscription (if not free)
            subscription_id = None
            if plan.price > 0:
                # This would use actual Stripe price IDs
                price_id = f"price_{plan_id}_monthly"
                subscription_id = self.stripe.create_subscription(customer_id, price_id)
            
            return {
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "plan_id": plan_id,
                "status": "active" if plan.price == 0 else "trialing"
            }
            
        except Exception as e:
            logging.error(f"Error creating customer subscription: {e}")
            return None
    
    def get_checkout_url(self, customer_id: str, plan_id: str, 
                        success_url: str, cancel_url: str) -> Optional[str]:
        """Get Stripe checkout URL for a plan"""
        try:
            plan = self.get_plan(plan_id)
            if not plan or plan.price == 0:
                return None
            
            # This would use actual Stripe price IDs
            price_id = f"price_{plan_id}_monthly"
            return self.stripe.create_checkout_session(
                customer_id, price_id, success_url, cancel_url
            )
            
        except Exception as e:
            logging.error(f"Error creating checkout URL: {e}")
            return None
    
    def handle_webhook(self, payload: str, signature: str) -> bool:
        """Handle Stripe webhook events"""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(payload, signature):
                logging.error("Invalid webhook signature")
                return False
            
            event = json.loads(payload)
            event_type = event["type"]
            
            if event_type == "customer.subscription.created":
                self._handle_subscription_created(event["data"]["object"])
            elif event_type == "customer.subscription.updated":
                self._handle_subscription_updated(event["data"]["object"])
            elif event_type == "customer.subscription.deleted":
                self._handle_subscription_deleted(event["data"]["object"])
            elif event_type == "invoice.payment_succeeded":
                self._handle_payment_succeeded(event["data"]["object"])
            elif event_type == "invoice.payment_failed":
                self._handle_payment_failed(event["data"]["object"])
            
            return True
            
        except Exception as e:
            logging.error(f"Error handling webhook: {e}")
            return False
    
    def _verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        # This would implement actual signature verification
        # For now, we'll just return True
        return True
    
    def _handle_subscription_created(self, subscription_data: Dict[str, Any]):
        """Handle subscription created event"""
        customer_id = subscription_data["customer"]
        subscription_id = subscription_data["id"]
        
        # Update user's subscription status in your database
        logging.info(f"Subscription created: {subscription_id} for customer {customer_id}")
    
    def _handle_subscription_updated(self, subscription_data: Dict[str, Any]):
        """Handle subscription updated event"""
        customer_id = subscription_data["customer"]
        subscription_id = subscription_data["id"]
        status = subscription_data["status"]
        
        # Update user's subscription status in your database
        logging.info(f"Subscription updated: {subscription_id} status: {status}")
    
    def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]):
        """Handle subscription deleted event"""
        customer_id = subscription_data["customer"]
        subscription_id = subscription_data["id"]
        
        # Downgrade user to free plan
        logging.info(f"Subscription deleted: {subscription_id} for customer {customer_id}")
    
    def _handle_payment_succeeded(self, invoice_data: Dict[str, Any]):
        """Handle successful payment event"""
        customer_id = invoice_data["customer"]
        amount = invoice_data["amount_paid"]
        
        # Update user's billing status
        logging.info(f"Payment succeeded: ${amount/100} for customer {customer_id}")
    
    def _handle_payment_failed(self, invoice_data: Dict[str, Any]):
        """Handle failed payment event"""
        customer_id = invoice_data["customer"]
        
        # Handle failed payment (send notification, suspend account, etc.)
        logging.info(f"Payment failed for customer {customer_id}")

class BillingUI:
    """UI components for billing and subscription management"""
    
    def __init__(self, parent, subscription_manager: SubscriptionManager):
        self.parent = parent
        self.subscription_manager = subscription_manager
    
    def show_pricing_modal(self):
        """Show pricing modal"""
        pricing_window = tk.Toplevel(self.parent)
        pricing_window.title("Choose Your Plan")
        pricing_window.geometry("600x500")
        pricing_window.resizable(False, False)
        pricing_window.transient(self.parent)
        pricing_window.grab_set()
        
        # Center the window
        pricing_window.update_idletasks()
        x = (pricing_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (pricing_window.winfo_screenheight() // 2) - (500 // 2)
        pricing_window.geometry(f"600x500+{x}+{y}")
        
        main_frame = ttk.Frame(pricing_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Choose Your Plan", 
                 font=("Helvetica", 18, "bold")).pack(pady=(0, 20))
        
        # Plans grid
        plans_frame = ttk.Frame(main_frame)
        plans_frame.pack(fill=tk.BOTH, expand=True)
        
        plans = self.subscription_manager.get_all_plans()
        
        for i, plan in enumerate(plans):
            self._create_plan_card(plans_frame, plan, i)
        
        # Close button
        ttk.Button(main_frame, text="Close", 
                  command=pricing_window.destroy).pack(pady=20)
    
    def _create_plan_card(self, parent, plan: SubscriptionPlan, index: int):
        """Create a plan card"""
        card_frame = ttk.LabelFrame(parent, text=plan.name, padding="15")
        card_frame.grid(row=0, column=index, padx=10, pady=10, sticky="nsew")
        
        # Price
        price_text = f"${plan.price:.2f}" if plan.price > 0 else "Free"
        ttk.Label(card_frame, text=price_text, 
                 font=("Helvetica", 24, "bold")).pack(pady=10)
        
        # Features
        for feature in plan.features:
            ttk.Label(card_frame, text=f"✓ {feature}").pack(anchor=tk.W, pady=2)
        
        # Select button
        if plan.price > 0:
            ttk.Button(card_frame, text="Upgrade", 
                      command=lambda: self._select_plan(plan)).pack(pady=10)
        else:
            ttk.Button(card_frame, text="Current Plan", 
                      state=tk.DISABLED).pack(pady=10)
        
        # Configure grid weights
        parent.grid_columnconfigure(index, weight=1)
    
    def _select_plan(self, plan: SubscriptionPlan):
        """Handle plan selection"""
        # This would redirect to Stripe checkout
        messagebox.showinfo("Upgrade", f"Redirecting to checkout for {plan.name} plan...")
    
    def show_billing_history(self, customer_id: str):
        """Show billing history"""
        # This would show the customer's billing history
        messagebox.showinfo("Billing History", "Billing history would be displayed here")
    
    def show_subscription_management(self, customer_id: str):
        """Show subscription management"""
        # This would show subscription management options
        messagebox.showinfo("Subscription Management", "Subscription management would be displayed here")

# Example usage
def create_payment_system():
    """Create payment system instance"""
    # These would be your actual Stripe keys
    stripe_api_key = "sk_test_your_stripe_secret_key"
    webhook_secret = "whsec_your_webhook_secret"
    
    stripe_processor = StripePaymentProcessor(stripe_api_key, webhook_secret)
    subscription_manager = SubscriptionManager(stripe_processor)
    
    return subscription_manager

if __name__ == "__main__":
    # Example usage
    subscription_manager = create_payment_system()
    
    # Get all plans
    plans = subscription_manager.get_all_plans()
    for plan in plans:
        print(f"{plan.name}: ${plan.price:.2f}/month")
        print(f"Features: {', '.join(plan.features)}")
        print()


