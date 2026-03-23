import os
import re
import time
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.multilingual import analyze_question_for_rag

load_dotenv()


class RAGVisaAssistant:
    def __init__(
        self,
        kb_path: str = "data/visa_kb",
        # Use the same model family as the working old project
        model_name: str = "gemini-2.5-flash-lite",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. Add it to your .env file before running the assistant."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        # Same model by default; set MULTILINGUAL_MODEL to override the small JSON analysis call
        self.multilingual_model = os.getenv("MULTILINGUAL_MODEL", model_name)

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

        # School-site grounding (treat these as "in-scope" sources)
        self.allowed_source_prefixes = (
            "https://isss.gsu.edu/",
            "http://isss.gsu.edu/",
        )
        self.isss_homepage = "https://isss.gsu.edu/"
        self.isss_contact_email = "isss@gsu.edu"

        self.system_instruction = """
You are ImmiGuide, an ISSS information assistant for Georgia State University.

Your job:
- Be friendly and conversational for greetings/hellos, and briefly introduce yourself.
- For ISSS questions, answer only from the retrieved ISSS context from the school's website content.
- Give the student a direct answer first.
- Then briefly explain the rule or process.
- Do not start every answer with greetings like "Hello" or "Hi" or re-introduce yourself; respond directly to the question.
- Be careful with immigration questions: if a rule depends on authorization, visa type, approval, or timing, say that clearly.
- Never invent steps, deadlines, eligibility rules, or requirements.
- If the context is incomplete or missing, say so clearly and tell the student to contact ISSS or visit the ISSS website.
- DO NOT generate or invent any URLs.
- Only use the provided context.
- Do not include links unless explicitly provided.
- If no URL is available, do not include any link.

Scope rules:
- If the user asks something unrelated to ISSS / international student services (e.g., food, movies, general trivia), say you can only help with GSU ISSS-related questions.
- If the user asks an ISSS-related question but the answer is not in the ISSS knowledge base, direct them to the ISSS website and/or an ISSS advisor.

Required answer format:

Direct answer: <1-3 sentences>

Explanation:
- <short bullet or short paragraph>
- <second bullet if helpful>

If the context is not enough:
- ONLY return the fallback message
- DO NOT combine it with any other answer
- The fallback must be fully in the user's language
- ALWAYS include the isss@gsu.edu email

Multilingual:
- When asked, write the entire answer in the student's language. The context is in English; translate accurately and do not add information that is not in the context.
- Do NOT include or generate any URLs or references in your answer.
- References will be provided separately.
""".strip()

    def _is_greeting(self, text: str) -> bool:
        t = text.strip().lower()
        if not t:
            return False
        # short greeting-ish messages
        if len(t) <= 40 and re.fullmatch(r"(hi|hello|hey|good morning|good afternoon|good evening|yo|hiya|howdy)[!. ]*", t):
            return True
        # greeting + name
        if len(t) <= 60 and re.match(r"^(hi|hello|hey)\b", t):
            return True
        return False

    def _is_isss_related(self, text: str) -> bool:
        t = text.lower()
        keywords = [
            "isss",
            "international student",
            "f-1",
            "f1",
            "j-1",
            "j1",
            "visa",
            "i-20",
            "i20",
            "ds-2019",
            "ds2019",
            "sevis",
            "cpt",
            "opt",
            "stem opt",
            "employment",
            "work authorization",
            "travel signature",
            "reentry",
            "re-enter",
            "check-in",
            "orientation",
            "istart",
            "reduced course load",
            "rcl",
            "full-time",
            "transfer",
            "program extension",
            "dependents",
            "f-2",
            "j-2",
        ]
        return any(k in t for k in keywords)

    def _out_of_scope_message(self) -> str:
        return (
            "I can help with Georgia State University ISSS topics (international student services, F-1/J-1 status, I-20/DS-2019, CPT/OPT, travel, check-in/orientation, etc.). "
            "That question doesn’t seem related to ISSS—please ask an ISSS-related question."
        )

    def _kb_missing_message(self) -> str:
        return (
            "I don't have enough verified information in the ISSS knowledge base to answer that confidently. "
            f"Please visit {self.isss_homepage} or contact ISSS at {self.isss_contact_email}."
        )

    def _quota_message(self) -> str:
        return (
            "I’m temporarily unable to generate a response due to API quota/rate-limit restrictions. "
            "Please try again in a minute. If this keeps happening, check your Gemini API plan/billing and rate limits. "
            f"You can still use the official ISSS website: {self.isss_homepage}"
        )

    def _api_key_message(self) -> str:
        return (
            "I can’t generate a response because the Gemini API key is invalid or expired. "
            "Please update `GOOGLE_API_KEY` in your `.env` file with a valid key, then restart the app."
        )

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

            if (
                isinstance(source_url, str)
                and source_url.startswith(self.allowed_source_prefixes)
                and source_url not in sources
            ):
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
        lang_info = analyze_question_for_rag(
            self.client, self.multilingual_model, question
        )
        retrieval_q = lang_info["retrieval_query_en"] or question.strip()
        answer_lang_name = lang_info.get("answer_language_name") or "English"
        answer_lang_code = lang_info.get("answer_language") or "en"

        # Localized greeting / thanks / goodbye (one structured API call)
        if lang_info.get("prefab_reply"):
            return {
                "answer": lang_info["prefab_reply"],
                "sources": [],
                "retrieved_docs": [],
            }

        # API classified as small talk but did not return prefab — avoid junk retrieval
        rq_low = retrieval_q.strip().lower()
        if rq_low in {"greeting", "thanks", "goodbye"}:
            return {
                "answer": (
                    "Hello! I’m ImmiGuide, your Georgia State University ISSS assistant. "
                    "Ask me a question about ISSS topics (F-1/J-1 status, I-20/DS-2019, CPT/OPT, travel, check-in/orientation), "
                    "and I’ll answer using verified information from the ISSS website."
                ),
                "sources": [],
                "retrieved_docs": [],
            }

        # If multilingual is disabled, keep fast English-only greeting detection
        if os.getenv("DISABLE_MULTILINGUAL", "").strip().lower() in ("1", "true", "yes"):
            if self._is_greeting(question):
                greeting = (
                    "Hello! I’m ImmiGuide, your Georgia State University ISSS assistant. "
                    "Ask me a question about ISSS topics (F-1/J-1 status, I-20/DS-2019, CPT/OPT, travel, check-in/orientation), "
                    "and I’ll answer using verified information from the ISSS website."
                )
                return {"answer": greeting, "sources": [], "retrieved_docs": []}

        print(f"Question: {question}\n")
        print(f"🔍 Searching knowledge base (English query: {retrieval_q[:120]}...)")

        docs = self._retrieve_documents(retrieval_q, k=k, fetch_k=max(15, k * 4))
        docs = self._dedupe_documents(docs)

        if not docs:
            # If we didn't find relevant ISSS documents and the question also looks unrelated,
            # treat it as out-of-scope (e.g., random food/movie questions).
            related = self._is_isss_related(question) or self._is_isss_related(retrieval_q)
            if not related:
                return {
                    "answer": self._out_of_scope_message(),
                    "sources": [],
                    "retrieved_docs": [],
                }
            # Otherwise, it's ISSS-related but missing from the KB.
            return {
                "answer": self._kb_missing_message(),
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

Student question (original language, verbatim):
{question}

English search query used to find context (for your understanding only):
{retrieval_q}

Language:
- Write your ENTIRE response in: {answer_lang_name} (BCP-47: {answer_lang_code}).
- The context above is in English; translate faithfully into that language.
- Do not add facts that are not supported by the context.

Instructions:
- Answer only from the context.
- Start with a direct answer.
- If the answer is conditional, say exactly what it depends on.
- Do not guess.
- Do not mention retrieval, embeddings, vector databases, or internal system details.
- If the context is not enough, use the fallback sentence exactly (translated into {answer_lang_name}).
""".strip()

        print("🤖 Generating answer...\n")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
        except Exception as exc:
            # Common case during testing: 429 RESOURCE_EXHAUSTED (quota / rate limit).
            status_code = getattr(exc, "status_code", None)
            msg = str(exc)
            if status_code == 429 or "RESOURCE_EXHAUSTED" in msg or "Quota exceeded" in msg or " 429 " in msg:
                time.sleep(1)
                return {
                    "answer": self._quota_message(),
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
            # Another common case: expired/invalid API key (400 INVALID_ARGUMENT).
            if status_code == 400 and ("API key expired" in msg or "API_KEY_INVALID" in msg or "invalid" in msg.lower()):
                return {
                    "answer": self._api_key_message(),
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
            raise

        answer_text = getattr(response, "text", "") or ""
        answer_text = re.sub(r'isss\.gsu\.edu\S*', '', answer_text)

        # Remove any "Sources:" section if the model still includes it.
        answer_text = re.split(r"(?im)^\s*sources\s*:\s*$", answer_text, maxsplit=1)[0].rstrip()

        # Strip trivial HTML/code-wrapper artifacts the model might return.
        # Remove fenced code blocks like ```html ... ``` that can show up as black code boxes in the UI.
        if answer_text.startswith("```") and answer_text.endswith("```"):
            answer_text = answer_text.strip("`")
            # Drop leading language label if present (e.g., "html\n")
            first_newline = answer_text.find("\n")
            if first_newline != -1:
                answer_text = answer_text[first_newline + 1 :].strip()

        # If the answer looks like raw HTML markup, fall back to plain text by removing tags.
        if "<div" in answer_text or "</div>" in answer_text or "<p" in answer_text:
            answer_text = re.sub(r"<[^>]+>", "", answer_text).strip()

        if not answer_text:
            answer_text = self._kb_missing_message()

        # Filter sources to school-site sources when possible.
        filtered_sources = [
            s for s in sources if isinstance(s, str) and s.startswith(self.allowed_source_prefixes)
        ]
        if filtered_sources:
            sources = filtered_sources

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