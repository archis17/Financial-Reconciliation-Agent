# AI Financial Reconciliation Agent

Automatically reconciles bank statements with internal ledgers using fuzzy matching, embeddings, and LLM-based explanations.

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** If you encounter disk space issues, PyTorch with CUDA support is very large. You can install CPU-only version:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 3. Configure OpenAI API Key

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here
```

## Usage

### Generate Test Data

```bash
python generate_test_data.py --num-transactions 100
```

### Test Ingestion

```bash
python test_ingestion.py
```

### Test Matching

```bash
python test_matching_with_data.py
```

### Test Discrepancy Detection

```bash
python test_discrepancy_simple.py
```

## Project Structure

```
Financial-Reconcilation/
├── ingestion/          # Data ingestion and normalization
├── matching/          # Matching engine (rule-based + embeddings)
├── discrepancy/       # Discrepancy detection and classification
├── synthetic_data/    # Test data generator
├── test_data/        # Generated test data
└── requirements.txt  # Python dependencies
```

## Phases Completed

- ✅ Phase 1: System Architecture & Data Contracts
- ✅ Phase 2: Synthetic Test Data Generator
- ✅ Phase 3: Data Ingestion & Normalization
- ✅ Phase 4: Matching Engine (Non-LLM)
- ✅ Phase 5: Discrepancy Detection
- ✅ Phase 6: LLM Explanation Layer
- ✅ Phase 7: Reporting & Actions
- ✅ Phase 8: API & Frontend UI
- ✅ Phase 9: Production Readiness (Docker, Error Handling, Performance)

## Production Deployment

For production deployment, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).

### Quick Start with Docker

```bash
# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Build and start services
docker-compose up -d --build

# Check health
curl http://localhost:8000/health
```

### Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
  PYTHONPATH=. ./venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
- **API Docs**: http://localhost:8000/api/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
  - **Username**: `admin`
  - **Password**: `admin` (default) or set via `GRAFANA_ADMIN_PASSWORD` env var
  - ⚠️ **Change password in production!**

### Production Features

- **Docker Support**: Full Docker and Docker Compose configuration
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Rate Limiting**: Built-in rate limiting middleware
- **Health Checks**: Health check endpoints with dependency verification
- **Caching**: In-memory caching (Redis support ready)
- **Security**: CORS configuration, file upload limits, input validation
- **Logging**: Structured logging with configurable log levels
- **Performance**: Optimized for production workloads

## License

MIT
