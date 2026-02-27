import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class VerifiedRAGAssistant:
    def __init__(self, kb_path='data/visa_kb'):
        # Load knowledge base
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        self.vectorstore = Chroma(
            persist_directory=kb_path,
            embedding_function=embeddings
        )
        
        # QA Agent
        self.qa_agent = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction='''
            You answer visa questions for GSU students.
            Use ONLY the provided context.
            Be clear, specific, and cite sources.
            '''
        )
        
        # Fact Checker Agent
        self.fact_checker = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction='''
            You verify visa information answers.
            
            Check if the answer:
            1. Uses ONLY information from the provided context
            2. Doesn't add information not in the context
            3. Correctly cites sources
            4. Is clear and helpful
            
            Respond with:
            "APPROVED" if the answer is good
            "NEEDS REVISION: [specific issue]" if it has problems
            
            Be strict - visa information must be accurate!
            '''
        )
    
    def answer_with_verification(self, question, max_attempts=2):
        #Answer with fact-checking loop
        
        # Get relevant documents
        docs = self.vectorstore.similarity_search(question, k=3)
        
        if not docs:
            return {
                'answer': "No information found. Contact ISSS.",
                'sources': [],
                'verified': False
            }
        
        # Format context
        context = "\\n\\n".join([
            f"Source: {doc.metadata['source']}\\n{doc.page_content}"
            for doc in docs
        ])
        
        sources = [doc.metadata['source'] for doc in docs]
        
        # Try to generate good answer
        for attempt in range(max_attempts):
            print(f"\\nAttempt {attempt + 1}:")
            
            # Generate answer
            qa_prompt = f'''
            Context: {context}
            
            Question: {question}
            
            Answer using ONLY the context. Cite sources.
            '''
            
            answer_response = self.qa_agent.generate_content(qa_prompt)
            answer = answer_response.text
            
            print(f"Generated answer: {answer[:100]}...")
            
            # Verify answer
            verify_prompt = f'''
            Context: {context}
            
            Question: {question}
            
            Answer: {answer}
            
            Verify this answer. Does it only use information from the context?
            '''
            
            verify_response = self.fact_checker.generate_content(verify_prompt)
            verdict = verify_response.text
            
            print(f"Verdict: {verdict[:50]}...")
            
            if "APPROVED" in verdict.upper():
                print("✅ Answer verified!")
                return {
                    'answer': answer,
                    'sources': sources,
                    'verified': True
                }
        
        # If we get here, we couldn't verify
        print("⚠️ Could not verify answer")
        return {
            'answer': answer,
            'sources': sources,
            'verified': False
        }

# Test it
if __name__ == "__main__":
    assistant = VerifiedRAGAssistant()
    
    questions = [
        "Can I work off-campus?",
        "What is the difference between CPT and OPT?",
    ]
    
    for q in questions:
        print("="*80)
        print(f"Question: {q}")
        print("="*80)
        
        result = assistant.answer_with_verification(q)
        
        print(f"\\nFinal Answer:\\n{result['answer']}")
        print(f"\\n✅ Verified: {result['verified']}")
        print(f"\\nSources: {', '.join(result['sources'])}")
        print("\\n")