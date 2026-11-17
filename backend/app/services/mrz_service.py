"""MRZ (Machine Readable Zone) parsing and ICAO 9303 check digit verification service."""

import datetime
from typing import Optional, Tuple, List, Dict, Any
from app.schemas import MRZValidationResult, PersonalDetails


# Weight array defined by ICAO 9303
ICAO_WEIGHTS = [7, 3, 1]

# Modular multiplicative inverses for weights 7, 3, 1 modulo 10
# (7 * 3 = 21 = 1 mod 10; 3 * 7 = 21 = 1 mod 10; 1 * 1 = 1 mod 10)
MODULAR_INVERSES_MOD_10 = {1: 1, 3: 7, 7: 3}

# Common OCR confusion characters on damaged/aged documents
OCR_CONFUSIONS = {
    '0': ['O', 'Q', 'D'],
    'O': ['0', 'Q', 'D'],
    'Q': ['0', 'O'],
    'D': ['0', 'O'],
    '1': ['I', 'L'],
    'I': ['1', 'L'],
    'L': ['1', 'I'],
    '8': ['B'],
    'B': ['8'],
    '5': ['S'],
    'S': ['5'],
    '2': ['Z'],
    'Z': ['2'],
    '6': ['G'],
    'G': ['6'],
    'U': ['V'],
    'V': ['U']
}


def repair_mrz_field(
    data: str,
    expected_check_digit: str,
    is_numeric_only: bool = False,
    visual_hint: Optional[str] = None,
    composite_validator: Optional[Any] = None
) -> Optional[Tuple[str, str]]:
    """Attempt algorithmic mathematical repair of a damaged or misread MRZ character.

    Forensic criteria for safe repair:
    1. Must match visual inspection zone hint if provided, OR
    2. Must satisfy BOTH field check digit AND composite checksum, OR
    3. Must resolve an explicit illegible placeholder ('?', '*', '_') confirmed by composite checksum.

    Returns:
        (repaired_data, note) if a mathematically valid repair is proven, otherwise None.
    """
    if not data or not expected_check_digit or expected_check_digit == '<':
        return None

    if verify_check_digit(data, expected_check_digit):
        return None  # Already valid, no repair needed

    target_cd = int(expected_check_digit) if expected_check_digit.isdigit() else -1
    if target_cd == -1:
        return None

    data_chars = list(data)
    n = len(data_chars)

    # Strategy 1: Test visual inspection zone hint if available
    if visual_hint:
        clean_hint = "".join(ch for ch in visual_hint.upper() if ch.isalnum() or ch == '<')
        if len(clean_hint) == n:
            for idx in range(n):
                if data_chars[idx] != clean_hint[idx]:
                    candidate = list(data_chars)
                    candidate[idx] = clean_hint[idx]
                    cand_str = "".join(candidate)
                    if verify_check_digit(cand_str, expected_check_digit):
                        if composite_validator is None or composite_validator(cand_str):
                            return cand_str, f"Repaired position {idx} from '{data_chars[idx]}' to '{clean_hint[idx]}' matching visual inspection zone"

    # Strategy 2: Test common OCR confusion character substitutions
    for idx in range(n):
        orig_char = data_chars[idx]
        alternatives = OCR_CONFUSIONS.get(orig_char, [])
        for alt in alternatives:
            if is_numeric_only and not alt.isdigit():
                continue
            candidate = list(data_chars)
            candidate[idx] = alt
            cand_str = "".join(candidate)
            if verify_check_digit(cand_str, expected_check_digit):
                # Verify candidate against composite check digit to eliminate false positives
                if composite_validator is None or composite_validator(cand_str):
                    return cand_str, f"Repaired OCR confusion at position {idx} from '{orig_char}' to '{alt}'"

    # Strategy 3: Solve explicit illegible/damaged characters (e.g. '?', '*', '_')
    for idx in range(n):
        if not data_chars[idx].isalnum() and data_chars[idx] != '<':
            weight = ICAO_WEIGHTS[idx % len(ICAO_WEIGHTS)]
            inv_w = MODULAR_INVERSES_MOD_10[weight]

            other_sum = 0
            for j in range(n):
                if j == idx:
                    continue
                ch = data_chars[j].upper()
                if '0' <= ch <= '9':
                    val = int(ch)
                elif 'A' <= ch <= 'Z':
                    val = ord(ch) - ord('A') + 10
                else:
                    val = 0
                other_sum += val * ICAO_WEIGHTS[j % len(ICAO_WEIGHTS)]

            delta = (target_cd - (other_sum % 10)) % 10
            req_mod_10 = (delta * inv_w) % 10
            cand_char = str(req_mod_10)

            candidate = list(data_chars)
            candidate[idx] = cand_char
            cand_str = "".join(candidate)
            if verify_check_digit(cand_str, expected_check_digit):
                if composite_validator is None or composite_validator(cand_str):
                    return cand_str, f"Solved illegible character at position {idx} to '{cand_char}' via check-digit equation"

    return None


def calculate_check_digit(data: str) -> str:
    """Calculate check digit for an MRZ string based on ICAO 9303 (weights 7, 3, 1).

    Each character maps to:
      - '0'-'9' -> 0-9
      - 'A'-'Z' -> 10-35
      - '<'     -> 0
    """
    total = 0
    for i, char in enumerate(data):
        char = char.upper()
        if '0' <= char <= '9':
            val = int(char)
        elif 'A' <= char <= 'Z':
            val = ord(char) - ord('A') + 10
        elif char == '<':
            val = 0
        else:
            val = 0
        weight = ICAO_WEIGHTS[i % len(ICAO_WEIGHTS)]
        total += val * weight
    return str(total % 10)


def verify_check_digit(data: str, expected_digit: str) -> bool:
    """Verify that the check digit matches expected digit."""
    if not expected_digit or expected_digit == '<':
        # In some implementations, '<' is accepted if optional data is empty
        return calculate_check_digit(data) in ('0', '<')
    return calculate_check_digit(data) == expected_digit


def parse_mrz_date(yymmdd: str, is_expiry: bool = False) -> Optional[str]:
    """Parse YYMMDD into ISO YYYY-MM-DD.

    For expiry dates, YY is usually within the current or next century.
    For birth dates, YY is typically in the 20th century unless YY <= current_year % 100.
    """
    if not yymmdd or len(yymmdd) != 6 or not yymmdd.isdigit():
        return None

    current_year = datetime.date.today().year
    current_two_digit = current_year % 100
    yy = int(yymmdd[0:2])
    mm = int(yymmdd[2:4])
    dd = int(yymmdd[4:6])

    if mm < 1 or mm > 12 or dd < 1 or dd > 31:
        return None

    if is_expiry:
        # Expiry is future or recent past
        year = (current_year // 100) * 100 + yy
        if year < current_year - 20:
            year += 100
    else:
        # Birth date
        if yy <= current_two_digit:
            year = (current_year // 100) * 100 + yy
        else:
            year = ((current_year // 100) - 1) * 100 + yy

    try:
        dt = datetime.date(year, mm, dd)
        return dt.isoformat()
    except ValueError:
        return None


def clean_mrz_line(line: Optional[str]) -> str:
    """Strip whitespace, normalize, and preserve 44-char positions including damage placeholders."""
    if not line:
        return ""
    cleaned = "".join(ch for ch in line.strip().upper() if ch.isalnum() or ch in ('<', '?', '*', '_'))
    return cleaned


def parse_td3_mrz(
    line1: Optional[str],
    line2: Optional[str],
    visual_details: Optional[PersonalDetails] = None
) -> MRZValidationResult:
    """Parse and validate standard 2-line x 44-character TD3 passport MRZ.

    Args:
        line1: First line of MRZ (44 characters)
        line2: Second line of MRZ (44 characters)
        visual_details: Extracted visual inspection zone data for cross-checking

    Returns:
        MRZValidationResult with validity flags and cross-check discrepancies
    """
    cleaned1 = clean_mrz_line(line1)
    cleaned2 = clean_mrz_line(line2)

    if not cleaned1 or not cleaned2:
        return MRZValidationResult(
            mrz_found=False,
            mrz_valid=False,
            raw_lines=[line1 or "", line2 or ""],
            discrepancies=["MRZ lines are missing or unreadable."]
        )

    # Check length
    discrepancies: List[str] = []
    if len(cleaned1) != 44:
        discrepancies.append(f"MRZ line 1 length is {len(cleaned1)}, expected 44.")
    if len(cleaned2) != 44:
        discrepancies.append(f"MRZ line 2 length is {len(cleaned2)}, expected 44.")

    if len(cleaned1) < 44 or len(cleaned2) < 44:
        return MRZValidationResult(
            mrz_found=True,
            mrz_valid=False,
            raw_lines=[cleaned1, cleaned2],
            discrepancies=discrepancies
        )

    # Line 1 Breakdown:
    # 0:2   - Document code ('P<')
    # 2:5   - Issuing state (3 chars)
    # 5:44  - Names (Surname<<Given<Names)
    doc_code = cleaned1[0:2]
    issuing_country = cleaned1[2:5].replace('<', '')
    raw_names = cleaned1[5:44]

    surname = ""
    given_names = ""
    if '<<' in raw_names:
        parts = raw_names.split('<<', 1)
        surname = parts[0].replace('<', ' ').strip()
        given_names = parts[1].replace('<', ' ').strip()
    else:
        surname = raw_names.replace('<', ' ').strip()

    # Line 2 Breakdown:
    # 0:9   - Document number (9 chars)
    # 9     - Document number check digit (1 char)
    # 10:13 - Nationality (3 chars)
    # 13:19 - Date of birth YYMMDD (6 chars)
    # 19    - Date of birth check digit (1 char)
    # 20    - Sex ('M', 'F', '<', 'X')
    # 21:27 - Expiry date YYMMDD (6 chars)
    # 27    - Expiry date check digit (1 char)
    # 28:42 - Optional data / Personal number (14 chars)
    # 42    - Optional data check digit (1 char)
    # 43    - Composite check digit (1 char)

    doc_num_raw = cleaned2[0:9]
    doc_num_clean = doc_num_raw.replace('<', '')
    doc_num_check_char = cleaned2[9]

    nationality = cleaned2[10:13].replace('<', '')
    dob_raw = cleaned2[13:19]
    dob_check_char = cleaned2[19]

    sex_char = cleaned2[20]
    sex = "M" if sex_char == 'M' else "F" if sex_char == 'F' else "X" if sex_char == 'X' else "Unspecified"

    expiry_raw = cleaned2[21:27]
    expiry_check_char = cleaned2[27]

    optional_raw = cleaned2[28:42]
    optional_clean = optional_raw.replace('<', '')
    optional_check_char = cleaned2[42]

    composite_check_char = cleaned2[43]

    repaired_fields: Dict[str, str] = {}

    # Composite validator callbacks to eliminate false-positive repairs
    def validate_composite_with_doc(cand: str) -> bool:
        test_comp = (
            cand + doc_num_check_char +
            dob_raw + dob_check_char +
            expiry_raw + expiry_check_char +
            optional_raw + optional_check_char
        )
        return verify_check_digit(test_comp, composite_check_char)

    def validate_composite_with_dob(cand: str) -> bool:
        test_comp = (
            doc_num_raw + doc_num_check_char +
            cand + dob_check_char +
            expiry_raw + expiry_check_char +
            optional_raw + optional_check_char
        )
        return verify_check_digit(test_comp, composite_check_char)

    def validate_composite_with_exp(cand: str) -> bool:
        test_comp = (
            doc_num_raw + doc_num_check_char +
            dob_raw + dob_check_char +
            cand + expiry_check_char +
            optional_raw + optional_check_char
        )
        return verify_check_digit(test_comp, composite_check_char)

    # Verify Check Digits (with Algorithmic Forensic Repair for Damaged Documents)
    doc_num_ok = verify_check_digit(doc_num_raw, doc_num_check_char)
    if not doc_num_ok:
        vis_num_hint = visual_details.passport_number if visual_details else None
        repaired = repair_mrz_field(
            doc_num_raw, doc_num_check_char,
            is_numeric_only=False,
            visual_hint=vis_num_hint,
            composite_validator=validate_composite_with_doc
        )
        if repaired:
            doc_num_raw, rep_note = repaired
            doc_num_clean = doc_num_raw.replace('<', '')
            doc_num_ok = True
            repaired_fields["passport_number"] = f"{rep_note} -> '{doc_num_clean}'"
            discrepancies.append(f"Forensic MRZ Repair: Passport number {rep_note} (validated by check digit).")

    dob_ok = verify_check_digit(dob_raw, dob_check_char)
    if not dob_ok:
        vis_dob_hint = visual_details.date_of_birth.replace('-', '')[2:] if (visual_details and visual_details.date_of_birth and len(visual_details.date_of_birth) == 10) else None
        repaired = repair_mrz_field(
            dob_raw, dob_check_char,
            is_numeric_only=True,
            visual_hint=vis_dob_hint,
            composite_validator=validate_composite_with_dob
        )
        if repaired:
            dob_raw, rep_note = repaired
            dob_ok = True
            repaired_fields["date_of_birth"] = f"{rep_note} -> '{dob_raw}'"
            discrepancies.append(f"Forensic MRZ Repair: Date of Birth {rep_note} (validated by check digit).")

    expiry_ok = verify_check_digit(expiry_raw, expiry_check_char)
    if not expiry_ok:
        vis_exp_hint = visual_details.date_of_expiry.replace('-', '')[2:] if (visual_details and visual_details.date_of_expiry and len(visual_details.date_of_expiry) == 10) else None
        repaired = repair_mrz_field(
            expiry_raw, expiry_check_char,
            is_numeric_only=True,
            visual_hint=vis_exp_hint,
            composite_validator=validate_composite_with_exp
        )
        if repaired:
            expiry_raw, rep_note = repaired
            expiry_ok = True
            repaired_fields["date_of_expiry"] = f"{rep_note} -> '{expiry_raw}'"
            discrepancies.append(f"Forensic MRZ Repair: Expiry Date {rep_note} (validated by check digit).")

    # Optional data check digit (can be '<' or 0 if unused)
    optional_ok = True
    if optional_clean:
        if optional_check_char != '<':
            optional_ok = verify_check_digit(optional_raw, optional_check_char)

    # Composite check digit (re-evaluated with any mathematically repaired fields)
    composite_data = (
        doc_num_raw + doc_num_check_char +
        dob_raw + dob_check_char +
        expiry_raw + expiry_check_char +
        optional_raw + optional_check_char
    )
    composite_ok = verify_check_digit(composite_data, composite_check_char)

    if not doc_num_ok:
        discrepancies.append(
            f"MRZ passport number check digit mismatch: computed {calculate_check_digit(doc_num_raw)}, got '{doc_num_check_char}'."
        )
    if not dob_ok:
        discrepancies.append(
            f"MRZ Date of Birth check digit mismatch: computed {calculate_check_digit(dob_raw)}, got '{dob_check_char}'."
        )
    if not expiry_ok:
        discrepancies.append(
            f"MRZ Expiry Date check digit mismatch: computed {calculate_check_digit(expiry_raw)}, got '{expiry_check_char}'."
        )
    if not composite_ok:
        discrepancies.append(
            f"MRZ Composite check digit mismatch: computed {calculate_check_digit(composite_data)}, got '{composite_check_char}'."
        )

    # Cross check against visual inspection zone
    parsed_dob = parse_mrz_date(dob_raw, is_expiry=False)
    parsed_expiry = parse_mrz_date(expiry_raw, is_expiry=True)

    if visual_details:
        if visual_details.passport_number:
            vis_num = "".join(ch for ch in visual_details.passport_number if ch.isalnum()).upper()
            if vis_num and vis_num != doc_num_clean:
                discrepancies.append(
                    f"Passport number mismatch: Visual zone reads '{visual_details.passport_number}', but MRZ reads '{doc_num_clean}'."
                )

        if visual_details.date_of_birth and parsed_dob:
            vis_dob = visual_details.date_of_birth.strip()
            if len(vis_dob) == 10 and vis_dob != parsed_dob:
                discrepancies.append(
                    f"Date of Birth mismatch: Visual zone reads '{vis_dob}', but MRZ decodes to '{parsed_dob}'."
                )

        if visual_details.date_of_expiry and parsed_expiry:
            vis_exp = visual_details.date_of_expiry.strip()
            if len(vis_exp) == 10 and vis_exp != parsed_expiry:
                discrepancies.append(
                    f"Expiry Date mismatch: Visual zone reads '{vis_exp}', but MRZ decodes to '{parsed_expiry}'."
                )

        if visual_details.issuing_country_code and issuing_country:
            vis_code = visual_details.issuing_country_code.strip().upper()
            if len(vis_code) == 3 and vis_code != issuing_country:
                discrepancies.append(
                    f"Issuing country code mismatch: Visual zone reads '{vis_code}', but MRZ reads '{issuing_country}'."
                )

    all_checks_passed = (
        doc_num_ok and
        dob_ok and
        expiry_ok and
        composite_ok and
        optional_ok and
        len(cleaned1) == 44 and
        len(cleaned2) == 44
    )

    parsed_data = {
        "document_code": doc_code,
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "passport_number": doc_num_clean,
        "nationality": nationality,
        "date_of_birth": parsed_dob,
        "sex": sex,
        "date_of_expiry": parsed_expiry,
        "optional_data": optional_clean
    }

    return MRZValidationResult(
        mrz_found=True,
        mrz_valid=all_checks_passed,
        raw_lines=[cleaned1, cleaned2],
        document_number_check=doc_num_ok,
        dob_check=dob_ok,
        expiry_check=expiry_ok,
        composite_check=composite_ok,
        parsed_details=parsed_data,
        discrepancies=discrepancies,
        repaired_fields=repaired_fields
    )

