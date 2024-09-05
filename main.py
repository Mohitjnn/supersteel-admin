from mongoengine import connect
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette_admin import DropDown
from starlette_admin import I18nConfig
from starlette_admin.contrib.mongoengine import Admin
from starlette_admin.views import Link

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")

# from app.config import config
from mongo_engine.models import Product, Category
from mongo_engine.views import CategoryView, ProductView

__all__ = ["admin", "connection"]

connection = connect(host=MONGO_URL)

admin = Admin(
    "MongoEngine Admin",
    base_url="/",
    route_name="admin-mongoengine",
    logo_url="https://preview.tabler.io/static/logo-white.svg",
    login_logo_url="https://preview.tabler.io/static/logo.svg",
    templates_dir="templates/admin/mongoengine",
    i18n_config=I18nConfig(language_switcher=["en", "fr"]),
)

admin.add_view(
    DropDown(
        label="Store",
        icon="fa fa-store",
        views=[ProductView(Product), CategoryView(Category, label="Categories")],
    )
)

admin.add_view(Link(label="Go Back to Home", icon="fa fa-link", url="/"))


app = FastAPI()

admin.mount_to(app)
