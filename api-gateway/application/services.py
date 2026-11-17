import json
from typing import Dict, Any, Tuple
from application.interfaces import HttpClient

class SummaryService:
    def __init__(self, http_client: HttpClient, customers_service_url: str, products_service_url: str):
        self._http_client = http_client
        self._customers_url = customers_service_url.rstrip("/")
        self._products_url = products_service_url.rstrip("/")

    def get_summary(self) -> Dict[str, Any]:
        summary = {
            "customersCount": 0,
            "productsCount": 0,
            "totalCatalogValueCents": 0,
            "totalPipelinesCount": 0,
        }
        try:
            c_res = self._http_client.get(f"{self._customers_url}/customers", timeout=3.0)
            if c_res.status_code == 200:
                customers_data = json.loads(c_res.content.decode("utf-8"))
                summary["customersCount"] = len(customers_data)
                summary["totalPipelinesCount"] = sum(int(c.get("pipelinesCount", 0)) for c in customers_data)
        except Exception:
            pass

        try:
            p_res = self._http_client.get(f"{self._products_url}/products", timeout=3.0)
            if p_res.status_code == 200:
                products_data = json.loads(p_res.content.decode("utf-8"))
                summary["productsCount"] = len(products_data)
                summary["totalCatalogValueCents"] = sum(int(p.get("price", 0)) for p in products_data)
        except Exception:
            pass

        return summary

class HealthService:
    def __init__(self, http_client: HttpClient, customers_service_url: str, products_service_url: str):
        self._http_client = http_client
        self._customers_url = customers_service_url.rstrip("/")
        self._products_url = products_service_url.rstrip("/")

    def check_health(self) -> Tuple[Dict[str, Any], int]:
        services_status = {}

        # Check Customer Service
        try:
            c_res = self._http_client.get(f"{self._customers_url}/health", timeout=2.0)
            services_status["customers"] = "UP" if c_res.status_code == 200 else f"ERROR ({c_res.status_code})"
        except Exception:
            services_status["customers"] = "DOWN"

        # Check Product Service
        try:
            p_res = self._http_client.get(f"{self._products_url}/health", timeout=2.0)
            services_status["products"] = "UP" if p_res.status_code == 200 else f"ERROR ({p_res.status_code})"
        except Exception:
            services_status["products"] = "DOWN"

        overall_status = "UP" if all(v == "UP" for v in services_status.values()) else "DEGRADED"

        response_body = {
            "gateway": "UP",
            "status": overall_status,
            "services": services_status
        }
        status_code = 200 if overall_status == "UP" else 207

        return response_body, status_code
