import scrapy
from scrapy.linkextractors import LinkExtractor
from typing import Dict, Any
from urllib.parse import urlparse

class UniversitySpider(scrapy.Spider):
    """Spider that crawls an entire university website by following links."""
    name = 'university_crawler'
    
    def __init__(self, base_url: str, crawl_rules: Dict[str, list] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [base_url]
        
        # Extract domain from base_url for restriction
        parsed = urlparse(base_url)
        self.allowed_domains = [parsed.netloc]
        
        # Get crawl rules from config or use defaults
        if crawl_rules is None:
            crawl_rules = {
                'allow_patterns': [],
                'deny_patterns': [
                    r'/login', r'/logout', r'/admin',
                    r'\.pdf$', r'\.jpg$', r'\.png$', r'\.gif$',
                    r'\.zip$', r'\.doc$', r'\.docx$',
                ]
            }
        
        # Store crawl rules for use in parse
        self.crawl_rules = crawl_rules
        self.link_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            allow=tuple(crawl_rules.get('allow_patterns', [])) or (),
            deny=tuple(crawl_rules.get('deny_patterns', [])),
            unique=True
        )
    
    def parse(self, response):
        """Parse each page, extract content, and follow links."""
        
        # Check content type - only process HTML
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore').lower()
        
        # Skip non-HTML content (PDFs, images, documents, etc.)
        if not any(html_type in content_type for html_type in ['text/html', 'text/plain', 'application/xhtml']):
            self.logger.warning(f'Skipping non-HTML content: {response.url} (Content-Type: {content_type})')
            return
        
        # Additional URL-based filtering for PDFs and other files
        url_lower = response.url.lower()
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                          '.zip', '.tar', '.gz', '.rar', '.jpg', '.jpeg', '.png', 
                          '.gif', '.svg', '.mp4', '.mp3', '.avi', '.mov', '.wav']
        
        if any(url_lower.endswith(ext) for ext in skip_extensions):
            self.logger.warning(f'Skipping file with blocked extension: {response.url}')
            return
        
        # Extract text content
        page_data = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'text': ' '.join(response.css('body *::text').getall()),
            'links': response.css('a::attr(href)').getall(),
        }
        
        self.logger.info(f'Scraped: {response.url}')
        yield page_data
        
        # Extract and follow links
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse)
