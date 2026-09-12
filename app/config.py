import os
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Project paths & environment loading
# -----------------------------------------------------------------------------

# Points to the directory containing app/, uploads/, storage/, and .env
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables explicitly from the project's .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

UPLOAD_DIR = BASE_DIR / "uploads"
STORAGE_DIR = BASE_DIR / "storage"
CHUNKS_DIR = STORAGE_DIR / "chunks"
INDEXES_DIR = STORAGE_DIR / "indexes"

# Create required folders automatically
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
INDEXES_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost/doculens",
)

# -----------------------------------------------------------------------------
# JWT authentication
# -----------------------------------------------------------------------------

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "DocuLensSecureJwtSecretKey2026ChangeThis",
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_DAYS = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_DAYS",
        "7",
    )
)

# -----------------------------------------------------------------------------
# Gemini configuration
# -----------------------------------------------------------------------------

GOOGLE_API_KEY = os.getenv(
    "GOOGLE_API_KEY",
    "",
)

GENERATIVE_MODEL_NAME = os.getenv(
    "GENERATIVE_MODEL_NAME",
    "gemini-2.5-flash",
)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)

# -----------------------------------------------------------------------------
# PDF upload settings
# -----------------------------------------------------------------------------

MAX_FILE_SIZE = int(
    os.getenv(
        "MAX_FILE_SIZE",
        str(10 * 1024 * 1024),
    )
)

# -----------------------------------------------------------------------------
# Text chunking
# -----------------------------------------------------------------------------

CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "500",
    )
)

CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "100",
    )
)

# -----------------------------------------------------------------------------
# Retrieval
# -----------------------------------------------------------------------------

RETRIEVAL_TOP_K = int(
    os.getenv(
        "RETRIEVAL_TOP_K",
        "5",
    )
)

MAX_CONTEXT_LENGTH = int(
    os.getenv(
        "MAX_CONTEXT_LENGTH",
        "12000",
    )
)

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

SUMMARY_CHUNKS = int(
    os.getenv(
        "SUMMARY_CHUNKS",
        "20",
    )
)

MAX_SUMMARY_LENGTH = int(
    os.getenv(
        "MAX_SUMMARY_LENGTH",
        "20000",
    )
)