# Contract Shield 🛡️

AI-powered contract risk analysis for freelancers. Upload PDF/DOCX contracts and get instant risk scores, red flag detection, negotiation tips, and draft response emails.

## Features

- 📄 **Contract Upload**: Support for PDF and DOCX formats
- 🎯 **Risk Detection**: Identifies unlimited liability, broad indemnity, and non-compete clauses
- 📊 **Risk Scoring**: 0-100 risk score with clear severity indicators
- 💡 **Negotiation Tips**: Actionable advice for each identified risk
- 📧 **Draft Email**: Auto-generated professional response to clients
- 📝 **Contract Summary**: Quick overview of extracted contract text

## Architecture

- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Backend**: FastAPI (Python) with pdfplumber and python-docx
- **Deployment**: Separate services on DigitalOcean App Platform

## Local Development

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The web app will be available at `http://localhost:3000`

## Deployment to DigitalOcean

### Using App Platform YAML

1. Fork/clone this repository to your GitHub account
2. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
3. Click "Create App" and select your repository
4. DigitalOcean will automatically detect the `.do/app.yaml` configuration
5. Review and deploy

### Manual Configuration

**Backend Service:**
- Type: Web Service
- Source: `/backend`
- Environment: Python
- Run Command: `uvicorn main:app --host 0.0.0.0 --port 8080`
- HTTP Port: 8080

**Frontend Service:**
- Type: Web Service
- Source: `/frontend`
- Environment: Node.js
- Build Command: `npm install && npm run build`
- Run Command: `npm start`
- HTTP Port: 3000
- Environment Variables:
  - `NEXT_PUBLIC_API_URL`: Set to your backend service URL

## API Endpoints

### `GET /`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "service": "Contract Shield API"
}
```

### `POST /api/analyze`
Analyze a contract file

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: File upload (PDF or DOCX)

**Response:**
```json
{
  "risk_score": 75,
  "red_flags": [
    {
      "title": "Unlimited Liability",
      "severity": "high",
      "explanation": "This contract contains clauses...",
      "negotiation_tip": "Request a liability cap..."
    }
  ],
  "negotiation_tips": ["Request a liability cap..."],
  "draft_email": "Subject: Contract Review...",
  "summary": "Contract summary text...",
  "text_length": 5420
}
```

## Risk Detection Heuristics

Contract Shield uses pattern matching to detect common risk factors:

1. **Unlimited Liability** (25 points)
   - Patterns: "unlimited liability", "without limitation", "shall be liable for all"

2. **Broad Indemnity Clause** (25 points)
   - Patterns: "indemnify and hold harmless", "against all claims"

3. **Non-Compete Clause** (20 points)
   - Patterns: "non-compete", "shall not compete", "restrictive covenant"

4. **Broad IP Assignment** (15 points)
   - Patterns: "all rights assigned", "work for hire"

5. **At-Will Termination** (15 points)
   - Patterns: "terminate at will", "terminate without cause"

6. **Automatic Renewal** (10 points)
   - Patterns: "automatic renewal", "auto-renew"

7. **Unfavorable Payment Terms** (10 points)
   - Patterns: Extended payment terms (Net 60+), payment only on completion

Maximum risk score is capped at 100.

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for Python
- **pdfplumber**: PDF text extraction
- **python-docx**: DOCX text extraction
- **Uvicorn**: ASGI server

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling

## Project Structure

```
contract-shield/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── app/
│   │   ├── page.tsx        # Main UI component
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   ├── package.json        # Node dependencies
│   └── .env.local          # Local environment config
├── .do/
│   └── app.yaml            # DigitalOcean deployment config
└── README.md               # This file
```

## Environment Variables

### Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

### Backend
No environment variables required for basic operation.

## Future Enhancements

While this is a minimal MVP, potential improvements include:

- User authentication and contract history
- More sophisticated NLP-based risk analysis
- Support for more document formats
- Contract comparison features
- Industry-specific risk profiles
- Integration with e-signature services

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
