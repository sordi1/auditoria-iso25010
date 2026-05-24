import subprocess
import os
import time
import threading
import json
import signal


class EficienciaDesempenho:
    """
    Modulo II - Eficiencia de Desempenho (ISO 25010).
    Benchmarking de rotas HTTP e analise de latencia por carga.
    """

    CARGAS = [100, 500, 1000, 5000]
    TIMEOUT_SUBIDA = 60
    PORTA_PADRAO = 8080

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.processo = None
        self.base_url = f"http://localhost:{self.PORTA_PADRAO}"

    def _tem_pom(self) -> bool:
        return os.path.exists(os.path.join(self.repo_path, "pom.xml"))

    def iniciar_aplicacao(self) -> bool:
        if not self._tem_pom():
            print("[Modulo II] pom.xml nao encontrado - benchmark ignorado.")
            return False

        print("[Modulo II] Compilando e iniciando aplicacao (mvn spring-boot:run)...")
        try:
            self.processo = subprocess.Popen(
                ["mvn", "spring-boot:run", "-q"],
                cwd=self.repo_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=(os.name == "nt"),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            )
        except FileNotFoundError:
            print("[Modulo II] Maven nao encontrado no PATH.")
            return False

        return self._aguardar_subida()

    def _aguardar_subida(self) -> bool:
        import urllib.request
        inicio = time.time()
        while time.time() - inicio < self.TIMEOUT_SUBIDA:
            try:
                urllib.request.urlopen(f"{self.base_url}/actuator/health", timeout=2)
                print("[Modulo II] Aplicacao respondendo.")
                return True
            except Exception:
                pass
            try:
                urllib.request.urlopen(self.base_url, timeout=2)
                print("[Modulo II] Aplicacao respondendo.")
                return True
            except Exception:
                pass
            time.sleep(1)
        print("[Modulo II] Timeout: aplicacao nao subiu a tempo.")
        return False

    def parar_aplicacao(self):
        if self.processo:
            try:
                if os.name == "nt":
                    subprocess.call(
                        ["taskkill", "/F", "/T", "/PID", str(self.processo.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    os.killpg(os.getpgid(self.processo.pid), signal.SIGTERM)
                self.processo.wait(timeout=15)
            except Exception:
                try:
                    self.processo.kill()
                except Exception:
                    pass
            self.processo = None
            time.sleep(3)  # aguarda o SO liberar os arquivos
            print("[Modulo II] Aplicacao encerrada.")

    def _descobrir_rotas(self) -> list:
        import urllib.request
        rotas = []

        try:
            resp = urllib.request.urlopen(f"{self.base_url}/actuator/mappings", timeout=3)
            data = json.loads(resp.read())
            contexts = data.get("contexts", {})
            for ctx in contexts.values():
                for mapping in ctx.get("mappings", {}).get("dispatcherServlets", {}).get("dispatcherServlet", []):
                    details = mapping.get("details", {})
                    req_info = details.get("requestMappingConditions", {})
                    patterns = req_info.get("patterns", [])
                    methods = req_info.get("methods", ["GET"])
                    if patterns and "GET" in methods:
                        rotas.append(patterns[0])
        except Exception:
            pass

        if not rotas:
            try:
                resp = urllib.request.urlopen(f"{self.base_url}/v3/api-docs", timeout=3)
                spec = json.loads(resp.read())
                for path, methods in spec.get("paths", {}).items():
                    if "get" in methods:
                        rotas.append(path)
            except Exception:
                pass

        if not rotas:
            rotas = ["/actuator/health", "/"]

        rotas_filtradas = [r for r in rotas if not r.startswith("/actuator")][:5]
        if not rotas_filtradas:
            rotas_filtradas = ["/actuator/health"]

        return rotas_filtradas

    def _medir_tempo(self, rota: str) -> float:
        import urllib.request
        try:
            inicio = time.perf_counter()
            urllib.request.urlopen(f"{self.base_url}{rota}", timeout=10)
            fim = time.perf_counter()
            return round((fim - inicio) * 1000, 2)
        except Exception:
            return -1.0

    def executar_benchmark(self, rotas: list) -> dict:
        print("\n[Modulo II] Iniciando benchmarking de rotas...")
        resultados = {}

        for rota in rotas:
            tempos = []
            for _ in range(5):
                t = self._medir_tempo(rota)
                if t >= 0:
                    tempos.append(t)
                time.sleep(0.1)

            if tempos:
                tempos.sort()
                mediana = tempos[len(tempos) // 2]
                resultados[rota] = {
                    "tempo_mediano_ms": mediana,
                    "tempo_min_ms": min(tempos),
                    "tempo_max_ms": max(tempos),
                    "amostras": len(tempos)
                }
                print(f"  {rota}: mediana={mediana}ms  min={min(tempos)}ms  max={max(tempos)}ms")
            else:
                resultados[rota] = {"erro": "Sem resposta"}

        return resultados

    def _requisicoes_paralelas(self, rota: str, n: int) -> float:
        import urllib.request
        tempos = []
        lock = threading.Lock()

        def fazer():
            t = self._medir_tempo(rota)
            if t >= 0:
                with lock:
                    tempos.append(t)

        threads = [threading.Thread(target=fazer) for _ in range(n)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        return round(sum(tempos) / len(tempos), 2) if tempos else -1.0

    def analisar_latencia(self, rota: str) -> dict:
        print(f"\n[Modulo II] Analise de latencia em '{rota}'...")
        resultado = {}
        latencia_base = None

        for carga in self.CARGAS:
            print(f"  Carga: {carga} requisicoes...", end=" ", flush=True)
            lat = self._requisicoes_paralelas(rota, min(carga, 200))
            if lat < 0:
                print("sem resposta")
                resultado[carga] = {"latencia_ms": -1, "aumento_pct": None}
                continue

            if latencia_base is None:
                latencia_base = lat
                aumento = 0.0
            else:
                aumento = round(((lat - latencia_base) / latencia_base) * 100, 1) if latencia_base > 0 else 0.0

            resultado[carga] = {"latencia_ms": lat, "aumento_pct": aumento}
            print(f"{lat}ms  (+{aumento}%)")

        return resultado

    def rodar_analise(self) -> dict:
        resultado = {"benchmark": {}, "latencia": {}, "status": "nao_executado"}

        subiu = self.iniciar_aplicacao()
        if not subiu:
            self.parar_aplicacao()
            resultado["status"] = "app_nao_iniciado"
            return resultado

        try:
            rotas = self._descobrir_rotas()
            print(f"[Modulo II] Rotas descobertas: {rotas}")

            resultado["benchmark"] = self.executar_benchmark(rotas)

            tempos_validos = {
                r: v["tempo_mediano_ms"]
                for r, v in resultado["benchmark"].items()
                if "tempo_mediano_ms" in v
            }
            rota_alvo = max(tempos_validos, key=tempos_validos.get) if tempos_validos else rotas[0]

            resultado["latencia"] = self.analisar_latencia(rota_alvo)
            resultado["status"] = "ok"

        finally:
            self.parar_aplicacao()

        return resultado
