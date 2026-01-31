import os
from typing import List, Tuple
from pinecone import Pinecone, ServerlessSpec
import openai
from openai import OpenAI
import hashlib
import json

class RAGEngine:
    def __init__(self):
        """Initialize the RAG engine with Pinecone and OpenAI"""
        # Get API keys from environment
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index_name = "acme-tech-chatbot"
        self.index = None
        
        # Embedding configuration
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimension = 1536
        
        # LLM configuration
        self.llm_model = "gpt-3.5-turbo"
        
        # Data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    async def initialize(self):
        """Initialize or connect to the Pinecone index and index documents"""
        # Create index if it doesn't exist
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"Creating new index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        
        # Connect to the index
        self.index = self.pc.Index(self.index_name)
        
        # Check if documents are already indexed
        stats = self.index.describe_index_stats()
        if stats['total_vector_count'] == 0:
            print("Indexing documents...")
            await self.index_documents()
        else:
            print(f"Index already contains {stats['total_vector_count']} vectors")
    
    def chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """
        Split text into chunks of approximately chunk_size words
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text using OpenAI"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    async def index_documents(self):
        """Read documents from data directory and index them in Pinecone"""
        documents = []
        
        # Read all text files from data directory
        for filename in os.listdir(self.data_dir):
            if filename.endswith(('.txt', '.md')):
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Chunk the document
                    chunks = self.chunk_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        documents.append({
                            'id': f"{filename}_{i}",
                            'text': chunk,
                            'source': filename,
                            'chunk_index': i
                        })
        
        print(f"Indexing {len(documents)} document chunks...")
        
        # Create embeddings and upsert to Pinecone
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Prepare vectors for upsert
            vectors = []
            for doc in batch:
                embedding = self.get_embedding(doc['text'])
                vectors.append({
                    'id': doc['id'],
                    'values': embedding,
                    'metadata': {
                        'text': doc['text'],
                        'source': doc['source'],
                        'chunk_index': doc['chunk_index']
                    }
                })
            
            # Upsert to Pinecone
            self.index.upsert(vectors=vectors)
        
        print(f"Successfully indexed {len(documents)} chunks")
    
    async def retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[dict]:
        """Retrieve the most relevant chunks for a query"""
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Search in Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Extract relevant chunks
        chunks = []
        for match in results['matches']:
            chunks.append({
                'text': match['metadata']['text'],
                'source': match['metadata']['source'],
                'score': match['score']
            })
        
        return chunks
    
    async def generate_response(self, query: str, context_chunks: List[dict]) -> str:
        """Generate a response using the LLM with retrieved context"""
        # Build context from retrieved chunks
        context = "\n\n".join([f"[Source: {chunk['source']}]\n{chunk['text']}" for chunk in context_chunks])
        
        # Create prompt
        prompt = f"""You are a helpful assistant for Acme Tech Solutions. Answer the user's question based on the following context from company documents.

Context:
{context}

User Question: {query}

Instructions:
- Answer based on the provided context
- Be helpful and conversational
- If the context doesn't contain enough information to answer fully, say so
- Do not make up information not present in the context

Answer:"""
        
        # Generate response using OpenAI
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Acme Tech Solutions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    async def query(self, user_query: str) -> Tuple[str, List[str]]:
        """
        Process a user query through the RAG pipeline
        Returns: (response, list of source documents)
        """
        # Retrieve relevant chunks
        relevant_chunks = await self.retrieve_relevant_chunks(user_query)
        
        # Generate response
        response = await self.generate_response(user_query, relevant_chunks)
        
        # Extract unique sources
        sources = list(set([chunk['source'] for chunk in relevant_chunks]))
        
        return response, sources
