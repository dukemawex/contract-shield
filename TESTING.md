# Testing Guide

## Running the Application Locally

### Prerequisites
- Python 3.12+
- Node.js 20+
- npm or yarn

### Backend Testing

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Start the server:**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

3. **Test the health endpoint:**
```bash
curl http://localhost:8000/
# Expected: {"status":"ok","service":"Contract Shield API"}
```

4. **Test file upload:**
```bash
# Create a test contract (see sample contracts below)
curl -X POST -F "file=@contract.pdf" http://localhost:8000/api/analyze
```

### Frontend Testing

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Start the development server:**
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

3. **Manual testing:**
- Open `http://localhost:3000` in your browser
- Upload a PDF or DOCX contract
- Verify the analysis results display correctly

## Sample Test Contracts

### High-Risk Contract (for testing)

Create a file `high_risk_contract.txt` with this content:

```
FREELANCE DEVELOPER AGREEMENT

This Agreement is between TechCorp Inc. ("Client") and Developer ("Contractor").

COMPENSATION
Payment of $5,000 upon completion. Payment terms: Net 90 days.

LIABILITY
Contractor shall indemnify and hold harmless Client against any and all claims, 
damages, losses, and expenses. Contractor's liability is unlimited and without limitation.

INTELLECTUAL PROPERTY  
All intellectual property, discoveries, and inventions shall be automatically assigned 
to Client. This is a work-for-hire agreement.

NON-COMPETE
Contractor agrees not to compete with Client for 3 years in North America and Europe.

TERMINATION
Client may terminate this agreement at will without cause at any time.

RENEWAL
This agreement automatically renews annually unless 120 days notice is provided.
```

Convert to PDF using any tool (e.g., Google Docs, Word).

### Low-Risk Contract (for testing)

```
CONSULTING SERVICES AGREEMENT

This Agreement is between Acme Corp ("Client") and Jane Smith ("Consultant").

SERVICES
Consultant will provide web development consulting services as outlined in Statement of Work.

COMPENSATION
$100/hour, billed monthly. Payment terms: Net 15 days. 
50% deposit required before work begins.

LIABILITY
Each party's liability is limited to the fees paid under this agreement. 
Consultant is not liable for indirect or consequential damages.

INTELLECTUAL PROPERTY
Client owns work product created specifically for this project. 
Consultant retains ownership of pre-existing IP and general skills.

TERM AND TERMINATION
Initial term of 3 months. Either party may terminate with 30 days written notice.
Consultant will be paid for work completed through termination date.

CONFIDENTIALITY
Both parties agree to maintain confidentiality of proprietary information 
for 2 years following termination.
```

## Expected Test Results

### High-Risk Contract
- **Risk Score**: 85-100
- **Red Flags**: 6-7 items
  - Unlimited Liability (HIGH)
  - Broad Indemnity (HIGH)
  - Non-Compete (MEDIUM)
  - Broad IP Assignment (MEDIUM)
  - At-Will Termination (MEDIUM)
  - Automatic Renewal (LOW)
  - Unfavorable Payment Terms (LOW)

### Low-Risk Contract
- **Risk Score**: 0-20
- **Red Flags**: 0-1 items
- **Email**: Should indicate readiness to proceed

## API Testing

### Using cURL

**Health Check:**
```bash
curl http://localhost:8000/
```

**Analyze Contract:**
```bash
curl -X POST \
  -F "file=@sample.pdf" \
  http://localhost:8000/api/analyze | jq .
```

### Using Python

```python
import requests

# Health check
response = requests.get('http://localhost:8000/')
print(response.json())

# Analyze contract
with open('contract.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/analyze', files=files)
    print(response.json())
```

### Using JavaScript

```javascript
// Health check
fetch('http://localhost:8000/')
  .then(res => res.json())
  .then(data => console.log(data));

// Analyze contract
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  body: formData
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## Edge Cases to Test

1. **Empty PDF**: Should return error about insufficient text
2. **Corrupted file**: Should return 500 error
3. **Wrong file type**: Should return 400 error (unsupported type)
4. **Large file** (>10MB): May timeout or fail (no explicit limit set)
5. **Scanned PDF** (image-only): Will extract little/no text
6. **Multiple uploads**: Should handle independently
7. **Safe contract**: Should return low risk score with positive email

## Performance Testing

### Backend Load Testing

Using Apache Bench:
```bash
# Create a test file first
ab -n 100 -c 10 -p contract.pdf -T 'multipart/form-data' \
  http://localhost:8000/api/analyze
```

Using wrk:
```bash
wrk -t4 -c100 -d30s http://localhost:8000/
```

### Expected Performance
- Health endpoint: <10ms response time
- Analysis endpoint: 200-500ms for typical contract
- Can handle ~50 concurrent requests on basic hardware

## Validation Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Can upload PDF file
- [ ] Can upload DOCX file
- [ ] Risk score displays correctly (0-100)
- [ ] Red flags are color-coded by severity
- [ ] Negotiation tips are shown
- [ ] Draft email is generated
- [ ] Contract summary displays
- [ ] Copy to clipboard works
- [ ] Error handling for invalid files
- [ ] CORS allows frontend requests
- [ ] Analysis completes in <2 seconds

## Troubleshooting

**Import errors:**
- Ensure all dependencies are installed
- Use Python 3.12+

**Port already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

**PDF extraction fails:**
- Ensure pdfplumber is installed correctly
- Try with a different PDF (some PDFs are image-only)

**CORS errors:**
- Verify backend CORS middleware is configured
- Check that API URL is correct in frontend
