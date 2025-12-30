# 🚀 Financial Reconciliation Agent - Quick Start

## Complete Setup Guide

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### 1. Backend Setup

```bash
# Navigate to project directory
cd /home/archis/Desktop/Financial-Reconcilation

# Activate virtual environment
source venv/bin/activate

# Start API server
python api/run.py
# or
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API Docs: `http://localhost:8000/api/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### 3. Test the System

1. Open `http://localhost:3000` in your browser
2. Upload a bank statement CSV file
3. Upload a ledger CSV file
4. Click "Start Reconciliation"
5. Watch the beautiful animations and view results!

### 4. Generate Test Data (Optional)

```bash
# Generate test data
python generate_test_data.py --num-transactions 50

# Test files will be in test_data/
```

## 🎨 Frontend Features

- **Sleek Design**: Modern glassmorphism UI with animated backgrounds
- **Smooth Animations**: Powered by Framer Motion
- **Interactive Charts**: Visual data representation with Recharts
- **Full Workflow**: Complete control from upload to results
- **Responsive**: Works on all devices

## 📡 API Endpoints

- `POST /api/reconcile` - Main reconciliation endpoint
- `GET /api/reports/{id}/csv` - Download CSV report
- `GET /api/tickets/{id}` - Get tickets in various formats
- `GET /api/health` - Health check

## 🔧 Configuration

### Backend
- Set `OPENAI_API_KEY` in environment for LLM features
- Adjust matching parameters in API request

### Frontend
- Update `NEXT_PUBLIC_API_URL` in `.env.local` if API is on different port

## 📚 Documentation

- `FRONTEND_SETUP.md` - Detailed frontend setup
- `N8N_INTEGRATION.md` - n8n workflow integration
- `README.md` - Project overview

## 🐛 Troubleshooting

### Backend not starting
- Check if port 8000 is available
- Verify virtual environment is activated
- Check Python dependencies are installed

### Frontend not connecting
- Verify backend is running
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for CORS errors

### File upload issues
- Ensure files are CSV or XLSX format
- Check file size limits
- Verify API is accepting multipart/form-data

## 🎉 You're Ready!

The system is now fully operational with:
- ✅ Complete backend API
- ✅ Beautiful frontend UI
- ✅ Full workflow control
- ✅ Report generation
- ✅ Ticket creation
- ✅ n8n integration ready

Enjoy your AI-powered financial reconciliation system! 🚀

