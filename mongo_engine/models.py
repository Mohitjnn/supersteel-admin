import mongoengine as me
from datetime import datetime
from enum import Enum
from starlette.requests import Request
from bson import ObjectId
from pymongo import MongoClient
from gridfs import GridFSBucket


class Unit(str, Enum):
    m = "m"
    cm = "cm"
    mm = "mm"


class Dimension(me.EmbeddedDocument):
    width = me.IntField(min_value=10, max_value=100)
    height = me.IntField(min_value=10, max_value=100)
    unit = me.EnumField(Unit)


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
    description = me.StringField()
    price = me.DecimalField(min_value=0.01)
    best_seller = me.BooleanField(default=False)
    type = me.StringField()  # Example: 'Seating', 'Tables', etc.
    images = me.ListField(me.EmbeddedDocumentField(Image))  # Allows multiple images
    dimension = me.EmbeddedDocumentField(Dimension)
    created_at = me.DateTimeField(default=datetime.utcnow)
    category = me.ReferenceField("Category")

    def save(self, *args, **kwargs):
        # Generate IDs for images in the format "Image01", "Image02", ...
        for index, image in enumerate(self.images):
            image.id = f"Image{index + 1:02}"
        super().save(*args, **kwargs)  # Call the parent save method

    def delete(self, *args, **kwargs):
        # Connect to the MongoDB instance using PyMongo
        client = MongoClient(
            "mongodb+srv://jnmohit29:Mohitjn123@cluster0.lfubgwo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        )  # Replace with your MongoDB connection string
        db = client["furnitureProducts"]  # Replace with your database name
        bucket = GridFSBucket(
            db, bucket_name="images"
        )  # Connect to the correct GridFS bucket

        # Delete all associated GridFS images when the product is deleted
        for image in self.images:
            if image.image_src:
                try:
                    # Convert image.image_src from string to ObjectId
                    file_id = ObjectId(image.image_src.get("$oid", image.image_src))
                    # Use GridFSBucket to delete the file by its ObjectId
                    bucket.delete(file_id)
                    print(f"Deleted image {image.id} successfully with ID {file_id}.")
                except Exception as e:
                    print(
                        f"Error deleting image {image.id} with ID {image.image_src}: {e}"
                    )

        # Call the parent delete method to delete the product document
        super().delete(*args, **kwargs)
        # Close the PyMongo client
        client.close()


class Category(me.Document):
    name = me.StringField(min_length=3, unique=True)
    description = me.StringField(min_length=3)
    images = me.ListField(me.EmbeddedDocumentField(Image), max_length=3)

    def __admin_repr__(self, request: Request):
        return self.name
