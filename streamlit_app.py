# streamlit_app.py
import streamlit as st
import requests
from datetime import datetime
import json
from bson import ObjectId

st.set_page_config(page_title="TechCorp X Marketing Bot", layout="wide")

def format_timestamp(timestamp_str):
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_message_body(body):
    # Replace newlines with HTML break tags
    return body.replace('\n', '<br>')

def display_conversation(thread):
    for message in thread:
        is_bot = message["sender"] == "MarketingBot"
        formatted_body = format_message_body(message['body'])
        timestamp = format_timestamp(message['timestamp'])
        
        if is_bot:
            col1, col2 = st.columns([1, 9])
            with col1:
                st.image("https://api.dicebear.com/7.x/bottts/svg?seed=bot", width=50)
            with col2:
                st.markdown(
                    f'<div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin-bottom: 10px">'
                    f'<strong>Marketing Bot</strong><br>'
                    f'<small>{timestamp}</small><br>'
                    f'{formatted_body}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            col1, col2 = st.columns([9, 1])
            with col1:
                st.markdown(
                    f'<div style="background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin-bottom: 10px; text-align: right">'
                    f'<strong>{message["sender"]}</strong><br>'
                    f'<small>{timestamp}</small><br>'
                    f'{formatted_body}'
                    f'</div>',
                    unsafe_allow_html=True
                )

def main():
    st.title("TechCorp X Marketing Bot")
    
    # Initialize session state if needed
    if 'last_email_id' not in st.session_state:
        st.session_state.last_email_id = ''
    if 'last_thread' not in st.session_state:
        st.session_state.last_thread = []
    
    # Sidebar for navigation
    page = st.sidebar.selectbox("Choose Action", ["New Email", "Reply to Email", "Search Emails"])
    
    if page == "Reply to Email":
        st.header("Reply to Email")
        
        # Fetch available email IDs
        try:
            response = requests.get("http://localhost:8000/get-email-ids")
            if response.status_code == 200:
                emails = response.json()
                
                # Create a list of options for the selectbox
                email_options = [
                    f"ID: {email['id']} | From: {email['sender']} | Subject: {email['subject']} | Date: {email['timestamp']}"
                    for email in emails
                ]
                
                if not email_options:
                    st.warning("No existing emails found. Please send a new email first.")
                    return
                
                # Default to the last email ID if it exists
                default_index = 0
                if st.session_state.last_email_id:
                    for i, opt in enumerate(email_options):
                        if st.session_state.last_email_id in opt:
                            default_index = i
                            break
                
                selected_email = st.selectbox(
                    "Select Email Thread",
                    options=email_options,
                    index=default_index
                )
                
                # Extract email ID from the selected option
                email_id = selected_email.split("|")[0].replace("ID:", "").strip()
                
                with st.form("reply_form"):
                    sender = st.text_input("Your Email")
                    reply_body = st.text_area("Reply Message")
                    
                    submitted = st.form_submit_button("Send Reply")
                    
                    if submitted:
                        try:
                            response = requests.post(
                                "http://localhost:8000/reply-email",
                                json={
                                    "email_id": email_id,
                                    "sender": sender,
                                    "body": reply_body
                                }
                            )
                            
                            if response.status_code == 200:
                                st.success("Reply sent successfully!")
                                data = response.json()
                                
                                # Display updated conversation
                                st.subheader("Updated Conversation")
                                display_conversation(data.get('thread', []))
                            else:
                                st.error(f"Error: {response.text}")
                        except Exception as e:
                            st.error(f"Error connecting to server: {str(e)}")
            else:
                st.error("Failed to fetch email IDs")
        except Exception as e:
            st.error(f"Error connecting to server: {str(e)}")

if __name__ == "__main__":
    main()