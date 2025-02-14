# Email-Conversation-Bot

TechCorp X Marketing Bot - System Documentation
Overview
The TechCorp X Marketing Bot is an AI-powered email communication system that handles customer inquiries, provides product information, and maintains conversation threads using the Llama language model via Groq's API.
System Architecture
Components

FastAPI Backend

Handles HTTP requests
Manages email conversations
Integrates with MongoDB
Communicates with Groq LLM API


MongoDB Database

Stores email threads
Maintains conversation history
Enables search functionality


Streamlit Frontend

User interface for sending emails
Displays conversations
Provides search functionality


LLM Integration (Groq/Llama)

Generates contextual responses
Maintains conversation coherence
Handles product inquiries



Data Flow
1. New Email Flow
CopyUser Input -> Streamlit -> FastAPI -> MongoDB
                                  -> Groq API
                                  -> Store Response
                                  -> Display Thread
2. Reply Flow
CopyUser Reply -> Find Thread -> Load Context
                         -> Generate Response
                         -> Update Thread
                         -> Display Update
3. Search Flow
CopySearch Query -> MongoDB Query -> Filter Results
                             -> Display Threads
Database Schema
jsonCopy{
    "_id": ObjectId,
    "sender": "string",
    "recipient": "string",
    "subject": "string",
    "body": "string",
    "timestamp": "datetime",
    "thread": [
        {
            "sender": "string",
            "body": "string",
            "timestamp": "datetime"
        }
    ]
}
Setup Instructions

Environment Setup

bashCopy# Set up Python environment
python -m venv venv
source venv/bin/activate  # Unix
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your-api-key-here"

Start Services

bashCopy# Start MongoDB
mongod

# Start FastAPI server
uvicorn main:app --reload

# Start Streamlit interface
streamlit run streamlit_app.py
API Endpoints
1. Send Email

POST /send-email

jsonCopy{
    "sender": "string",
    "recipient": "string",
    "subject": "string",
    "body": "string"
}
2. Reply to Email

POST /reply-email

jsonCopy{
    "email_id": "string",
    "sender": "string",
    "body": "string"
}
3. Search Emails

POST /get-emails

jsonCopy{
    "sender": "string (optional)",
    "recipient": "string (optional)",
    "keywords": "string (optional)"
}
Error Handling

Common Errors

Invalid email ID
MongoDB connection issues
LLM API failures
Invalid request data


Error Responses

400: Bad Request
404: Not Found
500: Internal Server Error



Best Practices

Using the System

Always provide clear subject lines
Use appropriate email addresses
Check conversation history before replying


Maintenance

Monitor MongoDB performance
Check LLM API usage
Review error logs regularly



Testing

Test Scripts

Use provided test_email_bot.py
Test all main functionalities
Verify responses


Manual Testing

Test through Streamlit interface
Verify conversation flow
Check error handling



Support and Troubleshooting

Common Issues

MongoDB connection errors
LLM API timeouts
Frontend display issues


Solutions

Check environment variables
Verify service status
Review error logs
