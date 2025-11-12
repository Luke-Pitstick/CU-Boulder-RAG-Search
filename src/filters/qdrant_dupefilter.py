"""Custom duplicate filter that checks Qdrant vector database."""
from scrapy.dupefilters import BaseDupeFilter
from scrapy.http import Request
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


class QdrantDupeFilter(BaseDupeFilter):
    """
    Duplicate filter that checks if URLs already exist in Qdrant.
    This allows the crawler to skip URLs that have already been processed
    and stored in the vector database.
    """
    
    def __init__(self, qdrant_url="http://localhost:6333", collection_name="cuboulder_pages"):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.fingerprints = set()  # Track URLs seen in this session
        
    @classmethod
    def from_settings(cls, settings):
        """Initialize from Scrapy settings."""
        return cls(
            qdrant_url=settings.get('QDRANT_URL', 'http://localhost:6333'),
            collection_name=settings.get('QDRANT_COLLECTION', 'cuboulder_pages')
        )
    
    def request_seen(self, request: Request) -> bool:
        """
        Check if this URL has been seen before.
        Returns True if the URL should be filtered (skipped).
        """
        url = request.url
        
        # Check if we've seen it in this session
        if url in self.fingerprints:
            return True
        
        # Check if it exists in Qdrant
        try:
            existing = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.url",
                            match=MatchValue(value=url)
                        )
                    ]
                ),
                limit=1
            )
            
            # If we found points with this URL, it's a duplicate
            if existing[0]:
                self.fingerprints.add(url)  # Cache for this session
                return True
                
        except Exception as e:
            # If Qdrant check fails, log but don't filter
            # This ensures the crawler continues even if Qdrant is down
            print(f"Warning: Qdrant check failed for {url}: {e}")
            return False
        
        # Not a duplicate - add to fingerprints and allow
        self.fingerprints.add(url)
        return False
    
    def close(self, reason: str) -> None:
        """Clean up when spider closes."""
        self.fingerprints.clear()
