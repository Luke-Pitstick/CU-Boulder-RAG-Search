from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="intfloat/e5-base-v2")
vectorstore = Qdrant.from_existing_collection(
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name="cuboulder_pages"
)

results = vectorstore.similarity_search("What does CU Boulder offer for international students?", k=3)
for doc in results:
    print(doc.metadata["url"])
    print(doc.page_content[:200])
    print("----")
