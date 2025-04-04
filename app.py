import streamlit as st
import os
from datetime import datetime

# Import our custom modules
from auth_handler import setup_authentication
from paypal_handler import initialize_paypal, display_payment_options, check_user_subscription, execute_paypal_payment
from document_processor import process_resume_file
from resume_analyzer import create_analysis_graph, GraphState

# Set the page title
st.set_page_config(page_title="Resume Matcher Pro", page_icon="📝")

# App title and description
st.title("Resume Matcher Pro")
st.write("Match your resume to job descriptions with AI-powered recommendations.")

# Check if we're coming back from a successful payment
if 'success' in st.query_params:
    execute_paypal_payment()
    # Clear the URL parameters after processing
    for param in list(st.query_params):
        del st.query_params[param]

# Set up authentication
is_authenticated, username, authenticator = setup_authentication()

# Initialize PayPal
paypal_initialized = initialize_paypal()

if is_authenticated and paypal_initialized:
    # Check if the user has an active subscription
    has_subscription, plan_type = check_user_subscription(username)
    
    if not has_subscription:
        # Display payment options if no subscription
        display_payment_options(username)
    else:
        # Show subscription info
        st.sidebar.success(f"Active Plan: {plan_type.capitalize()}")
        
        if plan_type == 'basic':
            analyses_remaining = st.session_state['user_subscriptions'][username]['analyses_remaining']
            st.sidebar.info(f"Analyses Remaining: {analyses_remaining}")
        
        # OpenAI API key
        api_key = os.environ.get('OPENAI_API_KEY')
        # Try to get from secrets if not in environment variables
        if not api_key and 'openai' in st.secrets:
            api_key = st.secrets["openai"]["api_key"]
            os.environ["OPENAI_API_KEY"] = api_key
        
        # If still not found, ask user to input
        if not api_key:
            api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
            if not api_key:
                st.warning("Please enter your OpenAI API key to proceed.")
                st.stop()
            else:
                os.environ["OPENAI_API_KEY"] = api_key
            
        # File uploader for resume
        resume_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
        resume_text = process_resume_file(resume_file)
            
        # Job description input
        job_description = st.text_area("Paste the job description here", height=300)

        # Check if we have enough analyses remaining
        can_analyze = False
        if username in st.session_state.get('user_subscriptions', {}):
            subscription = st.session_state['user_subscriptions'][username]
            if subscription['plan_type'] == 'premium' or subscription['analyses_remaining'] > 0:
                can_analyze = True

        # Button to analyze
        if st.button("Analyze Resume", disabled=not can_analyze):
            if resume_text and job_description:
                # Update the user's remaining analyses count
                if username in st.session_state['user_subscriptions']:
                    subscription = st.session_state['user_subscriptions'][username]
                    
                    if subscription['plan_type'] == 'basic':
                        subscription['analyses_remaining'] -= 1
                        st.session_state['user_subscriptions'][username] = subscription
                
                with st.spinner("Analyzing your resume against the job description..."):
                    # Initialize the graph
                    workflow = create_analysis_graph()
                    
                    # Run the graph
                    result = workflow.invoke({
                        "resume": resume_text,
                        "job_description": job_description,
                        "skills_analysis": {},
                        "experience_analysis": {},
                        "keyword_analysis": {}
                    })
                    
                    # Display results
                    st.subheader("Resume Optimization Recommendations")
                    st.markdown(result["final_recommendations"])
                    
                    # Show detailed analysis if wanted
                    with st.expander("View Detailed Analysis"):
                        st.subheader("Skills Analysis")
                        st.json(result["skills_analysis"])
                        
                        st.subheader("Experience Analysis")
                        st.json(result["experience_analysis"])
                        
                        st.subheader("Keyword Analysis")
                        st.json(result["keyword_analysis"])
            else:
                st.error("Please provide both your resume and the job description.")
                
        # If we're running out of analyses, show a prompt to upgrade
        if username in st.session_state.get('user_subscriptions', {}) and plan_type == 'basic':
            subscription = st.session_state['user_subscriptions'][username]
            if subscription['analyses_remaining'] <= 1:
                st.warning("You're running low on resume analyses. Consider upgrading to our Premium plan for unlimited analyses.")
                if st.button("Upgrade to Premium"):
                    display_payment_options(username)
