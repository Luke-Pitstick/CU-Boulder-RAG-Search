"""
Utility functions to prevent corrupted data from being added to the vector store.
Add these filters to your pipeline to validate text before embedding.
"""

import re
from typing import Optional


def is_valid_text(text: str, min_length: int = 50, max_replacement_ratio: float = 0.05) -> bool:
    """
    Check if text is valid for embedding.
    
    Args:
        text: The text to validate
        min_length: Minimum acceptable text length
        max_replacement_ratio: Maximum ratio of replacement characters (�)
    
    Returns:
        True if text is valid, False otherwise
    """
    if not text or len(text) < min_length:
        return False
    
    # Check for excessive replacement characters
    replacement_count = text.count('�')
    replacement_ratio = replacement_count / len(text)
    
    if replacement_ratio > max_replacement_ratio:
        return False
    
    # Check for reasonable ASCII ratio
    ascii_count = sum(1 for c in text if ord(c) < 128)
    ascii_ratio = ascii_count / len(text)
    
    # Should be at least 70% ASCII for English text
    if ascii_ratio < 0.7:
        return False
    
    # Check for reasonable alphanumeric content
    alnum_count = sum(1 for c in text if c.isalnum() or c.isspace())
    alnum_ratio = alnum_count / len(text)
    
    # Should be at least 80% alphanumeric + spaces
    if alnum_ratio < 0.8:
        return False
    
    return True


def clean_text(text: str) -> Optional[str]:
    """
    Clean text by removing problematic characters.
    
    Args:
        text: The text to clean
    
    Returns:
        Cleaned text or None if text is too corrupted to salvage
    """
    if not text:
        return None
    
    # Remove replacement characters
    text = text.replace('�', '')
    
    # Remove control characters except newlines and tabs
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Check if cleaned text is still valid
    if is_valid_text(text):
        return text
    
    return None


def validate_scraped_item(item: dict) -> bool:
    """
    Validate a scraped item before adding to the vector store.
    Use this in your Scrapy pipeline.
    
    Args:
        item: Dictionary containing scraped data with 'page_content' field
    
    Returns:
        True if item is valid, False otherwise
    """
    page_content = item.get('page_content', '')
    
    if not page_content:
        return False
    
    # Try to clean the text
    cleaned = clean_text(page_content)
    
    if cleaned and is_valid_text(cleaned):
        # Update the item with cleaned text
        item['page_content'] = cleaned
        return True
    
    return False


# Example Scrapy Pipeline Integration
class TextValidationPipeline:
    """
    Scrapy pipeline to filter out corrupted text items.
    
    Add to your Scrapy settings:
        ITEM_PIPELINES = {
            'prevent_corrupted_data.TextValidationPipeline': 100,
        }
    """
    
    def __init__(self):
        self.dropped_count = 0
        self.processed_count = 0
    
    def process_item(self, item, spider):
        self.processed_count += 1
        
        # Validate the item
        if not validate_scraped_item(item):
            self.dropped_count += 1
            spider.logger.warning(
                f"Dropped corrupted item from {item.get('url', 'unknown')}"
            )
            # Drop the item
            from scrapy.exceptions import DropItem
            raise DropItem("Invalid or corrupted text content")
        
        return item
    
    def close_spider(self, spider):
        spider.logger.info(
            f"Text Validation: Processed {self.processed_count} items, "
            f"dropped {self.dropped_count} corrupted items "
            f"({self.dropped_count/self.processed_count*100:.1f}%)"
        )


# Example usage in your embedding script
def filter_documents_before_embedding(documents: list) -> list:
    """
    Filter out corrupted documents before embedding.
    
    Args:
        documents: List of document dictionaries
    
    Returns:
        List of valid documents
    """
    valid_docs = []
    invalid_count = 0
    
    for doc in documents:
        page_content = doc.get('page_content', '')
        cleaned = clean_text(page_content)
        
        if cleaned and is_valid_text(cleaned):
            doc['page_content'] = cleaned
            valid_docs.append(doc)
        else:
            invalid_count += 1
            print(f"⚠️  Skipping invalid document: {doc.get('url', 'unknown')}")
    
    print(f"✅ Filtered {len(valid_docs)} valid documents, dropped {invalid_count} corrupted ones")
    return valid_docs


if __name__ == "__main__":
    # Test examples
    print("Testing text validation...\n")
    
    # Valid text
    valid = "This is a normal text about CU Boulder admission requirements."
    print(f"Valid text: {is_valid_text(valid)} ✓")
    
    # Corrupted text (like in the screenshot)
    corrupted = "��������������������������������������"
    print(f"Corrupted text: {is_valid_text(corrupted)} ✗")
    
    # Mixed text
    mixed = "Some text with a few � replacement characters"
    print(f"Mixed text: {is_valid_text(mixed)} ?")
    
    # Test cleaning
    print(f"\nCleaned corrupted: {clean_text(corrupted)}")
    print(f"Cleaned mixed: {clean_text(mixed)}")
