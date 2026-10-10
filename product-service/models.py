from database import db

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Integer, nullable=False, default=0)  # Valor em centavos (ex: 25999 = R$ 259,99)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "price": self.price
        }
