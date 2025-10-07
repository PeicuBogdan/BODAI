import re, random

patterns = [
    (re.compile(r"\b(salut|buna|hello|hi)\b"), ["Salut!", "Bună, eu sunt BODAI."]),
    (re.compile(r"\b(multumesc|merci|thanks?)\b"), ["Cu plăcere!", "Oricând."]),
    (re.compile(r"\b(cine esti|what are you)\b"), ["Sunt BODAI, asistentul tău personal."])
]

def match_pattern(text: str):
    for regex, responses in patterns:
        if regex.search(text):
            return random.choice(responses)
    return None
