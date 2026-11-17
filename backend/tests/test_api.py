"""Integration unit tests for FastAPI endpoints with mocked Gemini service."""

import io
import pytest
from PIL import Image
from fastapi import UploadFile, HTTPException

from app.main import app, health_check, extract_passport
from app.services.gemini_service import RawAIExtraction
from app.schemas import PersonalDetails, TravelEvent


def create_test_image_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(120, 180, 220))
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_health_check_endpoint():
    """Verify GET /api/health returns status ok."""
    res = health_check()
    assert res.status == "ok"
    assert res.gemini_model is not None
    assert isinstance(res.gemini_configured, bool)


def test_extract_endpoint_success(monkeypatch):
    """Verify POST /api/extract with a mocked Gemini client."""
    def mock_call_gemini(*args, **kwargs):
        return RawAIExtraction(
            personal_details=PersonalDetails(
                passport_number="L898902C3",
                surname="TRAVELER",
                given_names="ALEX MORGAN",
                date_of_birth="1988-06-15",
                date_of_expiry="2030-04-09",
                issuing_country_code="UTO",
                mrz_line_1="P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<",
                mrz_line_2="L898902C36UTO8806150M3004098988061599812<<68"
            ),
            travel_events=[
                TravelEvent(event_type="entry_stamp", country="France", date="2022-04-10", city_or_port="CDG"),
                TravelEvent(event_type="exit_stamp", country="France", date="2022-04-24", city_or_port="CDG")
            ],
            warnings=[],
            overall_confidence="high"
        )

    monkeypatch.setattr("app.services.gemini_service.call_gemini_with_retry", mock_call_gemini)
    monkeypatch.setattr("app.services.gemini_service.get_gemini_client", lambda: object())

    img_bytes = create_test_image_bytes()
    upload1 = UploadFile(
        filename="passport_page1.jpg",
        file=io.BytesIO(img_bytes),
        headers={"content-type": "image/jpeg"}
    )
    upload2 = UploadFile(
        filename="passport_page2.jpg",
        file=io.BytesIO(img_bytes),
        headers={"content-type": "image/jpeg"}
    )

    data = extract_passport([upload1, upload2])

    assert data.personal_details.passport_number == "L898902C3"
    assert data.personal_details.surname == "TRAVELER"
    assert data.mrz_validation.mrz_valid is True
    assert len(data.travel_events) == 2
    # France exit stamp should have days_stayed = 14
    assert data.travel_events[1].days_stayed == 14
    assert data.passport_status == "valid"
    assert data.travel_summary.total_countries == 1


def test_extract_endpoint_invalid_file():
    """Verify POST /api/extract rejects non-image files."""
    bad_upload = UploadFile(
        filename="malicious.txt",
        file=io.BytesIO(b"plain text"),
        headers={"content-type": "text/plain"}
    )

    with pytest.raises(HTTPException) as exc_info:
        extract_passport([bad_upload])
    assert exc_info.value.status_code == 400
    assert "not a valid" in exc_info.value.detail.lower()


def test_extract_endpoint_missing_api_key(monkeypatch):
    """Verify POST /api/extract returns 400 when GEMINI_API_KEY is not configured."""
    monkeypatch.setattr("app.services.gemini_service.get_gemini_client", lambda: None)

    img_bytes = create_test_image_bytes()
    upload = UploadFile(
        filename="passport.jpg",
        file=io.BytesIO(img_bytes),
        headers={"content-type": "image/jpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        extract_passport([upload])
    assert exc_info.value.status_code == 400
    assert "gemini_api_key is not configured" in exc_info.value.detail.lower()


def test_extract_endpoint_caching_and_force_refresh(monkeypatch):
    """Verify identical uploads hit cache and force_refresh bypasses cache."""
    call_count = 0

    def mock_call_gemini(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return RawAIExtraction(
            personal_details=PersonalDetails(
                passport_number="L898902C3",
                surname="TRAVELER",
                given_names="ALEX MORGAN",
                date_of_birth="1988-06-15",
                date_of_expiry="2030-04-09",
                issuing_country_code="UTO"
            ),
            travel_events=[],
            warnings=[],
            overall_confidence="high"
        )

    monkeypatch.setattr("app.services.gemini_service.call_gemini_with_retry", mock_call_gemini)
    monkeypatch.setattr("app.services.gemini_service.get_gemini_client", lambda: object())

    img_bytes = create_test_image_bytes()

    # Call 1: Cache Miss
    u1 = UploadFile(filename="page.jpg", file=io.BytesIO(img_bytes), headers={"content-type": "image/jpeg"})
    res1 = extract_passport([u1])
    assert res1.is_cached is False
    assert call_count == 1

    # Call 2 with identical image bytes: Cache Hit!
    u2 = UploadFile(filename="page.jpg", file=io.BytesIO(img_bytes), headers={"content-type": "image/jpeg"})
    res2 = extract_passport([u2])
    assert res2.is_cached is True
    assert call_count == 1  # Gemini was not called again

    # Call 3 with force_refresh=True: Bypasses Cache!
    u3 = UploadFile(filename="page.jpg", file=io.BytesIO(img_bytes), headers={"content-type": "image/jpeg"})
    res3 = extract_passport([u3], force_refresh=True)
    assert res3.is_cached is False
    assert call_count == 2  # Gemini was called again



