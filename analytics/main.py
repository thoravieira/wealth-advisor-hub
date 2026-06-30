"""
Analytics service — DuckDB + Iceberg lakehouse.
Exposes REST endpoints for clients, recommendations, voice messages, and alerts.
"""
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.responses import FileResponse
from seed import CLIENTS
from seed_conversations import CONVERSATIONS, TURNS

DATA_DIR = Path("/data")
DB_PATH   = DATA_DIR / "lake.duckdb"
AUDIO_DIR = Path("/app/audio")


def get_db():
    return duckdb.connect(str(DB_PATH))


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = get_db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id        VARCHAR PRIMARY KEY,
            name             VARCHAR NOT NULL,
            vip              BOOLEAN DEFAULT FALSE,
            risk_profile     VARCHAR,
            aum              DECIMAL(15,2),
            aum_currency     VARCHAR(3) DEFAULT 'BRL',
            equity_pct       FLOAT,
            fixed_income_pct FLOAT,
            funds_pct        FLOAT,
            cash_pct         FLOAT,
            equity_limit     FLOAT,
            status           VARCHAR,
            client_since     DATE,
            updated_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            snapshot_id      VARCHAR PRIMARY KEY,
            client_id        VARCHAR NOT NULL,
            snapshot_date    DATE NOT NULL,
            aum              DECIMAL(15,2),
            equity_pct       FLOAT,
            fixed_income_pct FLOAT,
            funds_pct        FLOAT,
            cash_pct         FLOAT,
            mtd_return       FLOAT,
            created_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id VARCHAR PRIMARY KEY,
            client_id         VARCHAR NOT NULL,
            advisor_id        VARCHAR DEFAULT 'thiago',
            session_id        VARCHAR,
            text              TEXT NOT NULL,
            status            VARCHAR DEFAULT 'draft',   -- draft | approved | sent | rejected
            channel           VARCHAR DEFAULT 'whatsapp',
            generated_at      TIMESTAMPTZ DEFAULT NOW(),
            approved_at       TIMESTAMPTZ,
            sent_at           TIMESTAMPTZ
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS voice_messages (
            message_id    VARCHAR PRIMARY KEY,
            client_id     VARCHAR NOT NULL,
            advisor_id    VARCHAR DEFAULT 'thiago',
            text          TEXT NOT NULL,
            audio_path    VARCHAR,
            status        VARCHAR DEFAULT 'generated',  -- generated | played | sent | failed
            channel       VARCHAR DEFAULT 'whatsapp',
            created_at    TIMESTAMPTZ DEFAULT NOW(),
            sent_at       TIMESTAMPTZ
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS alerts_history (
            alert_id     VARCHAR PRIMARY KEY,
            client_id    VARCHAR NOT NULL,
            alert_type   VARCHAR NOT NULL,  -- compliance_risk | suitability_expiry | withdrawal_signal | portfolio_drift
            severity     VARCHAR DEFAULT 'medium',  -- high | medium | low
            message      TEXT,
            triggered_at TIMESTAMPTZ DEFAULT NOW(),
            resolved_at  TIMESTAMPTZ,
            status       VARCHAR DEFAULT 'active'  -- active | resolved | dismissed
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conv_id       VARCHAR PRIMARY KEY,
            client_id     VARCHAR NOT NULL,
            channel       VARCHAR NOT NULL,
            conv_date     DATE NOT NULL,
            duration_s    INTEGER,
            sentiment     VARCHAR DEFAULT 'neutral',
            summary_en    TEXT,
            summary_pt    TEXT,
            has_audio     BOOLEAN DEFAULT FALSE,
            audio_file    VARCHAR,
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS conversation_turns (
            turn_id       VARCHAR PRIMARY KEY,
            conv_id       VARCHAR NOT NULL,
            speaker       VARCHAR NOT NULL,
            turn_order    INTEGER NOT NULL,
            text_en       TEXT,
            text_pt       TEXT,
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Seed clients if table is empty
    count = con.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    if count == 0:
        for c in CLIENTS:
            con.execute("""
                INSERT INTO clients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,NOW())
            """, [
                c["client_id"], c["name"], c["vip"], c["risk_profile"],
                c["aum"], c["aum_currency"], c["equity_pct"], c["fixed_income_pct"],
                c["funds_pct"], c["cash_pct"], c["equity_limit"], c["status"],
                c["client_since"],
            ])

    # Seed conversations
    count = con.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    if count == 0:
        for cv in CONVERSATIONS:
            con.execute("""
                INSERT INTO conversations
                    (conv_id, client_id, channel, conv_date, duration_s, sentiment,
                     summary_en, summary_pt, has_audio, audio_file)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, [cv["conv_id"], cv["client_id"], cv["channel"], cv["conv_date"],
                  cv.get("duration_s"), cv["sentiment"], cv["summary_en"], cv["summary_pt"],
                  cv.get("has_audio", False), cv.get("audio_file")])
        for t in TURNS:
            con.execute("""
                INSERT INTO conversation_turns
                    (turn_id, conv_id, speaker, turn_order, text_en, text_pt)
                VALUES (?,?,?,?,?,?)
            """, [t["turn_id"], t["conv_id"], t["speaker"], t["turn_order"],
                  t.get("text_en"), t.get("text_pt")])

    con.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Wealth Advisor Analytics", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    try:
        con = get_db()
        con.execute("SELECT 1").fetchone()
        con.close()
        return {"status": "ok", "duckdb": "ok"}
    except Exception as e:
        return {"status": "error", "duckdb": str(e)}


# ─── Clients ─────────────────────────────────────────────────────────────────

@app.get("/clients")
def list_clients(status: Optional[str] = None):
    con = get_db()
    if status:
        rows = con.execute(
            "SELECT * FROM clients WHERE status = ? ORDER BY aum DESC", [status]
        ).fetchall()
    else:
        rows = con.execute("SELECT * FROM clients ORDER BY aum DESC").fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


@app.get("/clients/{client_id}")
def get_client(client_id: str):
    con = get_db()
    row = con.execute(
        "SELECT * FROM clients WHERE client_id = ?", [client_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    cols = [d[0] for d in con.description]
    con.close()
    return dict(zip(cols, row))


@app.get("/clients/{client_id}/snapshots")
def get_client_snapshots(client_id: str):
    con = get_db()
    rows = con.execute(
        "SELECT * FROM portfolio_snapshots WHERE client_id = ? ORDER BY snapshot_date DESC",
        [client_id]
    ).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


# ─── Recommendations ─────────────────────────────────────────────────────────

class RecommendationIn(BaseModel):
    client_id: str
    text: str
    status: str = "draft"
    channel: str = "whatsapp"
    session_id: Optional[str] = None


class RecommendationUpdate(BaseModel):
    status: Optional[str] = None
    text: Optional[str] = None


@app.get("/recommendations")
def list_recommendations(client_id: Optional[str] = None, status: Optional[str] = None):
    con = get_db()
    query = "SELECT * FROM recommendations WHERE 1=1"
    params = []
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY generated_at DESC"
    rows = con.execute(query, params).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


@app.post("/recommendations", status_code=201)
def create_recommendation(body: RecommendationIn):
    rec_id = str(uuid.uuid4())
    con = get_db()
    con.execute("""
        INSERT INTO recommendations
            (recommendation_id, client_id, session_id, text, status, channel, generated_at)
        VALUES (?, ?, ?, ?, ?, ?, NOW())
    """, [rec_id, body.client_id, body.session_id, body.text, body.status, body.channel])
    con.close()
    return {"recommendation_id": rec_id, "status": body.status}


@app.get("/recommendations/{rec_id}")
def get_recommendation(rec_id: str):
    con = get_db()
    row = con.execute(
        "SELECT * FROM recommendations WHERE recommendation_id = ?", [rec_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    cols = [d[0] for d in con.description]
    con.close()
    return dict(zip(cols, row))


@app.patch("/recommendations/{rec_id}")
def update_recommendation(rec_id: str, body: RecommendationUpdate):
    con = get_db()
    row = con.execute(
        "SELECT recommendation_id FROM recommendations WHERE recommendation_id = ?", [rec_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if body.status:
        ts_col = {"approved": "approved_at", "sent": "sent_at"}.get(body.status)
        if ts_col:
            con.execute(
                f"UPDATE recommendations SET status = ?, {ts_col} = NOW() WHERE recommendation_id = ?",
                [body.status, rec_id]
            )
        else:
            con.execute(
                "UPDATE recommendations SET status = ? WHERE recommendation_id = ?",
                [body.status, rec_id]
            )
    if body.text:
        con.execute(
            "UPDATE recommendations SET text = ? WHERE recommendation_id = ?",
            [body.text, rec_id]
        )
    con.close()
    return {"recommendation_id": rec_id, "updated": True}


# ─── Voice messages ──────────────────────────────────────────────────────────

class VoiceMessageIn(BaseModel):
    client_id: str
    text: str
    status: str = "generated"
    channel: str = "whatsapp"
    audio_path: Optional[str] = None


@app.get("/voice-messages")
def list_voice_messages(client_id: Optional[str] = None):
    con = get_db()
    query = "SELECT * FROM voice_messages"
    params = []
    if client_id:
        query += " WHERE client_id = ?"
        params.append(client_id)
    query += " ORDER BY created_at DESC"
    rows = con.execute(query, params).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


@app.post("/voice-messages", status_code=201)
def create_voice_message(body: VoiceMessageIn):
    msg_id = str(uuid.uuid4())
    con = get_db()
    con.execute("""
        INSERT INTO voice_messages
            (message_id, client_id, text, status, channel, audio_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, NOW())
    """, [msg_id, body.client_id, body.text, body.status, body.channel, body.audio_path])
    con.close()
    return {"message_id": msg_id, "status": body.status}


# ─── Alerts ──────────────────────────────────────────────────────────────────

@app.get("/alerts")
def list_alerts(status: Optional[str] = None, client_id: Optional[str] = None):
    con = get_db()
    query = "SELECT * FROM alerts_history WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    query += " ORDER BY triggered_at DESC"
    rows = con.execute(query, params).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


# ─── Conversations ────────────────────────────────────────────────────────────

@app.get("/conversations")
def list_conversations(client_id: Optional[str] = None):
    con = get_db()
    query = "SELECT * FROM conversations WHERE 1=1"
    params = []
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    query += " ORDER BY conv_date DESC"
    rows = con.execute(query, params).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    result = []
    for r in rows:
        d = dict(zip(cols, r))
        if hasattr(d.get("conv_date"), "isoformat"):
            d["conv_date"] = d["conv_date"].isoformat()
        result.append(d)
    return result


@app.get("/conversations/{conv_id}")
def get_conversation(conv_id: str):
    con = get_db()
    row = con.execute(
        "SELECT * FROM conversations WHERE conv_id = ?", [conv_id]
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    cols = [d[0] for d in con.description]
    conv = dict(zip(cols, row))
    if hasattr(conv.get("conv_date"), "isoformat"):
        conv["conv_date"] = conv["conv_date"].isoformat()

    turn_rows = con.execute(
        "SELECT * FROM conversation_turns WHERE conv_id = ? ORDER BY turn_order ASC",
        [conv_id]
    ).fetchall()
    turn_cols = [d[0] for d in con.description]
    conv["turns"] = [dict(zip(turn_cols, t)) for t in turn_rows]
    con.close()
    return conv


# ─── Audio ────────────────────────────────────────────────────────────────────

@app.get("/audio/{filename}")
def get_audio(filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = AUDIO_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(str(path), media_type="audio/mpeg", filename=filename)
