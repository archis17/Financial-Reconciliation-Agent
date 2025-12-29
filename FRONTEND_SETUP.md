# Frontend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API URL

Create `.env.local` in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Running Both Backend and Frontend

### Terminal 1 - Backend API
```bash
cd /home/archis/Desktop/Financial-Reconcilation
source venv/bin/activate
python api/run.py
# or
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend
```bash
cd /home/archis/Desktop/Financial-Reconcilation/frontend
npm run dev
```

## Features

### 🎨 Design Highlights
- **Glassmorphism**: Modern glass-like UI elements
- **Gradient Backgrounds**: Animated blob backgrounds
- **Smooth Transitions**: Framer Motion animations throughout
- **Responsive Layout**: Works on desktop, tablet, and mobile

### 📊 Components
- **File Upload**: Drag-and-drop file upload with visual feedback
- **Progress Indicator**: Animated progress bar during processing
- **Summary Cards**: Beautiful cards showing key metrics
- **Charts**: Interactive pie and bar charts
- **Discrepancy List**: Detailed view of all discrepancies with AI explanations
- **Ticket View**: Formatted tickets ready for integration

### 🚀 Workflow
1. **Upload**: Drag and drop bank statement and ledger files
2. **Process**: Watch real-time progress with smooth animations
3. **Results**: View comprehensive results with charts and detailed breakdowns
4. **Download**: Export reports in CSV, JSON, or text format

## Customization

### Colors
Edit `tailwind.config.js` to customize the color scheme.

### Animations
Modify Framer Motion props in components to adjust animation timing and effects.

### API Endpoints
Update `NEXT_PUBLIC_API_URL` in `.env.local` to point to your API server.

## Production Build

```bash
npm run build
npm start
```

## Troubleshooting

### CORS Issues
Make sure the backend API has CORS enabled for `http://localhost:3000`

### API Connection
Verify the API is running and accessible at the URL specified in `.env.local`

### Port Conflicts
If port 3000 is in use, Next.js will automatically use the next available port.

