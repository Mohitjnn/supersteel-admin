from starlette.requests import Request
from starlette_admin.contrib.mongoengine import ModelView

from mongo_engine.fields import MoneyField
from mongo_engine.models import Product


class ProductView(ModelView):
    fields = [
        "id",
        "title",
        "description",
        MoneyField(
            "price",
            label="Price (USD)",
            help_text="Product price in dollars (US)",
        ),
        "dimension",
        "image",
        "manual",
        "created_at",
        "category",
    ]
    exclude_fields_from_list = [Product.description]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    fields_default_sort = [(Product.price, True)]


class CategoryView(ModelView):
    fields_default_sort = ["name"]

    def can_delete(self, request: Request) -> bool:
        return False
