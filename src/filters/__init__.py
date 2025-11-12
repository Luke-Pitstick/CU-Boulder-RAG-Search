"""Duplicate filtering modules."""
from .dupefilter import RedisBasedDupeFilter, SQLiteBasedDupeFilter, FileBasedDupeFilter
from .qdrant_dupefilter import QdrantDupeFilter

__all__ = ['RedisBasedDupeFilter', 'SQLiteBasedDupeFilter', 'FileBasedDupeFilter', 'QdrantDupeFilter']
