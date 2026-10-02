"""Project-wide paths and configuration, loaded from the repo root .env."""

from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_INTERIM_DIR = DATA_DIR / "interim"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
