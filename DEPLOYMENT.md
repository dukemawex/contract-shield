# Deployment Guide

## DigitalOcean App Platform Deployment

### Quick Deploy with App Spec

1. **Fork/Clone Repository**
   - Fork this repository to your GitHub account
   - Or clone it to your own repository

2. **Create New App on DigitalOcean**
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Choose "GitHub" as the source
   - Select your repository
   - DigitalOcean will auto-detect the `.do/app.yaml` configuration

3. **Review Configuration**
   - Backend service runs on port 8080
   - Frontend service runs on port 3000
   - Environment variables are automatically configured

4. **Deploy**
   - Click "Next" through the setup wizard
   - Review and click "Create Resources"
   - Wait for deployment to complete (5-10 minutes)

5. **Access Your App**
   - Frontend URL will be provided (e.g., `https://your-app.ondigitalocean.app`)
   - Backend API will be at the backend service URL

### Manual Configuration

If you prefer to configure manually:

**Backend Service:**
```yaml
Name: backend
Type: Web Service
Source Directory: /backend
Environment: Python
Build Command: pip install -r requirements.txt
Run Command: uvicorn main:app --host 0.0.0.0 --port 8080
HTTP Port: 8080
Instance Size: Basic (512MB RAM, 1 vCPU)
```

**Frontend Service:**
```yaml
Name: frontend
Type: Web Service
Source Directory: /frontend
Environment: Node.js
Build Command: npm install && npm run build
Run Command: npm start
HTTP Port: 3000
Instance Size: Basic (512MB RAM, 1 vCPU)
Environment Variables:
  - NEXT_PUBLIC_API_URL: ${backend.PUBLIC_URL}
```

### Cost Estimation

- Basic plan: ~$12/month ($6/service × 2 services)
- Includes:
  - 512MB RAM per service
  - 1 vCPU per service
  - 2GB bandwidth
  - Auto-scaling capabilities

### Custom Domain

1. Go to Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions
4. SSL certificate will be auto-provisioned

### Environment Variables

**Frontend:**
- `NEXT_PUBLIC_API_URL`: Set to backend service URL (auto-configured)

**Backend:**
- No additional environment variables required for basic operation
- In production, consider adding:
  - `ALLOWED_ORIGINS`: Comma-separated list of allowed frontend domains

## Alternative Deployment Options

### Vercel (Frontend) + Railway (Backend)

**Frontend on Vercel:**
```bash
cd frontend
vercel deploy
```

Set environment variable:
- `NEXT_PUBLIC_API_URL`: Your Railway backend URL

**Backend on Railway:**
1. Create new project on [Railway](https://railway.app)
2. Connect GitHub repository
3. Set root directory to `/backend`
4. Railway will auto-detect Python and deploy

### Docker Deployment

**Backend Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build
CMD ["npm", "start"]
```

### Heroku Deployment

**Backend (Procfile):**
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Frontend:**
Use the standard Node.js buildpack.

## Monitoring and Logs

### DigitalOcean
- Access logs from the App Platform dashboard
- View metrics (CPU, memory, bandwidth)
- Set up alerts for errors

### Application Logs
- Backend logs available via `uvicorn` output
- Frontend logs in browser console and server logs

## Security Considerations

1. **CORS Configuration**: Update `allow_origins` in backend to specific domains in production
2. **Rate Limiting**: Consider adding rate limiting to prevent abuse
3. **File Size Limits**: Currently no limit; add in production
4. **Input Validation**: Additional validation recommended for production

## Scaling

- DigitalOcean App Platform auto-scales based on load
- Consider upgrading instance sizes for heavy traffic
- Monitor memory usage, especially for large PDF processing

## Troubleshooting

**Backend not responding:**
- Check logs for errors
- Verify port 8080 is configured correctly
- Ensure all dependencies are installed

**Frontend can't reach backend:**
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS configuration
- Ensure backend service is running

**File upload fails:**
- Check file size (default limit ~10MB)
- Verify file format (PDF or DOCX)
- Check backend logs for extraction errors
