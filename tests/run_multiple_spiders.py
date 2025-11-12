"""
Example script to run multiple spiders concurrently.
Each spider will coordinate via the shared duplicate filter.
"""
import multiprocessing
from Crawler import Crawler
import sys
import time


def run_spider(spider_id: int, config_path: str):
    """Run a single spider instance."""
    print(f"[Spider {spider_id}] Starting...")
    try:
        crawler = Crawler(config_path)
        crawler.start()
        print(f"[Spider {spider_id}] Completed")
    except Exception as e:
        print(f"[Spider {spider_id}] Error: {e}")
        sys.exit(1)


def main():
    """Launch multiple spider processes."""
    config_path = 'config.json'
    num_spiders = 3  # Number of concurrent spiders
    
    print(f"Launching {num_spiders} spiders with shared URL deduplication...")
    print(f"Using config: {config_path}")
    print("-" * 60)
    
    # Create process pool
    processes = []
    for i in range(num_spiders):
        p = multiprocessing.Process(
            target=run_spider,
            args=(i + 1, config_path)
        )
        processes.append(p)
        p.start()
        # Small delay to stagger starts
        time.sleep(0.5)
    
    # Wait for all processes to complete
    for i, p in enumerate(processes):
        p.join()
        print(f"Spider {i + 1} finished with exit code: {p.exitcode}")
    
    print("-" * 60)
    print("All spiders completed!")


if __name__ == '__main__':
    # Required for multiprocessing on some platforms
    multiprocessing.set_start_method('spawn', force=True)
    main()
