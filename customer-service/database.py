# Backward compatibility bridge to infrastructure
from infrastructure.database import db
from infrastructure.models import CustomerModel as Customer

__all__ = ["db", "Customer"]
