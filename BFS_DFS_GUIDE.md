# BFS vs DFS Crawling Guide

## ✅ BFS is Now Enabled!

Your crawler is now set to use **Breadth-First Search (BFS)** instead of Depth-First Search (DFS).

## 🔄 What Changed?

### Updated Files:
1. **`config.json`** - Added `"USE_BFS": true`
2. **`src/crawlers/CrawlerCreator.py`** - Added BFS/DFS configuration logic

## 📊 BFS vs DFS: What's the Difference?

### **Depth-First Search (DFS)** - Default Scrapy Behavior
```
Homepage
  └─> Link 1
      └─> Link 1.1
          └─> Link 1.1.1  ← Goes deep first
              └─> Link 1.1.1.1
```

**Characteristics:**
- ✅ Follows links deeply before going wide
- ✅ Good for finding specific deep content quickly
- ❌ May miss important top-level pages if interrupted
- ❌ Can get stuck in deep link chains

**Example:** Starts at homepage → About page → Staff directory → Individual staff page → That person's publications → etc.

---

### **Breadth-First Search (BFS)** - Now Enabled!
```
Homepage
  ├─> Link 1        ← Crawls all links at same level first
  ├─> Link 2
  ├─> Link 3
  └─> Link 4
      ├─> Link 1.1
      ├─> Link 1.2
      └─> Link 1.3
```

**Characteristics:**
- ✅ Crawls all pages at same depth before going deeper
- ✅ Gets important top-level content first
- ✅ Better for interrupted crawls (saves important pages first)
- ✅ More predictable crawl order

**Example:** Starts at homepage → All main sections (About, Admissions, Academics) → All subsections → Individual pages

## 🎯 When to Use Each

### Use **BFS** (Current Setting) When:
- ✅ You want to prioritize top-level pages
- ✅ You have page limits (`CLOSESPIDER_PAGECOUNT`)
- ✅ You want broader coverage before depth
- ✅ Crawl might be interrupted
- ✅ **You want the most important pages first** ⭐

### Use **DFS** When:
- ✅ You need to fully explore specific sections
- ✅ No page limits (crawling entire site)
- ✅ Deep content is more valuable than broad content
- ✅ Following specific link chains

## 🔧 How to Switch

### Enable BFS (Current):
```json
{
  "settings": {
    "USE_BFS": true
  }
}
```

### Enable DFS:
```json
{
  "settings": {
    "USE_BFS": false
  }
}
```

Or simply remove the line (DFS is default).

## 📈 Practical Example: CU Boulder

### With BFS (✅ Current):
```
Crawl Order:
1. https://www.colorado.edu/
2. https://www.colorado.edu/academics
3. https://www.colorado.edu/admissions
4. https://www.colorado.edu/about
5. https://www.colorado.edu/campus-life
...then deeper pages in each section
```

**Result:** Gets overview of entire university before diving into details.

### With DFS:
```
Crawl Order:
1. https://www.colorado.edu/
2. https://www.colorado.edu/academics
3. https://www.colorado.edu/academics/programs
4. https://www.colorado.edu/academics/programs/computer-science
5. https://www.colorado.edu/academics/programs/computer-science/courses
...deeply explores academics before moving to admissions
```

**Result:** Fully explores one section before moving to next.

## 🎓 For Your Use Case

Since you have `"CLOSESPIDER_PAGECOUNT": 1000` (stops after 1000 pages), **BFS is better** because:

1. ✅ **Broader coverage** - Gets pages from all major sections
2. ✅ **Better RAG results** - More diverse content for search
3. ✅ **More important pages first** - Main pages before deep details
4. ✅ **Interrupted crawls** - Still have valuable data if stopped early

## 📊 Technical Details

What the code actually changes:

```python
# BFS Settings (USE_BFS: true)
DEPTH_PRIORITY = 1  # Higher depth = higher priority
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'  # FIFO = First In First Out
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'

# DFS Settings (USE_BFS: false)
DEPTH_PRIORITY = 0  # Depth doesn't affect priority
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleLifoDiskQueue'  # LIFO = Last In First Out
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.LifoMemoryQueue'
```

## 🧪 Testing

You can verify BFS is working by checking your logs:

```bash
# Start a crawl and watch the URLs
python main.py | grep "Scraped:"

# BFS will show pages at similar depth levels clustered together
# DFS will show deep chains of related pages
```

## 💡 Pro Tip

You can combine BFS with `DEPTH_LIMIT` for optimal coverage:

```json
{
  "settings": {
    "USE_BFS": true,
    "DEPTH_LIMIT": 3,  // Only go 3 levels deep
    "CLOSESPIDER_PAGECOUNT": 1000
  }
}
```

This ensures you get:
- ✅ Top 3 levels of entire site
- ✅ No wasted crawls on very deep pages
- ✅ Maximum breadth within reasonable depth

---

**Your crawler is now optimized with BFS!** 🚀
