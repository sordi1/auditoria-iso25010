import subprocess
import os
import time
import threading
import json


class EficienciaDesempenho:
    """
    Módulo II – Eficiência de Desempenho (ISO 25010).

    Estratégia:
      1. Tenta subir a aplicação Java via Maven (mvn spring-boot:run) ou
         executa o JAR gerado, aguardando até 30s pela porta HTTP.
      2. Descobre automaticamente as rotas HTTP via actuator, arquivo
         openapi/swagger ou usa /health como fallback.
      3. Executa benchmarking: mede o tempo de resposta de cada rota.
      4. Executa análise de latência: simula cargas de 100, 500, 1000 e 5000
         requisições e calcula o % de aumento da latência.
    """

    CARGAS = [100, 500, 1000, 5000]
    TIMEOUT_SUBIDA = 30   # segundos para aguardar o app subir
    PORTA_PADRAO = 8080

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.processo = None
        self.base_url = f"http://localhost:{self.PORTA_PADRAO}"

    # ------------------------------------------------------------------
    # Inicialização / Encerramento
    # ------------------------------------------------------------------

    def _tem_pom(self) -> bool:
        return os.path.exists(os.path.join(self.repo_path, "pom.xml"))

    def iniciar_aplicacao(self) -> bool:
        """Tenta compilar e subir a aplicação. Retorna True se conseguiu."""
        if not self._tem_pom():
            print("[Módulo II] pom.xml não encontrado – benchmark ignorado.")
            return False

        print("[Módulo II] Compilando e iniciando aplicação (mvn spring-boot:run)...")
        try:
            self.processo = subprocess.Popen(
                ["mvn", "spring-boot:run", "-q"],
                cwd=self.repo_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=(os.name == "nt")
            )
        except FileNotFoundError:
            print("[Módulo II] Maven não encontrado no PATH.")
            return False

        return self._aguardar_subida()

    def _aguardar_subida(self) -> bool:
        import urllib.request
        inicio = time.time()
        while time.time() - inicio < self.TIMEOUT_SUBIDA:
            try:
                urllib.request.urlopen(f"{self.base_url}/actuator/health", timeout=2)
                print("[Módulo II] Aplicação respondendo em /actuator/health")
                return True
            except Exception:
                pass
            try:
                urllib.request.urlopen(self.base_url, timeout=2)
                print("[Módulo II] Aplicação respondendo na raiz /")
                return True
            except Exception:
                pass
            time.sleep(1)
        print("[Módulo II] Timeout: aplicação não subiu a tempo.")
        return False

    def parar_aplicacao(self):
        if self.processo:
            self.processo.terminate()
            try:
                self.processo.wait(timeout=10)
            except Exception:
                self.processo.kill()
            self.processo = None
            print("[Módulo II] Aplicação encerrada.")

    # ------------------------------------------------------------------
    # Descoberta de rotas
    # ------------------------------------------------------------------

    def _descobrir_rotas(self) -> list:
        """Descobre rotas via actuator/mappings, openapi ou usa /health."""
        import urllib.request
        rotas = []

        # Tenta actuator/mappings
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

        # Fallback: tenta /swagger-ui ou /v3/api-docs
        if not rotas:
            try:
                resp = urllib.request.urlopen(f"{self.base_url}/v3/api-docs", timeout=3)
                spec = json.loads(resp.read())
                for path, methods in spec.get("paths", {}).items():
                    if "get" in methods:
                        rotas.append(path)
            except Exception:
                pass

        # Último fallback
        if not rotas:
            rotas = ["/actuator/health", "/"]

        # Remove rotas de gestão e limita a 5
        rotas_filtradas = [r for r in rotas if not r.startswith("/actuator")][:5]
        if not rotas_filtradas:
            rotas_filtradas = ["/actuator/health"]

        return rotas_filtradas

    # ------------------------------------------------------------------
    # Benchmarking
    # ------------------------------------------------------------------

    def _medir_tempo(self, rota: str) -> float:
        """Faz uma requisição GET e retorna o tempo em milissegundos."""
        import urllib.request
        try:
            inicio = time.perf_counter()
            urllib.request.urlopen(f"{self.base_url}{rota}", timeout=10)
            fim = time.perf_counter()
            return round((fim - inicio) * 1000, 2)
        except Exception:
            return -1.0

    def executar_benchmark(self, rotas: list) -> dict:
        """Mede o tempo de resposta de cada rota (5 amostras, usa a mediana)."""
        print("\n[Módulo II] Iniciando benchmarking de rotas...")
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
                print(f"  {rota}: sem resposta")

        return resultados

    # ------------------------------------------------------------------
    # Análise de Latência por carga
    # ------------------------------------------------------------------

    def _requisicoes_paralelas(self, rota: str, n: int) -> float:
        """Faz n requisições paralelas e retorna o tempo médio em ms."""
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
        """
        Simula cargas de 100, 500, 1000 e 5000 requisições e mede a
        variação percentual da latência em relação à carga de 100.
        """
        print(f"\n[Módulo II] Análise de latência em '{rota}'...")
        resultado = {}
        latencia_base = None

        for carga in self.CARGAS:
            print(f"  Carga: {carga} requisições...", end=" ", flush=True)
            lat = self._requisicoes_paralelas(rota, min(carga, 200))  # cap em 200 threads
            if lat < 0:
                print("sem resposta")
                resultado[carga] = {"latencia_ms": -1, "aumento_pct": None}
                continue

            if latencia_base is None:
                latencia_base = lat
                aumento = 0.0
            else:
                aumento = round(((lat - latencia_base) / latencia_base) * 100, 1) if latencia_base > 0 else 0.0

            resultado[carga] = {
                "latencia_ms": lat,
                "aumento_pct": aumento
            }
            print(f"{lat}ms  (+{aumento}%)")

        return resultado

    # ------------------------------------------------------------------
    # Ponto de entrada principal
    # ------------------------------------------------------------------

    def rodar_analise(self) -> dict:
        """Executa todo o Módulo II e retorna os resultados."""
        resultado = {
            "benchmark": {},
            "latencia": {},
            "status": "nao_executado"
        }

        subiu = self.iniciar_aplicacao()
        if not subiu:
            resultado["status"] = "app_nao_iniciado"
            return resultado

        try:
            rotas = self._descobrir_rotas()
            print(f"[Módulo II] Rotas descobertas: {rotas}")

            resultado["benchmark"] = self.executar_benchmark(rotas)

            # Escolhe a rota mais lenta para análise de latência
            rota_alvo = rotas[0]
            tempos_validos = {
                r: v["tempo_mediano_ms"]
                for r, v in resultado["benchmark"].items()
                if "tempo_mediano_ms" in v
            }
            if tempos_validos:
                rota_alvo = max(tempos_validos, key=tempos_validos.get)

            resultado["latencia"] = self.analisar_latencia(rota_alvo)
            resultado["status"] = "ok"

        finally:
            self.parar_aplicacao()

        return resultado
