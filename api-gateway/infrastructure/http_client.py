import json
from typing import Dict, Any
import requests
from application.interfaces import HttpClient, HttpResponse

class RequestsHttpClient(HttpClient):
    def forward(
        self,
        method: str,
        target_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: bytes,
        timeout: float = 5.0
    ) -> HttpResponse:
        try:
            resp = requests.request(
                method=method,
                url=target_url,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout
            )
            return HttpResponse(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except requests.exceptions.ConnectionError:
            err_body = json.dumps({
                "error": "Falha na comunicação com o microsserviço",
                "target": target_url,
                "status": "Service Unavailable"
            }).encode("utf-8")
            return HttpResponse(content=err_body, status_code=503, headers={"content-type": "application/json"})
        except requests.exceptions.Timeout:
            err_body = json.dumps({
                "error": "Tempo de requisição ao microsserviço expirou (Gateway Timeout)",
                "target": target_url
            }).encode("utf-8")
            return HttpResponse(content=err_body, status_code=504, headers={"content-type": "application/json"})
        except Exception as e:
            err_body = json.dumps({"error": str(e)}).encode("utf-8")
            return HttpResponse(content=err_body, status_code=500, headers={"content-type": "application/json"})

    def get(self, url: str, timeout: float = 2.0) -> HttpResponse:
        resp = requests.get(url, timeout=timeout)
        return HttpResponse(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )
