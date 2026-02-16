from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, desc

from common.core.settings import get_settings
from common.db.session import build_session_factory
from common.models import User, CreditLedger
from common.schemas.common import CreditMutation, CreditBalanceOut
from common.utils.deps import get_current_user

router = APIRouter(tags=["billing"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)


async def current_user_dep(authorization: str | None = Header(default=None)):
    return await get_current_user(authorization, settings)


@router.get("/credits/balance", response_model=CreditBalanceOut)
async def credit_balance(user=Depends(current_user_dep)):
    async with session_factory() as db:
        existing = await db.execute(select(User).where(User.id == user["id"]))
        db_user = existing.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return CreditBalanceOut(user_id=db_user.id, balance=db_user.credits_balance)


@router.post("/credits/add", response_model=CreditBalanceOut)
async def credit_add(payload: CreditMutation, user=Depends(current_user_dep)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    async with session_factory() as db:
        existing = await db.execute(select(User).where(User.id == user["id"]))
        db_user = existing.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        db_user.credits_balance += payload.amount
        db.add(
            CreditLedger(
                user_id=db_user.id,
                delta=payload.amount,
                reason=payload.reason,
                reference_id=payload.reference_id,
            )
        )
        await db.commit()
        return CreditBalanceOut(user_id=db_user.id, balance=db_user.credits_balance)


@router.post("/credits/deduct", response_model=CreditBalanceOut)
async def credit_deduct(payload: CreditMutation, user=Depends(current_user_dep)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    async with session_factory() as db:
        existing = await db.execute(select(User).where(User.id == user["id"]))
        db_user = existing.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        if db_user.credits_balance < payload.amount:
            raise HTTPException(status_code=402, detail="Insufficient credits")
        db_user.credits_balance -= payload.amount
        db.add(
            CreditLedger(
                user_id=db_user.id,
                delta=-payload.amount,
                reason=payload.reason,
                reference_id=payload.reference_id,
            )
        )
        await db.commit()
        return CreditBalanceOut(user_id=db_user.id, balance=db_user.credits_balance)


@router.get("/credits/ledger")
async def credit_ledger(limit: int = 50, user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(
            select(CreditLedger)
            .where(CreditLedger.user_id == user["id"])
            .order_by(desc(CreditLedger.created_at))
            .limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "id": row.id,
                "delta": row.delta,
                "reason": row.reason,
                "reference_id": row.reference_id,
                "created_at": row.created_at,
            }
            for row in rows
        ]

