import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class VisaQASystem:
    def __init__(self):
        # Agent 1 — Answerer
        self.answer_prompt = """
You are an international student visa advisor for Georgia State University (GSU).

Give accurate, careful answers about F-1 visa rules.

Rules:
- Be clear and short
- Never give legal guarantees
- Encourage contacting ISSS for confirmation
- If unsure → say unsure
"""
        
        # Agent 2 — Reviewer (CRITICAL IMPROVEMENT)
        self.review_prompt = """
You are a strict immigration compliance reviewer.

Evaluate the answer.

If GOOD:
APPROVED

If BAD:
NEEDS REVISION:
- explain what is wrong
- explain what is missing
- explain safety issues

Be strict.
"""
    
    def generate_answer(self, question, feedback=None):
        improve_section = f"\nImprove based on feedback:\n{feedback}" if feedback else ""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=f"{self.answer_prompt}\n\nQuestion: {question}{improve_section}"
        )

        return response.text

    def review_answer(self, question, answer):
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=f"{self.review_prompt}\n\nQuestion: {question}\nAnswer: {answer}"
        )
        return response.text

    def answer_with_review(self, question, max_attempts=4):

        print(f"\nQuestion: {question}")
        print("="*60)

        feedback = None
        final_answer = None

        for attempt in range(max_attempts):
            print(f"\n🧠 Attempt {attempt+1}")

            answer = self.generate_answer(question, feedback)
            print(f"\nAnswer:\n{answer}\n")

            review = self.review_answer(question, answer)
            print(f"Reviewer:\n{review}\n")

            final_answer = answer

            if "APPROVED" in review.upper():
                print("✅ Approved by reviewer\n")
                break

            feedback = review

        return final_answer


# Run demo
if __name__ == "__main__":
    qa = VisaQASystem()

    questions = [
        "Can I work 40 hours per week on F1 visa?",
        "What happens if I drop below full time?",
        "Can I stay in US forever after OPT?"
    ]

    for q in questions:
        result = qa.answer_with_review(q)
        print("FINAL ANSWER:")
        print(result)
        print("\n" + "="*80)