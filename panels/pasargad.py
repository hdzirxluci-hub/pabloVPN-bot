import aiohttp
import logging
from typing import Tuple, Optional
from .base import BasePanel

logger = logging.getLogger(__name__)

class PasargadPanel(BasePanel):
    async def test_connection(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.url}/api/status", timeout=10) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def create_user(self, username: str, traffic_gb: float, duration_days: int) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            payload = {
                "auth_user": self.username,
                "auth_pass": self.password,
                "username": username,
                "traffic": traffic_gb,
                "period": duration_days
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.url}/api/user/create", json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return True, data.get("sub_url"), data.get("config")
        except Exception as e:
            logger.error(f"Pasargad create error: {e}")
        return False, None, None

    async def delete_user(self, username: str) -> bool:
        return True