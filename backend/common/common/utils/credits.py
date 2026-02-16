"""Atomic credit operations with row-level locking and compensation."""

import logging
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from common.models import User, CreditLedger

logger = logging.getLogger(__name__)


async def deduct_credits(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    amount: int,
    reason: str,
    reference_id: str = "",
) -> int:
    """Atomically deduct credits with SELECT ... FOR UPDATE.

    Returns the new balance.
    Raises HTTPException 402 if insufficient, 404 if user not found.
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    async with session_factory() as db:
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        if db_user.credits_balance < amount:
            raise HTTPException(status_code=402, detail="Insufficient credits")

        db_user.credits_balance -= amount
        db.add(
            CreditLedger(
                user_id=user_id,
                delta=-amount,
                reason=reason,
                reference_id=reference_id,
            )
        )
        await db.commit()
        return db_user.credits_balance


async def refund_credits(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    amount: int,
    reason: str,
    reference_id: str = "",
) -> int:
    """Compensate credits back after a failed operation.

    Returns the new balance.
    """
    if amount <= 0:
        return 0

    async with session_factory() as db:
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            logger.error("Refund failed: user %s not found", user_id)
            return 0

        db_user.credits_balance += amount
        db.add(
            CreditLedger(
                user_id=user_id,
                delta=amount,
                reason=reason,
                reference_id=reference_id,
            )
        )
        await db.commit()
        logger.info("Refunded %d credits to user %s: %s", amount, user_id, reason)
        return db_user.credits_balance


async def add_credits(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    amount: int,
    reason: str,
    reference_id: str = "",
) -> int:
    """Atomically add credits with row locking. Returns new balance."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    async with session_factory() as db:
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        db_user.credits_balance += amount
        db.add(
            CreditLedger(
                user_id=user_id,
                delta=amount,
                reason=reason,
                reference_id=reference_id,
            )
        )
        await db.commit()
        return db_user.credits_balance
