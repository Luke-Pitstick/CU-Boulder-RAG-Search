# CU Boulder RAG Search

A Retrieval-Augmented Generation (RAG) search system for the CU Boulder website. This system crawls, indexes, and enables intelligent semantic search across CU Boulder web content using local LLMs and vector embeddings.

## Features

- **Web Crawler** - Scrapy-based crawler with BFS/DFS support and duplicate filtering
- **Vector Search** - Qdrant vector database for semantic search
- **Local LLM Integration** - Ollama-powered AI responses with source citations
- **Web Interface** - Modern Flask-based UI for interactive search
- **Flexible Configuration** - JSON-based configuration for crawling and search parameters
- **Multi-Spider Support** - Run multiple crawlers simultaneously for different domains
- **Data Cleanup Tools** - Utilities for managing and cleaning vector database

## Architecture

```
┌──────────────┐
│   Web Pages  │
└──────┬───────┘
       │ Scrapy Crawler
       ▼
┌──────────────┐
│  JSONL Data  │
└──────┬───────┘
       │ Embedding Pipeline
       ▼
┌──────────────┐     ┌──────────────┐
│   Qdrant DB  │────▶│  Flask App   │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Ollama    │
                     │     LLM      │
                     └──────────────┘
```

## Prerequisites

- **Python 3.8+**
- **Redis** - For duplicate URL filtering during crawling
- **Qdrant** - Vector database for semantic search
- **Ollama** - Local LLM inference (for search functionality)

## Installation

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd cuboulderRAGSearch
pip install -r requirements.txt
```

### 2. Setup Redis

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

### 3. Setup Qdrant

```bash
# Using Docker (recommended)
docker run -p 6333:6333 qdrant/qdrant

# Or install locally from https://qdrant.tech/documentation/
```

### 4. Setup Ollama (for search functionality)

```bash
# Install Ollama from https://ollama.com/
curl -fsSL https://ollama.com/install.sh | sh

# Pull the LLM model
ollama pull llama3.2
```

## Quick Start

### 1. Crawl CU Boulder Website

```bash
# Basic crawl with default settings
python main.py

# Or with custom configuration
python add_pages_to_db.py --config config.json

# Limit number of pages
python add_pages_to_db.py --config config.json --pagecount 100
```

### 2. Index Data into Vector Database

After crawling, the data is saved to `output/crawled_pages.jsonl`. The embedding pipeline will automatically process and index this data into Qdrant.

### 3. Run the Web Search Interface

```bash
python web_app.py
```

Then open your browser to `http://localhost:6634`

## Configuration

### Crawler Configuration (`config.json`)

```json
{
  "base_url": "https://www.colorado.edu/",
  "crawl_rules": {
    "allow_patterns": [],
    "deny_patterns": ["/login", "/admin", "\\.pdf$"]
  },
  "settings": {
    "DOWNLOAD_DELAY": 8,
    "CONCURRENT_REQUESTS": 16,
    "DEPTH_LIMIT": 0,
    "CLOSESPIDER_PAGECOUNT": 30,
    "USE_BFS": true
  }
}
```

### LLM Configuration (`config_llm.json`)

```json
{
  "llm": {
    "model": "llama3.2",
    "temperature": 0.1
  },
  "embedding": {
    "model_name": "intfloat/e5-base-v2",
    "device": "mps"
  },
  "vector_store": {
    "collection_name": "cuboulder_pages",
    "url": "http://localhost:6333"
  },
  "retrieval": {
    "search_type": "mmr",
    "k": 5
  }
}
```

## Project Structure

```
cuboulderRAGSearch/
├── src/
│   ├── crawlers/          # Scrapy spider implementations
│   ├── embedding/         # Vector embedding pipeline
│   ├── filters/           # Duplicate filtering (Redis, Qdrant)
│   ├── llm/              # LLM integration and search
│   └── utils/            # Utility functions
├── templates/            # Flask HTML templates
├── tests/               # Test scripts
├── markdown/            # Additional documentation
├── output/              # Crawler output (JSONL)
├── config.json          # Crawler configuration
├── config_llm.json      # LLM/search configuration
├── main.py             # Basic crawler entry point
├── add_pages_to_db.py  # Advanced crawler with options
├── web_app.py          # Flask web application
└── requirements.txt    # Python dependencies
```

## Advanced Usage

### Multiple Spider Crawling

Run multiple crawlers for different domains:

```bash
python run_both_crawlers.py
```

See `markdown/MULTI_SPIDER_GUIDE.md` for details.

### BFS vs DFS Crawling

Configure crawling strategy in `config.json`:

```json
{
  "settings": {
    "USE_BFS": true  // true for breadth-first, false for depth-first
  }
}
```

See `markdown/BFS_DFS_GUIDE.md` for details.

### Data Cleanup

```bash
# Clean corrupted vectors
python cleanup_corrupted_vectors.py

# Clean PDF-related vectors
python cleanup_pdf_vectors.py
```

See `markdown/CLEANUP_GUIDE.md` for details.

## API Usage

The web application exposes a REST API:

### POST /api/search

```bash
curl -X POST http://localhost:6634/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the admission requirements?"}'
```

### GET /api/health

```bash
curl http://localhost:6634/api/health
```

## Troubleshooting

### Crawler Issues

- **Redis connection failed**: Ensure Redis is running (`redis-cli ping`)
- **Rate limiting**: Increase `DOWNLOAD_DELAY` in config
- **Memory issues**: Reduce `CONCURRENT_REQUESTS`

### Search Issues

- **Ollama not found**: Ensure Ollama is running (`ollama list`)
- **Qdrant connection failed**: Check Qdrant is running (`curl http://localhost:6333/health`)
- **No results**: Verify data is indexed in Qdrant collection

### Performance Optimization

- **Faster crawling**: Decrease `DOWNLOAD_DELAY`, increase `CONCURRENT_REQUESTS`
- **Better search quality**: Use larger LLM models, increase `k` in retrieval config
- **Lower resource usage**: Use CPU device, smaller embedding models

## Additional Documentation

- `markdown/SETUP_GUIDE.md` - Detailed setup instructions
- `markdown/WEB_APP_README.md` - Web interface documentation
- `markdown/MULTI_SPIDER_GUIDE.md` - Multiple crawler setup
- `markdown/BFS_DFS_GUIDE.md` - Crawling strategy guide
- `markdown/CLEANUP_GUIDE.md` - Data cleanup procedures
- `markdown/PDF_FILTERING_GUIDE.md` - PDF handling guide

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style conventions
- Tests pass for any new functionality
- Documentation is updated as needed

## License

[Add your license here]

## Support

For issues or questions:
1. Check the documentation in the `markdown/` directory
2. Verify all services are running (Redis, Qdrant, Ollama)
3. Review configuration files
4. Check error logs for specific issues
