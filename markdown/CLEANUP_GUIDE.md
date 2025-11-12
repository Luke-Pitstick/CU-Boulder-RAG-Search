# Cleaning Up Corrupted Vectors in Qdrant

This guide helps you identify and remove corrupted vectors from your Qdrant database.

## Problem

Corrupted vectors have garbled text with encoding issues, appearing as `�` symbols or binary data. This typically happens due to:
- Encoding problems during web scraping
- Binary files being scraped as text (PDFs, images, etc.)
- Character encoding mismatches
- Network corruption during data transfer

## Solution 1: Clean Up Existing Corrupted Vectors

### Step 1: Scan for Corrupted Vectors

Run the cleanup script to identify corrupted vectors:

```bash
python cleanup_corrupted_vectors.py
```

This will:
1. ✅ Scan all vectors in your collection
2. ✅ Identify vectors with garbled/corrupted text
3. ✅ Show you examples of corrupted vectors
4. ✅ Calculate the percentage of corrupted data

### Step 2: Review and Delete

The script will show you:
- Total number of corrupted vectors
- Sample corrupted vectors with their URLs
- Percentage of corruption

After review, confirm deletion by typing `yes` when prompted.

### Expected Output:

```
🔍 Scanning collection 'cuboulder_pages' for corrupted vectors...
📊 Total points in collection: 1000
Scanning vectors: 100%|████████████| 1000/1000
✅ Scan complete!
🔴 Found 150 corrupted vectors (15.00%)

📋 Sample corrupted vectors:
  1. ID: 01eeab2e-5391-4e1f-a224-52f36134e7fc
     URL: https://www.colorado.edu/...
     Length: 2450 chars
     Preview: ���������...

⚠️  WARNING: This will delete 150 vectors from your collection!
Do you want to proceed with deletion? (yes/no):
```

### Step 3: Verify Cleanup

After deletion, you can verify the collection:
- Check Qdrant dashboard
- Run the script again to confirm no corrupted vectors remain
- Review `deleted_vectors.json` for a record of what was deleted

## Solution 2: Prevent Future Corruption

### Option A: Add to Scrapy Pipeline

Edit your Scrapy spider settings to include the validation pipeline:

```python
# In your scrapy settings.py or spider
from prevent_corrupted_data import TextValidationPipeline

ITEM_PIPELINES = {
    'prevent_corrupted_data.TextValidationPipeline': 100,
    # ... your other pipelines
}
```

### Option B: Filter Before Embedding

If you're manually adding documents, filter them first:

```python
from prevent_corrupted_data import filter_documents_before_embedding

# Before embedding
documents = load_your_documents()
clean_documents = filter_documents_before_embedding(documents)

# Now embed only clean documents
embed_documents(clean_documents)
```

### Option C: Update Your Spider

Add validation to your spider's parse method:

```python
from prevent_corrupted_data import is_valid_text, clean_text

def parse(self, response):
    content = response.xpath('//body//text()').getall()
    content = ' '.join(content)
    
    # Clean and validate
    cleaned_content = clean_text(content)
    
    if cleaned_content and is_valid_text(cleaned_content):
        yield {
            'url': response.url,
            'page_content': cleaned_content,
            'title': response.xpath('//title/text()').get()
        }
    else:
        self.logger.warning(f"Skipping corrupted page: {response.url}")
```

## Common Causes and Fixes

### 1. PDF Files Being Scraped as Text
**Cause:** Spider is downloading PDFs and treating them as HTML  
**Fix:** Add PDF detection and skip or process separately:
```python
if response.url.endswith('.pdf') or 'application/pdf' in response.headers.get('Content-Type', b'').decode():
    self.logger.info(f"Skipping PDF: {response.url}")
    return
```

### 2. Character Encoding Issues
**Cause:** Website uses non-UTF-8 encoding  
**Fix:** Detect and convert encoding:
```python
import chardet

def detect_and_decode(content_bytes):
    detected = chardet.detect(content_bytes)
    encoding = detected['encoding']
    return content_bytes.decode(encoding, errors='replace')
```

### 3. Binary Files
**Cause:** Images, videos, or other binary files being scraped  
**Fix:** Check Content-Type header:
```python
content_type = response.headers.get('Content-Type', b'').decode()
if not content_type.startswith('text/'):
    self.logger.info(f"Skipping non-text content: {response.url}")
    return
```

## Advanced: Batch Cleanup by URL Pattern

If you know specific URL patterns are corrupted:

```python
from cleanup_corrupted_vectors import scan_corrupted_vectors, delete_corrupted_vectors
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Find all points matching a URL pattern
points = client.scroll(
    collection_name="cuboulder_pages",
    scroll_filter={
        "must": [{
            "key": "url",
            "match": {
                "text": "facultyaffairs/media"  # Pattern to match
            }
        }]
    },
    limit=1000
)[0]

# Extract IDs and delete
ids_to_delete = [point.id for point in points]
delete_corrupted_vectors(ids_to_delete, dry_run=False)
```

## Monitoring

After cleanup, monitor your collection:

1. **Check collection stats:**
```bash
curl http://localhost:6333/collections/cuboulder_pages
```

2. **Run periodic scans:**
```bash
# Add to cron for weekly checks
0 0 * * 0 python cleanup_corrupted_vectors.py
```

3. **Track dropped items:**
The `TextValidationPipeline` logs dropped items automatically.

## Recovery

If you accidentally delete valid vectors:
- Review `deleted_vectors.json` for deleted IDs
- Re-crawl specific URLs if needed
- Restore from backup if available

## Best Practices

1. ✅ **Validate before embedding** - Always filter data before adding to vector store
2. ✅ **Monitor scraping logs** - Watch for encoding warnings
3. ✅ **Use content-type checking** - Skip non-text files
4. ✅ **Handle encoding properly** - Detect and convert encodings
5. ✅ **Regular cleanup** - Run periodic scans for corruption
6. ✅ **Backup before bulk delete** - Export collection before major cleanups

## Troubleshooting

### "Collection not found"
- Verify collection name in `config_llm.json`
- Check Qdrant is running: `curl http://localhost:6333/health`

### "Too many vectors flagged as corrupted"
- Adjust thresholds in `cleanup_corrupted_vectors.py`
- Review examples to see if detection is too aggressive

### "Script is too slow"
- Increase `batch_size` parameter
- Run during off-peak hours
- Consider processing in parallel

## Need Help?

1. Review the corrupted examples shown by the script
2. Check your spider logs for encoding warnings
3. Verify source URLs are accessible
4. Test with a small subset first (use dry_run=True)

---

**Remember:** Always backup your Qdrant data before bulk deletions!
