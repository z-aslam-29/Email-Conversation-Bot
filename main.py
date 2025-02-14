# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import motor.motor_asyncio
from datetime import datetime
import os
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from bson import ObjectId  
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Marketing Email Bot")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.email_bot_db
email_collection = db.emails

# Initialize Groq client with error checking
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Warning: GROQ_API_KEY not found in environment variables")
groq_client = AsyncGroq(api_key=api_key) if api_key else None

# Pydantic models
class EmailBase(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str

class EmailReply(BaseModel):
    email_id: str
    sender: str
    body: str

class EmailQuery(BaseModel):
    sender: Optional[str] = None
    recipient: Optional[str] = None
    keywords: Optional[str] = None

# Marketing bot using LLM
class MarketingBot:
    def __init__(self):
        self.company_info = """
        Company: TechCorp X
        
        About Us:
        TechCorp X is a leading technology solutions provider specializing in Cloud Services, AI Solutions, and Data Analytics.
        
        Products and Services:
        1. Cloud Services
           - Enterprise cloud infrastructure
           - Cloud storage solutions
           - Cloud security services
           Pricing: Starting at $99/month
        
        2. AI Solutions
           - Custom AI model development
           - AI integration services
           - Machine learning pipelines
           Pricing: Custom pricing based on requirements
        
        3. Data Analytics
           - Business intelligence tools
           - Real-time analytics
           - Predictive analytics
           Pricing: Starting at $199/month
        
        Support: 24/7 available via support@techcorpx.com or 1-800-TECH-X
        """
        
    async def generate_response(self, message: str, conversation_history: List[dict] = None) -> str:
        # Prepare conversation context
        system_prompt = f"""You are an AI marketing assistant for TechCorp X. 
        Use the following company information to respond to customer inquiries:
        
        {self.company_info}
        
        Guidelines:
        - Be professional but friendly
        - Provide specific information about our products and services
        - If you don't have specific information, be honest and offer to connect the customer with a sales representative
        - Always maintain a helpful and solution-oriented approach
        - Keep responses concise but informative
        """
        
        # Format conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            for msg in conversation_history:
                role = "assistant" if msg["sender"] == "MarketingBot" else "user"
                messages.append({"role": role, "content": msg["body"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            # Generate response using Groq with Llama model
            response = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Using Llama 2 70B model
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                top_p=1,
                stream=False
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating Llama response via Groq: {str(e)}")
            return "I apologize, but I'm having trouble generating a response. Please contact our support team at support@techcorpx.com for immediate assistance."

bot = MarketingBot()

# API endpoints
@app.post("/send-email")
async def send_email(email: EmailBase):
    try:
        # Create email document
        email_doc = {
            "sender": email.sender,
            "recipient": email.recipient,
            "subject": email.subject,
            "body": email.body,
            "timestamp": datetime.utcnow(),
            "thread": [{
                "sender": email.sender,
                "body": email.body,
                "timestamp": datetime.utcnow()
            }]
        }
        
        # Generate bot response using LLM
        bot_response = await bot.generate_response(email.body)
        
        # Add bot response to thread
        email_doc["thread"].append({
            "sender": "MarketingBot",
            "body": bot_response,
            "timestamp": datetime.utcnow()
        })
        
        # Insert into MongoDB
        result = await email_collection.insert_one(email_doc)
        
        return {"message": "Email sent successfully", "email_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reply-email")
async def reply_email(reply: EmailReply):
    try:
        # Convert string ID to ObjectId
        try:
            email_id = ObjectId(reply.email_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid email ID format")

        # Get email thread
        email = await email_collection.find_one({"_id": email_id})
        if not email:
            raise HTTPException(status_code=404, detail=f"Email not found with ID: {reply.email_id}")
        
        # Add human reply
        new_reply = {
            "sender": reply.sender,
            "body": reply.body,
            "timestamp": datetime.utcnow()
        }
        
        # Generate and add bot response
        try:
            bot_response = await bot.generate_response(reply.body, email.get("thread", []))
        except Exception as e:
            print(f"Error generating bot response: {str(e)}")
            bot_response = "I apologize for the technical difficulty. I've noted your message and a representative will get back to you shortly."
        
        bot_reply = {
            "sender": "MarketingBot",
            "body": bot_response,
            "timestamp": datetime.utcnow()
        }
        
        # Update thread
        result = await email_collection.update_one(
            {"_id": email_id},
            {
                "$push": {
                    "thread": {
                        "$each": [new_reply, bot_reply]
                    }
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update email thread")
            
        return {
            "message": "Reply added successfully",
            "thread": email["thread"] + [new_reply, bot_reply]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-emails")
async def get_emails(query: EmailQuery):
    try:
        # Build query
        filter_query = {}
        if query.sender:
            filter_query["sender"] = query.sender
        if query.recipient:
            filter_query["recipient"] = query.recipient
        if query.keywords:
            filter_query["$or"] = [
                {"subject": {"$regex": query.keywords, "$options": "i"}},
                {"body": {"$regex": query.keywords, "$options": "i"}}
            ]
        
        # Execute query
        cursor = email_collection.find(filter_query)
        emails = await cursor.to_list(length=100)
        
        # Convert ObjectId to string for JSON serialization
        for email in emails:
            email["_id"] = str(email["_id"])
        
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-email-ids")
async def get_email_ids():
    try:
        # Get all emails with their subjects for better context
        cursor = email_collection.find({}, {"subject": 1, "sender": 1, "timestamp": 1})
        emails = await cursor.to_list(length=100)
        
        # Format the results
        email_list = [{
            "id": str(email["_id"]),
            "subject": email.get("subject", "No subject"),
            "sender": email.get("sender", "No sender"),
            "timestamp": email.get("timestamp", datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")
        } for email in emails]
        
        return email_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))