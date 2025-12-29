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
- 🔄 Phase 6: LLM Explanation Layer (In Progress)
- ⏳ Phase 7: Reporting & Actions
- ⏳ Phase 8: API & Optional UI
- ⏳ Phase 9: Production Readiness

## License

MIT

