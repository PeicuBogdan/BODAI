from collections import deque
from typing import Deque, Dict, List
import json
import os

MAX_CONTEXT: int = 10
CONTEXT_FILE: str = "data/context.json"

# fiecare element are forma {"role": "user"|"bot", "text": "..."}
context_memory: Deque[Dict[str, str]] = deque(maxlen=MAX_CONTEXT)


# ------------------- FUNCȚII DE BAZĂ -------------------

def add_message(role: str, text: str) -> None:
    """Adaugă un mesaj (user/bot) în memorie și salvează în fișier"""
    context_memory.append({"role": role, "text": text})
    save_context()


def get_context() -> List[Dict[str, str]]:
    """Returnează lista conversațiilor recente"""
    return list(context_memory)


def clear_context() -> None:
    """Șterge complet memoria conversațională (RAM + fișier)"""
    context_memory.clear()
    if os.path.exists(CONTEXT_FILE):
        os.remove(CONTEXT_FILE)


# ------------------- PERSISTENȚĂ -------------------

def save_context() -> None:
    """Salvează conversația actuală în fișier JSON"""
    os.makedirs(os.path.dirname(CONTEXT_FILE), exist_ok=True)
    with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(context_memory), f, indent=2, ensure_ascii=False)


def load_context() -> None:
    """Încarcă ultimul context din fișier, dacă există"""
    if os.path.exists(CONTEXT_FILE):
        try:
            with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
                data: List[Dict[str, str]] = json.load(f)
                context_memory.extend(data[-MAX_CONTEXT:])
                print(f"[INFO] Context încărcat: {len(data)} mesaje.")
        except Exception as e:
            print(f"[WARN] Eroare la încărcarea contextului: {e}")
