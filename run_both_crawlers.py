"""
Run both colorado.edu and cubuffs.com crawlers concurrently.
Each crawler will scrape 200 pages and share the same duplicate filter.
"""
import multiprocessing
from src.crawlers.CrawlerCreator import CrawlerCreator
import sys
import time


def run_crawler(crawler_name: str, config_path: str):
    """Run a single crawler instance."""
    print(f"[{crawler_name}] Starting crawler with config: {config_path}")
    try:
        crawler = CrawlerCreator(config_path)
        crawler.start()
        print(f"[{crawler_name}] Completed successfully")
    except Exception as e:
        print(f"[{crawler_name}] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Launch both crawlers concurrently."""
    crawlers = [
        ("Colorado.edu", "config.json"),
        ("CUBuffs.com", "config_cubuffs.json")
    ]
    
    print("=" * 70)
    print("Starting concurrent crawlers:")
    for name, config in crawlers:
        print(f"  - {name}: {config}")
    print("=" * 70)
    print()
    
    # Create process pool
    processes = []
    for name, config_path in crawlers:
        p = multiprocessing.Process(
            target=run_crawler,
            args=(name, config_path)
        )
        processes.append((name, p))
        p.start()
        # Small delay to stagger starts
        time.sleep(1)
    
    # Wait for all processes to complete
    print("\nWaiting for crawlers to complete...")
    for name, p in processes:
        p.join()
        status = "✓ SUCCESS" if p.exitcode == 0 else f"✗ FAILED (exit code: {p.exitcode})"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 70)
    print("All crawlers completed!")
    print("=" * 70)


if __name__ == '__main__':
    # Required for multiprocessing on some platforms
    multiprocessing.set_start_method('spawn', force=True)
    main()
