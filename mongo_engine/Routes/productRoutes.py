# router.py

from fastapi import APIRouter, HTTPException, Depends, Query
import os
from dotenv import load_dotenv
from typing import List, Optional
from pymongo.database import Database
from bson import ObjectId
from mongo_engine.models.pydantic_models import (
    ProductModel,
    ProductSummaryModel,
    BestSellerModel,
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
async def get_products_by_category(
    base_url: str = Query(default=BASE_URL, description="Base URL for image paths"),
    category_name: Optional[str] = Query(
        default=None, description="Name of the category to filter products"
    ),
    variant: Optional[str] = Query(
        default=None, description="Variant name to filter products within the category"
    ),
):
    """
    Get products by category and optional variant.
    If variant is not provided or doesn't exist within the category, return all products from that category.
    """
    try:
        db = get_db()

        query = {}
        projection = {
            "title": 1,
            "subtitle": 1,
            "images": {"$slice": 1},
        }

        if category_name:
            # Case-insensitive search for category name
            category = db.category.find_one(
                {"name": {"$regex": f"^{category_name}$", "$options": "i"}}
            )
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

            query["category"] = category["_id"]

            if variant:
                # Check if the variant exists within the category's variants (case-insensitive)
                category_variants = [v.lower() for v in category.get("variants", [])]
                if variant.lower() in category_variants:
                    query["variant"] = variant
                else:
                    # Variant does not exist in this category; ignore variant filter
                    variant = None  # Optionally, notify the user

        elif variant:
            # Filter by variant across all categories (case-insensitive)
            query["variant"] = {"$regex": f"^{variant}$", "$options": "i"}

        # Execute the query with the constructed filters
        cursor = db.product.find(query, projection)

        # Serialize the list of products
        products = serialize_list(cursor, base_url, db)
        return products

    except HTTPException as he:
        raise he  # Re-raise HTTP exceptions to be handled by FastAPI
    except Exception as e:
        # Log the exception details for debugging (optional)
        # logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/products/{product_name}", response_model=ProductModel)
async def get_product(
    product_name: str,
    base_url: str = Query(default=BASE_URL, description="Base URL for image paths"),
):
    """
    Get a single product by name.
    """
    try:
        db = get_db()

        # Case-insensitive search for product title
        product = db.product.find_one(
            {"title": {"$regex": f"^{product_name}$", "$options": "i"}}
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return serialize_doc(
            product, base_url, db
        )  # Ensure ObjectIds are converted to strings
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/bestsellers", response_model=List[BestSellerModel])
async def get_bestsellers(
    base_url: str = Query(default=BASE_URL, description="Base URL for image paths")
):
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
                "title": 1,  # Only fetch the title
                "price": 1,  # Only fetch the price
                "images": {"$slice": 1},  # Fetch only the first image
            },
        )

        # Serialize the products with the base_url for image handling
        bestsellers = serialize_list(cursor, base_url, db)
        return bestsellers

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
