from mongoengine import connect
from mongo_engine.models.models import Admin
from bcrypt import hashpw, gensalt
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB Atlas using mongoengine
connect(
    db=os.getenv("MONGO_DB"),
    host=os.getenv("MONGO_CONNECTION_URL"),
)


# Create an admin user
def create_admin_user(username: str, password: str):
    try:
        # Check if an admin with the same username already exists
        if Admin.objects(username=username).first():
            print(f"Admin user with username '{username}' already exists.")
            return

        # Hash the password using bcrypt
        password_hash = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

        # Create and save the new admin user
        admin = Admin(username=username, password_hash=password_hash)
        admin.save()

        print(f"Admin user created with username: {admin.username}")
    except Exception as e:
        print(f"Error creating admin user: {e}")


# Usage
if __name__ == "__main__":
    username = "Replace with desired username"
    password = "Replace with desired password"
    create_admin_user(username, password)
