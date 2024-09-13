from fastapi import APIRouter, HTTPException, Depends
import os
from dotenv import load_dotenv
from typing import List
from pymongo.database import Database
from bson import ObjectId
from mongo_engine.models.pydantic_models import CategoryModel
from mongo_engine.db import get_db
from fastapi.responses import StreamingResponse
from gridfs import GridFSBucket

load_dotenv()

router = APIRouter()
BASE_URL = os.environ.get("BASE_URL")


def serialize_doc(doc, base_url: str, db: Database):
    """
    Serialize a MongoDB document to convert ObjectId to string
    and generate URL for images.
    """
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    # Replace category ObjectId with category name
    if "category" in doc and isinstance(doc["category"], ObjectId):
        category = db.category.find_one({"_id": ObjectId(doc["category"])})
        doc["category"] = category["name"] if category else "Unknown"
    if "images" in doc:
        for image in doc["images"]:
            if "image_src" in image and isinstance(image["image_src"], ObjectId):
                image["image_src"] = (
                    f"{base_url}/images/{image['image_src']}"  # Generate image URL
                )
    return doc


def serialize_list(cursor, base_url: str, db: Database):
    return [serialize_doc(doc, base_url, db) for doc in cursor]


@router.get("/categories", response_model=List[CategoryModel])
async def get_all_categories(base_url: str = BASE_URL):
    """
    Get all categories.
    """
    try:
        db = get_db()
        cursor = db.category.find()  # Fetch all categories from 'category' collection
        categories = serialize_list(
            cursor, base_url, db
        )  # Ensure ObjectIds are converted to strings
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/{category_name}", response_model=CategoryModel)
async def get_category(category_name: str, base_url: str = BASE_URL):
    """
    Get a single category by name.
    """
    try:
        db = get_db()

        # Fetch the category based on category_name
        category = db.category.find_one({"name": category_name})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        return serialize_doc(category, base_url, db)  # Serialize the category
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_id}")
async def get_image(image_id: str, db: Database = Depends(get_db)):
    """
    Fetch image by ID from GridFS with custom collections.
    """
    try:
        if not ObjectId.is_valid(image_id):
            raise HTTPException(status_code=400, detail="Invalid image ID format")

        # Specify the custom collection names for GridFS
        grid_fs = GridFSBucket(db, bucket_name="images")

        # Open a download stream for the image
        image_data = grid_fs.open_download_stream(ObjectId(image_id))

        # Retrieve the content type from the file metadata if available
        content_type = (
            image_data.content_type
            if image_data.content_type
            else "application/octet-stream"
        )

        return StreamingResponse(image_data, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
