# Multi-Spider Coordination Guide

This guide explains how to run multiple spiders concurrently without scraping duplicate pages.

## Overview

The shared duplicate filter system allows multiple spider instances to coordinate and avoid scraping the same URLs. Three implementations are available:

1. **SQLite** (Default) - File-based, no dependencies, good for local multi-process
2. **Redis** - Best for distributed crawling across machines
3. **File** - Simple text file, has race conditions (not recommended for production)

## Quick Start

### 1. Update Your Config

Add the duplicate filter settings to your `config.json`:

```json
{
  "settings": {
    "DUPEFILTER_CLASS": "sqlite",
    "DUPEFILTER_DB_PATH": "shared_urls.db"
  }
}
```

### 2. Run Multiple Spiders

**Option A: Using the provided script**
```bash
python run_multiple_spiders.py
```

**Option B: Manual multi-process**
```bash
# Terminal 1
python main.py

# Terminal 2 (simultaneously)
python main.py

# Terminal 3 (simultaneously)
python main.py
```

All spiders will coordinate automatically - no duplicate pages will be scraped!

## Configuration Options

### SQLite (Recommended for Local)

**Pros:**
- No additional dependencies
- Good concurrent access with WAL mode
- Persistent across runs
- Works on same machine

**Config:**
```json
{
  "settings": {
    "DUPEFILTER_CLASS": "sqlite",
    "DUPEFILTER_DB_PATH": "shared_urls.db"
  }
}
```

### Redis (Recommended for Distributed)

**Pros:**
- Excellent for distributed crawling
- Very fast
- Supports multiple machines
- Built-in expiration support

**Requirements:**
```bash
pip install redis
# Start Redis server
redis-server
```

**Config:**
```json
{
  "settings": {
    "DUPEFILTER_CLASS": "redis",
    "DUPEFILTER_REDIS_URL": "redis://localhost:6379/0",
    "DUPEFILTER_KEY_PREFIX": "scrapy:dupefilter:myproject"
  }
}
```

### File-Based (Simple but Limited)

**Pros:**
- No dependencies
- Simple to understand

**Cons:**
- Race conditions possible
- Not recommended for production

**Config:**
```json
{
  "settings": {
    "DUPEFILTER_CLASS": "file",
    "DUPEFILTER_FILE_PATH": "seen_urls.txt"
  }
}
```

## How It Works

1. Each spider checks the shared store before scraping a URL
2. If URL exists → skip it
3. If URL is new → mark it as seen and scrape it
4. All spiders see the same shared state

### URL Fingerprinting

URLs are converted to fingerprints (hashes) that include:
- URL path
- Query parameters
- Fragment identifiers

This ensures exact duplicate detection.

## Advanced Usage

### Clearing the Duplicate Filter

**SQLite:**
```bash
rm shared_urls.db
```

**Redis:**
```bash
redis-cli FLUSHDB
# Or use the clear method in code
```

**File:**
```bash
rm seen_urls.txt
```

### Monitoring Progress

**SQLite:**
```bash
sqlite3 shared_urls.db "SELECT COUNT(*) FROM seen_urls;"
```

**Redis:**
```bash
redis-cli DBSIZE
```

**File:**
```bash
wc -l seen_urls.txt
```

### Custom Implementation

You can create your own duplicate filter by extending `BaseDupeFilter`:

```python
from scrapy.dupefilters import BaseDupeFilter

class MyCustomDupeFilter(BaseDupeFilter):
    def request_seen(self, request):
        # Your logic here
        pass
```

## Troubleshooting

### SQLite: "Database is locked"

Increase timeout or ensure WAL mode is enabled (already configured).

### Redis: Connection refused

Make sure Redis server is running:
```bash
redis-server
```

### URLs still being duplicated

1. Check that all spiders use the same config
2. Verify the duplicate filter is properly configured
3. Check logs for errors

## Performance Tips

1. **SQLite**: Use WAL mode (already enabled) for better concurrency
2. **Redis**: Use connection pooling for high-volume crawling
3. **All**: Monitor memory usage with large URL sets
4. **All**: Consider TTL/expiration for long-running crawls

## Example: Distributed Crawling

### Machine 1:
```bash
# Start Redis (or use remote Redis)
redis-server

# Run spider
python main.py
```

### Machine 2:
```json
{
  "settings": {
    "DUPEFILTER_CLASS": "redis",
    "DUPEFILTER_REDIS_URL": "redis://machine1-ip:6379/0"
  }
}
```
```bash
python main.py
```

Both machines will coordinate automatically!

## Best Practices

1. **Use SQLite** for single-machine multi-process crawling
2. **Use Redis** for distributed crawling across machines
3. **Set unique key prefixes** when running multiple projects
4. **Monitor the store size** for long-running crawls
5. **Clear old data** periodically if needed
6. **Test with small page counts** first

## Integration with Existing Code

Your existing `Crawler` class automatically supports shared deduplication. Just update the config - no code changes needed!

```python
# This automatically uses shared deduplication
crawler = Crawler('config.json')
crawler.start()
```
