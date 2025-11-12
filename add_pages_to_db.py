from src.crawlers import CrawlerCreator
from src.utils import clear_redis

clear_redis()
crawler = CrawlerCreator('config.json')
crawler.start()