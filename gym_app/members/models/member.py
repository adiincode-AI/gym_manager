from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime

@dataclass(frozen=True)
class Member:
    id: int | None
    member_code: str
    full_name: str
    phone: str
    whatsapp: str
    gender: str | None
    age: int | None
    address: str | None
    plan_name: str            # Added
    join_date: date
    expiry_date: date         # Added
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_db_row(cls, row_dict: dict) -> Member:
        """Maps a dictionary row from DatabaseManager directly to a domain object."""
        return cls(
            id=row_dict["id"],
            member_code=row_dict["member_code"],
            full_name=row_dict["full_name"],
            phone=row_dict["phone"],
            whatsapp=row_dict["whatsapp"],
            gender=row_dict["gender"],
            age=row_dict["age"],
            address=row_dict["address"],
            plan_name=row_dict["plan_name"],
            join_date=date.fromisoformat(row_dict["join_date"]) if isinstance(row_dict["join_date"], str) else row_dict["join_date"],
            expiry_date=date.fromisoformat(row_dict["expiry_date"]) if isinstance(row_dict["expiry_date"], str) else row_dict["expiry_date"],
            is_active=bool(row_dict["is_active"]),
            created_at=datetime.fromisoformat(row_dict["created_at"]) if isinstance(row_dict["created_at"], str) else row_dict["created_at"],
            updated_at=datetime.fromisoformat(row_dict["updated_at"]) if isinstance(row_dict["updated_at"], str) else row_dict["updated_at"]
        )