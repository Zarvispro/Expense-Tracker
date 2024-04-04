from app import app, db

# Import all your models here to ensure they are registered with SQLAlchemy
from app.models import User  # Import all your models


def create_database():
    with app.app_context():
        # Create the database tables
        db.create_all()


if __name__ == "__main__":
    create_database()
