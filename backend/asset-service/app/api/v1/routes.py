import json
from fastapi import APIRouter, Depends, Header, HTTPException
import httpx
from sqlalchemy import select

from common.core.settings import get_settings
from common.db.session import build_session_factory
from common.models import Asset, AssetVersion
from common.schemas.common import AssetCreate, AssetUpdate, AssetOut, AssetVersionOut
from common.utils.deps import get_current_user

router = APIRouter(tags=["assets"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)


async def current_user_dep(authorization: str | None = Header(default=None)):
    return await get_current_user(authorization, settings)


async def upload_to_supabase(path: str, content: str) -> str:
    if not settings.supabase_service_role_key:
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
    return f"{settings.supabase_url}/storage/v1/object/public/{settings.storage_bucket}/{path}"


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


@router.get("/assets", response_model=list[AssetOut])
async def list_assets(user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(select(Asset).where(Asset.owner_id == user["id"]))
        return result.scalars().all()


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

