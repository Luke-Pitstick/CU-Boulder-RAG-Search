# CU Boulder Enhanced Search - Web Interface

A simple, modern web interface for the CU Boulder RAG (Retrieval-Augmented Generation) search system.

## Features

- 🎨 **Modern UI** - Clean, responsive design with TailwindCSS
- 🔍 **Real-time Search** - AI-powered search with instant results
- 📚 **Source Citations** - View and access all source documents
- ⚡ **Fast Response** - Optimized for quick query processing
- 📊 **Performance Metrics** - See response time and document count

## Prerequisites

Before running the web application, ensure you have:

1. **Python 3.8+** installed
2. **Ollama** installed and running
   ```bash
   # Install Ollama from https://ollama.com/
   # Pull the required model
   ollama pull llama3.2
   ```

3. **Qdrant** vector database running
   ```bash
   # Using Docker
   docker run -p 6333:6333 qdrant/qdrant
   ```

4. **Vector store populated** with CU Boulder data
   - Run the crawler and embedding pipeline first
   - Ensure the `cuboulder_pages` collection exists in Qdrant

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify configuration:**
   - Check `config_llm.json` for correct settings
   - Ensure Qdrant URL and collection name are correct

## Running the Web Application

1. **Start the web server:**
   ```bash
   python web_app.py
   ```

2. **Access the application:**
   - Open your browser and navigate to: `http://localhost:5000`

3. **Start searching:**
   - Type your question about CU Boulder in the search box
   - Click "Search" or press Enter
   - View the AI-generated answer and source citations

## Usage Examples

Try asking questions like:
- "What are the admission requirements for undergraduate students?"
- "Tell me about computer science programs at CU Boulder"
- "What housing options are available for students?"
- "How do I apply for financial aid?"
- "What research opportunities are available?"

## API Endpoints

The web application also exposes a REST API:

### POST /api/search
Search for information about CU Boulder.

**Request:**
```json
{
  "query": "What are the admission requirements?"
}
```

**Response:**
```json
{
  "answer": "Detailed answer from the AI...",
  "sources": [
    {
      "id": 1,
      "url": "https://www.colorado.edu/...",
      "title": "Page Title",
      "snippet": "Preview of content..."
    }
  ],
  "metadata": {
    "query": "What are the admission requirements?",
    "total_time": 2.34,
    "total_docs": 5
  },
  "status": "success"
}
```

### GET /api/health
Check the health status of the application.

**Response:**
```json
{
  "status": "healthy",
  "rag_initialized": true
}
```

## Troubleshooting

### "RAG system not initialized" error
- Ensure Ollama is running: `ollama list`
- Verify the model is available: `ollama pull llama3.2`
- Check Qdrant is accessible: `curl http://localhost:6333/health`

### "Collection not found" error
- Run the crawler and embedding pipeline first
- Verify the collection exists in Qdrant
- Check the collection name in `config_llm.json`

### Slow response times
- First query may take longer as models load into memory
- Subsequent queries should be faster
- Consider using a more powerful GPU/device

### Port already in use
- Change the port in `web_app.py` (default is 5000)
- Or stop the process using the port

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│  Flask App  │
└──────┬──────┘
       │
       ├─────────────────┐
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│   Qdrant    │   │   Ollama    │
│  (Vectors)  │   │    (LLM)    │
└─────────────┘   └─────────────┘
```

## Configuration

Edit `config_llm.json` to customize:
- LLM model and parameters
- Embedding model
- Retrieval settings (k, fetch_k, lambda_mult)
- Vector store settings

## Development

To run in development mode with auto-reload:
```bash
export FLASK_ENV=development
python web_app.py
```

## Production Deployment

For production use, consider:
1. Using a production WSGI server (gunicorn, uWSGI)
2. Setting up a reverse proxy (nginx, Apache)
3. Enabling HTTPS
4. Configuring proper logging
5. Setting up monitoring and health checks

Example with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

## License

See main project LICENSE file.

## Support

For issues or questions, please refer to the main project documentation or create an issue in the repository.
