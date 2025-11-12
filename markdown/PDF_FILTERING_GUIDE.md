# PDF and Binary File Filtering Guide

## 🚨 Problem

Your RAG system has PDFs and other binary files that were incorrectly scraped, causing:
- Garbled text in search results
- Poor quality answers
- Wasted vector storage space
- Slower search performance

## ✅ Complete Solution

### Step 1: Clean Up Existing PDF/Binary Vectors

Run the specialized cleanup script:

```bash
python cleanup_pdf_vectors.py
```

This script will:
1. ✅ Scan all vectors for PDF and binary content
2. ✅ Identify vectors by URL extension (.pdf, .doc, etc.)
3. ✅ Detect PDF indicators in the content itself
4. ✅ Show you examples grouped by issue type
5. ✅ Delete invalid vectors after confirmation

**Expected output:**
```
📄 PDF/Binary Vector Cleanup Utility
🔍 Scanning collection 'cuboulder_pages' for PDF/binary vectors...
📊 Total points in collection: 2500

✅ Scan complete!
🔴 Found 234 PDF/binary vectors (9.36%)

📊 Breakdown by issue type:
  • URL ends with .pdf: 189 vectors
  • URL contains .doc: 23 vectors
  • Contains PDF indicator: %PDF-: 15 vectors
  • URL ends with .ppt: 7 vectors
```

### Step 2: Prevention is Now Automatic! 🎉

Your codebase has been updated with **3 layers of protection**:

#### Layer 1: Spider Content-Type Filtering
**File:** `src/crawlers/university_crawler.py`

The spider now checks the HTTP Content-Type header:
- ✅ Only processes `text/html`, `text/plain`, `application/xhtml`
- ❌ Skips PDFs, images, documents automatically
- ❌ Skips files by URL extension

**What changed:**
```python
# NEW: Content-type check at spider level
content_type = response.headers.get('Content-Type', b'').decode()
if 'text/html' not in content_type:
    self.logger.warning(f'Skipping non-HTML: {response.url}')
    return

# NEW: URL extension check
if any(url.endswith(ext) for ext in ['.pdf', '.doc', '.ppt', ...]):
    self.logger.warning(f'Skipping file: {response.url}')
    return
```

#### Layer 2: Pipeline URL Validation
**File:** `src/pipeline.py`

The `DataCleaningPipeline` now validates URLs:
- ✅ Checks URL for invalid extensions
- ✅ Catches query param variations (e.g., `file.pdf?download=1`)
- ❌ Drops items before they reach the vector store

**What changed:**
```python
# NEW: URL validation in pipeline
if not self.is_valid_url(item.get('url', '')):
    raise DropItem(f"Invalid URL (PDF/binary): {item['url']}")
```

#### Layer 3: Text Quality Validation
**Already in place** - validates text content quality to catch any binary data that slipped through.

## 📊 Monitoring

After your next crawl, you'll see statistics like:

```
Data Cleaning Pipeline: Processed 1000 items, dropped 45 corrupted items (4.5%)
  • Dropped 30 PDF/binary files
  • Dropped 15 corrupted text items
```

## 🔍 What Gets Blocked

### By URL Extension:
- **Documents:** `.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- **Archives:** `.zip`, `.tar`, `.gz`, `.rar`, `.7z`
- **Media:** `.jpg`, `.png`, `.gif`, `.mp4`, `.mp3`, `.svg`
- **Executables:** `.exe`, `.dmg`, `.pkg`

### By Content-Type:
- `application/pdf`
- `image/*`
- `video/*`
- `audio/*`
- `application/zip`
- etc.

### By Content Pattern:
- PDF markers (`%PDF-`, `/Type /Page`)
- Binary data patterns
- Excessive replacement characters

## 🎯 Common Issues & Solutions

### Issue 1: Faculty profiles with PDF CVs

**Problem:** Faculty page links to their CV PDF
**Solution:** ✅ Already handled - PDF links won't be followed

### Issue 2: Course materials in PDF format

**Problem:** Course pages link to PDF syllabi
**Solution:** ✅ Already handled - content-type check catches these

### Issue 3: PDFs embedded with viewers

**Problem:** PDF displayed through a viewer URL
**Solution:** ✅ Handled - URL validation catches common patterns

### Issue 4: Some PDFs still getting through

**Solution:** 
1. Check spider logs for warnings
2. Add specific patterns to deny_patterns in `config.json`
3. Run `cleanup_pdf_vectors.py` periodically

## 🚀 Future Scraping Best Practices

### 1. **Monitor Your Logs**
Watch for spider warnings:
```bash
grep "Skipping" scrapy.log
```

### 2. **Use Custom Deny Patterns**
Add site-specific patterns to your config:
```json
{
  "crawl_rules": {
    "deny_patterns": [
      "r'/media/'",
      "r'/downloads/'",
      "r'/files/'",
      "r'.*\\.pdf$'"
    ]
  }
}
```

### 3. **Periodic Cleanup**
Run cleanup scripts monthly:
```bash
# Check for new PDFs
python cleanup_pdf_vectors.py

# Check for corruption
python cleanup_corrupted_vectors.py
```

### 4. **Review Dropped Items**
After each crawl, review what was dropped:
```bash
grep "DropItem" scrapy.log | head -20
```

### 5. **Test Before Large Crawls**
Test on a small subset first:
```bash
scrapy crawl university_crawler -a max_pages=50
```

## 📝 Advanced: Handle PDFs Properly

If you **want** to index PDF content (properly extracted), use a PDF text extraction library:

### Option A: PyPDF2 (Simple)
```python
import PyPDF2

def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text
```

### Option B: pdfplumber (Better)
```python
import pdfplumber

def extract_pdf_text(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text
```

### Add to Pipeline:
```python
class PDFProcessingPipeline:
    def process_item(self, item, spider):
        if item['url'].endswith('.pdf'):
            # Download and extract text properly
            text = extract_pdf_text(download_pdf(item['url']))
            item['text'] = text
        return item
```

## 🆘 Troubleshooting

### "Still seeing PDFs in search results"
1. Run `cleanup_pdf_vectors.py` again
2. Check logs: `grep "\.pdf" scrapy.log`
3. Verify filters are active in your pipeline

### "Too many items being dropped"
1. Check dropped item statistics in logs
2. Review examples: `grep "DropItem" scrapy.log | head -5`
3. Adjust thresholds if needed

### "Need to whitelist specific PDFs"
Modify the spider to allow specific patterns:
```python
# In university_crawler.py
if 'important-document.pdf' in url:
    # Process this specific PDF
    pass
```

## 📖 Summary

**What you need to do NOW:**
1. ✅ Run `python cleanup_pdf_vectors.py`
2. ✅ Confirm deletion when prompted
3. ✅ Re-crawl to get clean data

**What's automatic for FUTURE crawls:**
1. ✅ Content-type filtering in spider
2. ✅ URL validation in pipeline
3. ✅ Text quality validation
4. ✅ Statistics logging

**Ongoing maintenance:**
- Run cleanup scripts monthly
- Monitor logs for issues
- Adjust filters as needed

---

**Your RAG system is now PDF-proof!** 🎉
