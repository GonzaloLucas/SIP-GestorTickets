import sys
from pathlib import Path

import qrcode


OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "usuarios"
    / "static"
    / "usuarios"
    / "qr-assistech.png"
)


def main():
    if len(sys.argv) != 2:
        print("Uso: python generate_qr.py https://tu-usuario.pythonanywhere.com")
        raise SystemExit(1)

    site_url = sys.argv[1].strip()
    if not site_url.startswith(("http://", "https://")):
        print("La URL debe empezar con http:// o https://")
        raise SystemExit(1)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(site_url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_PATH)
    print(f"QR generado para {site_url}: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
