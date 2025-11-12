# Quick Fix: Remove Corrupted Vectors

## 🚨 Problem
You have corrupted vectors in Qdrant showing garbled text like: `���������������`

## ✅ Solution (2 Steps)

### Step 1: Clean Up Existing Corrupted Data

```bash
python cleanup_corrupted_vectors.py
```

When prompted, type `yes` to delete the corrupted vectors.

### Step 2: Prevent Future Corruption

**Good news!** Your `DataCleaningPipeline` has been updated to automatically filter corrupted data. 

The next time you run your crawler, it will:
- ✅ Automatically detect corrupted/garbled text
- ✅ Drop invalid items before they reach the vector store
- ✅ Log statistics about dropped items

## 📊 What Changed

The `src/pipeline.py` file now includes:
- **`is_valid_text()`** - Validates text quality
- **Automatic filtering** - Drops corrupted items
- **Statistics tracking** - Reports dropped items at the end

## 🔍 How to Check If It's Working

After running your next crawl, look for log messages like:
```
Data Cleaning Pipeline: Processed 500 items, dropped 15 corrupted items (3.0%)
```

## 📝 Optional: Review Before Delete

If you want to see what will be deleted without actually deleting:

```python
# Edit cleanup_corrupted_vectors.py, line 211:
delete_corrupted_vectors(
    corrupted_ids=corrupted_ids,
    collection_name=collection_name,
    qdrant_url=qdrant_url,
    dry_run=True  # Change to True for preview only
)
```

## 🆘 Need More Details?

See `CLEANUP_GUIDE.md` for comprehensive documentation.

## ⚡ TL;DR

1. Run cleanup script: `python cleanup_corrupted_vectors.py`
2. Type `yes` to confirm deletion
3. Your pipeline is already updated to prevent new corrupted data
4. Done! 🎉
