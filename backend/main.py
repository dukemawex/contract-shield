from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import httpx
import pdfplumber
from docx import Document
from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Field, Session, SQLModel, create_engine, select

from email_utils import send_limit_email, send_upgrade_email, send_welcome_email

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LEMONSQUEEZY_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
LEMONSQUEEZY_VARIANT_ID = os.getenv("LEMONSQUEEZY_VARIANT_ID", "")
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://contract-shield.vercel.app")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/contract_shield.db")

FREE_ANALYSES_LIMIT = 3
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_TEXT_CHARS = 12_000

# ── AI System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a contract risk analyst for freelancers and independent contractors.
Analyze the contract and return ONLY a raw JSON object.
No markdown fences, no explanation, no preamble. Raw JSON only.

Schema:
{
  "risk_score": <integer 0-100>,
  "severity": <"low"|"medium"|"high">,
  "red_flags": [
    {
      "title": <string>,
      "severity": <"low"|"medium"|"high">,
      "explanation": <string>,
      "negotiation_tip": <string>
    }
  ],
  "negotiation_tips": [<string>],
  "draft_email": <string>,
  "summary": <string>
}

Scoring guide:
  0-39  = low risk
  40-69 = medium risk
  70-100 = high risk

Identify clauses related to: unlimited liability, broad indemnity, non-compete,
broad IP assignment, at-will termination, unfavorable payment terms (Net 60+),
automatic renewal, unilateral modification rights, and exclusivity obligations.
"""

# ── Database ───────────────────────────────────────────────────────────────────

os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    is_pro: bool = Field(default=False)
    analyses_used: int = Field(default=0)
    ls_customer_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Analysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_email: str = Field(foreign_key="user.email", index=True)
    filename: str
    risk_score: int
    severity: str
    result_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    create_db_and_tables()
    yield


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Contract Shield API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def extract_text_from_pdf(content: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)


def is_pdf(content: bytes) -> bool:
    return content[:4] == b"%PDF"


def is_docx(content: bytes) -> bool:
    return content[:4] == b"PK\x03\x04"


async def call_openrouter(text: str) -> dict:
    """Send contract text to OpenRouter and parse the JSON response."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "max_tokens": 2048,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Analyze this contract:\n\n{text[:MAX_TEXT_CHARS]}",
            },
        ],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://contract-shield.vercel.app",
                "X-Title": "Contract Shield",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="AI service error")

    response_data = resp.json()
    choices = response_data.get("choices") or []
    if not choices:
        raise HTTPException(status_code=502, detail="AI service returned empty response")
    raw = choices[0].get("message", {}).get("content", "")
    if not raw:
        raise HTTPException(status_code=502, detail="AI service returned empty content")
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


# ── Routes ─────────────────────────────────────────────────────────────────────


def _analyses_remaining(user: User) -> Optional[int]:
    """Return remaining free analyses, or None for Pro users."""
    if user.is_pro:
        return None
    return max(0, FREE_ANALYSES_LIMIT - user.analyses_used)


def _user_status_dict(user: User) -> dict:
    return {
        "email": user.email,
        "is_pro": user.is_pro,
        "analyses_used": user.analyses_used,
        "analyses_remaining": _analyses_remaining(user),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"status": "ok", "service": "Contract Shield API"}


# -- Users --

@app.post("/users/register")
async def register_user(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    raw_email = body.get("email", "")

    try:
        info = validate_email(raw_email, check_deliverability=False)
        email = info.normalized
    except EmailNotValidError:
        raise HTTPException(status_code=422, detail="Invalid email address")

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        is_new = user is None
        if is_new:
            user = User(email=email)
            session.add(user)
            session.commit()
            session.refresh(user)

    if is_new:
        background_tasks.add_task(send_welcome_email, email)

    return _user_status_dict(user)


@app.get("/users/status")
async def user_status(email: str):
    try:
        info = validate_email(email, check_deliverability=False)
        email = info.normalized
    except EmailNotValidError:
        raise HTTPException(status_code=422, detail="Invalid email address")

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _user_status_dict(user)


# -- Analyze --

@app.post("/analyze")
async def analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    email: str = Form(...),
):
    # Validate email
    try:
        info = validate_email(email, check_deliverability=False)
        email = info.normalized
    except EmailNotValidError:
        raise HTTPException(status_code=422, detail="Invalid email address")

    # Ensure user exists and check usage
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Email not registered. Please register first.",
            )

        if not user.is_pro and user.analyses_used >= FREE_ANALYSES_LIMIT:
            background_tasks.add_task(send_limit_email, email)
            raise HTTPException(status_code=403, detail="limit_reached")

    # Read file
    content = await file.read()

    # Size check
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    # Magic bytes file type check
    if is_pdf(content):
        text = extract_text_from_pdf(content)
    elif is_docx(content):
        text = extract_text_from_docx(content)
    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload PDF or DOCX.",
        )

    if not text or len(text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Could not extract sufficient text from the file.",
        )

    # Call AI
    result = await call_openrouter(text)

    # Persist result and increment counter
    with Session(engine) as session:
        persisted_user = session.exec(select(User).where(User.email == email)).first()
        if not persisted_user:
            raise HTTPException(status_code=401, detail="Email not registered.")

        persisted_user.analyses_used += 1
        session.add(persisted_user)

        analysis = Analysis(
            user_email=email,
            filename=file.filename or "upload",
            risk_score=result.get("risk_score", 0),
            severity=result.get("severity", "low"),
            result_json=json.dumps(result),
        )
        session.add(analysis)
        session.commit()

    return JSONResponse(content=result)


# -- Billing --

@app.post("/billing/create-checkout")
async def create_checkout(request: Request):
    body = await request.json()
    raw_email = body.get("email", "")

    try:
        info = validate_email(raw_email, check_deliverability=False)
        email = info.normalized
    except EmailNotValidError:
        raise HTTPException(status_code=422, detail="Invalid email address")

    if not all([LEMONSQUEEZY_API_KEY, LEMONSQUEEZY_STORE_ID, LEMONSQUEEZY_VARIANT_ID]):
        raise HTTPException(status_code=503, detail="Billing not configured")

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": email,
                    "custom": {"user_email": email},
                },
                "product_options": {
                    "redirect_url": f"{FRONTEND_URL}/success",
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": LEMONSQUEEZY_STORE_ID}},
                "variant": {"data": {"type": "variants", "id": LEMONSQUEEZY_VARIANT_ID}},
            },
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.lemonsqueezy.com/v1/checkouts",
            headers={
                "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            },
            json=payload,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Checkout creation failed")

    checkout_url = resp.json()["data"]["attributes"]["url"]
    return {"checkout_url": checkout_url}


@app.post("/billing/webhook")
async def billing_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    x_signature = request.headers.get("X-Signature", "")

    if LEMONSQUEEZY_WEBHOOK_SECRET:
        digest = hmac.new(
            LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(digest, x_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    data = json.loads(raw_body)
    event_name = data.get("meta", {}).get("event_name", "")
    custom_data = data.get("meta", {}).get("custom_data", {})
    user_email = custom_data.get("user_email") or (
        data.get("data", {}).get("attributes", {}).get("user_email")
    )

    if not user_email:
        return {"received": True}

    if event_name in ("order_created", "subscription_created"):
        with Session(engine) as session:
            user = session.exec(select(User).where(User.email == user_email)).first()
            if user:
                user.is_pro = True
                ls_customer_id = (
                    data.get("data", {}).get("attributes", {}).get("customer_id")
                )
                if ls_customer_id:
                    user.ls_customer_id = str(ls_customer_id)
                session.add(user)
                session.commit()
        background_tasks.add_task(send_upgrade_email, user_email)

    elif event_name in ("subscription_cancelled", "subscription_expired"):
        with Session(engine) as session:
            user = session.exec(select(User).where(User.email == user_email)).first()
            if user:
                user.is_pro = False
                session.add(user)
                session.commit()

    return {"received": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
