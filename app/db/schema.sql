-- ABFI Intelligence Suite Database Schema
-- PostgreSQL with JSONB for flexible schema evolution

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Data Sources
-- ============================================================================

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    scraper_type VARCHAR(50) NOT NULL,
    scraper_config JSONB DEFAULT '{}',
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit_seconds FLOAT DEFAULT 1.0,
    last_scraped TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sources_active ON sources(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_sources_priority ON sources(priority DESC);

-- Seed data sources based on priority matrix
INSERT INTO sources (name, base_url, scraper_type, priority) VALUES
    ('AEMO NEMWEB', 'https://nemweb.com.au', 'aemo', 1),
    ('Clean Energy Regulator', 'https://www.cleanenergyregulator.gov.au', 'cer', 1),
    ('RenewEconomy', 'https://reneweconomy.com.au', 'reneweconomy', 1),
    ('Data.gov.au', 'https://data.gov.au', 'ckan', 2),
    ('ABS Data API', 'https://data.api.abs.gov.au', 'abs', 2),
    ('OpenAustralia', 'https://openaustralia.org.au', 'openaustralia', 3),
    ('ARENA', 'https://arena.gov.au', 'arena', 3),
    ('CEFC', 'https://www.cefc.com.au', 'cefc', 3);


-- ============================================================================
-- Raw Documents
-- ============================================================================

CREATE TABLE raw_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id INTEGER REFERENCES sources(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    raw_content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    http_status INTEGER DEFAULT 200,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(url, content_hash)
);

CREATE INDEX idx_raw_documents_source ON raw_documents(source_id);
CREATE INDEX idx_raw_documents_scraped ON raw_documents(scraped_at DESC);
CREATE INDEX idx_raw_documents_url ON raw_documents USING hash(url);


-- ============================================================================
-- Processed Articles
-- ============================================================================

CREATE TABLE processed_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_document_id UUID REFERENCES raw_documents(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    published_date TIMESTAMP WITH TIME ZONE,
    author VARCHAR(255),
    content_text TEXT NOT NULL,
    summary TEXT,

    -- NLP analysis results (JSONB for flexibility)
    entities JSONB DEFAULT '{}',
    sentiment_scores JSONB DEFAULT '{}',
    keywords JSONB DEFAULT '[]',
    topics JSONB DEFAULT '[]',

    -- Classification
    is_bioenergy_relevant BOOLEAN DEFAULT TRUE,
    relevance_score FLOAT DEFAULT 0.0,

    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_processed_articles_document ON processed_articles(raw_document_id);
CREATE INDEX idx_processed_articles_published ON processed_articles(published_date DESC);
CREATE INDEX idx_processed_articles_relevant ON processed_articles(is_bioenergy_relevant) WHERE is_bioenergy_relevant = TRUE;
CREATE INDEX idx_processed_articles_entities ON processed_articles USING gin(entities);
CREATE INDEX idx_processed_articles_keywords ON processed_articles USING gin(keywords);


-- ============================================================================
-- Labelling Infrastructure
-- ============================================================================

CREATE TABLE labelling_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    label_config JSONB NOT NULL,
    expert_instruction TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE TABLE labelling_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES labelling_projects(id) ON DELETE CASCADE,
    document_id UUID REFERENCES processed_articles(id) ON DELETE SET NULL,
    data JSONB NOT NULL, -- {"text": "...", "source": "...", "metadata": {...}}
    priority_score FLOAT DEFAULT 0, -- Uncertainty score for active learning
    is_honeypot BOOLEAN DEFAULT FALSE,
    honeypot_labels JSONB, -- Gold standard labels for honeypots
    status VARCHAR(50) DEFAULT 'pending', -- pending, assigned, completed, adjudication
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_labelling_tasks_project ON labelling_tasks(project_id);
CREATE INDEX idx_labelling_tasks_status ON labelling_tasks(status);
CREATE INDEX idx_labelling_tasks_priority ON labelling_tasks(priority_score DESC) WHERE status = 'pending';


CREATE TABLE annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES labelling_tasks(id) ON DELETE CASCADE,
    annotator_id VARCHAR(100) NOT NULL,
    result JSONB NOT NULL,
    /*
    Example result:
    {
        "sentiment": "BULLISH",
        "intensity": 4,
        "fear_components": ["REGULATORY_RISK", "FEEDSTOCK_RISK"],
        "temporal": "MEDIUM_TERM",
        "entities": [
            {"start": 45, "end": 49, "label": "LENDER", "text": "CEFC"},
            {"start": 120, "end": 145, "label": "PROJECT", "text": "Opal Bio Energy"}
        ]
    }
    */
    lead_time_seconds INTEGER,
    honeypot_correct BOOLEAN, -- NULL if not honeypot
    is_consensus BOOLEAN DEFAULT FALSE, -- Final consensus label
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_annotations_task ON annotations(task_id);
CREATE INDEX idx_annotations_annotator ON annotations(annotator_id);
CREATE INDEX idx_annotations_result ON annotations USING gin(result);


CREATE TABLE agreement_metrics (
    id SERIAL PRIMARY KEY,
    project_id UUID REFERENCES labelling_projects(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL, -- kappa, krippendorff_alpha, fleiss_kappa
    label_name VARCHAR(100) NOT NULL, -- sentiment, intensity, fear_components_*
    score FLOAT NOT NULL,
    sample_size INTEGER NOT NULL,
    annotator_ids JSONB DEFAULT '[]',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agreement_metrics_project ON agreement_metrics(project_id);


-- ============================================================================
-- Feedstock Prices
-- ============================================================================

CREATE TABLE feedstock_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commodity VARCHAR(50) NOT NULL, -- UCO, tallow, canola, palm_oil
    region VARCHAR(50) NOT NULL, -- AUS, SEA, EU, NA
    price FLOAT NOT NULL,
    currency VARCHAR(10) DEFAULT 'AUD',
    unit VARCHAR(20) DEFAULT 'MT',

    -- OHLC for candlestick charts
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    close_price FLOAT,
    volume INTEGER,

    source VARCHAR(100) NOT NULL, -- platts, argus, internal
    price_date DATE NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(commodity, region, source, price_date)
);

CREATE INDEX idx_feedstock_prices_commodity ON feedstock_prices(commodity);
CREATE INDEX idx_feedstock_prices_date ON feedstock_prices(price_date DESC);
CREATE INDEX idx_feedstock_prices_lookup ON feedstock_prices(commodity, region, price_date DESC);


CREATE TABLE forward_curves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commodity VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    spot_price FLOAT NOT NULL,
    forward_prices JSONB NOT NULL, -- {"M3": 1250, "M6": 1280, ...}
    curve_shape VARCHAR(20) NOT NULL, -- contango, backwardation, flat
    as_of_date DATE NOT NULL,
    source VARCHAR(100) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_forward_curves_lookup ON forward_curves(commodity, region, as_of_date DESC);


-- ============================================================================
-- Counterparty Risk
-- ============================================================================

CREATE TABLE counterparty_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    counterparty_name VARCHAR(255) NOT NULL,
    counterparty_type VARCHAR(50) NOT NULL, -- supplier, offtaker, developer

    -- Risk ratings
    overall_risk VARCHAR(20) NOT NULL, -- Low, Medium, High
    risk_score FLOAT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),

    -- Component scores
    financial_health FLOAT CHECK (financial_health >= 0 AND financial_health <= 100),
    operational_reliability FLOAT CHECK (operational_reliability >= 0 AND operational_reliability <= 100),
    contract_compliance FLOAT CHECK (contract_compliance >= 0 AND contract_compliance <= 100),
    esg_score FLOAT CHECK (esg_score >= 0 AND esg_score <= 100),

    -- Track record
    volume_mt FLOAT,
    reliability_pct FLOAT,
    price_tier VARCHAR(50),

    -- Metadata
    assessment_date DATE NOT NULL,
    assessor VARCHAR(100),
    notes TEXT,
    supporting_docs JSONB DEFAULT '[]',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_counterparty_ratings_name ON counterparty_ratings(counterparty_name);
CREATE INDEX idx_counterparty_ratings_risk ON counterparty_ratings(overall_risk);


-- ============================================================================
-- Policy Tracker
-- ============================================================================

CREATE TABLE policy_tracker (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    jurisdiction VARCHAR(50) NOT NULL, -- Federal, QLD, NSW, VIC, SA, WA
    policy_type VARCHAR(50) NOT NULL, -- mandate, incentive, regulation, consultation

    -- Status tracking
    status VARCHAR(50) NOT NULL, -- proposed, review, enacted, expired
    current_stage VARCHAR(100),

    -- Timeline
    introduced_date DATE,
    consultation_start DATE,
    consultation_end DATE,
    expected_decision DATE,
    enacted_date DATE,
    effective_date DATE,
    expiry_date DATE,

    -- Content
    summary TEXT NOT NULL,
    full_text_url TEXT,
    key_provisions JSONB DEFAULT '[]',
    affected_sectors JSONB DEFAULT '[]',

    -- Impact assessment
    impact_score FLOAT,
    market_impact VARCHAR(20), -- bullish, bearish, neutral

    -- Metadata
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_policy_tracker_jurisdiction ON policy_tracker(jurisdiction);
CREATE INDEX idx_policy_tracker_status ON policy_tracker(status);
CREATE INDEX idx_policy_tracker_type ON policy_tracker(policy_type);
CREATE INDEX idx_policy_tracker_timeline ON policy_tracker(expected_decision) WHERE status IN ('proposed', 'review');


-- ============================================================================
-- Carbon Revenue Calculator
-- ============================================================================

CREATE TABLE carbon_revenue_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(100) NOT NULL, -- bioenergy_plant, waste_to_energy, biogas

    -- Inputs
    annual_output_tonnes FLOAT NOT NULL,
    emission_factor FLOAT NOT NULL,
    baseline_year INTEGER NOT NULL,
    carbon_price FLOAT NOT NULL,

    -- Calculated revenues
    accu_credits INTEGER NOT NULL,
    accu_revenue FLOAT NOT NULL,
    safeguard_benefit FLOAT NOT NULL,
    total_annual_revenue FLOAT NOT NULL,

    -- Sensitivity
    sensitivity_low FLOAT,
    sensitivity_high FLOAT,

    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- ============================================================================
-- Lending Sentiment Index
-- ============================================================================

CREATE TABLE lending_sentiment_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    index_date DATE NOT NULL,

    -- Overall index
    overall_index FLOAT NOT NULL, -- -100 to +100
    bullish_count INTEGER NOT NULL,
    bearish_count INTEGER NOT NULL,
    neutral_count INTEGER NOT NULL,
    documents_analyzed INTEGER NOT NULL,

    -- Fear component breakdown
    fear_breakdown JSONB NOT NULL, -- {"REGULATORY_RISK": 0.34, ...}

    -- By lender
    lender_scores JSONB DEFAULT '{}', -- {"CEFC": +68, "NAB": +34, ...}

    -- Change metrics
    daily_change FLOAT,
    weekly_change FLOAT,
    monthly_change FLOAT,

    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(index_date)
);

CREATE INDEX idx_lending_sentiment_date ON lending_sentiment_index(index_date DESC);


-- ============================================================================
-- Views for Dashboard Queries
-- ============================================================================

-- Latest sentiment index
CREATE VIEW v_latest_sentiment AS
SELECT *
FROM lending_sentiment_index
ORDER BY index_date DESC
LIMIT 1;


-- Latest prices by commodity
CREATE VIEW v_latest_prices AS
SELECT DISTINCT ON (commodity, region)
    commodity,
    region,
    price,
    price_date,
    source
FROM feedstock_prices
ORDER BY commodity, region, price_date DESC;


-- Active policies by jurisdiction
CREATE VIEW v_active_policies AS
SELECT *
FROM policy_tracker
WHERE status IN ('proposed', 'review', 'enacted')
  AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
ORDER BY jurisdiction, status, expected_decision;


-- Annotator performance
CREATE VIEW v_annotator_performance AS
SELECT
    annotator_id,
    COUNT(*) as total_annotations,
    AVG(lead_time_seconds) as avg_time_seconds,
    SUM(CASE WHEN honeypot_correct = TRUE THEN 1 ELSE 0 END)::FLOAT /
        NULLIF(SUM(CASE WHEN honeypot_correct IS NOT NULL THEN 1 ELSE 0 END), 0) as honeypot_accuracy,
    MAX(completed_at) as last_active
FROM annotations
GROUP BY annotator_id;
