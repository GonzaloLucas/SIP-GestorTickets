from pathlib import Path

import qrcode


SITE_URL = "https://assistech.pythonanywhere.com"
OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "usuarios"
    / "static"
    / "usuarios"
    / "qr-assistech.png"
)


def main():
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(SITE_URL)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_PATH)
    print(f"QR generado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
