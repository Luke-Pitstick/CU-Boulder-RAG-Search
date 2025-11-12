from flask import Flask, render_template, request, jsonify
import time
from typing import Dict, Any
import json
from src.llm.enhanced_search import setup_rag_system, format_sources

app = Flask(__name__)

# Global variable to hold the RAG chain
rag_chain = None

def initialize_rag():
    """Initialize the RAG system on startup"""
    global rag_chain
    try:
        print("🔧 Initializing RAG system...")
        
        # Load config
        with open('config_llm.json', 'r') as f:
            config = json.load(f)
        
        rag_chain = setup_rag_system(
            collection_name=config['vector_store']['collection_name'],
            qdrant_url=config['vector_store']['url'],
            embedding_model=config['embedding']['model_name'],
            llm_model=config['llm']['model'],
            device=config['embedding']['device']
        )
        print("✅ RAG system initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        return False

@app.route('/')
def index():
    """Render the main search page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    """Handle search requests"""
    global rag_chain
    
    # Check if RAG system is initialized
    if rag_chain is None:
        return jsonify({
            'error': 'RAG system not initialized. Please check your configuration and ensure Ollama is running.',
            'status': 'error'
        }), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Please provide a search query',
                'status': 'error'
            }), 400
        
        # Run the RAG chain
        print(f"🔍 Processing query: {query}")
        start_time = time.time()
        
        chain_input = {"question": query}
        result = rag_chain.invoke(chain_input)
        
        total_time = time.time() - start_time
        
        # Format sources
        sources = format_sources(result["docs"])
        
        # Prepare response
        response = {
            "answer": result['answer'],
            "sources": sources,
            "metadata": {
                "query": query,
                "total_time": round(total_time, 2),
                "total_docs": len(sources)
            },
            "status": "success"
        }
        
        print(f"✅ Query processed in {total_time:.2f}s")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error processing search: {e}")
        return jsonify({
            'error': f'An error occurred while processing your query: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    global rag_chain
    return jsonify({
        'status': 'healthy' if rag_chain is not None else 'initializing',
        'rag_initialized': rag_chain is not None
    })

if __name__ == '__main__':
    # Initialize RAG system before starting the server
    if initialize_rag():
        print("\n🚀 Starting web server...")
        print("🌐 Access the application at: http://localhost:6634")
        app.run(debug=True, host='0.0.0.0', port=6634)
    else:
        print("\n❌ Failed to start web server due to RAG initialization failure")
        print("💡 Please ensure:")
        print("   1. Ollama is installed and running")
        print("   2. The llama3.2 model is available (run: ollama pull llama3.2)")
        print("   3. Qdrant is running on http://localhost:6333")
        print("   4. The vector store collection 'cuboulder_pages' exists")
