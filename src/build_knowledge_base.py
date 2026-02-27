import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

class KnowledgeBaseBuilder:
    def __init__(self):
        # Use free, open-source embeddings
        print("Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        print("✅ Embedding model loaded")
        
        # Text splitter - breaks documents into chunks
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,        # Each chunk ~1000 characters
            chunk_overlap=200,      # 200 character overlap for context
            length_function=len,
            separators=["\\n\\n", "\\n", ". ", " ", ""]
        )
    
    def load_scraped_content(self, filepath):
        #Load content from scraper
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to LangChain Document format
        documents = []
        for item in data:
            doc = Document(
                page_content=item['content'],
                metadata={
                    'source': item['url'],
                    'title': item['title']
                }
            )
            documents.append(doc)
        
        print(f"✅ Loaded {len(documents)} documents")
        return documents
    
    def split_documents(self, documents):
        #Split documents into smaller chunks
        print("Splitting documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"✅ Created {len(chunks)} chunks")
        return chunks
    
    def create_vector_store(self, chunks, persist_directory='data/visa_kb'):
        #Create and save vector database
        print(f"Creating vector database at {persist_directory}...")
        print("This might take a few minutes...")
        
        # Create the vector store
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        
        # Save to disk
        vectorstore.persist()
        
        print(f"✅ Vector database created and saved!")
        return vectorstore
    
    def build_from_scraped_data(self, json_file):
        #Complete pipeline: load → split → vectorize
        # Step 1: Load
        documents = self.load_scraped_content(json_file)
        
        # Step 2: Split
        chunks = self.split_documents(documents)
        
        # Step 3: Create vector DB
        vectorstore = self.create_vector_store(chunks)
        
        return vectorstore

# Test it
if __name__ == "__main__":
    print("="*60)
    print("BUILDING KNOWLEDGE BASE")
    print("="*60)
    
    builder = KnowledgeBaseBuilder()
    
    # Build from scraped ISSS content
    vectorstore = builder.build_from_scraped_data(
        'data/raw_docs/isss_content.json'
    )
    
    print("\\n" + "="*60)
    print("TESTING SEARCH")
    print("="*60)
    
    # Test search
    test_queries = [
        "Can I work off-campus?",
        "What is CPT?",
        "How do I apply for OPT?"
    ]
    
    for query in test_queries:
        print(f"\\nQuery: {query}")
        results = vectorstore.similarity_search(query, k=2)
        
        for i, doc in enumerate(results, 1):
            print(f"\\n  Result {i}:")
            print(f"  Source: {doc.metadata['source']}")
            print(f"  Content: {doc.page_content[:150]}...")