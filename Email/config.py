import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_ADDRESS = os.getenv("itzpasha7@gmail.com")
EMAIL_PASSWORD = os.getenv("ammu")
