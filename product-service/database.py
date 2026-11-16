# Backward compatibility bridge to infrastructure
from infrastructure.database import db
from infrastructure.models import ProductModel as Product

__all__ = ["db", "Product"]
