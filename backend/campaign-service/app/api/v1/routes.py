from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func

from common.core.settings import get_settings
from common.db.session import build_session_factory
from common.models import Campaign, CampaignStatus
from common.schemas.common import (
    CampaignCreate,
    CampaignOut,
    CampaignStatusUpdate,
    PaginatedCampaignOut,
)
from common.utils.deps import build_current_user_dep

router = APIRouter(tags=["campaigns"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)
current_user_dep = build_current_user_dep(settings)

VALID_STATUSES = {s.value for s in CampaignStatus}


@router.post("/campaigns", response_model=CampaignOut)
async def create_campaign(payload: CampaignCreate, user=Depends(current_user_dep)):
    async with session_factory() as db:
        campaign = Campaign(
            owner_id=user["id"],
            name=payload.name,
            goal=payload.goal,
            audience=payload.audience,
            status=CampaignStatus.draft.value,
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign


@router.get("/campaigns", response_model=PaginatedCampaignOut)
async def list_campaigns(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(current_user_dep),
):
    async with session_factory() as db:
        base = select(Campaign).where(Campaign.owner_id == user["id"])

        total_result = await db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = total_result.scalar() or 0

        result = await db.execute(
            base.order_by(Campaign.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return PaginatedCampaignOut(
            items=result.scalars().all(),
            total=total,
            page=page,
            limit=limit,
        )


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
async def update_status(
    campaign_id: int,
    payload: CampaignStatusUpdate,
    user=Depends(current_user_dep),
):
    async with session_factory() as db:
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id, Campaign.owner_id == user["id"])
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        campaign.status = payload.status.value
        await db.commit()
        await db.refresh(campaign)
        return campaign
