import re

class CardPayment:
    @staticmethod
    def clean_card_number(raw_card: str) -> str:
        return re.sub(r"\D", "", raw_card)

    @staticmethod
    def is_valid_card(card_number: str) -> bool:
        digits = CardPayment.clean_card_number(card_number)
        return len(digits) == 16