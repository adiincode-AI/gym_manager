from dataclasses import dataclass

@dataclass(frozen=True)
class DashboardStats:
    active_members: int
    total_members: int
    expiring_soon: int