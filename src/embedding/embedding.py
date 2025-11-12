import warnings
import logging
import os

# Suppress warnings and verbose output
warnings.filterwarnings('ignore')
logging.getLogger('transformers').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class HuggingFaceEmbedder:
    def __init__(self, model_name="intfloat/e5-base-v2"):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "mps"},
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=256,
            length_function=len,
            is_separator_regex=False,
        )
    
    def create_document_from_item(self, item):
        content = f"Title: {item['title']}\n\nURL: {item['url']}\n\nContent: {item['text']}"
        metadata = {"url": item["url"], "title": item["title"], "source": "scrapy crawl cuboulder"}
        document = Document(page_content=content, metadata=metadata)
        return document
    
    def embed_document(self, document):
        text_chunks = self.text_splitter.split_documents([document])
        texts = [chunk.page_content for chunk in text_chunks]
        embeddings = self.embeddings.embed_documents(texts)
        return list(zip(text_chunks, embeddings))

    def process_item(self, item, spider):
        document = self.create_document_from_item(item)
        chunk_embeddings = self.embed_document(document)

        results = []
        for chunk, emb in chunk_embeddings:
            results.append({
                "text": chunk.page_content,
                "embedding": emb
            })
        
        return results