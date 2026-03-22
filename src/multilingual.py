"""
Multilingual support for ISSS RAG.

- Knowledge base text is English (scraped ISSS site).
- We map each user message to an English `retrieval_query_en` for vector search.
- We ask the model to answer in the student's language.
- For pure greetings / short thanks, we optionally return a ready-made `prefab_reply`
  in the student's language (one structured JSON call).
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

_ANALYSIS_PROMPT = """You help an international student office chatbot for Georgia State University (ISSS).

The student message may be in any language. Official website content in the database is English.

Return ONLY one JSON object (no markdown code fences), with exactly these keys:

1) "retrieval_query_en" (string)
   - For real ISSS/immigration questions: rewrite the question in clear English for search.
   - If the message is already English, keep it (fix typos if needed). Keep terms like CPT, OPT, I-20, F-1, J-1, SEVIS, DS-2019.
   - If the message is ONLY a greeting, thanks, or goodbye (no substantive question), use one of: "greeting", "thanks", "goodbye".

2) "answer_language" (string)
   - BCP-47 tag for the student's language, e.g. "en", "es", "fr", "zh", "ko", "vi", "hi", "pt".

3) "answer_language_name" (string)
   - Full English name, e.g. "Spanish", "English".

4) "prefab_reply" (string or null)
   - If the message is ONLY greeting / thanks / goodbye: set a complete 2–4 sentence reply IN THE STUDENT'S LANGUAGE introducing ImmiGuide as the GSU ISSS assistant and listing topics (F-1/J-1, I-20/DS-2019, CPT/OPT, travel, check-in). No RAG needed.
   - Otherwise null.

Student message:
"""


def analyze_question_for_rag(
    client: Any,
    model_name: str,
    question: str,
) -> Dict[str, Optional[str]]:
    q = (question or "").strip()
    fallback = {
        "retrieval_query_en": q,
        "answer_language": "en",
        "answer_language_name": "English",
        "prefab_reply": None,
    }
    if not q:
        return fallback

    if os.getenv("DISABLE_MULTILINGUAL", "").strip().lower() in ("1", "true", "yes"):
        return fallback

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=_ANALYSIS_PROMPT + json.dumps(q, ensure_ascii=False),
        )
        raw = (getattr(response, "text", None) or "").strip()
        if not raw:
            return fallback

        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)
        ren = str(data.get("retrieval_query_en", "")).strip()
        al = str(data.get("answer_language", "en")).strip() or "en"
        aln = str(data.get("answer_language_name", "English")).strip() or "English"
        prefab = data.get("prefab_reply")
        if prefab is not None and not isinstance(prefab, str):
            prefab = None
        if isinstance(prefab, str):
            prefab = prefab.strip() or None

        if not ren:
            ren = q

        return {
            "retrieval_query_en": ren,
            "answer_language": al,
            "answer_language_name": aln,
            "prefab_reply": prefab,
        }
    except Exception:
        return fallback
