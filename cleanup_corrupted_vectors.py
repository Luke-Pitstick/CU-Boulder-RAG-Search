"""
Utility script to identify and remove corrupted vectors from Qdrant.
Corrupted vectors typically have garbled text with encoding issues (� symbols).
"""

import json
from qdrant_client import QdrantClient
from tqdm import tqdm
import re


def is_corrupted_text(text: str, threshold: float = 0.05) -> bool:
    """
    Check if text is corrupted based on the ratio of replacement characters.
    
    Args:
        text: The text content to check
        threshold: Max ratio of bad characters before considering corrupted (default 5%)
    
    Returns:
        True if text appears corrupted, False otherwise
    """
    if not text:
        return True
    
    # Count replacement characters (�) and other problematic patterns
    replacement_chars = text.count('�')
    
    # Also check for excessive control characters or binary patterns
    control_chars = sum(1 for c in text if ord(c) < 32 and c not in '\n\r\t')
    
    total_bad_chars = replacement_chars + control_chars
    bad_ratio = total_bad_chars / len(text)
    
    return bad_ratio > threshold


def is_mostly_garbled(text: str, threshold: float = 0.3) -> bool:
    """
    Check if text is mostly garbled/non-ASCII characters.
    
    Args:
        text: The text content to check
        threshold: Max ratio of non-ASCII chars before considering garbled
    
    Returns:
        True if text appears garbled, False otherwise
    """
    if not text:
        return True
    
    non_ascii = sum(1 for c in text if ord(c) > 127)
    non_ascii_ratio = non_ascii / len(text)
    
    return non_ascii_ratio > threshold


def scan_corrupted_vectors(
    collection_name: str = "cuboulder_pages",
    qdrant_url: str = "http://localhost:6333",
    batch_size: int = 100
):
    """
    Scan the collection and identify corrupted vectors.
    
    Args:
        collection_name: Name of the Qdrant collection
        qdrant_url: URL of the Qdrant server
        batch_size: Number of points to fetch per batch
    
    Returns:
        List of corrupted point IDs
    """
    print(f"🔍 Scanning collection '{collection_name}' for corrupted vectors...")
    
    client = QdrantClient(url=qdrant_url)
    
    # Get collection info
    collection_info = client.get_collection(collection_name)
    total_points = collection_info.points_count
    print(f"📊 Total points in collection: {total_points}")
    
    corrupted_ids = []
    corrupted_examples = []
    
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
                with_vectors=False  # We don't need the vectors, just the payload
            )
            
            if not points:
                break
            
            # Check each point
            for point in points:
                payload = point.payload or {}
                page_content = payload.get('page_content', '')
                
                # Check if corrupted
                if is_corrupted_text(page_content) or is_mostly_garbled(page_content):
                    corrupted_ids.append(point.id)
                    
                    # Save first 5 examples for review
                    if len(corrupted_examples) < 5:
                        corrupted_examples.append({
                            'id': point.id,
                            'url': payload.get('url', 'Unknown'),
                            'content_preview': page_content[:200] if page_content else 'Empty',
                            'content_length': len(page_content)
                        })
            
            processed += len(points)
            pbar.update(len(points))
            
            # Update offset for next batch
            offset = next_offset
            if offset is None:
                break
    
    print(f"\n✅ Scan complete!")
    print(f"🔴 Found {len(corrupted_ids)} corrupted vectors ({len(corrupted_ids)/total_points*100:.2f}%)")
    
    if corrupted_examples:
        print("\n📋 Sample corrupted vectors:")
        for i, example in enumerate(corrupted_examples, 1):
            print(f"\n  {i}. ID: {example['id']}")
            print(f"     URL: {example['url']}")
            print(f"     Length: {example['content_length']} chars")
            print(f"     Preview: {example['content_preview'][:100]}...")
    
    return corrupted_ids


def delete_corrupted_vectors(
    corrupted_ids: list,
    collection_name: str = "cuboulder_pages",
    qdrant_url: str = "http://localhost:6333",
    batch_size: int = 100,
    dry_run: bool = True
):
    """
    Delete corrupted vectors from the collection.
    
    Args:
        corrupted_ids: List of point IDs to delete
        collection_name: Name of the Qdrant collection
        qdrant_url: URL of the Qdrant server
        batch_size: Number of points to delete per batch
        dry_run: If True, only simulate deletion without actually deleting
    """
    if not corrupted_ids:
        print("✅ No corrupted vectors to delete!")
        return
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No vectors will be deleted")
        print(f"Would delete {len(corrupted_ids)} vectors")
        return
    
    print(f"\n🗑️  Deleting {len(corrupted_ids)} corrupted vectors...")
    
    client = QdrantClient(url=qdrant_url)
    
    # Delete in batches
    with tqdm(total=len(corrupted_ids), desc="Deleting vectors") as pbar:
        for i in range(0, len(corrupted_ids), batch_size):
            batch = corrupted_ids[i:i + batch_size]
            
            client.delete(
                collection_name=collection_name,
                points_selector=batch
            )
            
            pbar.update(len(batch))
    
    print(f"✅ Successfully deleted {len(corrupted_ids)} corrupted vectors!")


def main():
    """Main execution function"""
    print("="*70)
    print("🧹 Qdrant Vector Cleanup Utility")
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
    
    # Step 1: Scan for corrupted vectors
    corrupted_ids = scan_corrupted_vectors(
        collection_name=collection_name,
        qdrant_url=qdrant_url
    )
    
    if not corrupted_ids:
        print("\n🎉 No corrupted vectors found! Your collection is clean.")
        return
    
    # Step 2: Ask for confirmation
    print(f"\n⚠️  WARNING: This will delete {len(corrupted_ids)} vectors from your collection!")
    response = input("\nDo you want to proceed with deletion? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        delete_corrupted_vectors(
            corrupted_ids=corrupted_ids,
            collection_name=collection_name,
            qdrant_url=qdrant_url,
            dry_run=False
        )
        
        print("\n✅ Cleanup complete!")
        print(f"💾 Saved {len(corrupted_ids)} IDs to 'deleted_vectors.json' for reference")
        
        # Save deleted IDs for reference
        with open('deleted_vectors.json', 'w') as f:
            json.dump({
                'deleted_count': len(corrupted_ids),
                'deleted_ids': [str(id) for id in corrupted_ids]
            }, f, indent=2)
    else:
        print("\n❌ Deletion cancelled.")
        print("💡 Run with dry_run=True to see what would be deleted")


if __name__ == "__main__":
    main()
