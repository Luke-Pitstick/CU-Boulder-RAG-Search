import time
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from tqdm import tqdm
import json

# --- Helper Functions (Moved from the class) ---

def prepare_context(docs: List[Document], max_length: int = 4000) -> str:
    """Prepare context from retrieved documents"""
    context_parts = []
    current_length = 0
    
    for i, doc in enumerate(docs):
        source_info = f"[Source {i+1}: {doc.metadata.get('url', 'Unknown URL')}]"
        content = doc.page_content
        
        # Truncate content if necessary
        doc_length = len(source_info) + len(content)
        if current_length + doc_length > max_length:
            remaining_space = max_length - current_length - len(source_info) - 100
            if remaining_space > 200:  # Only include if we have meaningful content
                content = content[:remaining_space] + "..."
                context_parts.append(f"{source_info}\n{content}")
            break
        
        context_parts.append(f"{source_info}\n{content}")
        current_length += doc_length
    
    return "\n\n".join(context_parts)

def format_sources(docs: List[Document]) -> List[Dict[str, str]]:
    """Format source information"""
    sources = []
    seen_urls = set()
    
    for i, doc in enumerate(docs):
        metadata = doc.metadata
        url = metadata.get('url', 'Unknown URL')
        
        # Avoid duplicate URLs
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        title = metadata.get('title', metadata.get('source', 'Untitled'))
        
        # Create a short snippet
        content = doc.page_content
        snippet = content[:150] + "..." if len(content) > 150 else content
        
        sources.append({
            "id": i + 1,
            "url": url,
            "title": title,
            "snippet": snippet.strip()
        })
    
    return sources

def print_results(result: Dict[str, Any]):
    """Print formatted search results"""
    print("\n" + "="*80)
    print("🎯 SEARCH RESULTS")
    print("="*80)
    
    # Print answer
    print(f"\n📝 Answer:\n{result['answer']}")
    
    # Print sources
    if result['sources']:
        print(f"\n🔗 Sources ({len(result['sources'])}):")
        print("-" * 40)
        for source in result['sources']:
            print(f"\n[{source['id']}] {source['title']}")
            print(f"    URL: {source['url']}")
            print(f"    Snippet: {source['snippet']}")
    
    # Print metadata
    metadata = result['metadata']
    print(f"\n⏱️  Performance:")
    print(f"    • Total time: {metadata['total_time']:.2f}s")
    print(f"    • Documents used: {metadata['total_docs']}")
    
    print("\n" + "="*80)

def save_results(result: Dict[str, Any], filename: str = None):
    """Save results to JSON file"""
    if filename is None:
        timestamp = int(time.time())
        filename = f"search_result_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {filename}")

# --- Main RAG System Setup ---

def setup_rag_system(
    collection_name: str = "cuboulder_pages",
    qdrant_url: str = "http://localhost:6333",
    embedding_model: str = "intfloat/e5-base-v2",
    llm_model: str = "llama3.2",
    device: str = "mps"
):
    """Initialize components and build the LCEL RAG chain."""
    
    print("🔧 Initializing RAG system...")
    
    # 1. Initialize embeddings
    print("📚 Loading embedding model...")
    start_time = time.time()
    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={"device": device}
    )
    print(f"✅ Embeddings loaded ({time.time() - start_time:.2f}s)")
    
    # 2. Initialize vector store and retriever
    print("🔗 Connecting to vector database...")
    client = QdrantClient(url=qdrant_url)
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 10, "lambda_mult": 0.5}
    )
    
    # 3. Initialize local LLM
    print("🤖 Initializing local LLM...")
    try:
        llm = OllamaLLM(model=llm_model)
        # Test connection
        llm.invoke("Hello!")
        print(f"✅ LLM {llm_model} ready")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        print("💡 Make sure Ollama is installed, running, and you have the model:")
        print("   - Install: https://ollama.com/")
        print(f"   - Run: ollama pull {llm_model}")
        raise
    
    # 4. Create prompt template
    template = """
You are a helpful assistant answering questions about CU Boulder based on the provided context.
Please provide a comprehensive, well-structured answer to the user's question.

CONTEXT:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question based primarily on the provided context
2. If the context doesn't contain enough information, say so clearly
3. Organize your answer with clear headings and bullet points when appropriate
4. Be concise but thorough
5. Include specific details from the sources

ANSWER:
"""
    qa_prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    # 5. Build the modern LCEL RAG Chain
    # This chain:
    # 1. Takes the 'question' as input.
    # 2. Retrieves documents and passes them through as 'docs'.
    # 3. Passes the original 'question' through.
    # 4. Generates the 'answer' by formatting context, piping to prompt, LLM, and parser.
    
    # Helper function to format context for prompt
    def format_docs_for_prompt(x):
        return {
            "context": prepare_context(x["docs"]),
            "question": x["question"]
        }
    
    rag_chain = (
        RunnablePassthrough.assign(
            docs=(lambda x: x["question"]) | retriever
        )
        | RunnablePassthrough.assign(
            answer=(
                format_docs_for_prompt
                | qa_prompt
                | llm
                | StrOutputParser()
            )
        )
    )
    # The output of this chain is a dict: {"question": str, "docs": List[Doc], "answer": str}
    
    print("✅ RAG system ready!")
    return rag_chain

# --- Interactive Application ---

def interactive_search():
    """Run interactive search session"""
    print("🚀 CU Boulder Enhanced Search System")
    print("=" * 50)
    print("Type 'quit' or 'exit' to end the session")
    print("=" * 50)
    
    try:
        # Pass your config here
        rag_chain = setup_rag_system(
            llm_model="llama3.2" 
            # Add other params if not default
        )
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        return
    
    while True:
        try:
            query = input("\n🔍 What would you like to know about CU Boulder? ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            # 1. Run the chain
            print("🧠 Thinking...")
            start_time = time.time()
            chain_input = {"question": query}
            result = rag_chain.invoke(chain_input)
            total_time = time.time() - start_time
            
            # 2. Format results for printing and saving
            sources = format_sources(result["docs"])
            
            final_result = {
                "answer": result['answer'],
                "sources": sources,
                "metadata": {
                    "query": query,
                    "total_time": total_time,
                    "total_docs": len(sources)
                }
            }
            
            # 3. Print and Save
            print_results(final_result)
            
            save_choice = input("\n💾 Save these results? (y/n): ").strip().lower()
            if save_choice in ['y', 'yes']:
                save_results(final_result)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error during search: {e}")

if __name__ == "__main__":
    interactive_search()