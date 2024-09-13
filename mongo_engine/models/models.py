import mongoengine as me
from datetime import datetime
from enum import Enum
from starlette.requests import Request
from bcrypt import hashpw, gensalt


class Unit(str, Enum):
    m = "m"
    cm = "cm"
    mm = "mm"


class WeightUnit(str, Enum):
    kg = "kg"
    g = "g"


class Dimension(me.EmbeddedDocument):
    width = me.IntField(min_value=10, max_value=100)
    height = me.IntField(min_value=10, max_value=100)
    unit = me.EnumField(Unit)


class Weight(me.EmbeddedDocument):
    Weight = me.IntField(min_value=1)
    unit = me.EnumField(WeightUnit)


class Image(me.EmbeddedDocument):
    id = me.StringField(
        required=True
    )  # ID corresponds to the color of the product variant
    image_src = me.ImageField(
        thumbnail_size=(128, 128), required=True
    )  # Holds the ObjectId of the image in GridFS


class Product(me.Document):
    title = me.StringField(min_length=3)
    subtitle = me.StringField()
    description = me.ListField(me.StringField())
    color = me.StringField()
    price = me.DecimalField(min_value=0.01)
    best_seller = me.BooleanField(default=False)
    images = me.ListField(me.EmbeddedDocumentField(Image))  # Allows multiple images
    dimension = me.EmbeddedDocumentField(Dimension)
    weight = me.EmbeddedDocumentField(Weight)
    created_at = me.DateTimeField(default=datetime.utcnow)
    category = me.ReferenceField("Category")

    def save(self, *args, **kwargs):
        # Generate IDs for images in the format "Image01", "Image02", ...
        for index, image in enumerate(self.images):
            image.id = f"Image{index + 1:02}"
        super().save(*args, **kwargs)  # Call the parent save method


class Admin(me.Document):
    username = me.StringField(required=True, unique=True)
    password_hash = me.StringField(required=True)

    @classmethod
    def create_admin(cls, username: str, password: str):
        # Hash the password using bcrypt
        password_hash = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")
        # Create and save the new admin user
        admin = cls(username=username, password_hash=password_hash)
        admin.save()
        return admin


class Category(me.Document):
    name = me.StringField(min_length=3, unique=True)
    description = me.StringField(min_length=3)
    images = me.ListField(me.EmbeddedDocumentField(Image), max_length=3)

    def __admin_repr__(self, request: Request):
        return self.name
