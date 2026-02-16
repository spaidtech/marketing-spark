from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select

from common.core.settings import get_settings
from common.db.session import build_session_factory
from common.models import Campaign
from common.schemas.common import CampaignCreate, CampaignOut
from common.utils.deps import get_current_user

router = APIRouter(tags=["campaigns"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)


async def current_user_dep(authorization: str | None = Header(default=None)):
    return await get_current_user(authorization, settings)


@router.post("/campaigns", response_model=CampaignOut)
async def create_campaign(payload: CampaignCreate, user=Depends(current_user_dep)):
    async with session_factory() as db:
        campaign = Campaign(
            owner_id=user["id"],
            name=payload.name,
            goal=payload.goal,
            audience=payload.audience,
            status="draft",
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(select(Campaign).where(Campaign.owner_id == user["id"]))
        return result.scalars().all()


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut)
async def get_campaign(campaign_id: int, user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id, Campaign.owner_id == user["id"])
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign


@router.patch("/campaigns/{campaign_id}/status", response_model=CampaignOut)
async def update_status(campaign_id: int, status: str, user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id, Campaign.owner_id == user["id"])
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        campaign.status = status
        await db.commit()
        await db.refresh(campaign)
        return campaign

