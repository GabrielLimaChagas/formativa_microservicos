import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EventConsumer(ABC):
    @abstractmethod
    def start_listening(self) -> None:
        pass

    @abstractmethod
    def process_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        pass

class AuditService:
    def __init__(self, db_session, audit_model):
        self.db_session = db_session
        self.audit_model = audit_model

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
        record = self.audit_model(event_type=event_type, payload=payload_str)
        self.db_session.add(record)
        self.db_session.commit()
        logger.info(f"[AuditService] Evento '{event_type}' registrado com sucesso (ID: {record.id}).")
        return record.to_dict()

    def get_logs(self) -> List[Dict[str, Any]]:
        records = self.audit_model.query.order_by(self.audit_model.id.desc()).all()
        return [r.to_dict() for r in records]
