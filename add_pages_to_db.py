import argparse
from src.crawlers import CrawlerCreator
from src.utils import clear_redis

def main(config_path, *args, **kwargs):
    clear_redis()
    crawler = CrawlerCreator(config_path, *args, **kwargs)
    crawler.start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add pages to database with optional page count limit')
    parser.add_argument('--config', type=str, default='config.json', help='Path to config file')
    parser.add_argument('--pagecount', type=int, help='Maximum number of pages to crawl')
    
    args = parser.parse_args()
    
    kwargs = {}
    if args.pagecount:
        kwargs['pagecount'] = args.pagecount
    
    main(args.config, **kwargs)