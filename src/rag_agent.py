import os
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from google import genai
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()


class RAGVisaAssistant:
    def __init__(
        self,
        kb_path: str = "data/visa_kb",
        model_name: str = "gemini-2.0-flash",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. Add it to your .env file before running the assistant."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

        print("Loading knowledge base...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
        )

        self.vectorstore = Chroma(
            persist_directory=kb_path,
            embedding_function=self.embeddings,
        )
        print("✅ Knowledge base loaded\n")

        self.system_instruction = """
You are an ISSS visa information assistant for Georgia State University.

Your job:
- Answer only from the retrieved ISSS context.
- Give the student a direct answer first.
- Then briefly explain the rule or process.
- Be careful with immigration questions: if a rule depends on authorization, visa type, approval, or timing, say that clearly.
- Never invent steps, deadlines, eligibility rules, or requirements.
- If the context is incomplete, say so clearly and tell the student to contact ISSS.

Required answer format:

Direct answer: <1-3 sentences>

Explanation:
- <short bullet or short paragraph>
- <second bullet if helpful>

Sources:
- <exact source URL(s) from context>

If the context is not enough, say exactly:
"I don't have enough verified information in the ISSS knowledge base to answer that confidently. Please contact ISSS at isss@gsu.edu."
""".strip()

    def _expand_query(self, question: str) -> str:
        q = question.lower().strip()
        expansions: List[str] = [question]

        if "off-campus" in q or "off campus" in q or "work" in q or "job" in q or "employment" in q:
            expansions.append(
                "off-campus employment work authorization F-1 student CPT OPT on-campus off-campus"
            )

        if "cpt" in q or "curricular practical training" in q or "internship" in q:
            expansions.append(
                "curricular practical training CPT internship employment authorization while studying"
            )

        if "opt" in q or "optional practical training" in q:
            expansions.append(
                "optional practical training OPT post-completion employment authorization USCIS"
            )

        if "stem opt" in q or ("stem" in q and "opt" in q):
            expansions.append(
                "STEM OPT extension I-983 E-Verify employment reporting self-evaluation"
            )

        if "travel" in q or "reenter" in q or "re-entry" in q:
            expansions.append(
                "travel outside the United States reentry visa I-20 travel signature OPT"
            )

        if "i-20" in q:
            expansions.append(
                "I-20 issuance request financial documentation passport SEVIS"
            )

        if "j-1" in q or "exchange visitor" in q or "academic training" in q:
            expansions.append(
                "J-1 academic training exchange visitor DS-2019 employment authorization"
            )

        if "transfer" in q:
            expansions.append(
                "SEVIS transfer transfer to Georgia State transfer release"
            )

        if "housing" in q or "meal" in q or "dorm" in q:
            expansions.append(
                "housing meal plan university housing residence"
            )

        if "check in" in q or "orientation" in q or "arrival" in q:
            expansions.append(
                "international check-in orientation arrival airport pre-arrival"
            )

        return " | ".join(dict.fromkeys(expansions))

    def _retrieve_documents(self, question: str, k: int = 6, fetch_k: int = 20):
        expanded_query = self._expand_query(question)
        docs = self.vectorstore.max_marginal_relevance_search(
            expanded_query,
            k=k,
            fetch_k=fetch_k,
        )
        return docs

    def _dedupe_documents(self, docs) -> List[Any]:
        seen: set[Tuple[str, str, str]] = set()
        unique_docs = []

        for doc in docs:
            source = doc.metadata.get("source", "")
            title = doc.metadata.get("title", "")
            content_key = doc.page_content[:250]
            key = (source, title, content_key)

            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

        return unique_docs

    def _format_context(self, docs) -> Tuple[str, List[str]]:
        context_blocks: List[str] = []
        sources: List[str] = []

        for i, doc in enumerate(docs, 1):
            source_url = doc.metadata.get("source", "Unknown")
            title = doc.metadata.get("title", "Untitled")
            tags = doc.metadata.get("tags", "")

            sources.append(source_url)

            block = f"""Source {i}
Title: {title}
URL: {source_url}
Tags: {tags}

Content:
{doc.page_content}"""
            context_blocks.append(block)

        return "\n\n---\n\n".join(context_blocks), list(dict.fromkeys(sources))

    def answer_question(self, question: str, k: int = 6) -> Dict[str, Any]:
        print(f"Question: {question}\n")
        print("🔍 Searching knowledge base...")

        docs = self._retrieve_documents(question, k=k, fetch_k=max(15, k * 4))
        docs = self._dedupe_documents(docs)

        if not docs:
            fallback = (
                "I don't have enough verified information in the ISSS knowledge base "
                "to answer that confidently. Please contact ISSS at isss@gsu.edu."
            )
            return {
                "answer": fallback,
                "sources": [],
                "retrieved_docs": [],
            }

        print(f"✅ Found {len(docs)} relevant documents\n")

        context, sources = self._format_context(docs)

        prompt = f"""
System instructions:
{self.system_instruction}

Use only the context below from official ISSS materials.

Context:
{context}

Student question:
{question}

Instructions:
- Answer only from the context.
- Start with a direct answer.
- If the answer is conditional, say exactly what it depends on.
- Do not guess.
- Do not mention retrieval, embeddings, vector databases, or internal system details.
- Use only source URLs that appear in the context.
- If the context is not enough, use the fallback sentence exactly.
""".strip()

        print("🤖 Generating answer...\n")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        answer_text = getattr(response, "text", "") or ""
        answer_text = answer_text.strip()

        if not answer_text:
            answer_text = (
                "I don't have enough verified information in the ISSS knowledge base "
                "to answer that confidently. Please contact ISSS at isss@gsu.edu."
            )

        return {
            "answer": answer_text,
            "sources": sources,
            "retrieved_docs": [
                {
                    "source": doc.metadata.get("source", "Unknown"),
                    "title": doc.metadata.get("title", "Untitled"),
                    "preview": doc.page_content[:220].replace("\n", " ") + "...",
                }
                for doc in docs
            ],
        }


if __name__ == "__main__":
    assistant = RAGVisaAssistant()

    questions = [
        "Can I work off-campus on my F-1 visa?",
        "What is CPT and how do I apply?",
        "What are the requirements for OPT?",
        "Can I travel outside the US while on OPT?",
    ]

    for q in questions:
        print("=" * 80)
        result = assistant.answer_question(q)

        print("ANSWER:")
        print(result["answer"])

        print("\n📚 SOURCES:")
        for source in result["sources"]:
            print(f"  • {source}")

        print("\n🔎 RETRIEVED CONTEXT:")
        for item in result["retrieved_docs"]:
            print(f"  • {item['title']} | {item['source']}")
            print(f"    {item['preview']}")

        print("\n" + "=" * 80 + "\n")