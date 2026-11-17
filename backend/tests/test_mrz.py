"""Unit tests for MRZ (ICAO Doc 9303) parsing and check digit validation."""

import pytest
from app.services.mrz_service import (
    calculate_check_digit,
    verify_check_digit,
    parse_td3_mrz,
    parse_mrz_date
)
from app.schemas import PersonalDetails


def test_calculate_check_digit():
    """Verify ICAO 7-3-1 weight check digit calculation."""
    # Test standard known doc numbers
    assert calculate_check_digit("L898902C3") == "6"
    assert calculate_check_digit("880615") == "0"
    assert calculate_check_digit("300409") == "8"
    assert calculate_check_digit("HA5391091") == "1"


def test_valid_td3_mrz():
    """Verify parsing of completely valid TD3 MRZ lines."""
    line1 = "P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO8806150M3004098988061599812<<68"

    res = parse_td3_mrz(line1, line2)
    assert res.mrz_found is True
    assert res.mrz_valid is True
    assert res.document_number_check is True
    assert res.dob_check is True
    assert res.expiry_check is True
    assert res.composite_check is True
    assert len(res.discrepancies) == 0
    assert res.parsed_details["surname"] == "TRAVELER"
    assert res.parsed_details["given_names"] == "ALEX MORGAN"
    assert res.parsed_details["passport_number"] == "L898902C3"
    assert res.parsed_details["nationality"] == "UTO"
    assert res.parsed_details["date_of_birth"] == "1988-06-15"
    assert res.parsed_details["date_of_expiry"] == "2030-04-09"


def test_corrupted_doc_number_check_digit():
    """Verify failure detection when document number check digit is tampered."""
    line1 = "P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<"
    # Replace check digit '6' with '9' at index 9
    line2 = "L898902C39UTO8806150M3004098988061599812<<68"

    res = parse_td3_mrz(line1, line2)
    assert res.mrz_found is True
    assert res.mrz_valid is False
    assert res.document_number_check is False
    assert any("passport number check digit mismatch" in d.lower() for d in res.discrepancies)


def test_corrupted_dob_check_digit():
    """Verify failure detection when DOB check digit is tampered."""
    line1 = "P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<"
    # Replace DOB check digit '0' with '3' at index 19
    line2 = "L898902C36UTO8806153M3004098988061599812<<68"

    res = parse_td3_mrz(line1, line2)
    assert res.mrz_valid is False
    assert res.dob_check is False
    assert any("date of birth check digit mismatch" in d.lower() for d in res.discrepancies)


def test_visual_zone_mismatch_cross_checking():
    """Verify detection when visual zone extracted values conflict with MRZ."""
    line1 = "P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO8806150M3004098988061599812<<68"

    # Visual details have conflicting passport number and birth date
    visual = PersonalDetails(
        passport_number="L999999C0",
        date_of_birth="1992-01-01",
        date_of_expiry="2030-04-09",
        issuing_country_code="FRA"
    )

    res = parse_td3_mrz(line1, line2, visual_details=visual)
    assert res.mrz_valid is True  # The MRZ itself is mathematically valid
    assert len(res.discrepancies) >= 3
    assert any("passport number mismatch" in d.lower() for d in res.discrepancies)
    assert any("date of birth mismatch" in d.lower() for d in res.discrepancies)
    assert any("country code mismatch" in d.lower() for d in res.discrepancies)


def test_invalid_mrz_length():
    """Verify handling when lines are truncated or missing."""
    res = parse_td3_mrz("P<UTO SHORT", "L898902C3")
    assert res.mrz_found is True
    assert res.mrz_valid is False
    assert any("length" in d.lower() for d in res.discrepancies)

    res_empty = parse_td3_mrz(None, "")
    assert res_empty.mrz_found is False
    assert res_empty.mrz_valid is False


def test_algorithmic_repair_ocr_confusion():
    """Verify that an OCR confusion character (e.g. 'O' instead of '0') is repaired via check digit."""
    line1 = "P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<"
    # Replace '0' with 'O' at index 5 in doc number: L8989O2C3
    line2_corrupted = "L8989O2C36UTO8806150M3004098988061599812<<68"

    res = parse_td3_mrz(line1, line2_corrupted)
    assert res.mrz_found is True
    assert res.document_number_check is True
    assert res.parsed_details["passport_number"] == "L898902C3"
    assert "passport_number" in res.repaired_fields
    assert any("Forensic MRZ Repair" in d for d in res.discrepancies)


def test_algorithmic_repair_illegible_placeholder():
    """Verify that an illegible placeholder '?' is mathematically solved via modular inverse equation."""
    line1 = "P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<"
    # Corrupt DOB digit '8' at index 14 to '?': 8?0615
    line2_corrupted = "L898902C36UTO8?06150M3004098988061599812<<68"

    res = parse_td3_mrz(line1, line2_corrupted)
    assert res.mrz_found is True
    assert res.dob_check is True
    assert res.parsed_details["date_of_birth"] == "1988-06-15"
    assert "date_of_birth" in res.repaired_fields
    assert any("Solved illegible character" in d for d in res.discrepancies)


def test_algorithmic_repair_visual_hint():
    """Verify that a visual inspection zone hint resolves a torn/damaged MRZ character."""
    line1 = "P<UTOTRAVELER<<ALEX<MORGAN<<<<<<<<<<<<<<<<<<"
    # Corrupted char 'X' at position 3: L89X902C3
    line2_corrupted = "L89X902C36UTO8806150M3004098988061599812<<68"

    visual = PersonalDetails(
        passport_number="L898902C3",
        date_of_birth="1988-06-15",
        date_of_expiry="2030-04-09",
        issuing_country_code="UTO"
    )

    res = parse_td3_mrz(line1, line2_corrupted, visual_details=visual)
    assert res.mrz_found is True
    assert res.document_number_check is True
    assert res.parsed_details["passport_number"] == "L898902C3"
    assert "passport_number" in res.repaired_fields

