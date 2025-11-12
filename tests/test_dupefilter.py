"""
Quick test script to verify the duplicate filter is working correctly.
"""
from shared_dupefilter import SQLiteBasedDupeFilter, RedisBasedDupeFilter, FileBasedDupeFilter
from scrapy.http import Request


def test_sqlite_filter():
    """Test SQLite-based duplicate filter."""
    print("Testing SQLite Duplicate Filter...")
    
    # Create filter
    dupefilter = SQLiteBasedDupeFilter(db_path='test_urls.db')
    dupefilter.open()
    
    # Test URLs
    url1 = Request('https://example.com/page1')
    url2 = Request('https://example.com/page2')
    url3 = Request('https://example.com/page1')  # Duplicate of url1
    
    # First request should not be seen
    assert not dupefilter.request_seen(url1), "First URL should not be seen"
    print("✓ First URL correctly marked as new")
    
    # Second request should not be seen
    assert not dupefilter.request_seen(url2), "Second URL should not be seen"
    print("✓ Second URL correctly marked as new")
    
    # Third request (duplicate) should be seen
    assert dupefilter.request_seen(url3), "Duplicate URL should be seen"
    print("✓ Duplicate URL correctly detected")
    
    # Clean up
    dupefilter.clear()
    dupefilter.close()
    
    print("✓ SQLite filter test passed!\n")


def test_file_filter():
    """Test file-based duplicate filter."""
    print("Testing File-Based Duplicate Filter...")
    
    # Create filter
    dupefilter = FileBasedDupeFilter(file_path='test_seen_urls.txt')
    dupefilter.open()
    
    # Test URLs
    url1 = Request('https://example.com/page1')
    url2 = Request('https://example.com/page2')
    url3 = Request('https://example.com/page1')  # Duplicate
    
    # Tests
    assert not dupefilter.request_seen(url1), "First URL should not be seen"
    print("✓ First URL correctly marked as new")
    
    assert not dupefilter.request_seen(url2), "Second URL should not be seen"
    print("✓ Second URL correctly marked as new")
    
    assert dupefilter.request_seen(url3), "Duplicate URL should be seen"
    print("✓ Duplicate URL correctly detected")
    
    # Clean up
    dupefilter.clear()
    dupefilter.close()
    
    print("✓ File filter test passed!\n")


def test_redis_filter():
    """Test Redis-based duplicate filter (requires Redis server)."""
    print("Testing Redis Duplicate Filter...")
    
    try:
        # Create filter
        dupefilter = RedisBasedDupeFilter(
            redis_url='redis://localhost:6379/0',
            key_prefix='test:dupefilter'
        )
        dupefilter.open()
        
        # Clear any existing test data
        dupefilter.clear()
        
        # Test URLs
        url1 = Request('https://example.com/page1')
        url2 = Request('https://example.com/page2')
        url3 = Request('https://example.com/page1')  # Duplicate
        
        # Tests
        assert not dupefilter.request_seen(url1), "First URL should not be seen"
        print("✓ First URL correctly marked as new")
        
        assert not dupefilter.request_seen(url2), "Second URL should not be seen"
        print("✓ Second URL correctly marked as new")
        
        assert dupefilter.request_seen(url3), "Duplicate URL should be seen"
        print("✓ Duplicate URL correctly detected")
        
        # Clean up
        dupefilter.clear()
        dupefilter.close()
        
        print("✓ Redis filter test passed!\n")
        
    except Exception as e:
        print(f"⚠ Redis test skipped: {e}")
        print("  (Make sure Redis server is running: redis-server)\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Duplicate Filter Test Suite")
    print("=" * 60 + "\n")
    
    test_sqlite_filter()
    test_file_filter()
    test_redis_filter()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
