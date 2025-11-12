"""Duplicate filtering modules."""
from .dupefilter import RedisBasedDupeFilter, SQLiteBasedDupeFilter, FileBasedDupeFilter

__all__ = ['RedisBasedDupeFilter', 'SQLiteBasedDupeFilter', 'FileBasedDupeFilter']
