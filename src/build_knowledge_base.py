import json
import os
import re
import shutil
from typing import Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings


class KnowledgeBaseBuilder:
    def __init__(
        self,
        chunk_size: int = 450,
        chunk_overlap: int = 80,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        print("Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
        )
        print("✅ Embedding model loaded")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "; ", ": ", " ", ""],
        )

    def normalize_text(self, text: str) -> str:
        text = text.replace("\r", "\n")
        text = text.replace("\xa0", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    def detect_tags(self, url: str, title: str, content: str) -> List[str]:
        haystack = f"{url} {title} {content[:2000]}".lower()
        rules = {
            "opt": ["optional practical training", "opt"],
            "stem_opt": ["stem opt", "i-983", "stem extension"],
            "cpt": ["curricular practical training", "cpt"],
            "employment": ["employment", "work off-campus", "work on-campus", "internship"],
            "housing": ["housing", "meal plan", "dining", "university housing"],
            "arrival": ["arrival", "airport", "port of entry", "orientation", "check-in"],
            "visa": ["visa", "sevis", "i-20", "ds-2019"],
            "transfer": ["transfer"],
            "health": ["health", "clinic", "well-being", "counseling"],
            "safety": ["safety", "police", "emergency"],
            "directory": ["directory", "staff"],
            "policy": ["policy", "policies"],
            "incoming_students": ["incoming-students"],
            "current_students": ["current-students"],
            "j1": ["j-1", "exchange visitor"],
            "f1": ["f-1", "student visa"],
        }

        tags = [tag for tag, needles in rules.items() if any(n in haystack for n in needles)]
        return sorted(set(tags)) or ["general"]

    def build_search_hints(self, url: str, title: str, content: str, tags: List[str]) -> str:
        hints: List[str] = []
        text = f"{title}\n{content[:2500]}".lower()

        expansions = {
            "opt": "optional practical training off-campus employment work authorization after graduation",
            "stem_opt": "stem opt extension form i-983 e-verify reporting requirements",
            "cpt": "curricular practical training internship work authorization while studying",
            "employment": "employment work job on-campus off-campus labor authorization",
            "visa": "visa sevis immigration document i-20 ds-2019",
            "arrival": "arrival airport check-in orientation travel entering the u.s.",
            "housing": "housing dorm meal plan where to live",
            "transfer": "school transfer transfer sevis record",
            "j1": "j-1 exchange visitor academic training",
            "f1": "f-1 international student status",
        }

        for tag in tags:
            if tag in expansions:
                hints.append(expansions[tag])

        if "off-campus" in text or "off campus" in text:
            hints.append("off-campus work employment authorization")
        if "on-campus" in text or "on campus" in text:
            hints.append("on-campus work student employment")
        if "academic training" in text:
            hints.append("j-1 academic training work authorization")
        if "reduced course load" in text:
            hints.append("reduced course load rcl authorization")

        if "#" in url:
            hints.append(url.split("#", 1)[1].replace("-", " "))

        return " | ".join(dict.fromkeys(hints))

    def enrich_page_content(self, item: Dict) -> str:
        title = self.normalize_text(item.get("title", "Untitled"))
        url = item.get("url", "")
        content = self.normalize_text(item.get("content", ""))
        tags = self.detect_tags(url, title, content)
        hints = self.build_search_hints(url, title, content, tags)

        enriched_parts = [
            f"TITLE: {title}",
            f"URL: {url}",
            f"TAGS: {', '.join(tags)}",
        ]

        if hints:
            enriched_parts.append(f"SEARCH_HINTS: {hints}")

        enriched_parts.append("CONTENT:")
        enriched_parts.append(content)
        return "\n".join(enriched_parts).strip()

    def load_scraped_content(self, filepath: str) -> List[Document]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents: List[Document] = []
        for item in data:
            url = item.get("url", "")
            title = self.normalize_text(item.get("title", "Untitled"))
            raw_content = self.normalize_text(item.get("content", ""))
            tags = self.detect_tags(url, title, raw_content)
            enriched_content = self.enrich_page_content(item)

            doc = Document(
                page_content=enriched_content,
                metadata={
                    "source": url,
                    "title": title,
                    "tags": tags,
                },
            )
            documents.append(doc)

        print(f"✅ Loaded {len(documents)} documents")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        print("Splitting documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)

        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["content_preview"] = chunk.page_content[:160]

        print(f"✅ Created {len(chunks)} chunks")
        return chunks

    def create_vector_store(self, chunks: List[Document], persist_directory: str = "data/visa_kb") -> Chroma:
        print(f"Creating vector database at {persist_directory}...")
        print("This might take a few minutes...")

        if os.path.exists(persist_directory):
            shutil.rmtree(persist_directory)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=persist_directory,
        )

        print("✅ Vector database created and saved!")
        return vectorstore

    def build_from_scraped_data(self, json_file: str, persist_directory: str = "data/visa_kb") -> Chroma:
        documents = self.load_scraped_content(json_file)
        chunks = self.split_documents(documents)
        vectorstore = self.create_vector_store(chunks, persist_directory=persist_directory)
        return vectorstore

    def expand_query(self, query: str) -> str:
        q = query.strip().lower()
        additions: List[str] = []

        if "off-campus" in q or "off campus" in q or ("work" in q and "campus" in q):
            additions.extend([
                "off-campus employment",
                "work authorization",
                "cpt",
                "opt",
                "f-1 employment rules",
            ])

        if re.search(r"\bcpt\b", q) or "curricular practical training" in q:
            additions.extend(["curricular practical training", "internship authorization", "credit bearing course"])

        if re.search(r"\bopt\b", q) or "optional practical training" in q:
            additions.extend(["optional practical training", "uscis", "employment authorization"])

        if "stem" in q and "opt" in q:
            additions.extend(["i-983", "stem opt extension", "e-verify"])

        if "i-20" in q:
            additions.extend(["form i-20", "sevis", "immigration document"])

        if "visa" in q:
            additions.extend(["f-1 visa", "j-1 visa", "sevis fee"])

        expanded = " | ".join([query] + additions)
        return expanded

    def retrieve(self, vectorstore: Chroma, query: str, k: int = 5, fetch_k: int = 20) -> List[Document]:
        expanded_query = self.expand_query(query)
        return vectorstore.max_marginal_relevance_search(expanded_query, k=k, fetch_k=fetch_k)


if __name__ == "__main__":
    print("=" * 60)
    print("BUILDING KNOWLEDGE BASE")
    print("=" * 60)

    builder = KnowledgeBaseBuilder()
    vectorstore = builder.build_from_scraped_data("data/raw_docs/isss_content.json")

    print("\n" + "=" * 60)
    print("TESTING SEARCH")
    print("=" * 60)

    test_queries = [
        "Can I work off-campus?",
        "What is CPT?",
        "How do I apply for OPT?",
        "What is STEM OPT?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = builder.retrieve(vectorstore, query, k=5, fetch_k=20)

        for i, doc in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"  Source: {doc.metadata.get('source', 'Unknown source')}")
            print(f"  Title: {doc.metadata.get('title', 'Untitled')}")
            print(f"  Tags: {', '.join(doc.metadata.get('tags', []))}")
            print(f"  Content: {doc.page_content[:220]}...")
