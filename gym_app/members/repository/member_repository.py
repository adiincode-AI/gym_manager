from __future__ import annotations
import sqlite3
from gym_app.database import DatabaseManager
from gym_app.members.models.member import Member
from gym_app.exceptions import AppError, DuplicateRecordError

class MemberRepository:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def generate_next_member_code(self) -> str:
        """Generates sequential tracking codes (e.g., ITG-0001, ITG-0002)."""
        query = "SELECT member_code FROM members ORDER BY id DESC LIMIT 1"
        row_dict = self._db.fetch_one(query)
        if not row_dict:
            return "ITG-0001"
        
        try:
            last_code = row_dict["member_code"]
            last_num = int(last_code.split("-")[1])
            return f"ITG-{last_num + 1:04d}"
        except (KeyError, IndexError, ValueError):
            return "ITG-0001"

    def create(self, member: Member) -> int:
        """Inserts a new member record directly containing their chosen plan information."""
        query = """
            INSERT INTO members (member_code, full_name, phone, whatsapp, gender, age, address, plan_name, join_date, expiry_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            member.member_code, member.full_name, member.phone, member.whatsapp,
            member.gender, member.age, member.address, member.plan_name,
            member.join_date.isoformat(), member.expiry_date.isoformat(), 1
        )
        try:
            return self._db.execute(query, params)
        except DuplicateRecordError as exc:
            raise DuplicateRecordError(f"Member code '{member.member_code}' already exists.") from exc
        except Exception as exc:
            raise AppError(f"Database write failure: {exc}") from exc

    def get_all(self) -> list[Member]:
        """Fetches all raw rows from the members table and transforms them to domain objects."""
        query = "SELECT * FROM members ORDER BY id DESC"
        rows = self._db.fetch_all(query)
        return [Member.from_db_row(row) for row in rows]
    
    def search_members(self, search_term: str) -> list[Member]:
        """Searches members matching code, full name, or phone number strings."""
        if not search_term.strip():
            return []
            
        query = """
            SELECT * FROM members 
            WHERE member_code LIKE ? 
               OR full_name LIKE ? 
               OR phone LIKE ?
            LIMIT 5
        """
        # Wrap with standard SQL wildcard percentages
        like_term = f"%{search_term.strip()}%"
        rows = self._db.fetch_all(query, (like_term, like_term, like_term))
        
        return [Member.from_db_row(row) for row in rows]
    def get_expiring_soon(self, days_limit: int = 7) -> list[Member]:
        """Fetches active members whose plans expire within the next specified days."""
        query = """
            SELECT * FROM members 
            WHERE is_active = 1 
              AND expiry_date >= DATE('now')
              AND expiry_date <= DATE('now', ?)
            ORDER BY expiry_date ASC
        """
        days_param = f"+{days_limit} days"
        rows = self._db.fetch_all(query, (days_param,))
        return [Member.from_db_row(row) for row in rows]

    def get_recent_registrations(self, limit: int = 5) -> list[Member]:
        """Fetches the most recently registered gym members."""
        query = """
            SELECT * FROM members 
            ORDER BY id DESC 
            LIMIT ?
        """
        rows = self._db.fetch_all(query, (limit,))
        return [Member.from_db_row(row) for row in rows]
    
    def update(self, member: Member) -> None:
        """Updates an existing member's records in the single-table model."""
        query = """
            UPDATE members
            SET full_name = ?, phone = ?, whatsapp = ?, gender = ?, 
                age = ?, address = ?, plan_name = ?, expiry_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (
            member.full_name, member.phone, member.whatsapp, member.gender,
            member.age, member.address, member.plan_name, member.expiry_date.isoformat(),
            member.id
        )
        try:
            self._db.execute(query, params)
        except Exception as exc:
            raise AppError(f"Database update query failed: {exc}") from exc

    def delete(self, member_id: int) -> None:
        """Removes a member completely from the database using their primary ID key."""
        try:
            self._db.delete_by_id(table="members", record_id=member_id)
        except Exception as exc:
            raise AppError(f"Database deletion query failed: {exc}") from exc