import aiohttp
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class ZarinpalPayment:
    """
    پرداخت از طریق درگاه ریالی زرین‌پال.
    MerchantID رو از zarinpal.com بگیرید و در تنظیمات ربات ذخیره کنید.
    """

    REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
    VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
    GATEWAY_URL = "https://www.zarinpal.com/pg/StartPay/"

    def __init__(self, merchant_id: str, callback_url: str = ""):
        self.merchant_id = merchant_id
        self.callback_url = callback_url or "https://example.com/callback"

    async def create_payment(self, amount_toman: int, description: str = "", mobile: str = "", email: str = "") -> Optional[Dict]:
        if not self.merchant_id:
            logger.warning("Zarinpal MerchantID not set")
            return None

        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_toman * 10,  # تبدیل تومان به ریال
            "description": description or "شارژ کیف پول",
            "callback_url": self.callback_url,
            "metadata": {"mobile": mobile, "email": email}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.REQUEST_URL, json=payload, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        d = data.get("data", {})
                        if d.get("code") == 100:
                            authority = d.get("authority")
                            return {
                                "authority": authority,
                                "gateway_url": f"{self.GATEWAY_URL}{authority}"
                            }
                        else:
                            logger.error(f"Zarinpal error: {data.get('errors')}")
        except Exception as e:
            logger.error(f"Zarinpal request error: {e}")
        return None

    async def verify_payment(self, authority: str, amount_toman: int) -> Optional[Dict]:
        if not self.merchant_id:
            return None
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_toman * 10,
            "authority": authority
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.VERIFY_URL, json=payload, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        d = data.get("data", {})
                        if d.get("code") in [100, 101]:
                            return {
                                "success": True,
                                "ref_id": d.get("ref_id"),
                                "card_pan": d.get("card_pan")
                            }
        except Exception as e:
            logger.error(f"Zarinpal verify error: {e}")
        return {"success": False}