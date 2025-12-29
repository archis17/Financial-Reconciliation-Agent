# Financial Reconciliation Frontend

A beautiful, modern Next.js frontend for the AI Financial Reconciliation Agent.

## Features

- 🎨 **Sleek Design**: Modern UI with glassmorphism effects and smooth animations
- 📊 **Interactive Charts**: Visual representation of reconciliation results
- 🚀 **Smooth Animations**: Powered by Framer Motion
- 📱 **Responsive**: Works on all device sizes
- ⚡ **Fast**: Built with Next.js 15 and React 18

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
# Create .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Build for Production

```bash
npm run build
npm start
```

## Tech Stack

- **Next.js 15**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Framer Motion**: Animations
- **Recharts**: Data visualization
- **Lucide React**: Icons
- **Axios**: HTTP client

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx          # Main page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── ReconciliationResults.tsx
│   ├── SummaryCards.tsx
│   ├── Charts.tsx
│   ├── DiscrepancyList.tsx
│   └── ProgressIndicator.tsx
└── package.json
```
