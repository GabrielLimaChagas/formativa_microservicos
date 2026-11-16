from infrastructure.database import db

class CustomerModel(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    pipelines_count = db.Column(db.Integer, default=0, nullable=False)
