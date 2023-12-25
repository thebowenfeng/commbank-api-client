from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Account:
    acc_number: str
    id: str
    name: str
    balance: float
    currency: str
    funds: float


@dataclass
class Transaction:
    id: str | None
    transaction_details_request: str | None
    description: str
    created: datetime
    amount: float
    pending: bool
