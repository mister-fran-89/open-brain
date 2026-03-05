import json
import httpx
from typing import Optional

from src.ai.base import AIProvider
from src.core.models import ClassificationResult, Category, Item
from src.config import settings


CLASSIFY_PROMPT = """Analyze the following text and classify it into one of these categories:
- person: Information about a person (contact, meeting notes, relationship details)
- project: A task, initiative, or thing with next actions
- idea: A thought, concept, or creative spark
- admin: Administrative task, appointment, reminder

Extract a title and relevant metadata based on the category.

Respond with JSON only:
{
  "category": "person|project|idea|admin",
  "title": "Short descriptive title",
  "metadata": {"key": "value pairs relevant to category"},
  "tags": ["relevant", "tags"],
  "confidence": 0.0-1.0
}

Text to classify:
"""

QUERY_PROMPT = """You are a helpful assistant answering questions about the user's personal knowledge base.
Use the provided context to answer the question. If the answer isn't in the context, say so.
Cite sources by mentioning titles when relevant.

Context:
{context}

Question: {question}

Answer:"""

SUMMARIZE_PROMPT = """Generate a concise digest of the following items. Group by category, highlight action items, and note any patterns or connections.

Items:
{items}

Digest:"""



PREPROCESS_PROMPT = """Rewrite the note below as dense personal notes — maximum meaning, minimum words.

Rules:
- Keep ALL unique facts, people, dates, reasons, emotions, and context. If it adds meaning, keep it.
- Cut only true repetition: the same idea restated multiple times. Say it once, sharply.
- Do NOT reduce to a single action or task — the body must explain the full situation and why it matters.
- Fix spelling mistakes. Keep the author's first-person voice.
- Do not add any word or idea not already present.
- End with one line starting with "→": the single most important next step.

Example:
Input: "ugh so i keep forgetting to chase the accountant about the tax thing its been like 3 weeks since i sent the documents and nothing back its stressing me out because the deadline is end of month and if we miss it theres gonna be a penalty and i dont want to deal with that on top of everything else so i need to email him today or call him i just keep putting it off"
Output: "Sent tax documents to accountant 3 weeks ago — no response. Deadline end of month, penalty if missed. Been avoiding chasing it but can't anymore.
→ Call or email accountant today — don't put it off again."

Now rewrite this note:

Note: {text}

Distilled note:"""

class OllamaProvider(AIProvider):
    """Ollama-based AI provider for local inference."""

    def __init__(
        self,
        host: str = None,
        classify_model: str = None,
        embed_model: str = None,
        query_model: str = None,
        summarize_model: str = None,
        preprocess_model: str = None,
    ):
        self.host = host or settings.ollama_host
        self.classify_model = classify_model or settings.ollama_classify_model
        self.embed_model = embed_model or settings.ollama_embed_model
        self.query_model = query_model or settings.ollama_query_model
        self.summarize_model = summarize_model or settings.ollama_summarize_model
        self.preprocess_model = preprocess_model or settings.ollama_preprocess_model
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def _chat(self, model: str, prompt: str, temperature: float = 0.7) -> str:
        """Send chat completion request."""
        client = await self._get_client()
        response = await client.post(
            f"{self.host}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": temperature},
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    async def _embed(self, model: str, text: str) -> list[float]:
        """Generate embedding."""
        client = await self._get_client()
        response = await client.post(
            f"{self.host}/api/embeddings",
            json={"model": model, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]

    async def classify(self, text: str) -> ClassificationResult:
        """Classify text and extract metadata."""
        prompt = CLASSIFY_PROMPT + text
        response = await self._chat(self.classify_model, prompt)

        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            data = json.loads(response.strip())
        except json.JSONDecodeError:
            # Fallback for unparseable response
            data = {
                "category": "unknown",
                "title": text[:50],
                "metadata": {},
                "tags": [],
                "confidence": 0.3,
            }

        return ClassificationResult(
            category=Category(data.get("category", "unknown")),
            title=data.get("title", "Untitled"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            confidence=data.get("confidence", 0.5),
        )

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector."""
        return await self._embed(self.embed_model, text)

    async def query(self, question: str, context: list[str]) -> str:
        """Answer question using RAG context."""
        context_text = "\n\n---\n\n".join(context)
        prompt = QUERY_PROMPT.format(context=context_text, question=question)
        return await self._chat(self.query_model, prompt)

    async def summarize(self, items: list[Item]) -> str:
        """Generate digest from items."""
        items_text = "\n\n".join(
            f"[{item.category.value}] {item.title}\n{item.content}"
            for item in items
        )
        prompt = SUMMARIZE_PROMPT.format(items=items_text)
        return await self._chat(self.summarize_model, prompt)

    async def preprocess(self, text: str) -> str:
        """Clean, correct and synthesise raw input. Preserve meaning exactly."""
        prompt = PREPROCESS_PROMPT.format(text=text)
        result = await self._chat(self.preprocess_model, prompt, temperature=0.1)
        cleaned = result.strip()

        # Strip common model meta-commentary prefixes
        strip_prefixes = (
            "rewritten:", "cleaned:", "here is", "here's", "note:",
            "output:", "result:", "the final", "the cleaned",
        )
        lower = cleaned.lower()
        for prefix in strip_prefixes:
            if lower.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break

        # Strip meta-commentary preamble if the first paragraph looks like one
        double_newline = chr(10) + chr(10)
        if double_newline in cleaned:
            parts = [p.strip() for p in cleaned.split(double_newline) if p.strip()]
            preamble_markers = ("here is", "here's", "the following", "below is", "i have rewritten", "i've rewritten")
            if parts and any(parts[0].lower().startswith(m) for m in preamble_markers):
                parts = parts[1:]
            cleaned = double_newline.join(parts)

        # Safety: fall back to original if result is empty or too short
        if not cleaned or len(cleaned) < 3:
            return text
        return cleaned


    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
