from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
from docx import Document
import io
import re
from typing import Dict, List, Any

app = FastAPI(title="Contract Shield API")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    doc = Document(io.BytesIO(file_content))
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def analyze_contract(text: str) -> Dict[str, Any]:
    """
    Analyze contract text using heuristics to detect risk factors.
    Returns risk score, red flags, explanations, negotiation tips, and draft email.
    """
    text_lower = text.lower()
    red_flags = []
    risk_points = 0
    
    # Check for unlimited liability
    liability_patterns = [
        r"unlimited liability",
        r"without limitation",
        r"shall be liable for all",
        r"indemnify.*without limit",
        r"liability shall not be capped",
    ]
    for pattern in liability_patterns:
        if re.search(pattern, text_lower):
            red_flags.append({
                "title": "Unlimited Liability",
                "severity": "high",
                "explanation": "This contract contains clauses that expose you to unlimited financial liability. This means there's no cap on the amount you could be required to pay in case of disputes or damages.",
                "negotiation_tip": "Request a liability cap that's reasonable for the project scope, typically 1-2x the contract value."
            })
            risk_points += 25
            break
    
    # Check for broad indemnity clauses
    indemnity_patterns = [
        r"indemnify.*harmless",
        r"hold harmless",
        r"indemnify.*against all claims",
        r"indemnification.*any and all",
        r"defend.*indemnify.*hold harmless",
    ]
    for pattern in indemnity_patterns:
        if re.search(pattern, text_lower):
            red_flags.append({
                "title": "Broad Indemnity Clause",
                "severity": "high",
                "explanation": "You're required to protect the client from all claims, damages, and losses - even those not caused by you. This could make you responsible for the client's own mistakes.",
                "negotiation_tip": "Limit indemnification to claims directly arising from your negligence or breach of contract. Request mutual indemnification."
            })
            risk_points += 25
            break
    
    # Check for non-compete clauses
    noncompete_patterns = [
        r"non-compete",
        r"non compete",
        r"shall not compete",
        r"agree not to.*compete",
        r"competitive.*business",
        r"restrictive covenant",
    ]
    for pattern in noncompete_patterns:
        if re.search(pattern, text_lower):
            red_flags.append({
                "title": "Non-Compete Clause",
                "severity": "medium",
                "explanation": "This contract restricts your ability to work with competitors or in similar industries, potentially limiting your future income opportunities.",
                "negotiation_tip": "Narrow the scope to specific direct competitors, limit the duration (e.g., 6 months), and restrict geographical area."
            })
            risk_points += 20
            break
    
    # Check for IP assignment
    ip_patterns = [
        r"intellectual property.*assigned",
        r"all rights.*assigned",
        r"work for hire",
        r"work-for-hire",
        r"transfer.*all rights",
    ]
    for pattern in ip_patterns:
        if re.search(pattern, text_lower):
            red_flags.append({
                "title": "Broad IP Assignment",
                "severity": "medium",
                "explanation": "You may be assigning all intellectual property rights, including pre-existing work and general knowledge gained during the project.",
                "negotiation_tip": "Clarify that only work specifically created for this project is assigned. Retain rights to pre-existing IP and general skills."
            })
            risk_points += 15
            break
    
    # Check for automatic renewal
    renewal_patterns = [
        r"automatic renewal",
        r"automatically renew",
        r"auto-renew",
        r"unless.*notice.*terminate",
    ]
    for pattern in renewal_patterns:
        if re.search(pattern, text_lower):
            red_flags.append({
                "title": "Automatic Renewal",
                "severity": "low",
                "explanation": "The contract automatically renews unless you actively cancel it, which could lock you into unwanted terms.",
                "negotiation_tip": "Request explicit approval for renewals or shorten the notice period for termination."
            })
            risk_points += 10
            break
    
    # Check for payment terms
    payment_concerns = []
    if re.search(r"net\s+\d{2,}", text_lower):
        match = re.search(r"net\s+(\d{2,})", text_lower)
        if match:
            days = int(match.group(1))
            if days > 30:
                payment_concerns.append(f"Payment terms of Net {days} days")
    
    if re.search(r"upon completion", text_lower) and not re.search(r"milestone", text_lower):
        payment_concerns.append("Full payment only upon completion")
    
    if payment_concerns:
        red_flags.append({
            "title": "Unfavorable Payment Terms",
            "severity": "low",
            "explanation": f"Payment terms may impact your cash flow: {', '.join(payment_concerns)}.",
            "negotiation_tip": "Request milestone-based payments (e.g., 30% upfront, 40% midway, 30% on completion) and Net 15 or Net 30 terms."
        })
        risk_points += 10
    
    # Check for termination clauses
    termination_patterns = [
        r"terminate.*at will",
        r"terminate.*without cause",
        r"terminate.*any time.*without",
    ]
    for pattern in termination_patterns:
        if re.search(pattern, text_lower):
            red_flags.append({
                "title": "At-Will Termination",
                "severity": "medium",
                "explanation": "The client can terminate the contract at any time without cause, leaving you without guaranteed income.",
                "negotiation_tip": "Request a notice period (e.g., 30 days) and payment for work completed plus a kill fee."
            })
            risk_points += 15
            break
    
    # Cap risk score at 100
    risk_score = min(risk_points, 100)
    
    # Generate negotiation tips summary
    negotiation_tips = [flag["negotiation_tip"] for flag in red_flags]
    
    # Generate draft email
    draft_email = generate_draft_email(red_flags, risk_score)
    
    # Create summary
    summary = create_text_summary(text)
    
    return {
        "risk_score": risk_score,
        "red_flags": red_flags,
        "negotiation_tips": negotiation_tips,
        "draft_email": draft_email,
        "summary": summary,
        "text_length": len(text),
    }


def create_text_summary(text: str, max_chars: int = 500) -> str:
    """Create a summary of the extracted text."""
    # Remove extra whitespace and newlines
    cleaned = re.sub(r'\s+', ' ', text).strip()
    
    if len(cleaned) <= max_chars:
        return cleaned
    
    # Try to break at a sentence
    summary = cleaned[:max_chars]
    last_period = summary.rfind('.')
    if last_period > max_chars * 0.7:  # If we can find a period in the last 30%
        summary = summary[:last_period + 1]
    else:
        summary = summary + "..."
    
    return summary


def generate_draft_email(red_flags: List[Dict], risk_score: int) -> str:
    """Generate a draft email to send to the client."""
    if not red_flags:
        return """Subject: Contract Review - Ready to Proceed

Hi [Client Name],

I've reviewed the contract and I'm excited to move forward with this project. The terms look fair and I'm ready to sign.

Please let me know if you need any additional information.

Best regards,
[Your Name]"""
    
    severity_high = any(flag["severity"] == "high" for flag in red_flags)
    
    if severity_high:
        subject = "Contract Review - Important Concerns to Discuss"
        opening = "I've reviewed the contract and I'm interested in working together, but I have some concerns about certain terms that I'd like to discuss before signing."
    else:
        subject = "Contract Review - Minor Clarifications Needed"
        opening = "I've reviewed the contract and I'm looking forward to working together. I have a few minor points I'd like to clarify."
    
    concerns = []
    for i, flag in enumerate(red_flags[:3], 1):  # Limit to top 3 concerns
        concerns.append(f"{i}. {flag['title']}: {flag['negotiation_tip']}")
    
    concerns_text = "\n".join(concerns)
    
    email = f"""Subject: {subject}

Hi [Client Name],

{opening}

Here are the items I'd like to discuss:

{concerns_text}

I believe these modifications will make the agreement more balanced while still protecting both our interests. I'm happy to discuss these points at your convenience.

Looking forward to hearing from you.

Best regards,
[Your Name]"""
    
    return email


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Contract Shield API"}


@app.post("/api/analyze")
async def analyze_contract_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to upload and analyze a contract (PDF or DOCX).
    Returns risk analysis with score, red flags, tips, and draft email.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        filename = file.filename.lower() if file.filename else ""
        
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(content)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(content)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload PDF or DOCX files only."
            )
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text from the file. Please ensure the file is not corrupted."
            )
        
        # Analyze the contract
        analysis = analyze_contract(text)
        
        return JSONResponse(content=analysis)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
