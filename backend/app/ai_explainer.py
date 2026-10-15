"""
ai_explainer.py
----------------
Turns a raw security finding into a human-readable explanation using
prompt engineering + an LLM call (with a safe offline fallback so the
project still works without an API key).

GEN AI COURSE CONCEPTS USED:
1. Prompt engineering  -> a structured prompt template with clear role,
                           context, and instructions (system + user prompt)
2. Few-shot prompting  -> we show the model one example of the exact output
                           format we want, before asking it to do the real one
3. Context injection   -> the RAG-retrieved guideline (see rag_engine.py) is
                           inserted into the prompt so the model's answer is
                           grounded in real guidance, not just guessing
4. LLM API usage       -> calling a hosted model through its API
5. Temperature         -> controls how random/creative vs. deterministic the
                           model's output is (low temperature = more focused,
                           which is what you want for security explanations)
"""

import os
from typing import Dict

# Uses the OpenAI SDK if installed and an API key is set.
# pip install openai
try:
    from openai import OpenAI
    _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) if os.environ.get("OPENAI_API_KEY") else None
except ImportError:
    _client = None


SYSTEM_PROMPT = (
    "You are Tassie, an AI security engineer. You explain code vulnerabilities "
    "in plain, simple English for a developer, in 2-3 sentences. Always mention "
    "the specific risk and one concrete fix. Do not use jargon without explaining it."
)

# Few-shot example: showing the model what a good answer looks like
FEW_SHOT_EXAMPLE = """
Example:
Finding: Hardcoded Secret — API_KEY = "sk_live_123..."
Guideline: Store credentials in environment variables or a secrets manager.
Explanation: This line hardcodes a live API key directly into the source code, which means \
anyone with repo access (or a leaked copy of the code) could steal it. Move this value into \
an environment variable and load it with os.environ.get("API_KEY") instead.
"""


def build_prompt(category: str, line_text: str, guideline_text: str) -> str:
    """Constructs the final user prompt by injecting the RAG context.
    This is the 'Augmented' part of Retrieval-Augmented Generation."""
    return f"""{FEW_SHOT_EXAMPLE}

Now explain this one the same way:
Finding: {category} — {line_text}
Guideline: {guideline_text}
Explanation:"""


def _fallback_explanation(category: str, line_text: str, guideline_text: str) -> str:
    """Offline, template-based explanation used when no LLM API key is
    configured. This keeps the project fully runnable as a portfolio demo
    without requiring a paid API key."""
    return (
        f"This line was flagged for {category.lower()}: `{line_text}`. "
        f"{guideline_text}"
    )


def explain_finding(category: str, line_text: str, guideline_text: str, temperature: float = 0.3) -> Dict:
    """Returns an AI-generated explanation for one finding.
    Falls back to a template if no API key is configured."""

    if _client is None:
        return {
            "explanation": _fallback_explanation(category, line_text, guideline_text),
            "source": "fallback-template",
        }

    prompt = build_prompt(category, line_text, guideline_text)

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temperature,   # low temperature = focused, consistent answers
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return {
            "explanation": response.choices[0].message.content.strip(),
            "source": "llm",
        }
    except Exception as e:
        # Never let an API failure break the scan — fall back gracefully.
        return {
            "explanation": _fallback_explanation(category, line_text, guideline_text),
            "source": f"fallback-after-error: {e}",
        }
