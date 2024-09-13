from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AuthProvider, AdminUser
from starlette_admin.exceptions import LoginFailed
from mongoengine import connect
from mongo_engine.models.models import (
    Admin,
)  # Ensure your models.py contains the Admin model
from bcrypt import checkpw
from typing import Optional
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB Atlas
connect(db=os.getenv("MONGO_DB"), host=os.getenv("MONGO_URL"))


class MyAuthProvider(AuthProvider):

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        # Retrieve the admin from the MongoDB database using MongoEngine
        admin = Admin.objects(username=username).first()

        # Check if the admin exists and if the password is correct
        if not admin or not checkpw(
            password.encode("utf-8"), admin.password_hash.encode("utf-8")
        ):
            raise LoginFailed("Invalid username or password")

        # Store session details
        request.session.update({"username": admin.username})
        return response

    async def is_authenticated(self, request: Request) -> bool:
        # Check if the session contains a username
        username = request.session.get("username")
        if username:
            admin = Admin.objects(username=username).first()
            if admin:
                request.state.user = admin
                return True
        return False

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        # Retrieve the admin user from request state
        user = request.state.user
        if user:
            return AdminUser(username=user.username)
        return None

    async def logout(self, request: Request, response: Response) -> Response:
        # Clear the session to log out the admin
        request.session.clear()
        return response
