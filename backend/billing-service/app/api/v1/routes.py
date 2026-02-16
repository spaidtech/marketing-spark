from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc

from common.core.settings import get_settings
from common.db.session import build_session_factory
from common.models import User, CreditLedger
from common.schemas.common import (
    CreditMutation,
    CreditBalanceOut,
    LedgerEntryOut,
    PaginatedLedgerOut,
)
from common.utils.deps import build_current_user_dep
from common.utils.credits import add_credits, deduct_credits

router = APIRouter(tags=["billing"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)
current_user_dep = build_current_user_dep(settings)


@router.get("/credits/balance", response_model=CreditBalanceOut)
async def credit_balance(user=Depends(current_user_dep)):
    async with session_factory() as db:
        existing = await db.execute(select(User).where(User.id == user["id"]))
        db_user = existing.scalar_one_or_none()
        if not db_user:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")
        return CreditBalanceOut(user_id=db_user.id, balance=db_user.credits_balance)


@router.post("/credits/add", response_model=CreditBalanceOut)
async def credit_add(payload: CreditMutation, user=Depends(current_user_dep)):
    new_balance = await add_credits(
        session_factory, user["id"], payload.amount, payload.reason, payload.reference_id
    )
    return CreditBalanceOut(user_id=user["id"], balance=new_balance)


@router.post("/credits/deduct", response_model=CreditBalanceOut)
async def credit_deduct(payload: CreditMutation, user=Depends(current_user_dep)):
    new_balance = await deduct_credits(
        session_factory, user["id"], payload.amount, payload.reason, payload.reference_id
    )
    return CreditBalanceOut(user_id=user["id"], balance=new_balance)


@router.get("/credits/ledger", response_model=PaginatedLedgerOut)
async def credit_ledger(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(current_user_dep),
):
    async with session_factory() as db:
        base = select(CreditLedger).where(CreditLedger.user_id == user["id"])

        total_result = await db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = total_result.scalar() or 0

        result = await db.execute(
            base.order_by(desc(CreditLedger.created_at))
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = result.scalars().all()
        return PaginatedLedgerOut(
            items=[
                LedgerEntryOut(
                    id=r.id,
                    delta=r.delta,
                    reason=r.reason,
                    reference_id=r.reference_id,
                    created_at=r.created_at,
                )
                for r in rows
            ],
            total=total,
            page=page,
            limit=limit,
        )
