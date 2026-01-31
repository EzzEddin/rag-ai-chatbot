# Acme Tech Solutions RAG Chatbot

A full-stack Retrieval-Augmented Generation (RAG) chatbot application built with FastAPI, Pinecone, OpenAI, and React.

## Overview

This application allows users to ask questions about Acme Tech Solutions (a fictional company), and the chatbot retrieves relevant information from company documents before generating accurate, context-aware responses.

## Technology Stack

### Backend
- **FastAPI**: Web framework for building the REST API
- **Pinecone**: Vector database for storing and retrieving document embeddings
- **OpenAI**: 
  - `text-embedding-3-small` for generating embeddings
  - `gpt-3.5-turbo` for generating responses
- **Python 3.8+**

### Frontend
- **React**: UI framework
- **Vite**: Build tool and development server
- **Axios**: HTTP client for API calls

## Project Structure

```
rag_chatbot_fastapi_react/
├── backend/
│   ├── main.py              # FastAPI application and API endpoints
│   ├── rag_engine.py        # RAG implementation (Pinecone + OpenAI)
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (create this)
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── App.css         # Styles
│   │   ├── main.jsx        # React entry point
│   │   └── index.css       # Global styles
│   ├── index.html          # HTML template
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
├── data/
│   ├── company_history.txt # Knowledge source document
│   ├── core_products.txt   # Knowledge source document
│   └── hr_policy.txt       # Knowledge source document
└── README.txt              # This file
```

## Prerequisites

1. **Python 3.8 or higher**
2. **Node.js 16 or higher** and npm
3. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
4. **Pinecone API Key** - Get from https://www.pinecone.io/ (free tier available)

## Setup Instructions

### 1. Backend Setup

#### Step 1.1: Navigate to the backend directory
Open a terminal and run:
```
cd backend
```

#### Step 1.2: Create a Python virtual environment (recommended)
```
python -m venv venv
```

#### Step 1.3: Activate the virtual environment
On Windows:
```
venv\Scripts\activate
```

On Mac/Linux:
```
source venv/bin/activate
```

#### Step 1.4: Install Python dependencies
```
pip install -r requirements.txt
```

#### Step 1.5: Create environment variables file
Create a file named `.env` in the backend directory with the following content:
```
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

Replace the placeholder values with your actual API keys.

#### Step 1.6: Start the FastAPI server
```
python main.py
```

Or using uvicorn directly:
```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will start on http://localhost:8000

**Note**: On first run, the application will automatically:
- Create a Pinecone index named "acme-tech-chatbot"
- Read the documents from the data/ directory
- Chunk the documents into smaller pieces
- Generate embeddings using OpenAI
- Index all chunks in Pinecone

This process may take 1-2 minutes. Check the console output to see the progress.

### 2. Frontend Setup

#### Step 2.1: Open a NEW terminal and navigate to the frontend directory
```
cd frontend
```

#### Step 2.2: Install Node.js dependencies
```
npm install
```

#### Step 2.3: Start the development server
```
npm run dev
```

The frontend will start on http://localhost:3000

### 3. Using the Application

1. Open your web browser and go to http://localhost:3000
2. You'll see a modern chat interface with the Acme Tech Solutions branding
3. Type your question in the input box at the bottom
4. Click the send button or press Enter
5. The chatbot will retrieve relevant information and generate a response
6. Sources used for the answer will be displayed below each response

## Example Questions to Try

- "When was Acme Tech Solutions founded?"
- "What products does Acme offer?"
- "Tell me about AcmeFlow"
- "What is the company's HR policy on remote work?"
- "How does InsightEdge work?"
- "What services did Acme provide in 2017?"

## API Endpoints

### GET /
Returns API status and welcome message

### GET /health
Returns health status of the API and RAG engine

### POST /api/chat
Main chat endpoint that processes user queries

Request body:
```json
{
  "message": "Your question here"
}
```

Response:
```json
{
  "response": "Generated answer",
  "sources": ["company_history.txt", "core_products.txt"]
}
```

## How It Works

1. **Document Indexing** (happens on first run):
   - Documents are read from the data/ directory
   - Text is split into chunks of approximately 512 words
   - Each chunk is converted to an embedding using OpenAI
   - Embeddings are stored in Pinecone with metadata

2. **Query Processing**:
   - User submits a question through the frontend
   - Question is sent to the backend API
   - Question is converted to an embedding
   - Pinecone finds the 3 most similar document chunks
   - Retrieved chunks are used as context for the LLM
   - OpenAI GPT-3.5 generates a response based on the context
   - Response and source documents are returned to the user

## Troubleshooting

### Backend won't start
- Check that you've created the .env file with valid API keys
- Verify Python version: `python --version` (should be 3.8+)
- Check if port 8000 is already in use

### Frontend won't start
- Check Node.js version: `node --version` (should be 16+)
- Try deleting node_modules and running `npm install` again
- Check if port 3000 is already in use

### "RAG engine not initialized" error
- Wait a few minutes after starting the backend for indexing to complete
- Check the backend console logs for errors
- Verify your API keys are valid

### CORS errors
- Make sure the backend is running on port 8000
- Check that CORS middleware is properly configured in main.py

## Cost Considerations

- **OpenAI**: Charged per token for embeddings and completions
  - Initial indexing: ~$0.01-0.05 (one-time)
  - Per query: ~$0.001-0.01 depending on response length
- **Pinecone**: Free tier includes:
  - 1 index
  - Up to 100,000 vectors
  - Sufficient for this demo application

## Production Considerations

For production deployment, consider:
- Adding authentication and rate limiting
- Implementing caching for frequent queries
- Using environment-specific configurations
- Adding error tracking (e.g., Sentry)
- Implementing proper logging
- Adding automated tests
- Using a production WSGI server (e.g., Gunicorn)
- Hosting frontend on a CDN
- Setting up CI/CD pipelines

## License

This is a demonstration project for educational purposes.
