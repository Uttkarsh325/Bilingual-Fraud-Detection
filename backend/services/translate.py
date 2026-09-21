"""
LLM-powered translation between Indian languages.

Used by the "translate the response to English" button in the UI so users who
receive a Hindi (or other Indic language) answer can read it in English — and
vice versa. Reuses the configured LLM, so no extra API keys are required.
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from services.llm import get_llm

_TARGET_NAMES = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
}

_TRANSLATE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a professional translator for Indian languages. "
            "Translate the user's text into {target}. "
            "Preserve all markdown formatting (headings, tables, bold, lists, links). "
            "Keep numbers and proper nouns unchanged. "
            "Output ONLY the translated text — no explanations, quotes or notes.",
        ),
        ("human", "{text}"),
    ]
)


def _target_name(code: str) -> str:
    return _TARGET_NAMES.get(code, code)


async def translate_text(text: str, target: str = "en-IN") -> str:
    """Translate `text` into `target` (BCP-47 code). Returns the translation."""
    # Full analyses can be long (tables, steps, citations) — give the LLM a
    # larger output cap than the default chat model uses.
    chain = _TRANSLATE_PROMPT | get_llm(2048) | StrOutputParser()
    return (
        await chain.ainvoke({"text": text, "target": _target_name(target)})
    ).strip()