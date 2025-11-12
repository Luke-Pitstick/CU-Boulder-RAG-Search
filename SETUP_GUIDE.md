# CU Boulder Enhanced Search Setup Guide

This guide will help you set up the enhanced CU Boulder search system with local LLM integration.

## Prerequisites

- Python 3.8+
- Ollama installed locally
- Qdrant vector database running
- CU Boulder data already crawled and indexed

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install and Setup Ollama

#### Install Ollama
```bash
# macOS
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/
```

#### Start Ollama
```bash
ollama serve
```

#### Pull LLM Model
```bash
# Recommended model for good performance
ollama pull llama3.2

# Alternative models:
# ollama pull llama3.1:8b  # Larger, more capable
# ollama pull qwen2.5:7b   # Good alternative
# ollama pull mistral      # Lightweight option
```

### 3. Setup Qdrant Vector Database

#### Start Qdrant (if not already running)
```bash
# Using Docker (recommended)
docker run -p 6333:6333 qdrant/qdrant

# Or install locally
# Follow instructions at https://qdrant.tech/documentation/
```

#### Verify Data is Indexed
Make sure your CU Boulder data is already indexed in the `cuboulder_pages` collection.

### 4. Configuration

The system uses `config_llm.json` for configuration. You can modify:

- **LLM Model**: Change `"model"` to use different Ollama models
- **Device**: Set `"device"` to `"cuda"` for NVIDIA GPUs, `"mps"` for Apple Silicon, or `"cpu"`
- **Retrieval Parameters**: Adjust `k`, `fetch_k`, and `lambda_mult` for different search behaviors

## Usage

### Basic Interactive Search
```bash
python search.py
```

### Command Line Options

```bash
# Single query
python search.py --query "How do I apply to CU Boulder?"

# Use different model
python search.py --model mistral --query "What are the tuition fees?"

# Save results to file
python search.py --query "Campus housing" --output results.json --format markdown

# Session mode (saves all queries)
python search.py --session

# Basic search without LLM (just retrieval)
python search.py --query "Computer science" --no-llm
```

### Interactive Commands

When running in interactive mode, you can use:

- `save [filename]` - Save last result as JSON
- `export markdown` - Export as Markdown file
- `export html` - Export as HTML file  
- `stats` - Show session statistics
- `help` - Show available commands
- `quit` - Exit the program

## Features

### 🔍 Local LLM Integration
- Uses Ollama for completely local LLM inference
- No API keys or external services required
- Multiple model support (Llama3, Mistral, Qwen, etc.)

### 🔗 Source Link Extraction
- Automatically extracts and displays source URLs
- Shows page titles and content snippets
- Deduplicates similar sources

### 📊 Multiple Output Formats
- **Console**: Rich formatted output for terminal
- **JSON**: Structured data for programmatic use
- **Markdown**: Readable format for documentation
- **HTML**: Web-ready format with styling

### 📈 Performance Metrics
- Tracks retrieval and generation times
- Shows number of sources used
- Session statistics and history

### 💾 Search Sessions
- Save and load search sessions
- Export results in multiple formats
- Track query history and performance

## Troubleshooting

### Common Issues

#### "Ollama not found" or "Connection failed"
```bash
# Check if Ollama is running
ollama list

# Start Ollama if not running
ollama serve

# Check model is downloaded
ollama list
# If not present, download with:
ollama pull llama3.2
```

#### "Qdrant connection failed"
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# Start Qdrant if needed
docker run -p 6333:6333 qdrant/qdrant
```

#### "Import errors"
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check Python version (requires 3.8+)
python --version
```

#### "CUDA out of memory" (GPU users)
- Reduce `max_tokens` in config
- Use smaller model like `mistral`
- Set device to `"cpu"` in config

#### Slow performance
- Ensure you're using GPU acceleration (`"device": "cuda"` or `"mps"`)
- Try smaller models for faster inference
- Adjust `max_context_length` in config

### Performance Optimization

#### For Better Speed
1. Use smaller models: `mistral`, `qwen2.5:3b`
2. Reduce `max_context_length` to 2000-3000
3. Set `k` to 3-5 for fewer sources

#### For Better Quality
1. Use larger models: `llama3.1:8b`, `qwen2.5:14b`
2. Increase `max_context_length` to 6000-8000
3. Set `k` to 8-10 for more sources

#### For Resource Constraints
1. Set `"device": "cpu"` in config
2. Use lightweight models: `mistral`, `gemma2:2b`
3. Reduce `max_tokens` to 1024

## Advanced Configuration

### Custom Prompt Templates
Edit the `template` in `src/llm/enhanced_search.py` to customize how the LLM generates answers.

### Different Embedding Models
Change `embedding.model_name` in config to use different embedding models:
- `"sentence-transformers/all-MiniLM-L6-v2"` (faster, smaller)
- `"sentence-transformers/all-mpnet-base-v2"` (better quality)

### Multiple Vector Collections
Modify `vector_store.collection_name` to use different data sources or create separate search instances.

## Examples

### Academic Research Query
```bash
python search.py --query "What research is being done in quantum computing at CU Boulder?"
```

### Administrative Questions
```bash
python search.py --query "How do I get a student ID card?"
```

### Campus Life Information
```bash
python search.py --query "What dining options are available on campus?"
```

### Export for Documentation
```bash
python search.py --query "Academic calendar 2024" --output academic_calendar.md --format markdown
```

## Support

For issues or questions:

1. Check this guide for common problems
2. Verify all services are running (Ollama, Qdrant)
3. Check the configuration file settings
4. Review the error messages for specific issues

Enjoy your enhanced CU Boulder search experience! 🚀
