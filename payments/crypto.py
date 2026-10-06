import aiohttp
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CryptoPayment:
    """
    پرداخت رمزارز با استفاده از NowPayments API
    برای فعالسازی، API Key رو از nowpayments.io بگیرید و در تنظیمات ربات ذخیره کنید.
    """

    BASE_URL = "https://api.nowpayments.io/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def create_invoice(self, amount_usd: float, order_id: str, description: str = "") -> Optional[Dict]:
        if not self.api_key:
            logger.warning("NowPayments API key not set")
            return None

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "price_amount": amount_usd,
            "price_currency": "usd",
            "order_id": order_id,
            "order_description": description or f"Order #{order_id}",
            "ipn_callback_url": "",
            "success_url": "",
            "cancel_url": ""
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.BASE_URL}/invoice", json=payload, headers=headers, timeout=15) as resp:
                    if resp.status in [200, 201]:
                        data = await resp.json()
                        return {
                            "invoice_url": data.get("invoice_url"),
                            "invoice_id": data.get("id"),
                            "status": data.get("status", "waiting")
                        }
                    else:
                        text = await resp.text()
                        logger.error(f"NowPayments error {resp.status}: {text}")
        except Exception as e:
            logger.error(f"Crypto invoice error: {e}")
        return None

    async def get_payment_status(self, invoice_id: str) -> Optional[str]:
        if not self.api_key:
            return None
        headers = {"x-api-key": self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.BASE_URL}/payment/{invoice_id}", headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("payment_status")
        except Exception as e:
            logger.error(f"Crypto status check error: {e}")
        return None

    @staticmethod
    def toman_to_usd(amount_toman: float, usd_rate: float = 60000) -> float:
        """
        تبدیل تومان به دلار بر اساس نرخ تنظیم‌شده توسط مالک.
        """
        if usd_rate <= 0:
            usd_rate = 60000
        return round(amount_toman / usd_rate, 2)