"""
Shared duplicate filter for coordinating multiple Scrapy spiders.
Prevents multiple spiders from scraping the same URLs.
"""
from scrapy.dupefilters import RFPDupeFilter
from scrapy.utils.request import fingerprint
import redis
import sqlite3
from pathlib import Path
from typing import Optional


class RedisBasedDupeFilter(RFPDupeFilter):
    """
    Redis-based duplicate filter that allows multiple spiders to share
    the same URL tracking database.
    
    Requires Redis server running. Install: pip install redis
    """
    
    def __init__(self, fingerprinter=None, redis_url: str = 'redis://localhost:6379/0', key_prefix: str = 'scrapy:dupefilter'):
        super().__init__(fingerprinter=fingerprinter)
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_client = None
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create instance from crawler."""
        settings = crawler.settings
        redis_url = settings.get('DUPEFILTER_REDIS_URL', 'redis://localhost:6379/0')
        key_prefix = settings.get('DUPEFILTER_KEY_PREFIX', 'scrapy:dupefilter')
        return cls(
            fingerprinter=crawler.request_fingerprinter,
            redis_url=redis_url,
            key_prefix=key_prefix
        )
    
    def open(self):
        """Connect to Redis when spider opens."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
    
    def close(self, reason):
        """Close Redis connection when spider closes."""
        if self.redis_client:
            self.redis_client.close()
    
    def request_seen(self, request):
        """
        Check if request has been seen by any spider.
        Returns True if already seen, False otherwise.
        """
        fp = self._get_request_fingerprint(request)
        
        # Use Redis SET with NX (only set if not exists)
        # Returns 1 if key was set (first time seeing URL)
        # Returns 0 if key already exists (URL already seen)
        added = self.redis_client.set(f"{self.key_prefix}:{fp}", "1", nx=True)
        
        return not added  # Return True if URL was already seen
    
    def _get_request_fingerprint(self, request):
        """Generate fingerprint for request."""
        fp_bytes = fingerprint(request)
        return fp_bytes.hex() if isinstance(fp_bytes, bytes) else str(fp_bytes)
    
    def clear(self):
        """Clear all stored fingerprints (use with caution!)."""
        pattern = f"{self.key_prefix}:*"
        for key in self.redis_client.scan_iter(match=pattern):
            self.redis_client.delete(key)



class SQLiteBasedDupeFilter(RFPDupeFilter):
    """
    SQLite-based duplicate filter for multiple spiders on the same machine.
    Uses file-based SQLite database with proper locking.
    
    No additional dependencies required.
    """
    
    def __init__(self, fingerprinter=None, db_path: str = 'shared_urls.db'):
        super().__init__(fingerprinter=fingerprinter)
        self.db_path = Path(db_path)
        self.conn = None
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create instance from crawler."""
        settings = crawler.settings
        db_path = settings.get('DUPEFILTER_DB_PATH', 'shared_urls.db')
        return cls(
            fingerprinter=crawler.request_fingerprinter,
            db_path=db_path
        )
    
    def open(self):
        """Initialize SQLite database with proper settings."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect with timeout and WAL mode for better concurrency
        self.conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            isolation_level='DEFERRED',
            check_same_thread=False
        )
        
        # Enable WAL mode for better concurrent access
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA synchronous=NORMAL')
        
        # Create table if not exists
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS seen_urls (
                fingerprint TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def close(self, reason):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def request_seen(self, request):
        """
        Check if request has been seen by any spider.
        Returns True if already seen, False otherwise.
        """
        fp = self._get_request_fingerprint(request)
        
        try:
            # Try to insert the fingerprint
            self.conn.execute(
                'INSERT INTO seen_urls (fingerprint) VALUES (?)',
                (fp,)
            )
            self.conn.commit()
            return False  # Successfully inserted, URL not seen before
        except sqlite3.IntegrityError:
            # Primary key constraint violated - URL already exists
            return True  # URL already seen
    
    def _get_request_fingerprint(self, request):
        """Generate fingerprint for request."""
        fp_bytes = fingerprint(request)
        return fp_bytes.hex() if isinstance(fp_bytes, bytes) else str(fp_bytes)
    
    def clear(self):
        """Clear all stored fingerprints (use with caution!)."""
        self.conn.execute('DELETE FROM seen_urls')
        self.conn.commit()


class FileBasedDupeFilter(RFPDupeFilter):
    """
    Simple file-based duplicate filter using a text file.
    Less efficient but works without any dependencies.
    
    Note: This has race conditions with concurrent access.
    Use SQLite or Redis for production.
    """
    
    def __init__(self, fingerprinter=None, file_path: str = 'seen_urls.txt'):
        super().__init__(fingerprinter=fingerprinter)
        self.file_path = Path(file_path)
        self.seen_fingerprints = set()
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create instance from crawler."""
        settings = crawler.settings
        file_path = settings.get('DUPEFILTER_FILE_PATH', 'seen_urls.txt')
        return cls(
            fingerprinter=crawler.request_fingerprinter,
            file_path=file_path
        )
    
    def open(self):
        """Load existing fingerprints from file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                self.seen_fingerprints = set(line.strip() for line in f)
    
    def close(self, reason):
        """Save fingerprints to file."""
        with open(self.file_path, 'w') as f:
            for fp in sorted(self.seen_fingerprints):
                f.write(f"{fp}\n")
    
    def request_seen(self, request):
        """
        Check if request has been seen.
        Returns True if already seen, False otherwise.
        """
        fp = self._get_request_fingerprint(request)
        
        if fp in self.seen_fingerprints:
            return True
        
        self.seen_fingerprints.add(fp)
        
        # Append to file immediately (for cross-process visibility)
        with open(self.file_path, 'a') as f:
            f.write(f"{fp}\n")
        
        return False
    
    def _get_request_fingerprint(self, request):
        """Generate fingerprint for request."""
        fp_bytes = fingerprint(request)
        return fp_bytes.hex() if isinstance(fp_bytes, bytes) else str(fp_bytes)
    
    def clear(self):
        """Clear all stored fingerprints."""
        self.seen_fingerprints.clear()
        if self.file_path.exists():
            self.file_path.unlink()
