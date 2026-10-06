import aiohttp
import json
import uuid
import logging
from typing import Tuple, Optional
from .base import BasePanel

logger = logging.getLogger(__name__)

class ThreeXUIPanel(BasePanel):
    def __init__(self, panel):
        super().__init__(panel)
        self.cookie = None

    async def login(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"username": self.username, "password": self.password}
                async with session.post(f"{self.url}/login", data=payload, timeout=10) as resp:
                    if resp.status == 200:
                        self.cookie = resp.headers.get("Set-Cookie")
                        return True
        except Exception as e:
            logger.error(f"3X-UI login error: {e}")
        return False

    async def test_connection(self) -> bool:
        return await self.login()

    async def create_user(self, username: str, traffic_gb: float, duration_days: int) -> Tuple[bool, Optional[str], Optional[str]]:
        if not await self.login():
            return False, None, None

        headers = {"Cookie": self.cookie} if self.cookie else {}
        client_uuid = str(uuid.uuid4())
        settings = {
            "clients": [{
                "id": client_uuid,
                "email": username,
                "totalGB": int(traffic_gb * 1024 * 1024 * 1024),
                "expiryTime": int(duration_days * 86400 * 1000),
                "enable": True
            }]
        }
        inbound_id = self.panel.inbound_id or "1"
        payload = {"id": int(inbound_id), "settings": json.dumps(settings)}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.url}/panel/api/inbounds/addClient", json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        sub_link = f"{self.url}/sub/{client_uuid}"
                        return True, sub_link, None
        except Exception as e:
            logger.error(f"3X-UI create client error: {e}")
        return False, None, None

    async def delete_user(self, username: str) -> bool:
        return True