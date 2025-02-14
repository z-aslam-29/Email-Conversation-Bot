# test_email_bot.py
import asyncio
import aiohttp
import json
from datetime import datetime
import os

async def test_email_marketing_bot():
    base_url = "http://localhost:8000"
    
    # Check for GROQ_API_KEY
    if not os.getenv("GROQ_API_KEY"):
        print("Warning: GROQ_API_KEY not set in environment variables")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test Case 1: Initial Product Inquiry
            print("\n1. Testing Initial Product Inquiry...")
            initial_email = {
                "sender": "john.doe@company.com",
                "recipient": "sales@techcorpx.com",
                "subject": "Cloud Services Inquiry",
                "body": "Hi, I'm interested in your cloud services. Can you tell me about your pricing and what makes your service different from competitors?"
            }
            
            async with session.post(f"{base_url}/send-email", json=initial_email) as response:
                if response.status != 200:
                    print(f"Error sending email: {await response.text()}")
                    return
                
                result = await response.json()
                email_id = result.get("email_id")
                print(f"Email sent. ID: {email_id}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Wait a moment for the server to process
                await asyncio.sleep(2)
            
            # Test Case 2: Follow-up Question
            if email_id:
                print("\n2. Testing Follow-up Reply...")
                follow_up = {
                    "email_id": email_id,
                    "sender": "john.doe@company.com",
                    "body": "Thank you for the information. Do you offer any trial period?"
                }
                
                async with session.post(f"{base_url}/reply-email", json=follow_up) as response:
                    if response.status != 200:
                        print(f"Error sending reply: {await response.text()}")
                    else:
                        result = await response.json()
                        print(f"Reply sent. Thread updated: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    # Set up environment variable for testing
    if not os.getenv("GROQ_API_KEY"):
        print("Please set GROQ_API_KEY environment variable before running tests")
        print("Example: export GROQ_API_KEY='your-api-key-here'")
    
    asyncio.run(test_email_marketing_bot())