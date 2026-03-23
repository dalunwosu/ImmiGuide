from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List
from langchain.embeddings import HuggingFaceEmbeddings
from build_knowledge_base import KnowledgeBaseBuilder

# Load existing vector database
print("Loading knowledge base...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

vectorstore = Chroma(
    persist_directory='data/visa_kb',
    embedding_function=embeddings
)
print("✅ Knowledge base loaded!\\n")

def search_knowledge_base(query, k=3):
    #Search for relevant information
    print(f"Question: {query}")
    print("="*60)
    
    # Search with scores
    results = vectorstore.similarity_search_with_score(query, k=k)
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"\\nResult {i} (relevance: {1-score:.2f}):")
        print(f"Source: {doc.metadata['source']}")
        print(f"Content:\\n{doc.page_content}\\n")
        print("-"*60)
    
    return results

# Test with different questions
if __name__ == "__main__":
    questions = [
        "Can I work off-campus on my F-1 visa?",
        "What is the difference between CPT and OPT?",
        "Do I need a visa to travel to Canada?",
        "How long can I stay in the US after graduation?",
    ]
    
    for q in questions:
        search_knowledge_base(q, k=2)
        print("\\n" + "="*80 + "\\n")