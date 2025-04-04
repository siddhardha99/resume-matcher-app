import streamlit as st
import paypalrestsdk
import os
from datetime import datetime, timedelta

# Initialize PayPal with your API credentials
def initialize_paypal():
    # Get PayPal API credentials from environment variables or Streamlit secrets
    client_id = os.environ.get('PAYPAL_CLIENT_ID') 
    client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
    
    # Try to get from secrets if not in environment variables
    if not client_id and 'paypal' in st.secrets:
        client_id = st.secrets["paypal"]["client_id"]
    
    if not client_secret and 'paypal' in st.secrets:
        client_secret = st.secrets["paypal"]["client_secret"]
    
    # If still not found, ask user to input
    if not client_id or not client_secret:
        client_id = st.sidebar.text_input("Enter your PayPal Client ID", type="password")
        client_secret = st.sidebar.text_input("Enter your PayPal Client Secret", type="password")
        
        if not client_id or not client_secret:
            st.warning("Please enter your PayPal API credentials to enable payments.")
            return False
    
    # Configure the SDK
    paypalrestsdk.configure({
        "mode": "sandbox",  # Change to "live" for production
        "client_id": client_id,
        "client_secret": client_secret
    })
    
    return True

# Create a PayPal payment for the basic plan
def create_basic_plan_payment(return_url, cancel_url):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        },
        "transactions": [{
            "amount": {
                "total": "9.99",
                "currency": "USD"
            },
            "description": "Resume Matcher Pro - Basic Plan"
        }]
    })
    
    if payment.create():
        # Extract approval URL to redirect the user
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = link.href
                # Store the payment ID in session state for later verification
                st.session_state['paypal_payment_id'] = payment.id
                return approval_url
    else:
        st.error(f"Error creating PayPal payment: {payment.error}")
        return None

# Create a PayPal billing agreement for the premium subscription
def create_premium_subscription(return_url, cancel_url):
    # First, create a billing plan
    billing_plan = paypalrestsdk.BillingPlan({
        "name": "Resume Matcher Premium Monthly",
        "description": "Monthly subscription for Resume Matcher Pro",
        "type": "INFINITE",
        "payment_definitions": [{
            "name": "Regular Monthly Payments",
            "type": "REGULAR",
            "frequency": "MONTH",
            "frequency_interval": "1",
            "amount": {
                "value": "19.99",
                "currency": "USD"
            },
            "cycles": "0"
        }],
        "merchant_preferences": {
            "setup_fee": {
                "value": "0",
                "currency": "USD"
            },
            "return_url": return_url,
            "cancel_url": cancel_url,
            "auto_bill_amount": "YES",
            "initial_fail_amount_action": "CONTINUE",
            "max_fail_attempts": "3"
        }
    })
    
    if billing_plan.create() and billing_plan.activate():
        # Create billing agreement
        # Add sufficient time to the start date (1 day in the future)
        start_date = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
        
        billing_agreement = paypalrestsdk.BillingAgreement({
            "name": "Resume Matcher Premium Subscription",
            "description": "Monthly subscription for unlimited resume analyses",
            "start_date": start_date,
            "plan": {
                "id": billing_plan.id
            },
            "payer": {
                "payment_method": "paypal"
            }
        })
        
        if billing_agreement.create():
            for link in billing_agreement.links:
                if link.rel == "approval_url":
                    # Store the billing agreement ID in session state
                    st.session_state['paypal_agreement_id'] = billing_agreement.id
                    return link.href
        else:
            st.error(f"Error creating billing agreement: {billing_agreement.error}")
    else:
        st.error(f"Error creating or activating billing plan: {billing_plan.error}")
    
    return None

# Function to display payment options
def display_payment_options(username):
    st.header("Choose a Plan")
    
    col1, col2 = st.columns(2)
    
    # Generate the return and cancel URLs
    base_url = st.get_option('server.baseUrlPath') or "http://localhost:8501"
    return_url = f"{base_url}?success=true&plan=basic"
    cancel_url = f"{base_url}?canceled=true"
    subscription_return_url = f"{base_url}?success=true&plan=premium"
    
    with col1:
        st.subheader("Basic Plan")
        st.write("- 5 Resume Analyses")
        st.write("- Basic Recommendations")
        st.write("- Valid for 30 days")
        st.write("**$9.99**")
        
        if st.button("Purchase Basic Plan"):
            # Create PayPal payment
            payment_url = create_basic_plan_payment(return_url, cancel_url)
            if payment_url:
                # Store the user's selection in the session state
                st.session_state['selected_plan'] = 'basic'
                st.session_state['username'] = username
                
                # Redirect the user to PayPal
                st.markdown(f'<meta http-equiv="refresh" content="0;url={payment_url}">', unsafe_allow_html=True)
                st.write("Redirecting to PayPal...")
    
    with col2:
        st.subheader("Premium Plan")
        st.write("- Unlimited Resume Analyses")
        st.write("- Advanced AI Recommendations")
        st.write("- Keyword Optimization")
        st.write("- Monthly Subscription")
        st.write("**$19.99/month**")
        
        if st.button("Subscribe to Premium Plan"):
            # Create PayPal subscription
            subscription_url = create_premium_subscription(subscription_return_url, cancel_url)
            if subscription_url:
                # Store the user's selection in the session state
                st.session_state['selected_plan'] = 'premium'
                st.session_state['username'] = username
                
                # Redirect the user to PayPal
                st.markdown(f'<meta http-equiv="refresh" content="0;url={subscription_url}">', unsafe_allow_html=True)
                st.write("Redirecting to PayPal...")

# Function to verify if a user has an active subscription
def check_user_subscription(username):
    # Debug information
    if st.checkbox("Show subscription debug info", key="debug_subscription"):
        st.write({
            "Username": username,
            "Subscriptions data": st.session_state.get('user_subscriptions', {})
        })
    
    # In a real app, you would query your database to check the user's subscription status
    # For this example, we'll use a session state variable to simulate a database
    
    if 'user_subscriptions' not in st.session_state:
        st.session_state['user_subscriptions'] = {}
    
    # Add test subscription for debugging if needed
    if username not in st.session_state['user_subscriptions'] and st.checkbox("Add test subscription", key="add_test_sub"):
        expiry = datetime.now() + timedelta(days=30)
        st.session_state['user_subscriptions'][username] = {
            'plan_type': 'basic',
            'expiry_date': expiry,
            'analyses_remaining': 5,
            'payment_id': 'test_payment'
        }
        st.success(f"Added test subscription for {username}")
    
    if username in st.session_state['user_subscriptions']:
        subscription = st.session_state['user_subscriptions'][username]
        
        try:
            expiry_date = subscription['expiry_date']
            # Handle different date formats
            if isinstance(expiry_date, str):
                expiry_date = datetime.fromisoformat(expiry_date)
                
            if expiry_date > datetime.now():
                return True, subscription['plan_type']
        except Exception as e:
            st.error(f"Error checking subscription: {e}")
    
    return False, None

def execute_paypal_payment():
    # Get the PayPal payment ID and payer ID from URL parameters
    params = dict(st.query_params)  # Convert to dictionary for easier access
    
    st.write(f"Payment parameters: {params}")
    
    if 'success' in params and params['success'] == 'true':
        plan = params.get('plan', 'basic')
        st.write(f"Processing plan: {plan}")
        
        if plan == 'basic' and 'paymentId' in params and 'PayerID' in params:
            payment_id = params['paymentId']
            payer_id = params['PayerID']
            
            # Verify that this payment ID matches the one we stored
            if 'paypal_payment_id' in st.session_state and payment_id == st.session_state['paypal_payment_id']:
                # Execute the payment
                try:
                    payment = paypalrestsdk.Payment.find(payment_id)
                    if payment.execute({"payer_id": payer_id}):
                        # Payment successful, update the user's subscription
                        if 'username' in st.session_state:
                            username = st.session_state['username']
                            
                            if 'user_subscriptions' not in st.session_state:
                                st.session_state['user_subscriptions'] = {}
                            
                            # Set expiry date 30 days from now
                            expiry = datetime.now() + timedelta(days=30)
                            st.session_state['user_subscriptions'][username] = {
                                'plan_type': 'basic',
                                'expiry_date': expiry,
                                'analyses_remaining': 5,
                                'payment_id': payment_id
                            }
                            
                            st.success("Payment successful! You now have access to the Basic Plan.")
                            return True
                    else:
                        st.error(f"Error executing payment: {payment.error}")
                except Exception as e:
                    st.error(f"Exception during payment execution: {str(e)}")
        
        elif plan == 'premium' and 'token' in params:
            token = params['token']
            st.write(f"Premium plan token: {token}")
            
            try:
                # Execute the billing agreement
                agreement = paypalrestsdk.BillingAgreement.execute(token)
                
                # Check if execution was successful
                if hasattr(agreement, 'id'):
                    # Agreement successful, update the user's subscription
                    if 'username' in st.session_state:
                        username = st.session_state['username']
                        
                        if 'user_subscriptions' not in st.session_state:
                            st.session_state['user_subscriptions'] = {}
                        
                        # Set expiry date 1 month from now
                        expiry = datetime.now() + timedelta(days=30)
                        st.session_state['user_subscriptions'][username] = {
                            'plan_type': 'premium',
                            'expiry_date': expiry,
                            'analyses_remaining': float('inf'),
                            'agreement_id': agreement.id
                        }
                        
                        st.success("Subscription successful! You now have access to the Premium Plan.")
                        return True
                else:
                    st.error("Error executing billing agreement - no agreement ID returned")
            except Exception as e:
                st.error(f"Exception during agreement execution: {str(e)}")
    
    return False
