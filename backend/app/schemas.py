from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class PersonalDetails(BaseModel):
    """Personal information extracted from the passport biodata page."""
    document_type: Optional[str] = Field(default=None, description="Document type, e.g., 'Passport' or 'P'")
    issuing_country: Optional[str] = Field(default=None, description="Country of issuance full name, e.g., 'United States'")
    issuing_country_code: Optional[str] = Field(default=None, description="3-letter ISO code, e.g., 'USA'")
    passport_number: Optional[str] = Field(default=None, description="Passport or document number")
    surname: Optional[str] = Field(default=None, description="Holder surname/primary identifier")
    given_names: Optional[str] = Field(default=None, description="Holder given names/secondary identifiers")
    full_name: Optional[str] = Field(default=None, description="Full reconstructed name")
    nationality: Optional[str] = Field(default=None, description="Holder nationality or citizenship")
    sex: Optional[str] = Field(default=None, description="Sex / Gender, typically 'M', 'F', or 'X'")
    date_of_birth: Optional[str] = Field(default=None, description="ISO YYYY-MM-DD or partial readable format")
    place_of_birth: Optional[str] = Field(default=None, description="Place or city of birth")
    date_of_issue: Optional[str] = Field(default=None, description="ISO YYYY-MM-DD or partial readable format")
    date_of_expiry: Optional[str] = Field(default=None, description="ISO YYYY-MM-DD or partial readable format")
    issuing_authority: Optional[str] = Field(default=None, description="Issuing authority / office")
    personal_number: Optional[str] = Field(default=None, description="National ID or personal number if present")
    father_name: Optional[str] = Field(default=None, description="Father's name if present (e.g. Indian passports)")
    mother_name: Optional[str] = Field(default=None, description="Mother's name if present")
    spouse_name: Optional[str] = Field(default=None, description="Spouse's name if present")
    address: Optional[str] = Field(default=None, description="Address if present on last/observation page")
    old_passport_details: Optional[str] = Field(default=None, description="Previous passport number/details if recorded")
    mrz_line_1: Optional[str] = Field(default=None, description="First line of Machine Readable Zone (44 characters)")
    mrz_line_2: Optional[str] = Field(default=None, description="Second line of Machine Readable Zone (44 characters)")


class TravelEvent(BaseModel):
    """A visa, entry stamp, exit stamp, or residence permit entry."""
    id: Optional[str] = Field(default=None, description="Unique identifier for frontend rendering")
    event_type: Literal["visa", "entry_stamp", "exit_stamp", "residence_permit", "other"] = Field(
        default="other", description="Type of travel document / stamp"
    )
    country: Optional[str] = Field(default=None, description="Country associated with the event")
    city_or_port: Optional[str] = Field(default=None, description="Border crossing, airport or city name")
    date: Optional[str] = Field(default=None, description="ISO YYYY-MM-DD or partial date for sorting")
    valid_from: Optional[str] = Field(default=None, description="Visa or permit validity start date")
    valid_until: Optional[str] = Field(default=None, description="Visa or permit expiration date")
    visa_type: Optional[str] = Field(default=None, description="Visa category or type, e.g., 'Tourist', 'B1/B2', 'Schengen C'")
    visa_number: Optional[str] = Field(default=None, description="Visa sticker number or identifier")
    number_of_entries: Optional[str] = Field(default=None, description="Number of entries allowed: '1', '2', 'MULT'")
    duration_of_stay: Optional[str] = Field(default=None, description="Duration permitted, e.g., '90 days'")
    source_page: Optional[int] = Field(default=None, description="Page index (1-based) where stamp/visa was found")
    confidence: Literal["high", "medium", "low"] = Field(default="high", description="OCR confidence level")
    notes: Optional[str] = Field(default=None, description="Observation notes, e.g., 'Ink smudge on date'")
    days_stayed: Optional[int] = Field(default=None, description="Calculated duration between entry and subsequent exit")


class MRZValidationResult(BaseModel):
    """Result of algorithmic MRZ check digit validation."""
    mrz_found: bool = Field(default=False)
    mrz_valid: bool = Field(default=False)
    raw_lines: List[str] = Field(default_factory=list)
    document_number_check: Optional[bool] = None
    dob_check: Optional[bool] = None
    expiry_check: Optional[bool] = None
    composite_check: Optional[bool] = None
    parsed_details: Dict[str, Any] = Field(default_factory=dict)
    discrepancies: List[str] = Field(default_factory=list)
    repaired_fields: Dict[str, str] = Field(default_factory=dict)


class TravelSummary(BaseModel):
    """Derived statistics across all travel events."""
    total_countries: int = 0
    countries_visited: List[str] = Field(default_factory=list)
    total_events: int = 0
    total_visas: int = 0
    total_entry_stamps: int = 0
    total_exit_stamps: int = 0
    visas_summary: List[Dict[str, Any]] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Complete extraction payload returned to client."""
    personal_details: PersonalDetails
    travel_events: List[TravelEvent] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    overall_confidence: Literal["high", "medium", "low"] = "high"
    mrz_validation: Optional[MRZValidationResult] = None
    passport_status: Literal["valid", "expiring_soon", "expired", "unknown"] = "unknown"
    days_until_expiry: Optional[int] = None
    travel_summary: Optional[TravelSummary] = None
    is_cached: bool = Field(default=False, description="Whether this response was served from in-memory cache")


class HealthResponse(BaseModel):
    """Server health status response."""
    status: str
    gemini_model: str
    gemini_configured: bool
    version: str = "1.0.0"
    cache_stats: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    error: str
    detail: Optional[str] = None

