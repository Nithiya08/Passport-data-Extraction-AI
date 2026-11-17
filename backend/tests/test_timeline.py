"""Unit tests for timeline sorting, deduplication, days stayed calculation, and expiry."""

import datetime
import pytest
from app.schemas import TravelEvent, PersonalDetails
from app.services.timeline_service import (
    process_timeline,
    deduplicate_events,
    parse_comparable_date,
    build_travel_summary,
    evaluate_passport_status,
)


def test_parse_comparable_date():
    """Test standard ISO, partial ISO, and invalid date parsing."""
    d, exact = parse_comparable_date("2023-05-18")
    assert d == datetime.date(2023, 5, 18)
    assert exact is True

    d_partial, exact_partial = parse_comparable_date("2023-05")
    assert d_partial == datetime.date(2023, 5, 1)
    assert exact_partial is False

    d_year, exact_year = parse_comparable_date("2023")
    assert d_year == datetime.date(2023, 1, 1)
    assert exact_year is False

    d_invalid, exact_invalid = parse_comparable_date("unknown-date")
    assert d_invalid == datetime.date.max
    assert exact_invalid is False


def test_deduplicate_events():
    """Verify exact duplicates are eliminated while unique events are retained."""
    events = [
        TravelEvent(event_type="entry_stamp", country="France", date="2022-04-10", city_or_port="CDG"),
        TravelEvent(event_type="entry_stamp", country="France", date="2022-04-10", city_or_port="CDG"),
        TravelEvent(event_type="exit_stamp", country="France", date="2022-04-24", city_or_port="CDG"),
    ]
    deduped = deduplicate_events(events)
    assert len(deduped) == 2


def test_chronological_sorting_and_undated_placement():
    """Verify events are sorted ascending by date and undated events are placed at the end."""
    events = [
        TravelEvent(id="3", event_type="entry_stamp", country="UK", date="2023-08-12"),
        TravelEvent(id="1", event_type="visa", country="France", date="2022-03-01"),
        TravelEvent(id="undated", event_type="entry_stamp", country="Spain", date=None),
        TravelEvent(id="2", event_type="entry_stamp", country="France", date="2022-04-10"),
    ]

    sorted_events, warnings = process_timeline(events)

    assert sorted_events[0].id == "1"
    assert sorted_events[1].id == "2"
    assert sorted_events[2].id == "3"
    assert sorted_events[3].id == "undated"
    assert any("illegible or missing date" in w.lower() for w in warnings)


def test_days_stayed_calculation():
    """Verify entry and exit pairing calculates correct days stayed."""
    events = [
        TravelEvent(event_type="entry_stamp", country="France", date="2022-04-10", city_or_port="CDG"),
        TravelEvent(event_type="exit_stamp", country="France", date="2022-04-24", city_or_port="CDG"),
        TravelEvent(event_type="entry_stamp", country="UK", date="2023-08-10", city_or_port="LHR"),
        TravelEvent(event_type="exit_stamp", country="UK", date="2023-08-20", city_or_port="LGW"),
    ]

    sorted_events, _ = process_timeline(events)

    # France exit stamp should reflect 14 days stayed
    france_exit = [e for e in sorted_events if e.country == "France" and e.event_type == "exit_stamp"][0]
    assert france_exit.days_stayed == 14

    # UK exit stamp should reflect 10 days stayed
    uk_exit = [e for e in sorted_events if e.country == "UK" and e.event_type == "exit_stamp"][0]
    assert uk_exit.days_stayed == 10


def test_travel_summary_metrics():
    """Verify aggregated metrics for countries, visas, and stamps."""
    events = [
        TravelEvent(event_type="visa", country="France", date="2022-03-01", visa_type="Type C"),
        TravelEvent(event_type="entry_stamp", country="France", date="2022-04-10"),
        TravelEvent(event_type="exit_stamp", country="France", date="2022-04-24"),
        TravelEvent(event_type="entry_stamp", country="UK", date="2023-08-12"),
    ]

    summary = build_travel_summary(events)
    assert summary.total_countries == 2
    assert "France" in summary.countries_visited
    assert "UK" in summary.countries_visited
    assert summary.total_events == 4
    assert summary.total_visas == 1
    assert summary.total_entry_stamps == 2
    assert summary.total_exit_stamps == 1


def test_travel_summary_excludes_home_country():
    """Verify that the holder's home/issuing country is not counted as a visited country."""
    events = [
        TravelEvent(event_type="exit_stamp", country="India", date="2023-01-10"),
        TravelEvent(event_type="entry_stamp", country="United Arab Emirates", date="2023-01-10"),
        TravelEvent(event_type="exit_stamp", country="United Arab Emirates", date="2023-01-20"),
        TravelEvent(event_type="entry_stamp", country="India", date="2023-01-20"),
    ]
    home_details = PersonalDetails(
        issuing_country="India",
        nationality="Indian",
        issuing_country_code="IND"
    )
    summary = build_travel_summary(events, personal_details=home_details)
    assert summary.total_countries == 1
    assert "United Arab Emirates" in summary.countries_visited
    assert "India" not in summary.countries_visited


def test_evaluate_passport_status():
    """Verify passport expiration calculations."""
    today = datetime.date.today()

    # Expired passport
    past_date = (today - datetime.timedelta(days=30)).isoformat()
    status, days, warnings = evaluate_passport_status(past_date)
    assert status == "expired"
    assert days < 0
    assert any("expired" in w.lower() for w in warnings)

    # Expiring soon (< 180 days)
    soon_date = (today + datetime.timedelta(days=90)).isoformat()
    status_soon, days_soon, warnings_soon = evaluate_passport_status(soon_date)
    assert status_soon == "expiring_soon"
    assert 0 <= days_soon <= 180
    assert any("expires soon" in w.lower() for w in warnings_soon)

    # Valid passport (> 180 days)
    valid_date = (today + datetime.timedelta(days=500)).isoformat()
    status_valid, days_valid, warnings_valid = evaluate_passport_status(valid_date)
    assert status_valid == "valid"
    assert days_valid > 180

    # Missing date
    status_unknown, days_unknown, warnings_unknown = evaluate_passport_status(None)
    assert status_unknown == "unknown"
    assert days_unknown is None

