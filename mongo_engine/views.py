from typing import List, Any
from starlette_admin.contrib.mongoengine import ModelView
from starlette.requests import Request
from pymongo import MongoClient
from gridfs import GridFSBucket
from bson import ObjectId
from mongo_engine.models.models import Product
import os
from dotenv import load_dotenv
from starlette_admin import RequestAction


load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_BUCKET_NAME = os.environ.get("MONGO_BUCKET_NAME")


class ProductView(ModelView):
    fields = [
        "id",
        "title",
        "subtitle",
        "color",
        "description",
        "price",
        "best_seller",
        "images",
        "dimension",
        "weight",
        "created_at",
        "category",
        "variant",
    ]
    exclude_fields_from_list = [
        "description",
        # "images",
    ]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    fields_default_sort = [("price", True)]

    async def delete(self, request: Request, pks: List[Any]) -> int | None:
        # Connect to MongoDB using PyMongo
        client = MongoClient(MONGO_URL)
        db = client[MONGO_DB]
        bucket = GridFSBucket(db, bucket_name=MONGO_BUCKET_NAME)

        for pk in pks:
            product = Product.objects(id=pk).first()
            if product:
                for image in product.images:
                    # Handle both main image and thumbnail files
                    file_ids = [image.image_src._id]

                    # Check if a thumbnail exists
                    if hasattr(image.image_src, "thumbnail_id"):
                        file_ids.append(image.image_src.thumbnail_id)

                    for file_id in file_ids:
                        file_id = ObjectId(str(file_id))
                        try:
                            bucket.delete(file_id)
                            print(f"Deleted image with ID {file_id} successfully.")
                        except Exception as e:
                            print(f"Error deleting image with ID {file_id}: {e}")

                # Delete the product itself
                product.delete()

        client.close()

        return await super().delete(request, pks)


class CategoryView(ModelView):
    fields = ["id", "name", "description", "images"]
    exclude_fields_from_list = ["images", "description"]
    fields_default_sort = ["name"]

    def can_delete(self, request: Request) -> bool:
        return False
