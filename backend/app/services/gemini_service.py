"""Google Gemini AI extraction service with retry logic, structured output, and specimen fallback."""

import time
import json
import logging
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.schemas import PersonalDetails, TravelEvent, ExtractionResult
from app.prompts import PASSPORT_EXTRACTION_SYSTEM_PROMPT
from app.services.mrz_service import parse_td3_mrz
from app.services.timeline_service import (
    process_timeline,
    build_travel_summary,
    evaluate_passport_status,
)

logger = logging.getLogger("passport_extractor.gemini")


class RawAIExtraction(BaseModel):
    """Raw structured output schema requested from Gemini."""
    personal_details: PersonalDetails
    travel_events: List[TravelEvent] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    overall_confidence: str = Field(default="high")


def get_gemini_client() -> Optional[genai.Client]:
    """Initialize official google-genai client if API key is configured."""
    key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
    if not key or key == "your_gemini_api_key_here":
        return None
    return genai.Client(api_key=key)


def get_mock_specimen_extraction() -> RawAIExtraction:
    """Return realistic specimen extraction for testing when API key is not configured."""
    return RawAIExtraction(
        personal_details=PersonalDetails(
            document_type="Passport",
            issuing_country="Utopia",
            issuing_country_code="UTO",
            passport_number="L898902C3",
            surname="TRAVELER",
            given_names="ALEX MORGAN",
            full_name="Alex Morgan Traveler",
            nationality="Utopian",
            sex="M",
            date_of_birth="1988-06-15",
            place_of_birth="UTOPIA CITY",
            date_of_issue="2020-04-10",
            date_of_expiry="2030-04-09",
            issuing_authority="MINISTRY OF FOREIGN AFFAIRS",
            personal_number="988061599812",
            father_name="ROBERT TRAVELER",
            mother_name="ELENA TRAVELER",
            spouse_name=None,
            address="42 HARBOR WAY, UTOPIA METROPOLIS",
            old_passport_details="K776512A0 (ISSUED 2010)",
            mrz_line_1="P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<",
            mrz_line_2="L898902C36UTO8806150M3004098988061599812<<68"
        ),
        travel_events=[
            TravelEvent(
                id="evt_1",
                event_type="visa",
                country="Schengen / France",
                city_or_port="PARIS",
                date="2022-03-01",
                valid_from="2022-03-01",
                valid_until="2022-09-01",
                visa_type="Short Stay Tourist (Type C)",
                visa_number="FRA99823145",
                number_of_entries="MULT",
                duration_of_stay="90 Days",
                source_page=2,
                confidence="high",
                notes="Valid multi-entry Schengen sticker"
            ),
            TravelEvent(
                id="evt_2",
                event_type="entry_stamp",
                country="France",
                city_or_port="CDG Airport Paris",
                date="2022-04-10",
                source_page=2,
                confidence="high",
                notes="Clear blue rectangular entry stamp"
            ),
            TravelEvent(
                id="evt_3",
                event_type="exit_stamp",
                country="France",
                city_or_port="CDG Airport Paris",
                date="2022-04-24",
                source_page=2,
                confidence="high",
                notes="Green exit stamp indicating departure"
            ),
            TravelEvent(
                id="evt_4",
                event_type="entry_stamp",
                country="United Kingdom",
                city_or_port="London Heathrow (LHR)",
                date="2023-08-12",
                source_page=3,
                confidence="high",
                notes="UK Border Force entry stamp"
            ),
            TravelEvent(
                id="evt_5",
                event_type="exit_stamp",
                country="United Kingdom",
                city_or_port="London Gatwick (LGW)",
                date="2023-08-26",
                source_page=3,
                confidence="high",
                notes="Departure stamp from Gatwick"
            ),
            TravelEvent(
                id="evt_6",
                event_type="entry_stamp",
                country="United Arab Emirates",
                city_or_port="Dubai International (DXB)",
                date="2024-01-05",
                source_page=3,
                confidence="high",
                notes="GDRFA Dubai arrival stamp"
            ),
            TravelEvent(
                id="evt_7",
                event_type="exit_stamp",
                country="United Arab Emirates",
                city_or_port="Dubai International (DXB)",
                date="2024-01-12",
                source_page=3,
                confidence="high",
                notes="Departure stamp"
            )
        ],
        warnings=[
            "DEMO MODE: No GEMINI_API_KEY detected in backend/.env. Returned synthetic specimen extraction for verification."
        ],
        overall_confidence="high"
    )


def call_gemini_with_retry(
    client: genai.Client,
    image_buffers: List[bytes],
    max_retries: int = 3
) -> RawAIExtraction:
    """Call Gemini generate_content with structured schema and exponential backoff on transient errors."""
    contents: List[types.Part] = []

    # Attach all pages as JPEG image parts
    for img_bytes in image_buffers:
        contents.append(
            types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/jpeg"
            )
        )

    # Prompt text instructing synthesis across all pages
    prompt_text = (
        f"{PASSPORT_EXTRACTION_SYSTEM_PROMPT}\n\n"
        f"You are given {len(image_buffers)} page image(s) from a passport or travel document set. "
        "Extract the holder personal details from the biodata page, read both MRZ lines, "
        "and systematically find all visas, entry stamps, exit stamps, and permits across all pages. "
        "Return the output in the requested JSON structure."
    )
    contents.insert(0, types.Part.from_text(text=prompt_text))

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=RawAIExtraction,
    )

    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=config
            )

            raw_text = response.text
            if not raw_text:
                raise ValueError("Empty response received from Gemini API.")

            data = json.loads(raw_text)
            return RawAIExtraction.model_validate(data)

        except (APIError, Exception) as exc:
            last_error = exc
            is_rate_limit = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)
            is_transient = is_rate_limit or "503" in str(exc) or "UNAVAILABLE" in str(exc)

            if is_transient and attempt < max_retries:
                delay = (2 ** attempt) * 1.5
                logger.warning(
                    f"Gemini API transient error (attempt {attempt}/{max_retries}): {exc}. Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                break

    raise HTTPException(
        status_code=502,
        detail=f"Gemini API extraction failed: {str(last_error)}"
    )


def extract_passport_data(image_buffers: List[bytes]) -> ExtractionResult:
    """End-to-end extraction pipeline:

    1. Call Gemini (or fallback mock if API key not set).
    2. Perform algorithmic TD3 MRZ check-digit verification & cross-check with visual fields.
    3. Process travel events: sort chronologically, deduplicate, calculate stay days.
    4. Compute high-level travel summary.
    5. Evaluate passport expiration status.
    6. Collate warnings and return unified ExtractionResult.
    """
    client = get_gemini_client()

    if client is None:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY is not configured. Please add your Google Gemini API key to backend/.env and restart the server to extract passport documents."
        )

    raw = call_gemini_with_retry(client, image_buffers)

    # 1. MRZ algorithmic verification
    mrz_res = parse_td3_mrz(
        raw.personal_details.mrz_line_1,
        raw.personal_details.mrz_line_2,
        visual_details=raw.personal_details
    )

    # 2. Travel timeline sorting, deduplication, and stay calculation
    sorted_events, timeline_warnings = process_timeline(raw.travel_events)

    # 3. Travel summary statistics
    travel_summary = build_travel_summary(sorted_events, personal_details=raw.personal_details)

    # 4. Passport expiration check
    passport_status, days_until_expiry, expiry_warnings = evaluate_passport_status(
        raw.personal_details.date_of_expiry
    )

    # 5. Collate all warnings
    all_warnings = list(raw.warnings)
    all_warnings.extend(timeline_warnings)
    all_warnings.extend(expiry_warnings)
    if mrz_res.discrepancies:
        all_warnings.extend(mrz_res.discrepancies)

    # De-duplicate warnings while preserving order
    unique_warnings = list(dict.fromkeys(all_warnings))

    # Overall confidence adjustment
    confidence = raw.overall_confidence
    if not mrz_res.mrz_valid or len(mrz_res.discrepancies) > 0:
        if confidence == "high":
            confidence = "medium"

    return ExtractionResult(
        personal_details=raw.personal_details,
        travel_events=sorted_events,
        warnings=unique_warnings,
        overall_confidence=confidence,
        mrz_validation=mrz_res,
        passport_status=passport_status,
        days_until_expiry=days_until_expiry,
        travel_summary=travel_summary
    )

