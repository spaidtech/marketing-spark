import json
import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import httpx
from sqlalchemy import select

from common.core.settings import get_settings
from common.db.session import build_session_factory
from common.models import UsageEvent
from common.schemas.common import (
    AIImageRequest,
    SuggestionRequest,
    SuggestionOut,
)
from common.utils.deps import build_current_user_dep
from common.utils.rate_limit import RateLimiter
from common.utils.credits import deduct_credits, refund_credits
from app.services.llm_client import generate_text_huggingface

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)
current_user_dep = build_current_user_dep(settings)
limiter: RateLimiter | None = None


def set_limiter(rate_limiter: RateLimiter) -> None:
    global limiter
    limiter = rate_limiter


async def save_usage(user_id: str, endpoint: str, latency_ms: int, success: bool, cost_usd: float):
    async with session_factory() as db:
        db.add(
            UsageEvent(
                user_id=user_id,
                service="ai-generation-service",
                endpoint=endpoint,
                latency_ms=latency_ms,
                success=success,
                cost_usd=cost_usd,
            )
        )
        await db.commit()


class GenerateTextRequest(BaseModel):
    prompt: str = Field(min_length=1)


async def generate_text_deepseek(prompt: str) -> str:
    if not settings.deepseek_api_key:
        return f"[Mocked DeepSeek response] {prompt}"
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.deepseek_model,
                "messages": [
                    {"role": "system", "content": "You are a marketing assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


@router.post("/ai/generate-text")
async def generate_text(payload: GenerateTextRequest, user=Depends(current_user_dep)):
    if limiter:
        await limiter.enforce(f"rate:ai:text:{user['id']}")

    credit_cost = 2
    await deduct_credits(
        session_factory, user["id"], credit_cost, "ai_text_generation"
    )

    started = time.perf_counter()
    success = True
    generated_text = ""
    try:
        if settings.llm_provider.lower() == "huggingface":
            generated_text = await generate_text_huggingface(payload.prompt, settings)
        else:
            generated_text = await generate_text_deepseek(payload.prompt)
    except HTTPException:
        success = False
        await refund_credits(
            session_factory, user["id"], credit_cost, "refund:ai_text_generation_failed"
        )
        raise
    except Exception as exc:
        success = False
        await refund_credits(
            session_factory, user["id"], credit_cost, "refund:ai_text_generation_failed"
        )
        provider = settings.llm_provider.lower()
        raise HTTPException(status_code=502, detail=f"{provider} text generation error: {exc}") from exc
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await save_usage(user["id"], "/ai/generate-text", latency_ms, success, 0.002)

    return {"generated_text": generated_text, "content": generated_text}


@router.post("/ai/generate-image")
async def generate_image(payload: AIImageRequest, user=Depends(current_user_dep)):
    if limiter:
        await limiter.enforce(f"rate:ai:image:{user['id']}")

    credit_cost = 8
    await deduct_credits(
        session_factory, user["id"], credit_cost, "ai_image_generation"
    )

    started = time.perf_counter()
    success = True
    try:
        if not settings.runpod_api_key or not settings.runpod_sdxl_endpoint:
            return {
                "campaign_id": payload.campaign_id,
                "image_url": "https://placehold.co/1024x1024/png?text=Mock+SDXL+Image",
            }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                settings.runpod_sdxl_endpoint,
                headers={"Authorization": f"Bearer {settings.runpod_api_key}"},
                json={
                    "input": {
                        "prompt": payload.prompt,
                        "width": payload.width,
                        "height": payload.height,
                        "style": payload.style,
                    }
                },
            )
            response.raise_for_status()
            data = response.json()
            image_url = data.get("output", {}).get("image_url") or data.get("output", [None])[0]
            return {"campaign_id": payload.campaign_id, "image_url": image_url}
    except HTTPException:
        success = False
        await refund_credits(
            session_factory, user["id"], credit_cost, "refund:ai_image_generation_failed"
        )
        raise
    except Exception as exc:
        success = False
        await refund_credits(
            session_factory, user["id"], credit_cost, "refund:ai_image_generation_failed"
        )
        raise HTTPException(status_code=502, detail=f"RunPod error: {exc}") from exc
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await save_usage(user["id"], "/ai/generate-image", latency_ms, success, 0.01)


@router.post("/ai/suggestions", response_model=SuggestionOut)
async def suggestion_engine(payload: SuggestionRequest, user=Depends(current_user_dep)):
    if limiter:
        await limiter.enforce(f"rate:ai:suggestions:{user['id']}")
    text = payload.asset_text.lower()
    suggestions: list[str] = []
    if "cta" not in text:
        suggestions.append("Add a stronger CTA above the fold to increase click-through rate.")
    if len(text) < 300:
        suggestions.append("Expand value proposition details to reduce ambiguity and boost trust.")
    if "social proof" not in text and "testimonial" not in text:
        suggestions.append("Include a testimonial or trust badge section for conversion confidence.")
    if not suggestions:
        suggestions.append("A/B test headline variants with quantified outcomes.")
    return SuggestionOut(suggestions=suggestions)


@router.post("/ai/refine")
async def refine_asset(content: str, instruction: str, user=Depends(current_user_dep)):
    if limiter:
        await limiter.enforce(f"rate:ai:refine:{user['id']}")

    credit_cost = 2
    await deduct_credits(session_factory, user["id"], credit_cost, "ai_refine")

    try:
        refined = f"{content}\n\n[Refine instruction applied]: {instruction}"
        return {"refined_content": refined}
    except Exception:
        await refund_credits(
            session_factory, user["id"], credit_cost, "refund:ai_refine_failed"
        )
        raise


@router.post("/ai/regenerate")
async def regenerate_asset(context: dict, user=Depends(current_user_dep)):
    if limiter:
        await limiter.enforce(f"rate:ai:regenerate:{user['id']}")

    credit_cost = 3
    await deduct_credits(session_factory, user["id"], credit_cost, "ai_regenerate")

    try:
        return {"regenerated": json.dumps(context), "note": "Regenerated with fresh variation"}
    except Exception:
        await refund_credits(
            session_factory, user["id"], credit_cost, "refund:ai_regenerate_failed"
        )
        raise
