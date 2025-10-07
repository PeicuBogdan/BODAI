import sys
import requests

API_URL = "http://localhost:8000/chat"

def ask_bodai(message: str):
    payload = {"message": message}
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print("🤖 BODAI:", response.json().get("reply"))
        else:
            print("❌ Eroare:", response.status_code, response.text)
    except Exception as e:
        print("⚠️ Nu pot contacta serverul:", e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # rulezi: python test_chat.py "mesajul tau"
        ask_bodai(" ".join(sys.argv[1:]))
    else:
        # fallback - chat interactiv
        print("Scrie 'exit' ca sa iesi.")
        while True:
            msg = input("Tu: ")
            if msg.lower() in {"exit", "quit"}:
                break
            ask_bodai(msg)
