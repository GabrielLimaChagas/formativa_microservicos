from database import db

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    pipelines_count = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "pipelinesCount": self.pipelines_count
        }
