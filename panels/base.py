from abc import ABC, abstractmethod
from typing import Tuple, Optional
from database.models import Panel

class BasePanel(ABC):
    def __init__(self, panel: Panel):
        self.panel = panel
        self.url = panel.url.rstrip("/")
        self.username = panel.username
        self.password = panel.password

    @abstractmethod
    async def test_connection(self) -> bool:
        pass

    @abstractmethod
    async def create_user(self, username: str, traffic_gb: float, duration_days: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        خروجی: (موفقیت، لینک اشتراک، کانفیگ مستقیم)
        """
        pass

    @abstractmethod
    async def delete_user(self, username: str) -> bool:
        pass