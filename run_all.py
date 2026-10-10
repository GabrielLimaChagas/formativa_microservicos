"""
Script orquestrador para inicializar todos os microsserviços e o API Gateway simultaneamente.
Execução: python backend/run_all.py
"""
import subprocess
import sys
import os
import time
import signal

SERVICES = [
    {
        "name": "Customer Service",
        "dir": os.path.join(os.path.dirname(__file__), "customer-service"),
        "script": "app.py",
        "port": 5001,
        "env": {"PORT": "5001"}
    },
    {
        "name": "Product Service",
        "dir": os.path.join(os.path.dirname(__file__), "product-service"),
        "script": "app.py",
        "port": 5002,
        "env": {"PORT": "5002"}
    },
    {
        "name": "API Gateway / BFF",
        "dir": os.path.join(os.path.dirname(__file__), "api-gateway"),
        "script": "app.py",
        "port": 5000,
        "env": {
            "PORT": "5000",
            "CUSTOMERS_SERVICE_URL": "http://localhost:5001",
            "PRODUCTS_SERVICE_URL": "http://localhost:5002"
        }
    }
]

processes = []

def stop_services(sig=None, frame=None):
    print("\n[Orquestrador] Encerrando todos os microsserviços...")
    for proc, srv in processes:
        try:
            print(f"[Orquestrador] Finalizando {srv['name']} (PID: {proc.pid})...")
            proc.terminate()
        except Exception:
            pass
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, stop_services)
    signal.signal(signal.SIGTERM, stop_services)

    print("=" * 65)
    print("  INICIALIZANDO ECOSSISTEMA DE MICROSSERVIÇOS (ASC11)")
    print("=" * 65)

    for srv in SERVICES:
        env = os.environ.copy()
        env.update(srv["env"])
        
        print(f"-> Iniciando {srv['name']} na porta {srv['port']}...")
        p = subprocess.Popen(
            [sys.executable, srv["script"]],
            cwd=srv["dir"],
            env=env
        )
        processes.append((p, srv))
        time.sleep(1)

    print("\n" + "=" * 65)
    print("  TODOS OS SERVIÇOS ESTÃO EM EXECUÇÃO:")
    print("  - API Gateway (BFF):      http://localhost:5000")
    print("  - Microsserviço Clientes: http://localhost:5001")
    print("  - Microsserviço Produtos: http://localhost:5002")
    print("  - Health Check Geral:     http://localhost:5000/api/health")
    print("  - Resumo BFF:             http://localhost:5000/api/summary")
    print("=" * 65)
    print("Pressione Ctrl+C para encerrar todos os serviços.\n")

    try:
        while True:
            time.sleep(1)
            for proc, srv in processes:
                poll = proc.poll()
                if poll is not None:
                    print(f"[ALERTA] {srv['name']} finalizou inesperadamente com código {poll}.")
    except KeyboardInterrupt:
        stop_services()

if __name__ == "__main__":
    main()
