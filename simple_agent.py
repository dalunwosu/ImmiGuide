import os
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Create a simple visa information agent
SYSTEM_PROMPT = """
You are a helpful visa information assistant for GSU international students.

Rules:
1. Be clear and concise
2. If you don't know something, say so
3. Always be encouraging and supportive
"""

# Test it
def ask_question(question):
    print(f"\nStudent: {question}")
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"{SYSTEM_PROMPT}\n\nStudent Question: {question}"
    )
    print(f"\nAssistant: {response.text}")
    print("\n" + "="*60)

# Try some questions
if __name__ == "__main__":
    print("="*60)
    print("SIMPLE VISA AGENT - DEMO")
    print("="*60)
    
    ask_question("What is an F-1 visa?")
    ask_question("Can I work while studying?")
    ask_question("What is OPT?")