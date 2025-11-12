"""
Utility script to identify and remove PDF and other non-HTML content from Qdrant.
These are vectors that were incorrectly scraped from binary files.
"""

import json
from qdrant_client import QdrantClient
from tqdm import tqdm
import re


# File extensions that should not be in a text vector store
INVALID_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.webp',
    '.mp4', '.mp3', '.avi', '.mov', '.wmv', '.flv', '.wav',
    '.exe', '.dmg', '.pkg', '.deb', '.rpm',
    '.csv', '.xml', '.json'  # These might be okay, but usually not useful for RAG
]

# Common patterns in PDF text extraction that indicate binary/corrupted content
PDF_INDICATORS = [
    'application/pdf',
    '%PDF-',
    'stream\nendstream',
    '/Type /Page',
    '/Contents ',
    'obj\nendobj',
]


def is_pdf_or_binary_content(text: str, url: str) -> tuple[bool, str]:
    """
    Check if content appears to be from a PDF or binary file.
    
    Args:
        text: The page content
        url: The URL of the page
    
    Returns:
        Tuple of (is_invalid, reason)
    """
    # Check URL extension
    url_lower = url.lower()
    for ext in INVALID_EXTENSIONS:
        if url_lower.endswith(ext):
            return True, f"URL ends with {ext}"
        # Also check for extension in middle of URL (e.g., file.pdf?download=1)
        if f'{ext}?' in url_lower or f'{ext}#' in url_lower:
            return True, f"URL contains {ext}"
    
    # Check for PDF indicators in content
    if text:
        for indicator in PDF_INDICATORS:
            if indicator in text:
                return True, f"Contains PDF indicator: {indicator[:20]}"
        
        # Check for excessive binary-like patterns
        # PDFs extracted as text often have many short "words" separated by spaces
        words = text.split()
        if len(words) > 50:
            # Count very short words (1-2 chars) which are common in binary text
            short_words = sum(1 for w in words[:100] if len(w) <= 2)
            if short_words > 40:  # More than 40% are very short
                return True, "Too many short words (likely binary)"
        
        # Check for common binary/PDF patterns
        if text.count('�') > len(text) * 0.02:  # More than 2% replacement chars
            return True, "High replacement character ratio"
    
    return False, ""


def scan_pdf_vectors(
    collection_name: str = "cuboulder_pages",
    qdrant_url: str = "http://localhost:6333",
    batch_size: int = 100
):
    """
    Scan the collection and identify PDF/binary vectors.
    
    Args:
        collection_name: Name of the Qdrant collection
        qdrant_url: URL of the Qdrant server
        batch_size: Number of points to fetch per batch
    
    Returns:
        List of PDF/binary point IDs and their details
    """
    print(f"🔍 Scanning collection '{collection_name}' for PDF/binary vectors...")
    
    client = QdrantClient(url=qdrant_url)
    
    # Get collection info
    collection_info = client.get_collection(collection_name)
    total_points = collection_info.points_count
    print(f"📊 Total points in collection: {total_points}")
    
    invalid_vectors = []
    examples_by_type = {}
    
    # Scroll through all points
    offset = None
    processed = 0
    
    with tqdm(total=total_points, desc="Scanning vectors") as pbar:
        while True:
            # Fetch batch of points
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                break
            
            # Check each point
            for point in points:
                payload = point.payload or {}
                url = payload.get('url', '')
                page_content = payload.get('page_content', '')
                
                # Check if this is PDF/binary content
                is_invalid, reason = is_pdf_or_binary_content(page_content, url)
                
                if is_invalid:
                    invalid_vectors.append({
                        'id': point.id,
                        'url': url,
                        'reason': reason
                    })
                    
                    # Save example for each reason type
                    if reason not in examples_by_type:
                        examples_by_type[reason] = {
                            'id': point.id,
                            'url': url,
                            'content_preview': page_content[:200] if page_content else 'Empty',
                            'content_length': len(page_content)
                        }
            
            processed += len(points)
            pbar.update(len(points))
            
            # Update offset for next batch
            offset = next_offset
            if offset is None:
                break
    
    print(f"\n✅ Scan complete!")
    print(f"🔴 Found {len(invalid_vectors)} PDF/binary vectors ({len(invalid_vectors)/total_points*100:.2f}%)")
    
    if examples_by_type:
        print(f"\n📋 Sample vectors by issue type:")
        for reason, example in list(examples_by_type.items())[:10]:
            print(f"\n  Issue: {reason}")
            print(f"  URL: {example['url']}")
            print(f"  Length: {example['content_length']} chars")
            if example['content_preview']:
                print(f"  Preview: {example['content_preview'][:100]}...")
    
    # Group by reason
    reason_counts = {}
    for vec in invalid_vectors:
        reason = vec['reason']
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    if reason_counts:
        print(f"\n📊 Breakdown by issue type:")
        for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {reason}: {count} vectors")
    
    return invalid_vectors


def delete_pdf_vectors(
    invalid_vectors: list,
    collection_name: str = "cuboulder_pages",
    qdrant_url: str = "http://localhost:6333",
    batch_size: int = 100,
    dry_run: bool = True
):
    """
    Delete PDF/binary vectors from the collection.
    
    Args:
        invalid_vectors: List of vector info dicts with 'id' field
        collection_name: Name of the Qdrant collection
        qdrant_url: URL of the Qdrant server
        batch_size: Number of points to delete per batch
        dry_run: If True, only simulate deletion
    """
    if not invalid_vectors:
        print("✅ No PDF/binary vectors to delete!")
        return
    
    invalid_ids = [vec['id'] for vec in invalid_vectors]
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No vectors will be deleted")
        print(f"Would delete {len(invalid_ids)} vectors")
        return
    
    print(f"\n🗑️  Deleting {len(invalid_ids)} PDF/binary vectors...")
    
    client = QdrantClient(url=qdrant_url)
    
    # Delete in batches
    with tqdm(total=len(invalid_ids), desc="Deleting vectors") as pbar:
        for i in range(0, len(invalid_ids), batch_size):
            batch = invalid_ids[i:i + batch_size]
            
            client.delete(
                collection_name=collection_name,
                points_selector=batch
            )
            
            pbar.update(len(batch))
    
    print(f"✅ Successfully deleted {len(invalid_ids)} PDF/binary vectors!")


def main():
    """Main execution function"""
    print("="*70)
    print("📄 PDF/Binary Vector Cleanup Utility")
    print("="*70)
    
    # Load config
    try:
        with open('config_llm.json', 'r') as f:
            config = json.load(f)
        
        collection_name = config['vector_store']['collection_name']
        qdrant_url = config['vector_store']['url']
    except FileNotFoundError:
        print("⚠️  config_llm.json not found, using defaults")
        collection_name = "cuboulder_pages"
        qdrant_url = "http://localhost:6333"
    
    print(f"\n📍 Configuration:")
    print(f"   Collection: {collection_name}")
    print(f"   Qdrant URL: {qdrant_url}")
    print()
    
    # Step 1: Scan for PDF/binary vectors
    invalid_vectors = scan_pdf_vectors(
        collection_name=collection_name,
        qdrant_url=qdrant_url
    )
    
    if not invalid_vectors:
        print("\n🎉 No PDF/binary vectors found! Your collection is clean.")
        return
    
    # Save details for reference
    print(f"\n💾 Saving list of invalid vectors to 'invalid_vectors.json'...")
    with open('invalid_vectors.json', 'w') as f:
        json.dump({
            'total_count': len(invalid_vectors),
            'vectors': invalid_vectors
        }, f, indent=2)
    
    # Step 2: Ask for confirmation
    print(f"\n⚠️  WARNING: This will delete {len(invalid_vectors)} vectors from your collection!")
    response = input("\nDo you want to proceed with deletion? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        delete_pdf_vectors(
            invalid_vectors=invalid_vectors,
            collection_name=collection_name,
            qdrant_url=qdrant_url,
            dry_run=False
        )
        
        print("\n✅ Cleanup complete!")
        print(f"📋 Details saved in 'invalid_vectors.json'")
    else:
        print("\n❌ Deletion cancelled.")
        print("💡 Run with dry_run=True to preview what would be deleted")


if __name__ == "__main__":
    main()
