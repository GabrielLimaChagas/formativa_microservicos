from infrastructure.database import db

class ProductModel(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Integer, nullable=False, default=0)

class AuditLogModel(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(80), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "eventType": self.event_type,
            "payload": self.payload,
            "createdAt": str(self.created_at) if self.created_at else None
        }
