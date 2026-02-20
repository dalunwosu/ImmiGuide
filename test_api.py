import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ ERROR: No API key found in .env file")
    exit()

print(f"✅ API key loaded: {api_key[:10]}...")

# Configure Gemini
client = genai.Client(api_key=api_key)

# Test with simple question
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Say hello!"
)

print("\\n✅ API is working!")
print(f"Response: {response.text}")