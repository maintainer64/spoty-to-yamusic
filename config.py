import os
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
YANDEX_MUSIC_TOKEN = os.getenv("YANDEX_MUSIC_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
TG_BOT = os.getenv("TG_BOT")
