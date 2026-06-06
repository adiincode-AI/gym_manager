from gym_app.database import DatabaseManager

class DashboardRepository:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def get_total_members_count(self) -> int:
        """Counts every single member ever registered."""
        row = self._db.fetch_one("SELECT COUNT(*) as count FROM members")
        return row["count"] if row else 0

    def get_active_members_count(self) -> int:
        """Counts members whose expiry date has not passed yet."""
        row = self._db.fetch_one("SELECT COUNT(*) as count FROM members WHERE expiry_date >= DATE('now')")
        return row["count"] if row else 0

    def get_expiring_soon_count(self, days_limit: int = 7) -> int:
        """Counts members whose plans expire within the next X days."""
        query = """
            SELECT COUNT(*) as count FROM members 
            WHERE expiry_date >= DATE('now') 
              AND expiry_date <= DATE('now', ?)
        """
        row = self._db.fetch_one(query, (f"+{days_limit} days",))
        return row["count"] if row else 0