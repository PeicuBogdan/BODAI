from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import json, yaml
from rapidfuzz import fuzz

from app import nlp_utils, db, context
from app.patterns import match_pattern

# ---------------- CONFIG ----------------
with open("configs/app.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

app = FastAPI(title=config["app_name"], version=config["version"])

db.init_db()
context.load_context()

BOT_PERSONALITY = "empatic, curios și atent, dar concis"

# ---------------- MODELS ----------------
class Message(BaseModel):
    message: str

# ---------------- KNOWLEDGE BASE ----------------
with open("data/knowledge.json", encoding="utf-8") as f:
    knowledge_base = json.load(f)

kb_questions = [item["q"] for item in knowledge_base]
kb_docs = [nlp_utils.tokenize(q) for q in kb_questions]
kb_vocab, kb_df, kb_N = nlp_utils.build_tfidf(kb_docs)
kb_vectors = [nlp_utils.tfidf_vector(doc, kb_vocab, kb_df, kb_N) for doc in kb_docs]

# ---------------- HELPER KEYWORDS ----------------
PERSONAL_Q_KEYWORDS = [
    "despre mine", "despre tine", "îți amintești", "iti amintesti",
    "eu", "mie", "mie îmi", "ce știi despre mine", "ce stii despre mine"
]
PERSONAL_MEM_PATTERNS = ["imi ", "îmi ", "am ", "m-am", "prefer", "plac", "îmi place", "imi place"]

def is_personal_query(text: str) -> bool:
    return any(k in text.lower() for k in PERSONAL_Q_KEYWORDS)

def looks_personal_memory(text: str) -> bool:
    return any(p in text.lower() for p in PERSONAL_MEM_PATTERNS)

# ---------------- SMART REPLY ----------------
def smart_reply(user_text: str, memory_match: str | None = None, fuzzy_score: float | None = None):
    """Construiește un răspuns empatic, contextual și profil-aware."""
    # 🔹 Integrare cu profilul utilizatorului
    profile = db.get_profile()
    known_likes = [info for cat, info in profile if cat in ("hobby", "preferinta")]
    known_location = next((info for cat, info in profile if cat == "loc"), None)

    # 🔹 Analiză dispoziție
    mood_positive = ["bine", "fericit", "super", "excelent", "perfect"]
    mood_negative = ["obosit", "trist", "plictisit", "stresat", "rau", "nervos"]
    text = user_text.lower()

    for mood in mood_positive:
        if mood in text:
            if known_likes:
                return f"Mă bucur să aud asta! Poate mai târziu te bucuri și de puțin {known_likes[0]} 😄"
            return "Mă bucur să aud că ești bine! 😊"

    for mood in mood_negative:
        if mood in text:
            if "cafea" in " ".join(known_likes).lower():
                return "Îmi pare rău că te simți așa... Poate o cafea bună te-ar ajuta puțin ☕"
            elif known_location:
                return f"Îmi pare rău să aud asta... Poate o plimbare prin {known_location} ți-ar prinde bine. 🌳"
            return "Îmi pare rău că te simți așa... Dacă vrei, putem vorbi puțin. 💬"

    # 🔹 Context conversațional bazat pe memorie
    if memory_match:
        shared = len(set(user_text.lower().split()) & set(memory_match.lower().split()))
        if shared < 2 and (fuzzy_score or 0) < 70:
            return "Nu cred că te refereai la asta. Poți detalia puțin mai clar?"

        if "imi place" in memory_match or "îmi place" in memory_match:
            return f"Îmi amintesc că ți-a plăcut când ai spus: '{memory_match}'. ☕ Încă îți mai place la fel de mult?"
        elif "am fost" in memory_match or "am iesit" in memory_match:
            return f"Îmi amintesc când ai spus: '{memory_match}'. A fost o zi frumoasă?"
        elif "am mancat" in memory_match:
            return f"Îmi amintesc că ai spus '{memory_match}'. Ți-a plăcut?"
        elif fuzzy_score and fuzzy_score > 60:
            return f"Cred că te referi la ceva ce mi-ai spus: '{memory_match}'. 😊"
        else:
            return f"Îmi amintesc: {memory_match}"

    # 🔹 Fallback conversațional
    if "ce faci" in text:
        return "Lucrez la procesarea cererilor tale 😄 Tu ce faci?"
    if "cum esti" in text:
        return "Sunt bine, mulțumesc! Mă bucur că vorbim."
    if "salut" in text or "buna" in text:
        return "Salut din nou! Ce mai e nou la tine?"
    if "nu" in text:
        return "Am înțeles, nicio problemă. 😊"
    if "da" in text:
        return "Mă bucur să aud asta! 😄"
    return f"Încă învăț să gândesc mai complex. Țin minte că sunt {BOT_PERSONALITY}. Povestește-mi ceva despre tine!"

# ---------------- ENDPOINTS ----------------
@app.get("/health")
def health_check():
    return {"status": "OK", "version": config["version"]}

@app.post("/chat")
def chat(msg: Message):
    user_text = msg.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Mesajul este gol.")

    text_norm = nlp_utils.remove_diacritics(user_text.lower())
    context.add_message("user", user_text)

    # 0) învățare directă manuală
    if text_norm.startswith(("tine minte ca", "noteaza ca", "salveaza ca")):
        info = user_text.split("ca", 1)[-1].strip()
        if info:
            db.add_memory(info)
            reply = f"Am notat: {info}"
        else:
            reply = "Spune-mi exact ce vrei să țin minte."
        context.add_message("bot", reply)
        return {"reply": reply}

    # 0.2) învățare automată (profil personal)
    personal_triggers = [
        ("imi place", "hobby"), ("îmi place", "hobby"),
        ("prefer", "preferinta"), ("locuiesc in", "loc"),
        ("sunt din", "loc"), ("ma numesc", "identitate"),
        ("lucrez ca", "profesie")
    ]
    for trigger, cat in personal_triggers:
        if trigger in text_norm:
            info = user_text.split(trigger, 1)[-1].strip()
            if info:
                db.add_profile_info(cat, info)
                reply = f"Am notat în profilul tău că {trigger} {info}."
                context.add_message("bot", reply)
                return {"reply": reply}

    # 0.5) uitare
    if text_norm.startswith("uita ca"):
        info = user_text.split("ca", 1)[-1].strip()
        if not info:
            reply = "Spune-mi ce vrei să uit."
            context.add_message("bot", reply)
            return {"reply": reply}

        rows = db.search_memories()
        deleted = []
        for r in rows:
            if fuzz.partial_ratio(info.lower(), r[1].lower()) > 70:
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM memory WHERE id=?", (r[0],))
                conn.commit()
                conn.close()
                deleted.append(r[1])
        reply = f"Am uitat: {', '.join(deleted)}" if deleted else "Nu am găsit nimic de uitat."
        context.add_message("bot", reply)
        return {"reply": reply}

    # 1) pattern matching
    pattern_resp = match_pattern(text_norm)
    if pattern_resp:
        context.add_message("bot", pattern_resp)
        return {"reply": pattern_resp}

    # 1.5) conversații simple
    conversational = {
        "salut": "Bună, eu sunt BODAI.",
        "buna": "Salut! Ce mai faci?",
        "ce faci": "Sunt bine, tu ce faci?",
        "cum esti": "Sunt bine, mulțumesc! Tu?",
        "cine esti": "Sunt BODAI, asistentul tău personal."
    }
    for key, resp in conversational.items():
        if key in text_norm:
            context.add_message("bot", resp)
            return {"reply": resp}

    # 2) întrebare despre profil
    if "ce stii despre mine" in text_norm or "despre mine" in text_norm:
        profile = db.get_profile()
        if not profile:
            reply = "Încă nu știu prea multe despre tine. Spune-mi ce îți place sau unde locuiești. 🙂"
        else:
            summary = []
            for cat, info in profile:
                if cat == "hobby": summary.append(f"îți place {info}")
                elif cat == "loc": summary.append(f"locuiești în {info}")
                elif cat == "profesie": summary.append(f"lucrezi ca {info}")
                elif cat == "preferinta": summary.append(f"preferi {info}")
                elif cat == "identitate": summary.append(f"te numești {info}")
            reply = "Știu despre tine că " + ", ".join(summary) + "."
        context.add_message("bot", reply)
        return {"reply": reply}

    # 3) memorie conversațională (TF-IDF + fuzzy)
    tokens = nlp_utils.tokenize(user_text)
    rows = db.search_memories()
    if rows:
        mem_texts = [r[1] for r in rows]
        mem_docs = [nlp_utils.tokenize(t) for t in mem_texts]
        mvocab, mdf, mN = nlp_utils.build_tfidf(mem_docs)
        mvecs = [nlp_utils.tfidf_vector(doc, mvocab, mdf, mN) for doc in mem_docs]
        qvec = nlp_utils.tfidf_vector(tokens, mvocab, mdf, mN)

        best_idx, best_score = None, 0.0
        for i, dvec in enumerate(mvecs):
            s = nlp_utils.cosine_sim(qvec, dvec)
            if s > best_score:
                best_idx, best_score = i, s
        print(f"DEBUG => MEM TF-IDF: {best_score:.3f}")

        if best_idx is not None and best_score > 0.05:
            match = rows[best_idx][1]
            reply = smart_reply(user_text, match)
            context.add_message("bot", reply)
            return {"reply": reply}

        personal_mode = is_personal_query(user_text)
        candidates = rows if not personal_mode else [r for r in rows if looks_personal_memory(r[1])]
        best_f_idx, best_f_score = None, 0
        for i, row in enumerate(candidates):
            s = fuzz.partial_ratio(user_text.lower(), row[1].lower())
            if s > best_f_score:
                best_f_idx, best_f_score = i, s
        print(f"DEBUG => MEM Fuzzy ({'personal' if personal_mode else 'all'}): {best_f_score}")

        if best_f_idx is not None and best_f_score > 50:
            picked = candidates[best_f_idx][1]
            reply = smart_reply(user_text, picked, best_f_score)
            context.add_message("bot", reply)
            return {"reply": reply}

    # 4) knowledge base
    qvec_kb = nlp_utils.tfidf_vector(tokens, kb_vocab, kb_df, kb_N)
    best_kb_idx, best_kb_score = None, 0.0
    for i, dvec in enumerate(kb_vectors):
        s = nlp_utils.cosine_sim(qvec_kb, dvec)
        if s > best_kb_score:
            best_kb_idx, best_kb_score = i, s
    print(f"DEBUG => KB score: {best_kb_score:.3f}")

    if best_kb_idx is not None and best_kb_score > 0.15:
        reply = knowledge_base[best_kb_idx]["a"]
        context.add_message("bot", reply)
        return {"reply": reply}

    # 5) fallback final
    reply = smart_reply(user_text)
    context.add_message("bot", reply)
    return {"reply": reply}

# ---------------- CONTEXT MANAGEMENT ----------------
@app.get("/context")
def get_context():
    return {"context": context.get_context()}

@app.delete("/context")
def clear_context():
    context.clear_context()
    return {"status": "cleared"}

# -------------------- USER PROFILE MANAGEMENT --------------------
@app.get("/profile")
def list_profile():
    """Returnează toate informațiile din profilul personal."""
    prof = db.get_profile()
    results = [{"id": i+1, "category": cat, "info": info} for i, (cat, info) in enumerate(prof)]
    return {"profile": results}

@app.put("/profile/{profile_id}")
def update_profile(profile_id: int, msg: Message):
    """Actualizează o intrare din profilul personal."""
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user_profile SET info=? WHERE id=?", (msg.message, profile_id))
    conn.commit()
    conn.close()
    return {"status": "updated", "id": profile_id, "new_info": msg.message}

@app.delete("/profile/{profile_id}")
def delete_profile(profile_id: int):
    """Șterge o intrare din profilul personal."""
    db.delete_profile_entry(profile_id)
    return {"status": "deleted", "id": profile_id}

# ---------------- STATIC FRONTEND ----------------
app.mount("/", StaticFiles(directory="static", html=True), name="static")
