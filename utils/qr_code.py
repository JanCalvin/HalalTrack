import io, qrcode

def make_qr_png_bytes(data: str) -> bytes:
    """
    Generate QR code PNG (bytes) dari string data.
    """
    qr = qrcode.QRCode(
        version=None,              # auto
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()