import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
import os

def setup_authentication():
    # Delete existing config file if having issues
    if os.path.exists("auth_config.yaml"):
        os.remove("auth_config.yaml")
    
    # Hard-coded credentials for simplicity
    names = ["Demo User"]
    usernames = ["demo"]
    passwords = ["password"]  # Plain text for initial creation
    
    # Hash passwords
    hashed_passwords = stauth.Hasher(passwords).generate()
    
    # Create config dictionary
    credentials = {
        "usernames": {
            usernames[0]: {
                "name": names[0],
                "password": hashed_passwords[0]
            }
        }
    }
    
    # Cookie details
    cookie = {
        "expiry_days": 30,
        "key": "resume_matcher_app",
        "name": "resume_matcher_auth"
    }
    
    # Save config
    config = {
        "credentials": credentials,
        "cookie": cookie
    }
    
    with open("auth_config.yaml", "w") as file:
        yaml.dump(config, file)
    
    # Load from file
    with open("auth_config.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Create authenticator
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"]
    )
    
    # Create login widget
    name, authentication_status, username = authenticator.login("Login", "main")
    
    # Handle authentication status
    if authentication_status == False:
        st.error("Username/password is incorrect")
        return False, None, authenticator
    
    elif authentication_status == None:
        st.warning("Please enter your username and password")
        with st.expander("Don't have an account? Register here"):
            register_user(authenticator, config)
        return False, None, authenticator
    
    else:
        st.sidebar.write(f"Welcome, {name}!")
        authenticator.logout("Logout", "sidebar")
        return True, username, authenticator

def register_user(authenticator, config):
    with st.form("Registration"):
        new_username = st.text_input("Username", key="reg_username")
        new_name = st.text_input("Full Name", key="reg_name")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        register_button = st.form_submit_button("Register")
        
        if register_button:
            if new_password != confirm_password:
                st.error("Passwords don't match!")
                return
            
            try:
                # Hash password
                hashed_password = stauth.Hasher([new_password]).generate()[0]
                
                # Add new user
                config["credentials"]["usernames"][new_username] = {
                    "name": new_name,
                    "password": hashed_password
                }
                
                # Save updated config
                with open("auth_config.yaml", "w") as file:
                    yaml.dump(config, file)
                
                st.success("Registration successful! You can now log in with username: " + new_username)
                
            except Exception as e:
                st.error(f"Registration failed: {e}")