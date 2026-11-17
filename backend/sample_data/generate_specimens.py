"""Generate synthetic SPECIMEN passport images for unit testing and frontend demo."""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add backend directory to path so we can import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.mrz_service import calculate_check_digit


def get_default_font(size: int = 16):
    """Attempt to load a clean truetype font, fallback to default."""
    font_names = ["arial.ttf", "segoeui.ttf", "cour.ttf", "DejaVuSans.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            continue
    return ImageFont.load_default()


def get_mono_font(size: int = 18):
    """Attempt to load monospace font for MRZ."""
    font_names = ["consola.ttf", "cour.ttf", "lucon.ttf", "DejaVuSansMono.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            continue
    return ImageFont.load_default()


def create_specimen_bio_page(output_path: str):
    """Generate realistic specimen passport biodata page."""
    width, height = 1200, 800
    img = Image.new("RGB", (width, height), color=(248, 246, 240))
    draw = ImageDraw.Draw(img)

    # Decorative security guilloche border
    for i in range(5):
        draw.rectangle(
            [15 + i * 2, 15 + i * 2, width - (15 + i * 2), height - (15 + i * 2)],
            outline=(210 + i * 5, 205 + i * 5, 195)
        )

    title_font = get_default_font(28)
    label_font = get_default_font(14)
    val_font = get_default_font(20)
    bold_val_font = get_default_font(22)
    mono_font = get_mono_font(24)

    # Header
    draw.text((60, 45), "PASSPORT / PASSEPORT", fill=(30, 41, 59), font=title_font)
    draw.text((850, 45), "UTOPIA / UTO", fill=(71, 85, 105), font=title_font)
    draw.line([(60, 90), (width - 60, 90)], fill=(148, 163, 184), width=2)

    # Photo Box / Silhouette
    photo_box = [60, 120, 320, 460]
    draw.rectangle(photo_box, fill=(226, 232, 240), outline=(148, 163, 184), width=2)
    # Head silhouette
    draw.ellipse([140, 180, 240, 280], fill=(148, 163, 184))
    # Body silhouette
    draw.chord([100, 290, 280, 470], start=0, end=180, fill=(148, 163, 184))
    # Specimen watermark over photo
    draw.text((105, 340), "SPECIMEN", fill=(220, 38, 38), font=title_font)

    # Visual Inspection Zone Fields
    fields = [
        ("Type / Type", "P", 360, 120),
        ("Country Code / Code du pays", "UTO", 520, 120),
        ("Passport No. / No. du passeport", "L898902C3", 750, 120),
        ("Surname / Nom", "TRAVELER", 360, 180),
        ("Given Names / Prenoms", "ALEX MORGAN", 360, 240),
        ("Nationality / Nationalite", "UTOPIAN", 360, 300),
        ("Date of birth / Date de naissance", "15 JUN / JUIN 1988", 750, 300),
        ("Sex / Sexe", "M", 360, 360),
        ("Place of birth / Lieu de naissance", "UTOPIA CITY", 520, 360),
        ("Date of issue / Date de delivrance", "10 APR / AVR 2020", 360, 420),
        ("Date of expiry / Date d'expiration", "09 APR / AVR 2030", 750, 420),
        ("Authority / Autorite", "MINISTRY OF FOREIGN AFFAIRS", 360, 480),
    ]

    for label, val, x, y in fields:
        draw.text((x, y), label, fill=(100, 116, 139), font=label_font)
        draw.text((x, y + 20), val, fill=(15, 23, 42), font=val_font)

    # Watermark text across page
    draw.text((450, 280), "SPECIMEN DOCUMENT - NOT VALID FOR TRAVEL", fill=(230, 210, 210), font=get_default_font(30))

    # Divider before MRZ
    draw.line([(40, 560), (width - 40, 560)], fill=(148, 163, 184), width=2)

    # MRZ Calculation
    # Line 1: P<UTO + TRAVELER<<ALEX<MORGAN + padded to 44
    l1_raw = "P<UTOTRAVELER<<ALEX<MORGAN"
    mrz_line_1 = (l1_raw + "<" * 44)[:44]

    # Line 2 components:
    # Doc num: L898902C3 (9 chars)
    doc_num = "L898902C3"
    doc_chk = calculate_check_digit(doc_num)

    nationality = "UTO"
    dob = "880615"
    dob_chk = calculate_check_digit(dob)

    sex = "M"
    exp = "300409"
    exp_chk = calculate_check_digit(exp)

    optional = "988061599812<<"
    opt_chk = calculate_check_digit(optional)

    # Composite: doc_num + doc_chk + dob + dob_chk + exp + exp_chk + optional + opt_chk
    composite_data = (
        doc_num + doc_chk +
        dob + dob_chk +
        exp + exp_chk +
        optional + opt_chk
    )
    composite_chk = calculate_check_digit(composite_data)

    mrz_line_2 = f"{doc_num}{doc_chk}{nationality}{dob}{dob_chk}{sex}{exp}{exp_chk}{optional}{opt_chk}{composite_chk}"

    # Draw MRZ Zone in OCR Monospace font
    draw.rectangle([40, 600, width - 40, 750], fill=(255, 255, 255), outline=(203, 213, 225), width=1)
    draw.text((60, 625), mrz_line_1, fill=(15, 23, 42), font=mono_font)
    draw.text((60, 680), mrz_line_2, fill=(15, 23, 42), font=mono_font)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Generated specimen bio page: {output_path}")
    print(f"MRZ 1: {mrz_line_1}")
    print(f"MRZ 2: {mrz_line_2}")


def create_specimen_visa_page(output_path: str):
    """Generate specimen visa sticker page."""
    width, height = 1200, 800
    img = Image.new("RGB", (width, height), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)

    title_font = get_default_font(26)
    label_font = get_default_font(14)
    val_font = get_default_font(18)

    # Page Header
    draw.text((60, 35), "VISAS", fill=(100, 116, 139), font=title_font)
    draw.text((1050, 35), "Page 12", fill=(100, 116, 139), font=get_default_font(20))
    draw.line([(60, 75), (width - 60, 75)], fill=(203, 213, 225), width=2)

    # Visa Sticker Container
    sticker_box = [100, 120, width - 100, 680]
    draw.rectangle(sticker_box, fill=(254, 252, 232), outline=(202, 138, 4), width=3)

    # Sticker Header
    draw.text((140, 140), "SCHENGEN VISA / VISA SCHENGEN", fill=(133, 77, 14), font=get_default_font(24))
    draw.text((800, 140), "FRA99823145", fill=(180, 83, 9), font=get_default_font(26))

    # Visa details
    details = [
        ("VALID FOR / VALABLE POUR", "ETATS SCHENGEN", 140, 200),
        ("FROM / DU", "01-03-2022", 140, 270),
        ("UNTIL / AU", "01-09-2022", 450, 270),
        ("NUMBER OF ENTRIES / NOMBRE D'ENTREES", "MULT", 750, 270),
        ("DURATION OF STAY / DUREE DE SEJOUR", "90 DAYS", 140, 340),
        ("TYPE OF VISA / TYPE DE VISA", "C (SHORT STAY TOURIST)", 450, 340),
        ("ISSUED IN / DELIVRE A", "PARIS", 140, 410),
        ("ON / LE", "01-03-2022", 450, 410),
        ("PASSPORT NUMBER / NUMERO DE PASSEPORT", "L898902C3", 140, 480),
        ("SURNAME, NAME / NOM, PRENOM", "TRAVELER, ALEX MORGAN", 450, 480),
    ]

    for label, val, x, y in details:
        draw.text((x, y), label, fill=(161, 98, 7), font=label_font)
        draw.text((x, y + 22), val, fill=(30, 41, 59), font=val_font)

    # Specimen stamp across visa
    draw.text((320, 560), "SPECIMEN - SAMPLE VISA ONLY", fill=(220, 38, 38), font=get_default_font(32))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Generated specimen visa page: {output_path}")


def create_specimen_stamps_page(output_path: str):
    """Generate specimen page with entry and exit stamps."""
    width, height = 1200, 800
    img = Image.new("RGB", (width, height), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    title_font = get_default_font(26)
    stamp_title_font = get_default_font(18)
    stamp_text_font = get_default_font(16)

    # Page Header
    draw.text((60, 35), "ENTRIES / EXITS - SORTIES / ENTREES", fill=(100, 116, 139), font=title_font)
    draw.text((1050, 35), "Page 14", fill=(100, 116, 139), font=get_default_font(20))
    draw.line([(60, 75), (width - 60, 75)], fill=(203, 213, 225), width=2)

    # Stamp 1: France Entry (CDG) - 2022-04-10 (Blue rectangle)
    draw.rectangle([100, 120, 420, 320], outline=(37, 99, 235), width=3)
    draw.text((120, 140), "FRANCE - BORDER CONTROL", fill=(37, 99, 235), font=stamp_title_font)
    draw.text((120, 180), "--> [ENTRY / ENTREE]", fill=(37, 99, 235), font=stamp_text_font)
    draw.text((120, 220), "DATE: 2022-04-10", fill=(30, 58, 138), font=get_default_font(22))
    draw.text((120, 260), "PORT: PARIS - CDG AIRPORT", fill=(37, 99, 235), font=stamp_text_font)

    # Stamp 2: France Exit (CDG) - 2022-04-24 (Green oval)
    draw.ellipse([480, 120, 800, 320], outline=(22, 163, 74), width=3)
    draw.text((530, 145), "FRANCE - DEPARTURE", fill=(22, 163, 74), font=stamp_title_font)
    draw.text((540, 185), "<-- [EXIT / SORTIE]", fill=(22, 163, 74), font=stamp_text_font)
    draw.text((530, 220), "DATE: 2022-04-24", fill=(20, 83, 45), font=get_default_font(22))
    draw.text((530, 260), "PORT: PARIS - CDG AIRPORT", fill=(22, 163, 74), font=stamp_text_font)

    # Stamp 3: UK Entry (LHR) - 2023-08-12 (Dark blue rounded)
    draw.rectangle([100, 400, 420, 600], outline=(30, 41, 59), width=3)
    draw.text((120, 420), "UK BORDER FORCE", fill=(30, 41, 59), font=stamp_title_font)
    draw.text((120, 460), "HEATHROW AIRPORT (LHR)", fill=(30, 41, 59), font=stamp_text_font)
    draw.text((120, 500), "IMMIGRATION OFFICER - 12 AUG 2023", fill=(15, 23, 42), font=get_default_font(18))
    draw.text((120, 540), "LEAVE TO ENTER FOR 6 MONTHS", fill=(71, 85, 105), font=stamp_text_font)

    # Stamp 4: UK Exit (LGW) - 2023-08-26 (Dark blue circle)
    draw.ellipse([480, 400, 800, 600], outline=(71, 85, 105), width=3)
    draw.text((520, 430), "UK BORDER - GATWICK (LGW)", fill=(71, 85, 105), font=stamp_title_font)
    draw.text((560, 470), "DEPARTURE / EMBARKED", fill=(71, 85, 105), font=stamp_text_font)
    draw.text((550, 510), "DATE: 26 AUG 2023", fill=(15, 23, 42), font=get_default_font(20))

    # Stamp 5: UAE Dubai Entry - 2024-01-05 (Purple rectangle)
    draw.rectangle([840, 120, 1140, 320], outline=(147, 51, 234), width=3)
    draw.text((855, 140), "UNITED ARAB EMIRATES", fill=(147, 51, 234), font=stamp_title_font)
    draw.text((855, 180), "DUBAI AIRPORT (DXB)", fill=(147, 51, 234), font=stamp_text_font)
    draw.text((855, 220), "ENTRY: 05-01-2024", fill=(88, 28, 135), font=get_default_font(20))
    draw.text((855, 260), "GDRFA IMMIGRATION", fill=(147, 51, 234), font=stamp_text_font)

    # Stamp 6: UAE Dubai Exit - 2024-01-12 (Red rounded)
    draw.rectangle([840, 400, 1140, 600], outline=(220, 38, 38), width=3)
    draw.text((855, 420), "UNITED ARAB EMIRATES", fill=(220, 38, 38), font=stamp_title_font)
    draw.text((855, 460), "DUBAI AIRPORT (DXB)", fill=(220, 38, 38), font=stamp_text_font)
    draw.text((855, 500), "EXIT: 12-01-2024", fill=(153, 27, 27), font=get_default_font(20))
    draw.text((855, 540), "DEPARTURE STAMP", fill=(220, 38, 38), font=stamp_text_font)

    # Watermark
    draw.text((350, 680), "SPECIMEN TRAVEL STAMPS - FOR SYSTEM TESTING ONLY", fill=(203, 213, 225), font=get_default_font(22))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Generated specimen stamps page: {output_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    create_specimen_bio_page(os.path.join(base_dir, "specimen_passport_bio.png"))
    create_specimen_visa_page(os.path.join(base_dir, "specimen_visas_page.png"))
    create_specimen_stamps_page(os.path.join(base_dir, "specimen_stamps_page.png"))

