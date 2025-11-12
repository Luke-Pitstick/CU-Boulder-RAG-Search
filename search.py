from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant

COLLECTION_NAME = "cuboulder_pages"

# Initialize Database retrieval
embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/e5-base-v2",
            model_kwargs={"device": "mps"}
        )

client = QdrantClient(url="http://localhost:6333")

vectorstore = Qdrant(
            client=client,
            collection_name=COLLECTION_NAME,
            embeddings=embeddings
        )


retriever = vectorstore.as_retriever()

user_input = input("What do you want to know about CU Boulder?: ")

docs = retriever.get_relevant_documents(user_input)

for doc in docs:
    print(doc.metadata["url"])
    print(doc.page_content[:200])
    print("----")

