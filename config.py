import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database Configuration
DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "exam_system.db")
# To use MySQL, change to:
# DATABASE_URL = "mysql+pymysql://username:password@localhost/exam_db"

# Upload folder for scanned images
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# Generated PDFs folder
GENERATED_PAPERS_FOLDER = os.path.join(BASE_DIR, "generated_papers")

# Max upload file size (16 MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Allowed image extensions for upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

# Flask secret key — override with SECRET_KEY env variable in production
SECRET_KEY = os.environ.get("SECRET_KEY", "exam-system-secret-key-change-in-production")

# Debug mode — set to False in production.
# Override via environment variable: DEBUG=1 python app.py
DEBUG = os.environ.get("DEBUG", "0") == "1"
