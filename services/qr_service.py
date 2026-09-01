import random
import string
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode
from core.config import QR_DIR

def generate_student_token() -> str:
    """Generate non-guessable student ID token (e.g. LIB-8F4K2M)."""
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"LIB-{random_chars}"

def generate_qr_image(payload: str, box_size: int = 10, border: int = 2) -> Image.Image:
    """Generate standard QR Code PIL Image from text payload."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e1b4b", back_color="#ffffff").convert('RGB')
    return img

def generate_student_id_card(student_id: str, student_name: str, seat_number: str, library_name: str = "Apex Study Library") -> Path:
    """
    Generate a high-resolution, printable student attendance pass card.
    Saves to data/qr_cards/{student_id}.png and returns path.
    """
    card_w, card_h = 500, 680
    card = Image.new("RGB", (card_w, card_h), "#ffffff")
    draw = ImageDraw.Draw(card)

    # Header background gradient or bar
    draw.rectangle([(0, 0), (card_w, 100)], fill="#3730a3")
    
    # Border
    draw.rounded_rectangle([(8, 8), (card_w - 8, card_h - 8)], radius=20, outline="#c7d2fe", width=3)

    # Header text
    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_sub = ImageFont.truetype("arial.ttf", 14)
        font_name = ImageFont.truetype("arialbd.ttf", 22)
        font_seat = ImageFont.truetype("arialbd.ttf", 18)
        font_token = ImageFont.truetype("cour.ttf", 16)
        font_footer = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_name = font_title
        font_seat = font_title
        font_token = font_title
        font_footer = font_title

    # Header Title
    draw.text((card_w // 2, 40), library_name.upper(), fill="#ffffff", font=font_title, anchor="mm")
    draw.text((card_w // 2, 72), "OFFICIAL STUDENT ATTENDANCE PASS", fill="#c7d2fe", font=font_sub, anchor="mm")

    # Generate and paste QR Code in center
    qr_img = generate_qr_image(student_id, box_size=8, border=2)
    qr_w, qr_h = qr_img.size
    qr_pos = ((card_w - qr_w) // 2, 130)
    card.paste(qr_img, qr_pos)

    # Draw QR frame
    draw.rectangle([(qr_pos[0] - 4, qr_pos[1] - 4), (qr_pos[0] + qr_w + 4, qr_pos[1] + qr_h + 4)], outline="#e0e7ff", width=2)

    # Student Info section
    info_top = qr_pos[1] + qr_h + 30
    draw.text((card_w // 2, info_top), student_name, fill="#0f172a", font=font_name, anchor="mm")
    
    # Seat Badge
    seat_badge_w, seat_badge_h = 180, 40
    seat_x = (card_w - seat_badge_w) // 2
    seat_y = info_top + 25
    draw.rounded_rectangle([(seat_x, seat_y), (seat_x + seat_badge_w, seat_y + seat_badge_h)], radius=10, fill="#e0e7ff")
    draw.text((card_w // 2, seat_y + 20), f"SEAT: {seat_number}", fill="#3730a3", font=font_seat, anchor="mm")

    # Token ID
    draw.text((card_w // 2, seat_y + 65), f"Scan Token: {student_id}", fill="#64748b", font=font_token, anchor="mm")

    # Footer note
    draw.text((card_w // 2, card_h - 30), "Present this QR card at the webcam station upon entry/exit.", fill="#94a3b8", font=font_footer, anchor="mm")

    output_path = QR_DIR / f"{student_id}.png"
    card.save(output_path, "PNG")
    return output_path
