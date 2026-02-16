import httpx
from fastapi import HTTPException

from common.core.settings import Settings


async def generate_text_huggingface(prompt: str, settings: Settings) -> str:
    """Send a prompt to Hugging Face Inference API and return generated text."""
    if not settings.huggingface_api_key:
        raise HTTPException(status_code=500, detail="HUGGINGFACE_API_KEY is not configured")
    if not settings.hf_llm_model:
        raise HTTPException(status_code=500, detail="HF_LLM_MODEL is not configured")

    url = f"https://api-inference.huggingface.co/models/{settings.hf_llm_model}"
    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 220, "temperature": 0.7, "return_full_text": False},
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Hugging Face request error: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text[:300] if response.text else "Unknown Hugging Face API error"
        raise HTTPException(status_code=502, detail=f"Hugging Face API error: {detail}")

    data = response.json()
    if isinstance(data, list) and data and isinstance(data[0], dict):
        generated = data[0].get("generated_text", "")
        if generated:
            return generated.strip()
    if isinstance(data, dict) and isinstance(data.get("generated_text"), str):
        return data["generated_text"].strip()

    raise HTTPException(status_code=502, detail="Hugging Face API returned an unexpected payload")

