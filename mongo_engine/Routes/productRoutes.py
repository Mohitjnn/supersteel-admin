from fastapi import APIRouter, HTTPException, Depends
import os
from dotenv import load_dotenv
from typing import List
from pymongo.database import Database
from bson import ObjectId
from mongo_engine.models.pydantic_models import (
    ProductModel,
    ProductSummaryModel,
BestSellerModel
)
from mongo_engine.db import get_db

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


@router.get("/products", response_model=List[ProductSummaryModel])
async def get_products_by_category(base_url: str = BASE_URL, category_name: str = None):
    """
    Get products by category, returning only title, subtitle, and first image for scalability.
    """
    try:
        db = get_db()

        # Filter by category name if provided
        if category_name:
            category = db.category.find_one({"name": category_name})
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

            # Fetch only the necessary fields
            cursor = db.product.find(
                {"category": category["_id"]},
                {
                    "title": 1,
                    "subtitle": 1,
                    "images": {"$slice": 1},
                },  # Projection to fetch only the first image
            )
        else:
            # Fetch all products if no category filter is applied, with projection
            cursor = db.product.find(
                {}, {"title": 1, "subtitle": 1, "images": {"$slice": 1}}
            )

        # Serialize the list of products
        products = serialize_list(cursor, base_url, db)
        return products

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_name}", response_model=ProductModel)
async def get_product(product_name: str, base_url: str = BASE_URL):
    """
    Get a single product by ID.
    """
    try:
        db = get_db()
        # if not ObjectId.is_valid(product_id):
        #     raise HTTPException(status_code=400, detail="Invalid product ID format")

        product = db.product.find_one({"title": product_name})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return serialize_doc(
            product, base_url, db
        )  # Ensure ObjectIds are converted to strings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bestsellers", response_model=List[BestSellerModel])
async def get_bestsellers(base_url: str = BASE_URL):
    """
    Get all products marked as bestsellers (best_seller: true), returning only
    title, price, and the first image for scalability.
    """
    try:
        db = get_db()

        # Query the products collection for bestsellers, fetching only the necessary fields
        cursor = db.product.find(
            {"best_seller": True},
            {
                "title": 1,             # Only fetch the title
                "price": 1,             # Only fetch the price
                "images": {"$slice": 1}  # Fetch only the first image
            }
        )

        # Serialize the products with the base_url for image handling
        bestsellers = serialize_list(cursor, base_url, db)
        return bestsellers

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))