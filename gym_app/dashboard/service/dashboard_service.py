from gym_app.dashboard.repository.dashboard_repository import DashboardRepository
from gym_app.dashboard.models.dashboard_stats import DashboardStats
from gym_app.exceptions import AppError

class DashboardService:
    def __init__(self, repo: DashboardRepository) -> None:
        self._repo = repo

    def get_summary(self) -> DashboardStats:
        """Aggregates dashboard metrics from the database."""
        try:
            return DashboardStats(
                active_members=self._repo.get_active_members_count(),
                total_members=self._repo.get_total_members_count(),
                expiring_soon=self._repo.get_expiring_soon_count(days_limit=7)
            )
        except Exception as exc:
            raise AppError(f"Failed to load dashboard statistics: {exc}") from exc