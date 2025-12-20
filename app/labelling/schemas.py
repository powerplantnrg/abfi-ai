"""
Pydantic schemas for ABFI labelling data.

Aligned with Label Studio export format and HuggingFace datasets.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    """Primary lending sentiment classification."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class FearComponent(str, Enum):
    """Fear/risk component multi-labels."""
    REGULATORY_RISK = "REGULATORY_RISK"
    TECHNOLOGY_RISK = "TECHNOLOGY_RISK"
    FEEDSTOCK_RISK = "FEEDSTOCK_RISK"
    COUNTERPARTY_RISK = "COUNTERPARTY_RISK"
    MARKET_RISK = "MARKET_RISK"
    ESG_CONCERNS = "ESG_CONCERNS"


class TemporalSignal(str, Enum):
    """Temporal relevance of sentiment signal."""
    SHORT_TERM = "SHORT_TERM"    # 0-12 months
    MEDIUM_TERM = "MEDIUM_TERM"  # 1-3 years
    LONG_TERM = "LONG_TERM"      # 3+ years


class EntityType(str, Enum):
    """Entity annotation types."""
    LENDER = "LENDER"
    PROJECT = "PROJECT"
    POLICY = "POLICY"
    COMPANY = "COMPANY"


class EntityAnnotation(BaseModel):
    """Span-based entity annotation."""
    start: int = Field(..., description="Character start position")
    end: int = Field(..., description="Character end position")
    label: EntityType
    text: str = Field(..., description="Annotated text span")


class SentimentAnnotation(BaseModel):
    """
    Complete sentiment annotation for a document.

    Matches Label Studio export format.
    """
    # Document identification
    document_id: str
    text: str

    # Primary classification
    sentiment: Sentiment
    intensity: int = Field(..., ge=1, le=5, description="Signal intensity 1-5")

    # Multi-label fear components
    fear_components: list[FearComponent] = []

    # Temporal signal
    temporal: TemporalSignal

    # Entity annotations
    entities: list[EntityAnnotation] = []

    # Metadata
    source: Optional[str] = None
    published_date: Optional[datetime] = None
    url: Optional[str] = None

    # Annotation metadata
    annotator_id: Optional[str] = None
    annotated_at: Optional[datetime] = None
    annotation_time_seconds: Optional[int] = None


class LabelStudioTask(BaseModel):
    """Label Studio task format for import."""
    id: Optional[int] = None
    data: dict = Field(..., description="Task data including text")
    annotations: list[dict] = []
    predictions: list[dict] = []
    meta: dict = {}


class LabelStudioAnnotation(BaseModel):
    """Label Studio annotation result format."""
    id: Optional[int] = None
    task: int
    completed_by: Optional[int] = None
    result: list[dict]
    lead_time: Optional[float] = None
    created_at: Optional[datetime] = None


class TrainingExample(BaseModel):
    """
    Training example for HuggingFace datasets.

    Flattened format suitable for model training.
    """
    text: str
    sentiment: str
    intensity: int
    fear_components: list[str]
    temporal: str
    entities: list[dict]
    source: Optional[str] = None
    date: Optional[str] = None


class AgreementMetrics(BaseModel):
    """Inter-annotator agreement metrics."""
    project_id: str
    metric_type: str  # kappa, krippendorff_alpha, fleiss_kappa
    label_name: str   # sentiment, intensity, fear_components_*
    score: float
    sample_size: int
    calculated_at: datetime = Field(default_factory=datetime.now)


class AnnotatorPerformance(BaseModel):
    """Annotator quality metrics."""
    annotator_id: str
    total_annotations: int
    honeypot_accuracy: float
    average_time_seconds: float
    agreement_with_consensus: float
    last_active: datetime


def convert_label_studio_to_training(
    annotation: LabelStudioAnnotation,
    task_data: dict
) -> TrainingExample:
    """
    Convert Label Studio annotation to training format.

    Args:
        annotation: Label Studio annotation result
        task_data: Original task data containing text

    Returns:
        TrainingExample suitable for model training
    """
    result = annotation.result
    text = task_data.get("text", "")

    # Extract values from result
    sentiment = None
    intensity = None
    fear_components = []
    temporal = None
    entities = []

    for item in result:
        item_type = item.get("type")
        value = item.get("value", {})

        if item_type == "choices":
            from_name = item.get("from_name")
            choices = value.get("choices", [])

            if from_name == "sentiment" and choices:
                sentiment = choices[0]
            elif from_name == "fear_components":
                fear_components = choices
            elif from_name == "temporal" and choices:
                temporal = choices[0]

        elif item_type == "rating":
            intensity = value.get("rating")

        elif item_type == "labels":
            labels = value.get("labels", [])
            if labels:
                entities.append({
                    "start": value.get("start"),
                    "end": value.get("end"),
                    "label": labels[0],
                    "text": value.get("text"),
                })

    return TrainingExample(
        text=text,
        sentiment=sentiment or "NEUTRAL",
        intensity=intensity or 3,
        fear_components=fear_components,
        temporal=temporal or "MEDIUM_TERM",
        entities=entities,
        source=task_data.get("source"),
        date=task_data.get("published_date"),
    )


def export_to_huggingface_jsonl(
    annotations: list[TrainingExample],
    output_path: str
) -> None:
    """
    Export training examples to HuggingFace-compatible JSONL.

    Args:
        annotations: List of training examples
        output_path: Output file path
    """
    import json

    with open(output_path, 'w') as f:
        for example in annotations:
            f.write(example.model_dump_json() + '\n')
