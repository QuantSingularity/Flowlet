"""
Database access layer - repository pattern.

Provides strongly-typed repository classes that encapsulate all SQLAlchemy
queries and keep ORM logic out of route handlers and service functions.

Usage
-----
    from src.database import AccountRepository, TransactionRepository

    with db.session() as session:
        repo  = AccountRepository(session)
        acct  = repo.get_by_id("acct-uuid")
        txns  = TransactionRepository(session).list_by_account("acct-uuid", limit=20)
"""

from .repositories import (
    AccountRepository,
    CardRepository,
    TransactionRepository,
    UserRepository,
)

__all__ = [
    "AccountRepository",
    "CardRepository",
    "TransactionRepository",
    "UserRepository",
]
