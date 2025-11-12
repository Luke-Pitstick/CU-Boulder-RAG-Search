import json
from pathlib import Path
from typing import Dict, Any
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import scrapy
from .university_crawler import UniversitySpider

class CrawlerCreator:
    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        self.settings = self._build_scrapy_settings()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate configuration from JSON file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with config_file.open('r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in config file: {e.msg}", e.doc, e.pos
            )
        
        # Validate required keys
        required_keys = ['base_url', 'settings']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise KeyError(f"Missing required config keys: {missing_keys}")
        
        return config
    
    def _build_scrapy_settings(self) -> scrapy.settings.Settings:
        """Build Scrapy settings from configuration."""
        settings = get_project_settings()
        
        # Extract settings with defaults
        config_settings = self.config.get('settings', {})
        
        # Determine which duplicate filter to use
        dupefilter_class = config_settings.get('DUPEFILTER_CLASS', 'redis')
        dupefilter_mapping = {
            'redis': 'src.filters.dupefilter.RedisBasedDupeFilter',
            'sqlite': 'src.filters.dupefilter.SQLiteBasedDupeFilter',
            'file': 'src.filters.dupefilter.FileBasedDupeFilter',
        }
        
        # Determine crawl order: BFS (breadth-first) or DFS (depth-first, default)
        use_bfs = config_settings.get('USE_BFS', False)
        
        settings.setdict({
            'USER_AGENT': config_settings.get(
                'USER_AGENT', 
                'Mozilla/5.0 (compatible; CustomCrawler/1.0)'
            ),
            'ROBOTSTXT_OBEY': config_settings.get('ROBOTSTXT_OBEY', True),
            'DOWNLOAD_DELAY': config_settings.get('DOWNLOAD_DELAY', 1),
            'CONCURRENT_REQUESTS': config_settings.get('CONCURRENT_REQUESTS', 16),
            'CONCURRENT_REQUESTS_PER_DOMAIN': config_settings.get('CONCURRENT_REQUESTS_PER_DOMAIN', 8),
            'DEPTH_LIMIT': config_settings.get('DEPTH_LIMIT', 0),  # 0 = no limit
            'CLOSESPIDER_PAGECOUNT': config_settings.get('CLOSESPIDER_PAGECOUNT', 0),  # 0 = no limit
            'HTTPCACHE_ENABLED': config_settings.get('HTTPCACHE_ENABLED', True),
            'HTTPCACHE_EXPIRATION_SECS': config_settings.get('HTTPCACHE_EXPIRATION_SECS', 86400),
            'HTTPCACHE_DIR': config_settings.get('HTTPCACHE_DIR', 'httpcache'),
            'BASE_URL': self.config['base_url'],
            # BFS/DFS Configuration
            'DEPTH_PRIORITY': 1 if use_bfs else 0,  # 1 = BFS (breadth-first), 0 = DFS (depth-first)
            'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue' if use_bfs else 'scrapy.squeues.PickleLifoDiskQueue',
            'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue' if use_bfs else 'scrapy.squeues.LifoMemoryQueue',
            # Shared duplicate filter for multi-spider coordination
            'DUPEFILTER_CLASS': dupefilter_mapping.get(dupefilter_class, dupefilter_mapping['redis']),
            'DUPEFILTER_REDIS_URL': config_settings.get('DUPEFILTER_REDIS_URL', 'redis://localhost:6379/0'),
            'DUPEFILTER_DB_PATH': config_settings.get('DUPEFILTER_DB_PATH', 'shared_urls.db'),
            'DUPEFILTER_FILE_PATH': config_settings.get('DUPEFILTER_FILE_PATH', 'seen_urls.txt'),
            'DUPEFILTER_KEY_PREFIX': config_settings.get('DUPEFILTER_KEY_PREFIX', 'scrapy:dupefilter'),
            # Configure item pipelines
            'ITEM_PIPELINES': {
                'src.pipeline.DataCleaningPipeline': 100,
                'src.pipeline.EmbeddingPipeline': 200,
                'src.pipeline.VectorDatabasePipeline': 300,
            },
            # Add feeds export for saving results
            'FEEDS': {
                'output/crawled_pages.jsonl': {
                    'format': 'jsonlines',
                    'encoding': 'utf8',
                    'overwrite': True,
                },
            },
        })
        
        return settings
    
    def start(self):
        """Start the crawler process."""
        process = CrawlerProcess(self.settings)
        process.crawl(
            UniversitySpider,
            base_url=self.config['base_url'],
            crawl_rules=self.config.get('crawl_rules')
        )
        process.start()
        