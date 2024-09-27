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
    If variant is provided, return all products matching that variant.
    If no variant is provided, return all products sorted by the priority of the variant, only if a category is mentioned.
    If the category does not have variants, return products without sorting.
    """
    try:
        db = get_db()

        query = {}
        projection = {
            "title": 1,
            "subtitle": 1,
            "images": {"$slice": 1},
            "variant": 1,
            "category": 1,
        }

        # Step 1: Filter by Category
        if category_name:
            # Case-insensitive search for category name
            category = db.category.find_one(
                {"name": {"$regex": f"^{category_name}$", "$options": "i"}}
            )

            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

            query["category"] = category["_id"]

            # Fetch the variant priorities from the category
            category_variants = category.get("variants", [])

            # Step 2: If a variant is provided, filter by it
            if variant:
                variant_names = [v["variant"].lower() for v in category_variants]
                if variant.lower() in variant_names:
                    query["variant"] = variant
                else:
                    raise HTTPException(
                        status_code=404, detail="Variant not found in the category"
                    )

        # Step 3: Fetch products based on query
        cursor = db.product.find(query, projection)
        products = serialize_list(cursor, base_url, db)

        # Step 4: If category is mentioned and no variant is provided, sort by variant priority
        if category_name and not variant:
            if category_variants:
                # If the category has variants, assign priority to each product based on the variant's priority
                variant_priority_map = {
                    v["variant"].lower(): v.get("Priority", 0)
                    for v in category_variants
                }

                # Assign priority to each product based on the variant's priority
                for product in products:
                    product_variant = product.get("variant", "").lower()
                    product["priority"] = variant_priority_map.get(product_variant, 0)

                # Sort the products list by the priority field
                products = sorted(products, key=lambda x: x.get("priority", 0))
            else:
                # If no variants exist for the category, return products without sorting
                pass

        # If no category_name or variant is mentioned, return products without sorting
        return products

    except HTTPException as he:
        raise he  # Re-raise HTTP exceptions to be handled by FastAPI
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
