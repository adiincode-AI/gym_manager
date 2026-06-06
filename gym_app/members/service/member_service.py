from __future__ import annotations
from datetime import date, timedelta
from gym_app.members.repository.member_repository import MemberRepository
from gym_app.members.models.member import Member
from gym_app.exceptions import AppError

class MemberService:
    def __init__(self, member_repo: MemberRepository) -> None:
        self._repo = member_repo

    def register_new_member(
        self,
        full_name: str,
        phone: str,
        whatsapp: str,
        gender: str | None,
        age: int | None,
        address: str | None,
        plan_name: str,
        join_date: date | None = None
    ) -> Member:
        """Handles business rules for registering a new member with their plan timeline info."""
        if not join_date:
            join_date = date.today()

        # Parse number of months straight out of the selection string (e.g., "3 Month Plan" -> 3)
        try:
            months = int(plan_name.split()[0])
        except (IndexError, ValueError):
            months = 1

        expiry_date = join_date + timedelta(days=months * 30)

        new_member = Member(
            id=None,
            member_code=self._repo.generate_next_member_code(),
            full_name=full_name.strip().title(),
            phone=phone.strip(),
            whatsapp=whatsapp.strip(),
            gender=gender,
            age=age,
            address=address.strip() if address else None,
            plan_name=plan_name,
            join_date=join_date,
            expiry_date=expiry_date
        )

        member_id = self._repo.create(new_member)
        
        return Member(
            id=member_id,
            member_code=new_member.member_code,
            full_name=new_member.full_name,
            phone=new_member.phone,
            whatsapp=new_member.whatsapp,
            gender=new_member.gender,
            age=new_member.age,
            address=new_member.address,
            plan_name=new_member.plan_name,
            join_date=new_member.join_date,
            expiry_date=new_member.expiry_date
        )

    def get_all_members(self) -> list[Member]:
        """Retrieves the complete list of registered members from the single table repository."""
        try:
            return self._repo.get_all()
        except Exception as exc:
            raise AppError(f"Failed to load member records: {exc}") from exc
        
    def search_active_members(self, search_term: str) -> list[Member]:
        """Retrieves matching member entries based on user string input filters."""
        try:
            return self._repo.search_members(search_term)
        except Exception as exc:
            raise AppError(f"Search query processing failed: {exc}") from exc
    def get_expiring_members(self) -> list[Member]:
        """Retrieves list of members needing imminent renewal notices."""
        try:
            return self._repo.get_expiring_soon(days_limit=7)
        except Exception as exc:
            raise AppError(f"Failed to fetch expiring alerts: {exc}") from exc

    def get_newest_members(self) -> list[Member]:
        """Retrieves list of recently onboarded gym profiles."""
        try:
            return self._repo.get_recent_registrations(limit=5)
        except Exception as exc:
            raise AppError(f"Failed to fetch recent registrations: {exc}") from exc
    def update_member_details(self, member_id: int, code: str, name: str, phone: str, whatsapp: str, gender: str, age: int | None, address: str | None, plan_name: str, join_date: date) -> None:
        """Calculates updated expiration schedules and commits profile alterations."""
        try:
            # Re-calculate expiration target date if plan was shifted during edit
            try:
                months = int(plan_name.split()[0])
            except (IndexError, ValueError):
                months = 1
            new_expiry = join_date + timedelta(days=months * 30)

            updated_member = Member(
                id=member_id, member_code=code, full_name=name.strip().title(),
                phone=phone.strip(), whatsapp=whatsapp.strip(), gender=gender,
                age=age, address=address.strip() if address else None,
                plan_name=plan_name, join_date=join_date, expiry_date=new_expiry
            )
            self._repo.update(updated_member)
        except Exception as exc:
            raise AppError(f"Failed to update member profile: {exc}") from exc

    def remove_member(self, member_id: int) -> None:
        """Processes request to delete an infrastructure profile record."""
        try:
            self._repo.delete(member_id)
        except Exception as exc:
            raise AppError(f"Failed to execute member deletion: {exc}") from exc
    def renew_member_plan(self, member: Member, new_plan_name: str) -> None:
        """Processes a membership renewal, intelligently extending expiration timelines."""
        try:
            try:
                months = int(new_plan_name.split()[0])
            except (IndexError, ValueError):
                months = 1

            today = date.today()
            
            # Smart Date Extension Engine
            base_date = member.expiry_date if member.expiry_date >= today else today
            new_expiry = base_date + timedelta(days=months * 30)

            # Reconstruct the domain object with the updated timelines
            updated_member = Member(
                id=member.id, member_code=member.member_code, full_name=member.full_name,
                phone=member.phone, whatsapp=member.whatsapp, gender=member.gender,
                age=member.age, address=member.address, plan_name=new_plan_name,
                join_date=member.join_date, expiry_date=new_expiry, is_active=True
            )
            self._repo.update(updated_member)
            
        except Exception as exc:
            raise AppError(f"Failed to process renewal database transaction: {exc}") from exc
        
    def has_received_reminder_recently(self, member_id: int) -> bool:
        """Returns True if the member got a message in the last 7 days."""
        query = """
            SELECT COUNT(*) as count FROM message_logs 
            WHERE member_id = ? AND sent_date >= DATE('now', '-7 days')
        """
        row = self._repo._db.fetch_one(query, (member_id,))
        return row["count"] > 0

    def log_reminder_sent(self, member_id: int) -> None:
        """Saves a record that we messaged this member."""
        query = "INSERT INTO message_logs (member_id, sent_date) VALUES (?, DATE('now'))"
        self._repo._db.execute(query, (member_id,))