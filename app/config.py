import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev")
        self.SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/classroom.db")
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.WTF_CSRF_ENABLED = os.getenv("WTF_CSRF_ENABLED", "true").lower() == "true"
        # Uploads
        self.UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/app/instance/uploads")
        self.MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
        self.ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
