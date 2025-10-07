import sqlite3, os, time

DB_PATH = "data/bodai.sqlite3"

# -------------------- INIT --------------------
def init_db():
    """Creează structura de bază de date dacă nu există."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Memoria generală (amintiri conversaționale)
    c.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
    """)

    # Profil personal (informații despre utilizator)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        info TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()

# -------------------- MEMORY MANAGEMENT --------------------
def add_memory(text: str):
    """Adaugă o amintire conversațională."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO memory (text, timestamp) VALUES (?, ?)", (text, int(time.time())))
    conn.commit()
    conn.close()

def get_memories():
    """Returnează toate amintirile."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, text, timestamp FROM memory ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def search_memories():
    """Returnează toate amintirile (pentru căutare)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, text, timestamp FROM memory")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_memory(mem_id: int):
    """Șterge o amintire după ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM memory WHERE id=?", (mem_id,))
    conn.commit()
    conn.close()

def update_memory(mem_id: int, text: str):
    """Actualizează textul unei amintiri."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE memory SET text=? WHERE id=?", (text, mem_id))
    conn.commit()
    conn.close()

# -------------------- USER PROFILE --------------------
def add_profile_info(category: str, info: str):
    """Adaugă o informație despre utilizator (profil personal)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO user_profile (category, info, timestamp) VALUES (?, ?, ?)", 
              (category, info, int(time.time())))
    conn.commit()
    conn.close()

def get_profile():
    """Returnează întregul profil personal (categorie + informație)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT category, info FROM user_profile ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_profile_entry(profile_id: int):
    """Șterge o înregistrare din profilul personal."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM user_profile WHERE id=?", (profile_id,))
    conn.commit()
    conn.close()

def clear_profile():
    """Șterge complet profilul personal."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM user_profile")
    conn.commit()
    conn.close()

# -------------------- CONNECTION --------------------
def get_connection():
    """Returnează o conexiune activă (pentru operații manuale)."""
    return sqlite3.connect(DB_PATH)
