# Pipeline for processing scraped data
# 1. Scrape data from university website
# 2. Clean data
# 3. Use embedding model to transform into vectors
# 4. Store in infinity vector database

# TODO: Implement pipeline

from bs4 import BeautifulSoup
import re
from src.embedding import HuggingFaceEmbedder
from tqdm import tqdm
from langchain_qdrant import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from langchain_core.documents import Document

JAVASCRIPT_CODE = "{;if(!''.replace(/^/,String)){];;c=1};g{3 c=2.r();}}u(e){}}6 h(a){4(a.8)a=a.8;4(a==\\'\\')v;3 b=[1];3 c;3 d=2.x(\\'y\\');z(3 i=0;i<d.5;i++)4(d[i].A==\\'B-C-D\\')c=d[i];4(2.j(\\'k\\')==E||2.j(\\'k\\').l.5==0||c.5==0||c.l.5==0){F(6(){h(a)},G)}g{c.8=b;7(c,\\'m\\');7(c,\\'m\\')}}',43,43,'||document|var|if|length|function|GTranslateFireEvent|value|createEvent||||||true|else|doGTranslate||getElementById||innerHTML|change|try|HTMLEvents|initEvent|dispatchEvent|createEventObject|fireEvent|on|catch|return|split|getElementsByTagName|select|for|className|goog|te|combo|null|setTimeout|500'.split('|'),0,{}))"


class DataCleaningPipeline:
    def __init__(self):
        self.dropped_count = 0
        self.processed_count = 0
    
    def process_item(self, item, spider):
        """Clean HTML content by removing scripts, styles, and extracting clean text."""
        self.processed_count += 1
        
        # First check if URL is valid (not a PDF, image, etc.)
        if not self.is_valid_url(item.get('url', '')):
            self.dropped_count += 1
            from scrapy.exceptions import DropItem
            raise DropItem(f"Invalid URL (PDF/binary file): {item.get('url', 'unknown')}")
        
        item['text'] = self.clean_text(item['text'])
        
        # Validate the cleaned text to prevent corrupted data
        if not self.is_valid_text(item['text']):
            self.dropped_count += 1
            from scrapy.exceptions import DropItem
            raise DropItem(f"Corrupted or invalid text from {item.get('url', 'unknown')}")
        
        return item
    
    def clean_text(self, text):
        """Clean HTML content by removing scripts, styles, and extracting clean text."""
        soup = BeautifulSoup(text, 'html.parser')
        
        # Remove all script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ')
        
        # Remove JavaScript code patterns (inline JS that was extracted as text)
        text = re.sub(r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}', '', text)  # Remove function declarations
        text = re.sub(r'eval\s*\([^)]+\)', '', text)  # Remove eval() calls
        text = re.sub(r'new\s+\w+\.\w+\([^)]*\)', '', text)  # Remove new Object() patterns
        text = re.sub(r'var\s+\w+\s*=\s*[^;]+;', '', text)  # Remove var declarations
        text = re.sub(r'(let|const)\s+\w+\s*=\s*[^;]+;', '', text)  # Remove let/const declarations
        text = re.sub(r'if\s*\([^)]+\)\s*\{[^}]*\}', '', text)  # Remove if statements
        text = re.sub(r'for\s*\([^)]*\)[^{]*\{[^}]*\}', '', text)  # Remove for loops
        text = re.sub(r'while\s*\([^)]*\)[^{]*\{[^}]*\}', '', text)  # Remove while loops
        text = re.sub(r'window\.\w+\s*=\s*function[^}]*\}', '', text)  # Remove window functions
        text = re.sub(r'document\.\w+\([^)]*\)', '', text)  # Remove document methods
        text = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', text)  # Remove /* */ comments
        text = re.sub(r'//[^\n]*', '', text)  # Remove // comments
        
        # Remove obfuscated/minified JavaScript patterns
        text = re.sub(r'\w+\s*=\s*function\([^)]*\)\s*\{[^}]+\}', '', text)  # Minified function assignments
        text = re.sub(r"'[^']*\\[bwx][^']*'", '', text)  # Escaped string patterns common in obfuscation
        text = re.sub(r'[a-z]\.[a-z]\([^)]*\)', '', text, flags=re.IGNORECASE)  # Short method calls (a.b())
        
        # Remove Google Translate widget code specifically
        text = re.sub(r'googleTranslateElementInit\d*\(\)', '', text)
        text = re.sub(r'google\.translate\.TranslateElement', '', text)
        text = re.sub(r'google_translate_element\d*', '', text)
        
        # Remove common navigation/UI noise
        text = re.sub(r'Skip to main content', '', text)
        text = re.sub(r'Translate (English|Spanish|Chinese|French|German|Korean|Lao|Nepali|Japanese|Tibetan)+', '', text)
        text = re.sub(r'Search Enter the terms you wish to search for', '', text)
        
        # Remove CSS classes and inline styles patterns
        text = re.sub(r'\.[\w-]+\s*\{[^}]*\}', '', text)  # Remove CSS rules
        text = re.sub(r'@media[^{]+\{[^}]*\}', '', text)  # Remove @media queries
        text = re.sub(r'padding[-\w]*:\s*[\d\w\s;%]+', '', text)  # Remove padding declarations
        text = re.sub(r'margin[-\w]*:\s*[\d\w\s;%]+', '', text)  # Remove margin declarations
        
        # Remove specific JavaScript code (literal string replacement)
        text = text.replace(JAVASCRIPT_CODE, '')
        
        # Remove CSS class references (like .ucb-bootstrap-layout-section .section-6896110c4f3b9)
        text = re.sub(r'\.[a-zA-Z0-9_-]+(\s+\.[a-zA-Z0-9_-]+)*', '', text)  # Remove class selectors
        
        
        
        # Remove remaining JavaScript fragments
        text = text.replace("'');}", "")
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = text.strip()
        
        
        # Update the item
        return text
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL points to a valid HTML page (not PDF, image, etc.)
        
        Args:
            url: The URL to validate
        
        Returns:
            True if URL is valid, False otherwise
        """
        url_lower = url.lower()
        
        # File extensions that should not be in vector store
        invalid_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.webp',
            '.mp4', '.mp3', '.avi', '.mov', '.wmv', '.wav'
        ]
        
        # Check if URL ends with or contains invalid extension
        for ext in invalid_extensions:
            if url_lower.endswith(ext):
                return False
            # Also check for extension in query params (e.g., file.pdf?download=1)
            if f'{ext}?' in url_lower or f'{ext}#' in url_lower:
                return False
        
        return True
    
    def is_valid_text(self, text: str, min_length: int = 50, max_replacement_ratio: float = 0.05) -> bool:
        """
        Validate that text is not corrupted.
        
        Args:
            text: The text to validate
            min_length: Minimum acceptable text length
            max_replacement_ratio: Maximum ratio of replacement characters (�)
        
        Returns:
            True if text is valid, False otherwise
        """
        if not text or len(text) < min_length:
            return False
        
        # Check for excessive replacement characters (encoding errors)
        replacement_count = text.count('�')
        replacement_ratio = replacement_count / len(text)
        
        if replacement_ratio > max_replacement_ratio:
            return False
        
        # Check for reasonable ASCII ratio (should be mostly readable English)
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
    
    def close_spider(self, spider):
        """Log statistics when spider closes"""
        if self.processed_count > 0:
            spider.logger.info(
                f"Data Cleaning Pipeline: Processed {self.processed_count} items, "
                f"dropped {self.dropped_count} corrupted items "
                f"({self.dropped_count/self.processed_count*100:.1f}%)"
            )
    
class EmbeddingPipeline:
    def __init__(self):
        self.embedder = HuggingFaceEmbedder()
    
    def process_item(self, item, spider):
        #tqdm.write(f"Processing item: {item['url']}")
        item['embeddings'] = self.embedder.process_item(item, spider)
        #tqdm.write(f"Processed item: {item['url']}")
        return item
    

class VectorDatabasePipeline:
    def __init__(self):
        # Connect to your local Qdrant instance
        self.client = QdrantClient(url="http://localhost:6333")

        # Initialize embeddings (same model as your embedder)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/e5-base-v2",
            model_kwargs={"device": "mps"}
        )

        # Set a collection name for your university data
        self.collection_name = "cuboulder_pages"

        # Create the collection if it doesn't exist
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config={"size": 768, "distance": "Cosine"}
        )

        # Wrap in LangChain’s vectorstore for convenience
        self.vectorstore = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )

    def process_item(self, item, spider):
        """Insert crawled item’s embeddings into Qdrant."""
        #tqdm.write(f"Inserting item: {item['url']}")

        docs = [
            Document(
                page_content=chunk["text"],
                metadata={
                    "url": item["url"],
                    "title": item.get("title", ""),
                    "source": "cuboulder_scraper"
                }
            )
            for chunk in item["embeddings"]
        ]

        self.vectorstore.add_documents(docs)
        tqdm.write(f"✅ Inserted {len(docs)} chunks for {item['url']}")
        return item