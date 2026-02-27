import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class RAGVisaAssistant:
    def __init__(self, kb_path='data/visa_kb'):
        # Load vector database
        print("Loading knowledge base...")
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        self.vectorstore = Chroma(
            persist_directory=kb_path,
            embedding_function=embeddings
        )
        print("✅ Knowledge base loaded\\n")
        
        # Create agent
        self.agent = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction='''
            You are a visa information assistant for GSU international students.
            
            CRITICAL RULES:
            1. Answer ONLY based on the context provided
            2. If the context doesn't contain the answer, say:
               "I don't have verified information about this in my knowledge base. 
               Please contact ISSS at isss@gsu.edu for accurate information."
            3. Always cite the source URL
            4. Be clear and specific
            5. Use bullet points for multi-step processes
            6. Never make assumptions or guess
            
            Format your answer like this:
            
            [Your answer based on context]
            
            📚 Source: [URL from context]
            '''
        )
    
    def answer_question(self, question, k=3):
        #Answer question using RAG
        
        print(f"Question: {question}\\n")
        
        # Step 1: Retrieve relevant documents
        print(f"🔍 Searching knowledge base...")
        docs = self.vectorstore.similarity_search(question, k=k)
        
        if not docs:
            return {
                'answer': "I couldn't find relevant information. Please contact ISSS directly.",
                'sources': []
            }
        
        print(f"✅ Found {len(docs)} relevant documents\\n")
        
        # Step 2: Format context for agent
        context = ""
        sources = []
        
        for i, doc in enumerate(docs, 1):
            source_url = doc.metadata.get('source', 'Unknown')
            sources.append(source_url)
            
            context += f'''
            --- Source {i}: {source_url} ---
            {doc.page_content}
            
            '''
        
        # Step 3: Create prompt with context
        prompt = f'''
        Context from official ISSS sources:
        
        {context}
        
        ---
        
        Student Question: {question}
        
        Please answer this question using ONLY the information from the context above.
        Cite your sources.
        '''
        
        # Step 4: Generate answer
        print("🤖 Generating answer...\\n")
        response = self.agent.generate_content(prompt)
        
        return {
            'answer': response.text,
            'sources': list(set(sources))  # Remove duplicates
        }

# Test it
if __name__ == "__main__":
    assistant = RAGVisaAssistant()
    
    questions = [
        "Can I work off-campus on my F-1 visa?",
        "What is CPT and how do I apply?",
        "What are the requirements for OPT?",
        "Can I travel outside the US while on OPT?",
    ]
    
    for q in questions:
        print("="*80)
        result = assistant.answer_question(q)
        
        print("ANSWER:")
        print(result['answer'])
        
        print("\\n📚 SOURCES:")
        for source in result['sources']:
            print(f"  • {source}")
        
        print("\\n" + "="*80 + "\\n")