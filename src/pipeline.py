# Pipeline for processing scraped data
# 1. Scrape data from university website
# 2. Clean data
# 3. Use embedding model to transform into vectors
# 4. Store in infinity vector database

# TODO: Implement pipeline

JAVASCRIPT_CODE = "{;if(!''.replace(/^/,String)){];;c=1};g{3 c=2.r();}}u(e){}}6 h(a){4(a.8)a=a.8;4(a==\\'\\')v;3 b=[1];3 c;3 d=2.x(\\'y\\');z(3 i=0;i<d.5;i++)4(d[i].A==\\'B-C-D\\')c=d[i];4(2.j(\\'k\\')==E||2.j(\\'k\\').l.5==0||c.5==0||c.l.5==0){F(6(){h(a)},G)}g{c.8=b;7(c,\\'m\\');7(c,\\'m\\')}}',43,43,'||document|var|if|length|function|GTranslateFireEvent|value|createEvent||||||true|else|doGTranslate||getElementById||innerHTML|change|try|HTMLEvents|initEvent|dispatchEvent|createEventObject|fireEvent|on|catch|return|split|getElementsByTagName|select|for|className|goog|te|combo|null|setTimeout|500'.split('|'),0,{}))"

from bs4 import BeautifulSoup
import re

class DataCleaningPipeline:
    def __init__(self):
        pass
    
    def process_item(self, item, spider):
        """Clean HTML content by removing scripts, styles, and extracting clean text."""
        item['text'] = self.clean_text(item['text'])
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
    
class EmbeddingPipeline:
    def __init__(self):
        pass
    
    def process_item(self, item, spider):
        print(item)
        return item
    

class VectorDatabasePipeline:
    def __init__(self):
        pass
    
    def process_item(self, item, spider):
        print(item)
        return item