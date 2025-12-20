# ABFI.io Intelligence Suite

> AI-powered market intelligence platform for the Australian bioenergy and sustainable fuels industry.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org)
[![License](https://img.shields.io/badge/License-Proprietary-orange.svg)]()

## Overview

The ABFI Intelligence Suite provides institutional-grade market intelligence for biofuel project developers, lenders, and offtakers through three integrated products:

| Product | Description |
|---------|-------------|
| **Lending Sentiment Index** | ML-powered analysis of lender appetite and risk perception from financial documents |
| **Feedstock Price Index** | IOSCO-compliant price discovery for UCO, tallow, canola, and biomass feedstocks |
| **Policy & Carbon Platform** | Real-time policy tracking, mandate scenarios, and carbon revenue calculator |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ABFI INTELLIGENCE SUITE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │   Lending        │  │   Feedstock      │  │   Policy &       │   │
│  │   Sentiment      │  │   Price Index    │  │   Carbon Revenue │   │
│  │   Index          │  │   & Counterparty │  │   Platform       │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘   │
│           │                     │                     │              │
│           ▼                     ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                 UNIFIED ML INFERENCE LAYER                    │   │
│  │   • DeBERTa-v3 embeddings    • Multi-task prediction heads   │   │
│  │   • Document processing       • Entity extraction             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│           │                     │                     │              │
│           ▼                     ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    DATA INGESTION LAYER                       │   │
│  │   • Web scrapers    • API connectors    • PDF extractors      │   │
│  │   • RSS feeds       • ABFI.io DB        • Document processors │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **ML Framework** | PyTorch + HuggingFace Transformers | Model training & inference |
| **Base Model** | DeBERTa-v3-large (304M params) | Document understanding |
| **API** | FastAPI | Async REST API |
| **Database** | PostgreSQL + TimescaleDB | Time-series & relational data |
| **Vector Store** | pgvector | Document embeddings |
| **Job Scheduler** | Prefect | Batch pipeline orchestration |
| **ML Ops** | MLflow | Experiment tracking & model registry |
| **Inference** | Triton Inference Server | GPU model serving |

## Products

### 1. Lending Sentiment Index

Analyzes financial documents from CEFC, ARENA, RBA, APRA, and major banks to produce:

- **Lending Appetite Index** (-3 to +3 scale)
- **Risk Perception Index** (-3 to +3 scale)
- **Fear Component Scores** (policy reversal, technology risk, offtake uncertainty, etc.)
- **7-day Momentum Indicators**

**Data Sources:** ~500-1000 documents/week from 10+ authoritative sources

### 2. Feedstock Price Index

IOSCO-compliant price discovery for Australian biofuel feedstocks:

| Index Code | Feedstock | Region |
|------------|-----------|--------|
| ABFI-UCO-VIC | Used Cooking Oil | Victoria |
| ABFI-UCO-QLD | Used Cooking Oil | Queensland |
| ABFI-TAL-NAT | Tallow (bleachable) | National |
| ABFI-CAN-NAT | Canola Oil | National |
| ABFI-RES-QLD | Agricultural Residue | Queensland |

**Counterparty Risk Scoring:** AAA to D rating scale with trend indicators

### 3. Policy & Carbon Revenue Platform

- **Policy Tracker:** Federal + 8 state jurisdictions, auto-classified by relevance
- **Mandate Scenario Model:** SAF mandate probability by year (2025-2035)
- **Carbon Revenue Calculator:** ACCU, CORSIA, EU RED III, Scope 3 pathway analysis

## Installation

### Prerequisites

- Python 3.11+
- CUDA 12.1+ (for GPU inference)
- PostgreSQL 15+ with TimescaleDB & pgvector extensions
- Redis 7+

### Setup

```bash
# Clone repository
git clone https://github.com/steeldragon666/abfi-ai.git
cd abfi-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_trf

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### GPU Setup (Training/Inference)

```bash
# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install HuggingFace ecosystem
pip install transformers datasets accelerate peft bitsandbytes

# Verify GPU access
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## API Reference

### Endpoints

```
GET  /api/v1/sentiment/index          # Current lending sentiment index
POST /api/v1/sentiment/analyze        # Analyze document for sentiment

GET  /api/v1/prices/index/{feedstock} # Feedstock price index time series
GET  /api/v1/counterparty/{id}/rating # Counterparty risk rating

GET  /api/v1/policy/tracker           # Policy updates feed
GET  /api/v1/policy/mandate-scenarios # SAF mandate probability scenarios
POST /api/v1/carbon/calculate         # Carbon revenue calculator
```

### Example Usage

```python
from abfi_client import ABFIClient

client = ABFIClient(api_key="your-api-key")

# Get sentiment index
sentiment = client.get_sentiment_index(lookback_days=30)
print(f"Lending Appetite: {sentiment.lending_appetite_index}")

# Get feedstock prices
prices = client.get_price_index(
    feedstock="UCO",
    region="VIC",
    start_date="2024-01-01"
)

# Calculate carbon revenue
revenue = client.calculate_carbon_revenue(
    project_type="saf",
    feedstock="uco",
    annual_volume_litres=10_000_000,
    target_market="domestic"
)
```

## Project Structure

```
abfi-ai/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── sentiment.py
│   │   │   ├── prices.py
│   │   │   ├── policy.py
│   │   │   ├── carbon.py
│   │   │   └── counterparty.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── sentiment.py
│   │   ├── pricing.py
│   │   └── policy.py
│   └── main.py
├── ml/
│   ├── training/
│   │   ├── sentiment_trainer.py
│   │   ├── policy_classifier.py
│   │   └── counterparty_model.py
│   ├── inference/
│   │   └── triton_config/
│   └── data/
│       ├── scrapers/
│       └── processors/
├── workflows/
│   ├── daily_sentiment.py
│   ├── weekly_prices.py
│   └── policy_ingestion.py
├── tests/
├── alembic/
├── docker/
├── requirements.txt
└── README.md
```

## Hardware Requirements

### Production Workstation (Training + Batch Inference)

| Component | Specification |
|-----------|---------------|
| CPU | AMD Threadripper Pro 9765WX (64C/128T) |
| GPU | 2x NVIDIA RTX 6000 Ada (48GB each) |
| RAM | 256GB DDR5 ECC |
| Storage | 2TB NVMe (OS/models) + 8TB NVMe (data) |

### Capacity

| Workload | Requirement | Capacity | Headroom |
|----------|-------------|----------|----------|
| Fine-tune 7B model | 24GB VRAM | 96GB | 4x |
| Fine-tune 13B model | 40GB VRAM | 96GB | 2.4x |
| Daily inference (10K docs) | ~2 hours | 24h available | 12x |

## Deployment

### Cloud Infrastructure

| Service | Provider | Purpose |
|---------|----------|---------|
| Frontend | Vercel | React dashboard |
| API | Railway/Fly.io | FastAPI application |
| Database | Railway PostgreSQL | TimescaleDB + pgvector |
| Cache | Redis (Upstash) | API caching, job queue |
| GPU Inference | Local workstation | Triton Inference Server |

### Estimated Costs

| Component | Monthly Cost (AUD) |
|-----------|-------------------|
| Vercel Pro | $30 |
| Railway (API + DB) | $100-200 |
| Redis | $20-50 |
| Workstation power | $50-100 |
| **Total** | **$200-380** |

## Development

### Running Tests

```bash
pytest tests/ -v --cov=app
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
black .

# Type checking
mypy app/
```

### Training Models

```bash
# Domain adaptation (Stage 1)
python ml/training/sentiment_trainer.py --stage domain_adaptation

# Supervised fine-tuning (Stage 2)
python ml/training/sentiment_trainer.py --stage supervised

# Active learning iteration
python ml/training/sentiment_trainer.py --stage active_learning
```

## License

Proprietary - ABFI Pty Ltd. All rights reserved.

## Contact

- **Technical:** tech@abfi.io
- **Commercial:** hello@abfi.io
- **Website:** https://abfi.io
