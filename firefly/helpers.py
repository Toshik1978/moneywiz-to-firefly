import re


def to_amount(amount: str) -> str:
    return re.sub('[-+,]', '', amount)
