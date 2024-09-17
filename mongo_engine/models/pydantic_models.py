from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Pydantic model for dimensions of the product
class DimensionModel(BaseModel):
    width: int
    height: int
    unit: str


class WeightModel(BaseModel):
    Weight: int
    unit: str


# Pydantic model for images associated with the product
class ImageModel(BaseModel):
    id: str
    image_src: str  # This will store the actual image URL from GridFS (excluding the thumbnail)

class BestSellerModel(BaseModel):
    title: str
    price: float
    images: List[ImageModel]


class ProductSummaryModel(BaseModel):
    title: str
    subtitle: str
    images: List[ImageModel]


# Full Pydantic model for a Product
class ProductModel(BaseModel):
    id: str = Field(alias="_id")  # MongoDB ObjectId
    title: str
    subtitle: Optional[str]
    description: List[str]
    price: float
    color: str
    best_seller: bool = False
    images: List[ImageModel]  # List of main images
    dimension: DimensionModel
    weight: WeightModel
    created_at: datetime
    category: str  # Storing category ID as a string


# Pydantic model for Category
class CategoryModel(BaseModel):
    id: str = Field(alias="_id")  # MongoDB ObjectId
    name: str
    description: Optional[str] = None
    images: List[ImageModel]  # List of main images
