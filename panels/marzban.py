import aiohttp
import logging
from typing import Tuple, Optional
from .base import BasePanel

logger = logging.getLogger(__name__)

class MarzbanPanel(BasePanel):
    async def get_token(self) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                data = {"username": self.username, "password": self.password}
                async with session.post(f"{self.url}/api/admin/token", data=data, timeout=10) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        return res.get("access_token")
        except Exception as e:
            logger.error(f"Marzban token error: {e}")
        return None

    async def test_connection(self) -> bool:
        return await self.get_token() is not None

    async def create_user(self, username: str, traffic_gb: float, duration_days: int) -> Tuple[bool, Optional[str], Optional[str]]:
        token = await self.get_token()
        if not token:
            return False, None, None

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "username": username,
            "data_limit": int(traffic_gb * 1024 * 1024 * 1024),
            "expire": int((duration_days * 86400) + 0),
            "proxies": {"vless": {}, "vmess": {}, "trojan": {}, "shadowsocks": {}},
            "inbounds": {}
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.url}/api/user", json=payload, headers=headers, timeout=10) as resp:
                    if resp.status in [200, 201]:
                        res = await resp.json()
                        sub_link = res.get("subscription_url", "")
                        return True, sub_link, None
        except Exception as e:
            logger.error(f"Marzban create user error: {e}")
        return False, None, None

    async def delete_user(self, username: str) -> bool:
        token = await self.get_token()
        if not token:
            return False
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.url}/api/user/{username}", headers=headers, timeout=10) as resp:
                    return resp.status == 200
        except Exception:
            return False