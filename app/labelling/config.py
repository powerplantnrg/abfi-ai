"""
Label Studio Configuration for ABFI Lending Sentiment Labelling.

Multi-dimensional label schema capturing:
- Primary sentiment (Bullish/Bearish/Neutral)
- Signal intensity (1-5 Likert scale)
- Fear components (multi-label)
- Temporal signal
- Entity annotations (span highlighting)
"""

from typing import Optional


# Label Studio XML Configuration
LENDING_SENTIMENT_CONFIG = """
<View>
    <Header value="Document Context"/>
    <Text name="text" value="$text"/>

    <Header value="1. Overall Lending Sentiment"/>
    <Choices name="sentiment" toName="text" required="true">
        <Choice value="BULLISH" hotkey="b"/>
        <Choice value="BEARISH" hotkey="r"/>
        <Choice value="NEUTRAL" hotkey="n"/>
    </Choices>

    <Header value="2. Signal Intensity (1=Very Weak, 5=Very Strong)"/>
    <Rating name="intensity" toName="text" maxRating="5" required="true"/>

    <Header value="3. Fear Components (select all that apply)"/>
    <Choices name="fear_components" toName="text" choice="multiple">
        <Choice value="REGULATORY_RISK" hotkey="1"/>
        <Choice value="TECHNOLOGY_RISK" hotkey="2"/>
        <Choice value="FEEDSTOCK_RISK" hotkey="3"/>
        <Choice value="COUNTERPARTY_RISK" hotkey="4"/>
        <Choice value="MARKET_RISK" hotkey="5"/>
        <Choice value="ESG_CONCERNS" hotkey="6"/>
    </Choices>

    <Header value="4. Temporal Signal"/>
    <Choices name="temporal" toName="text" required="true">
        <Choice value="SHORT_TERM" hotkey="s"/>
        <Choice value="MEDIUM_TERM" hotkey="m"/>
        <Choice value="LONG_TERM" hotkey="l"/>
    </Choices>

    <Header value="5. Entity Annotation (highlight relevant spans)"/>
    <Labels name="entities" toName="text">
        <Label value="LENDER" background="#2196F3"/>
        <Label value="PROJECT" background="#4CAF50"/>
        <Label value="POLICY" background="#FF9800"/>
        <Label value="COMPANY" background="#9C27B0"/>
    </Labels>
</View>
"""


class LabelStudioConfig:
    """Label Studio project configuration."""

    PROJECT_NAME = "ABFI Lending Sentiment"
    PROJECT_DESCRIPTION = """
    Multi-dimensional lending sentiment labelling for Australian bioenergy market intelligence.

    Label dimensions:
    1. Overall Sentiment: BULLISH, BEARISH, or NEUTRAL
    2. Signal Intensity: 1-5 scale (Very Weak to Very Strong)
    3. Fear Components: Multi-label risk classification
    4. Temporal Signal: SHORT_TERM, MEDIUM_TERM, or LONG_TERM
    5. Entity Annotations: LENDER, PROJECT, POLICY, COMPANY spans
    """

    # Honeypot configuration (8-10% of tasks)
    HONEYPOT_RATIO = 0.09
    HONEYPOT_ACCURACY_THRESHOLD = 0.80

    # Inter-annotator agreement targets
    IAA_KRIPPENDORFF_ALPHA_TARGET = 0.75
    IAA_MINIMUM_ACCEPTABLE = 0.67

    # Consensus voting
    CONSENSUS_ANNOTATORS = 3
    CONSENSUS_MAJORITY_THRESHOLD = 2

    # Active learning threshold
    UNCERTAINTY_THRESHOLD = 0.7
    ACTIVE_LEARNING_BATCH_SIZE = 50
    SEED_DATASET_SIZE = 500

    @classmethod
    def get_label_config(cls) -> str:
        """Return Label Studio XML configuration."""
        return LENDING_SENTIMENT_CONFIG

    @classmethod
    def get_project_params(cls) -> dict:
        """Return project creation parameters."""
        return {
            "title": cls.PROJECT_NAME,
            "description": cls.PROJECT_DESCRIPTION,
            "label_config": cls.get_label_config(),
            "expert_instruction": cls.get_annotator_guidelines(),
        }

    @classmethod
    def get_annotator_guidelines(cls) -> str:
        """Return annotator guidelines."""
        return """
## ABFI Lending Sentiment Annotation Guidelines

### Overall Sentiment (Required)
- **BULLISH**: Signals increased lending appetite, favorable terms, market expansion
  - Examples: New project financing, expanded credit facilities, positive policy changes
- **BEARISH**: Signals reduced lending appetite, tightened terms, market contraction
  - Examples: Loan defaults, facility closures, regulatory setbacks
- **NEUTRAL**: Factual reporting without clear directional signal
  - Examples: Project updates, routine announcements, industry statistics

### Signal Intensity (Required)
Rate the strength of the sentiment signal:
1. Very weak signal - minor implication
2. Weak signal - some implication but ambiguous
3. Moderate signal - clear but not definitive
4. Strong signal - clear and significant
5. Very strong signal - major market-moving event

### Fear Components (Multi-select)
Select ALL risk factors mentioned:
- **REGULATORY_RISK**: Policy uncertainty, compliance concerns, permit issues
- **TECHNOLOGY_RISK**: Unproven technology, performance concerns, scaling issues
- **FEEDSTOCK_RISK**: Supply chain issues, price volatility, availability concerns
- **COUNTERPARTY_RISK**: Borrower creditworthiness, offtaker concerns
- **MARKET_RISK**: Demand uncertainty, price offtake risk, competition
- **ESG_CONCERNS**: Greenwashing allegations, sustainability questions

### Temporal Signal (Required)
- **SHORT_TERM**: Relevant for 0-12 months
- **MEDIUM_TERM**: Relevant for 1-3 years
- **LONG_TERM**: Relevant for 3+ years

### Entity Annotation (Highlight spans)
Highlight and label key entities:
- **LENDER**: Financial institutions (CEFC, NAB, CBA, etc.)
- **PROJECT**: Specific bioenergy projects
- **POLICY**: Legislation, mandates, incentives
- **COMPANY**: Project developers, offtakers, suppliers
"""


# Fear component definitions for model training
FEAR_COMPONENTS = {
    "REGULATORY_RISK": {
        "description": "Policy uncertainty, compliance concerns, permit issues",
        "keywords": [
            "regulation", "policy", "legislation", "compliance",
            "permit", "approval", "government", "mandate", "law",
            "consultation", "review", "uncertainty"
        ],
    },
    "TECHNOLOGY_RISK": {
        "description": "Unproven technology, performance concerns, scaling issues",
        "keywords": [
            "technology", "technical", "performance", "efficiency",
            "scaling", "prototype", "pilot", "demonstration",
            "reliability", "maintenance", "failure", "risk"
        ],
    },
    "FEEDSTOCK_RISK": {
        "description": "Supply chain issues, price volatility, availability",
        "keywords": [
            "feedstock", "supply", "availability", "price",
            "volatility", "shortage", "procurement", "logistics",
            "storage", "quality", "contamination", "seasonal"
        ],
    },
    "COUNTERPARTY_RISK": {
        "description": "Borrower creditworthiness, offtaker concerns",
        "keywords": [
            "creditworthy", "default", "bankruptcy", "insolvency",
            "counterparty", "offtaker", "customer", "contract",
            "payment", "credit rating", "financial health"
        ],
    },
    "MARKET_RISK": {
        "description": "Demand uncertainty, price offtake risk, competition",
        "keywords": [
            "demand", "market", "price", "competition",
            "oversupply", "commodity", "export", "import",
            "trading", "forecast", "outlook", "uncertainty"
        ],
    },
    "ESG_CONCERNS": {
        "description": "Greenwashing allegations, sustainability questions",
        "keywords": [
            "greenwashing", "sustainability", "ESG", "environmental",
            "carbon", "emissions", "certification", "standards",
            "controversy", "criticism", "social", "governance"
        ],
    },
}


# Entity types for NER
ENTITY_TYPES = {
    "LENDER": {
        "description": "Financial institutions providing or considering project finance",
        "examples": [
            "CEFC", "Clean Energy Finance Corporation",
            "NAB", "National Australia Bank",
            "CBA", "Commonwealth Bank",
            "ANZ", "Westpac", "Macquarie",
            "ARENA", "EIB", "ADB",
        ],
    },
    "PROJECT": {
        "description": "Specific bioenergy or renewable energy projects",
        "examples": [
            "Opal Bio Energy", "Barcaldine Biomass",
            "Condong Cogeneration", "Invicta Mill",
        ],
    },
    "POLICY": {
        "description": "Legislation, mandates, incentives, regulatory frameworks",
        "examples": [
            "Renewable Fuel Standard", "LCFS", "SAF mandate",
            "Safeguard Mechanism", "NGER", "ERF",
            "B20 mandate", "Renewable Energy Target",
        ],
    },
    "COMPANY": {
        "description": "Project developers, offtakers, suppliers",
        "examples": [
            "Qantas", "BP", "Shell", "Cargill",
            "Wilmar", "Bioenergy Australia",
        ],
    },
}
