"""Timeline service for merging, deduplicating, sorting, and analyzing travel events."""

import datetime
import uuid
from typing import List, Tuple, Optional, Dict, Any
from app.schemas import TravelEvent, TravelSummary, PersonalDetails


def parse_comparable_date(date_str: Optional[str]) -> Tuple[datetime.date, bool]:
    """Parse a date string into a comparable datetime.date object.

    Returns:
        (datetime.date, is_exact): Tuple with parsed date and boolean flag indicating if exact.
        If date cannot be parsed, returns (datetime.date.max, False).
    """
    if not date_str or not date_str.strip():
        return datetime.date.max, False

    clean_str = date_str.strip()

    # Case 1: Full ISO YYYY-MM-DD
    try:
        parts = clean_str.split('-')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime.date(year, month, day), True
    except (ValueError, IndexError):
        pass

    # Case 2: Partial ISO YYYY-MM
    try:
        parts = clean_str.split('-')
        if len(parts) == 2:
            year, month = int(parts[0]), int(parts[1])
            return datetime.date(year, month, 1), False
    except (ValueError, IndexError):
        pass

    # Case 3: Year only YYYY
    try:
        if len(clean_str) == 4 and clean_str.isdigit():
            year = int(clean_str)
            return datetime.date(year, 1, 1), False
    except ValueError:
        pass

    # Unparseable
    return datetime.date.max, False


def deduplicate_events(events: List[TravelEvent]) -> List[TravelEvent]:
    """Remove exact or near-identical duplicate travel events."""
    seen_signatures = set()
    unique_events: List[TravelEvent] = []

    for event in events:
        # Signature based on normalized event_type, country, date, city_or_port, visa_number
        sig = (
            (event.event_type or "").strip().lower(),
            (event.country or "").strip().lower(),
            (event.date or "").strip(),
            (event.city_or_port or "").strip().lower(),
            (event.visa_number or "").strip().lower(),
        )
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            unique_events.append(event)

    return unique_events


def calculate_days_stayed(events: List[TravelEvent]) -> None:
    """Pair entry stamps with subsequent exit stamps for the same country to calculate days stayed.

    Modifies events in-place.
    """
    # Track open entries per country: country -> list of (event_index, entry_date)
    open_entries: Dict[str, List[Tuple[int, datetime.date]]] = {}

    for idx, event in enumerate(events):
        country_key = (event.country or "").strip().lower()
        if not country_key:
            continue

        event_date, is_exact = parse_comparable_date(event.date)
        if event_date == datetime.date.max or not is_exact:
            continue

        if event.event_type == "entry_stamp":
            if country_key not in open_entries:
                open_entries[country_key] = []
            open_entries[country_key].append((idx, event_date))

        elif event.event_type == "exit_stamp":
            if country_key in open_entries and open_entries[country_key]:
                entry_idx, entry_date = open_entries[country_key].pop(0)
                if event_date >= entry_date:
                    delta_days = (event_date - entry_date).days
                    # Assign days_stayed to the exit stamp and note on entry
                    events[idx].days_stayed = delta_days


def process_timeline(events: List[TravelEvent]) -> Tuple[List[TravelEvent], List[str]]:
    """Sort, deduplicate, compute stay durations, and flag undated events.

    Returns:
        (sorted_events, warnings)
    """
    warnings: List[str] = []

    # Ensure all events have unique frontend IDs
    for event in events:
        if not event.id:
            event.id = f"evt_{uuid.uuid4().hex[:8]}"

    # Deduplicate
    initial_count = len(events)
    deduped = deduplicate_events(events)
    if len(deduped) < initial_count:
        warnings.append(f"Removed {initial_count - len(deduped)} duplicate travel stamp/visa records.")

    # Sort: events with valid dates ascending, undated/unparseable events placed at the end
    def sort_key(e: TravelEvent):
        parsed_dt, is_exact = parse_comparable_date(e.date)
        # Undated events get sorted last
        has_date = 0 if parsed_dt != datetime.date.max else 1
        return (has_date, parsed_dt)

    sorted_events = sorted(deduped, key=sort_key)

    # Flag undated events
    for event in sorted_events:
        dt, _ = parse_comparable_date(event.date)
        if dt == datetime.date.max:
            if not event.notes:
                event.notes = "Date illegible or unrecorded"
            warnings.append(
                f"Travel event ({event.event_type} - {event.country or 'Unknown'}) has an illegible or missing date."
            )

    # Calculate stay durations between entries and exits
    calculate_days_stayed(sorted_events)

    return sorted_events, warnings


def is_home_country(country_name: str, personal_details: Optional[PersonalDetails] = None) -> bool:
    """Check if a country name string corresponds to the passport holder's home/issuing country."""
    if not country_name or not personal_details:
        return False

    target = country_name.strip().lower()

    # Collect known home identifiers
    home_names = set()
    if personal_details.issuing_country:
        home_names.add(personal_details.issuing_country.strip().lower())
    if personal_details.issuing_country_code:
        home_names.add(personal_details.issuing_country_code.strip().lower())
    if personal_details.nationality:
        nat = personal_details.nationality.strip().lower()
        home_names.add(nat)
        # Demonym handling (e.g. 'Indian' -> 'India', 'Utopian' -> 'Utopia', 'American' -> 'America')
        if nat.endswith("ian"):
            home_names.add(nat[:-3] + "ia")
            home_names.add(nat[:-3])
        elif nat.endswith("an"):
            home_names.add(nat[:-2])

    for home in home_names:
        if not home:
            continue
        if home == target or home in target or target in home:
            return True

    return False


def build_travel_summary(
    events: List[TravelEvent],
    personal_details: Optional[PersonalDetails] = None
) -> TravelSummary:
    """Compute high-level travel statistics from events.

    Excludes the passport holder's home/issuing country from visited countries count.
    """
    unique_countries = set()
    total_visas = 0
    total_entries = 0
    total_exits = 0
    visas_summary: List[Dict[str, Any]] = []

    for event in events:
        country_name = (event.country or "").strip()
        if country_name:
            if not is_home_country(country_name, personal_details):
                unique_countries.add(country_name)

        if event.event_type == "visa":
            total_visas += 1
            visas_summary.append({
                "country": event.country,
                "visa_type": event.visa_type,
                "visa_number": event.visa_number,
                "valid_from": event.valid_from,
                "valid_until": event.valid_until,
                "duration_of_stay": event.duration_of_stay
            })
        elif event.event_type == "entry_stamp":
            total_entries += 1
        elif event.event_type == "exit_stamp":
            total_exits += 1

    sorted_countries = sorted(list(unique_countries))

    return TravelSummary(
        total_countries=len(sorted_countries),
        countries_visited=sorted_countries,
        total_events=len(events),
        total_visas=total_visas,
        total_entry_stamps=total_entries,
        total_exit_stamps=total_exits,
        visas_summary=visas_summary
    )


def evaluate_passport_status(date_of_expiry: Optional[str]) -> Tuple[str, Optional[int], List[str]]:
    """Determine passport status (valid, expiring_soon, expired, unknown) and days until expiry.

    Returns:
        (status, days_until_expiry, warnings)
    """
    warnings: List[str] = []
    if not date_of_expiry:
        return "unknown", None, ["Passport expiry date is missing or illegible."]

    exp_dt, is_exact = parse_comparable_date(date_of_expiry)
    if exp_dt == datetime.date.max:
        return "unknown", None, [f"Could not parse passport expiry date '{date_of_expiry}'."]

    today = datetime.date.today()
    days_left = (exp_dt - today).days

    if days_left < 0:
        warnings.append(f"Passport has EXPIRED on {date_of_expiry} ({abs(days_left)} days ago).")
        return "expired", days_left, warnings
    elif days_left <= 180:
        warnings.append(
            f"Passport expires soon on {date_of_expiry} ({days_left} days remaining, less than 6 months validity!)."
        )
        return "expiring_soon", days_left, warnings
    else:
        return "valid", days_left, warnings

