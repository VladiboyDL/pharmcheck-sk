#!/usr/bin/env python3
"""Download DDInter and Czech SÚKL data if not already present."""

import os
import urllib.request
import zipfile
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DDINTER_DIR = DATA_DIR / "ddinter_raw"
SUKL_DIR = DATA_DIR / "sukl_cz"


def download_ddinter():
    DDINTER_DIR.mkdir(parents=True, exist_ok=True)
    codes = ["A", "B", "D", "H", "L", "P", "R", "V"]
    for code in codes:
        dest = DDINTER_DIR / f"ddinter_downloads_code_{code}.csv"
        if dest.exists() and dest.stat().st_size > 100:
            continue
        url = f"https://ddinter.scbdd.com/static/media/download/ddinter_downloads_code_{code}.csv"
        print(f"  Sťahujem DDInter kód {code}...")
        urllib.request.urlretrieve(url, str(dest))
    print(f"  DDInter dáta stiahnuté")


def download_sukl():
    SUKL_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = SUKL_DIR / "dlp.zip"
    marker = SUKL_DIR / "dlp_lecivepripravky.csv"
    if marker.exists() and marker.stat().st_size > 1000:
        print("  SÚKL dáta už existujú")
        return
    url = "https://opendata.sukl.cz/soubory/SODERECEPT/DLPAKTUALNI.zip"
    print("  Sťahujem SÚKL databázu...")
    urllib.request.urlretrieve(url, str(zip_path))
    print("  Rozbaľujem...")
    with zipfile.ZipFile(str(zip_path), "r") as z:
        z.extractall(str(SUKL_DIR))
    print("  SÚKL dáta stiahnuté a rozbalené")


if __name__ == "__main__":
    print("1. DDInter v1...")
    download_ddinter()
    print("2. SÚKL CZ...")
    download_sukl()
    print("Hotovo!")
