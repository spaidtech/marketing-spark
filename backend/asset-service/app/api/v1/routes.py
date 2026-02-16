import json
from fastapi import APIRouter, Depends, HTTPException, Query
import httpx
from sqlalchemy import select, func

from common.core.settings import get_settings
from common.db.session import build_session_factory
from common.models import Asset, AssetVersion
from common.schemas.common import (
    AssetCreate,
    AssetUpdate,
    AssetOut,
    AssetVersionOut,
    PaginatedAssetOut,
)
from common.utils.deps import build_current_user_dep

router = APIRouter(tags=["assets"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)
current_user_dep = build_current_user_dep(settings)


async def upload_to_supabase(path: str, content: str) -> str:
    if not settings.supabase_service_role_key or settings.supabase_service_role_key == "dummy":
        return f"mock://{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{settings.supabase_url}/storage/v1/object/{settings.storage_bucket}/{path}"
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
                "Content-Type": "application/json",
            },
            content=content.encode("utf-8"),
        )
        if resp.status_code not in (200, 201):
            return f"mock://{path}"
    # Return internal path; serve via signed URL endpoint instead of public URL
    return f"storage://{settings.storage_bucket}/{path}"


async def create_signed_url(path: str, expires_in: int = 3600) -> str:
    """Generate a short-lived signed URL for private storage access."""
    if not settings.supabase_service_role_key or settings.supabase_service_role_key == "dummy":
        return f"mock://{path}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{settings.supabase_url}/storage/v1/object/sign/{settings.storage_bucket}/{path}",
            headers={"Authorization": f"Bearer {settings.supabase_service_role_key}"},
            json={"expiresIn": expires_in},
        )
        if resp.status_code == 200:
            data = resp.json()
            return f"{settings.supabase_url}/storage/v1{data.get('signedURL', '')}"
    return f"mock://{path}"


@router.post("/assets", response_model=AssetOut)
async def create_asset(payload: AssetCreate, user=Depends(current_user_dep)):
    async with session_factory() as db:
        asset = Asset(
            campaign_id=payload.campaign_id,
            owner_id=user["id"],
            asset_type=payload.asset_type,
            title=payload.title,
            content=payload.content,
            metadata_json=json.dumps({"storage_url": ""}),
            current_version=1,
        )
        db.add(asset)
        await db.flush()
        db.add(
            AssetVersion(
                asset_id=asset.id,
                version_number=1,
                content=payload.content,
                change_note="initial",
            )
        )
        storage_path = f"{user['id']}/asset-{asset.id}/v1.txt"
        storage_url = await upload_to_supabase(storage_path, payload.content)
        asset.metadata_json = json.dumps({"storage_url": storage_url})
        await db.commit()
        await db.refresh(asset)
        return asset


@router.get("/assets", response_model=PaginatedAssetOut)
async def list_assets(
    campaign_id: int | None = Query(default=None, description="Filter by campaign"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(current_user_dep),
):
    async with session_factory() as db:
        base = select(Asset).where(Asset.owner_id == user["id"])
        if campaign_id is not None:
            base = base.where(Asset.campaign_id == campaign_id)

        total_result = await db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = total_result.scalar() or 0

        result = await db.execute(
            base.order_by(Asset.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return PaginatedAssetOut(
            items=result.scalars().all(),
            total=total,
            page=page,
            limit=limit,
        )


@router.patch("/assets/{asset_id}", response_model=AssetOut)
async def update_asset(asset_id: int, payload: AssetUpdate, user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(
            select(Asset).where(Asset.id == asset_id, Asset.owner_id == user["id"])
        )
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        next_version = asset.current_version + 1
        db.add(
            AssetVersion(
                asset_id=asset.id,
                version_number=next_version,
                content=payload.content,
                change_note=payload.change_note,
            )
        )
        storage_path = f"{user['id']}/asset-{asset.id}/v{next_version}.txt"
        storage_url = await upload_to_supabase(storage_path, payload.content)
        asset.content = payload.content
        asset.current_version = next_version
        asset.metadata_json = json.dumps({"storage_url": storage_url})
        await db.commit()
        await db.refresh(asset)
        return asset


@router.get("/assets/{asset_id}/versions", response_model=list[AssetVersionOut])
async def list_versions(asset_id: int, user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(
            select(AssetVersion)
            .join(Asset, Asset.id == AssetVersion.asset_id)
            .where(Asset.id == asset_id, Asset.owner_id == user["id"])
            .order_by(AssetVersion.version_number.desc())
        )
        return result.scalars().all()


@router.post("/assets/{asset_id}/undo", response_model=AssetOut)
async def undo_asset(asset_id: int, user=Depends(current_user_dep)):
    return await switch_version(asset_id, -1, user["id"])


@router.post("/assets/{asset_id}/redo", response_model=AssetOut)
async def redo_asset(asset_id: int, user=Depends(current_user_dep)):
    return await switch_version(asset_id, +1, user["id"])


async def switch_version(asset_id: int, delta: int, user_id: str):
    async with session_factory() as db:
        asset_res = await db.execute(
            select(Asset).where(Asset.id == asset_id, Asset.owner_id == user_id)
        )
        asset = asset_res.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        target_version = asset.current_version + delta
        version_res = await db.execute(
            select(AssetVersion).where(
                AssetVersion.asset_id == asset_id,
                AssetVersion.version_number == target_version,
            )
        )
        target = version_res.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=400, detail="No version available")
        asset.current_version = target.version_number
        asset.content = target.content
        await db.commit()
        await db.refresh(asset)
        return asset
