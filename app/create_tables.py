from app.database import Base, engine

# Import all models
from app.models import User, Chat, PDFDocument, Message, Summary


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")


if __name__ == "__main__":
    create_tables()