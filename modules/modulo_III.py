import subprocess
import os
import xml.etree.ElementTree as ET


class Confiabilidade:
    """
    Módulo III – Confiabilidade / Testabilidade (ISO 25010).

    Executa os testes JUnit via Maven com o plugin JaCoCo e
    extrai a cobertura de linhas total e por arquivo.

    Pontuação: >=80% ALTA | >=50% MEDIA | <50% BAIXA
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _tem_pom(self) -> bool:
        return os.path.exists(os.path.join(self.repo_path, "pom.xml"))

    def _injetar_jacoco_se_necessario(self):
        """
        Se o pom.xml não tiver o plugin JaCoCo, injeta automaticamente.
        """
        pom = os.path.join(self.repo_path, "pom.xml")
        with open(pom, "r", encoding="utf-8", errors="ignore") as f:
            conteudo = f.read()

        if "jacoco" in conteudo.lower():
            return  # já tem

        print("[Módulo III] Injetando plugin JaCoCo no pom.xml...")
        jacoco_plugin = """
        <plugin>
          <groupId>org.jacoco</groupId>
          <artifactId>jacoco-maven-plugin</artifactId>
          <version>0.8.11</version>
          <executions>
            <execution>
              <goals><goal>prepare-agent</goal></goals>
            </execution>
            <execution>
              <id>report</id>
              <phase>test</phase>
              <goals><goal>report</goal></goals>
            </execution>
          </executions>
        </plugin>"""

        # Insere antes do fechamento de </plugins>
        if "</plugins>" in conteudo:
            conteudo = conteudo.replace("</plugins>", jacoco_plugin + "\n        </plugins>", 1)
            with open(pom, "w", encoding="utf-8") as f:
                f.write(conteudo)

    def executar_testes(self) -> bool:
        """Executa mvn test com JaCoCo e retorna True se bem-sucedido."""
        if not self._tem_pom():
            print("[Módulo III] pom.xml não encontrado – cobertura indisponível.")
            return False

        self._injetar_jacoco_se_necessario()

        print("[Módulo III] Rodando testes (mvn clean test jacoco:report)...")
        try:
            result = subprocess.run(
                ["mvn", "clean", "test", "jacoco:report", "-q"],
                cwd=self.repo_path,
                timeout=300,
                shell=(os.name == "nt")
            )
            if result.returncode != 0:
                print("[Módulo III] Testes falharam ou não existem.")
                return False
            return True
        except subprocess.TimeoutExpired:
            print("[Módulo III] Timeout ao executar Maven.")
            return False
        except FileNotFoundError:
            print("[Módulo III] Maven não encontrado no PATH.")
            return False

    def extrair_cobertura(self) -> dict:
        """
        Extrai cobertura total e por arquivo do relatório JaCoCo XML.

        Retorna:
            {
                'total': float,              # cobertura total em %
                'arquivos': { 'Arquivo.java': float }
                'classificacao': str         # ALTA / MEDIA / BAIXA
            }
        """
        xml_path = os.path.join(self.repo_path, "target", "site", "jacoco", "jacoco.xml")

        if not os.path.exists(xml_path):
            print("[Módulo III] Relatório JaCoCo não encontrado.")
            return {"total": 0.0, "arquivos": {}, "classificacao": "SEM_TESTES"}

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Cobertura total
        total_cobertura = 0.0
        for counter in root.findall("counter"):
            if counter.get("type") == "LINE":
                covered = int(counter.get("covered", 0))
                missed  = int(counter.get("missed",  0))
                total   = covered + missed
                if total > 0:
                    total_cobertura = round((covered / total) * 100, 2)
                break

        # Cobertura por arquivo
        arquivos_cobertura = {}
        for package in root.findall("package"):
            for sourcefile in package.findall("sourcefile"):
                nome = sourcefile.get("name")
                for counter in sourcefile.findall("counter"):
                    if counter.get("type") == "LINE":
                        covered = int(counter.get("covered", 0))
                        missed  = int(counter.get("missed",  0))
                        total   = covered + missed
                        cobertura = round((covered / total) * 100, 2) if total > 0 else 0.0
                        arquivos_cobertura[nome] = cobertura
                        break

        classificacao = (
            "ALTA"  if total_cobertura >= 80 else
            "MEDIA" if total_cobertura >= 50 else
            "BAIXA"
        )

        return {
            "total": total_cobertura,
            "arquivos": arquivos_cobertura,
            "classificacao": classificacao
        }

    def rodar_analise(self) -> dict:
        """Executa os testes e retorna os dados de cobertura."""
        print("\n[Módulo III] Iniciando análise de confiabilidade (cobertura)...")
        sucesso = self.executar_testes()
        dados = self.extrair_cobertura()

        if sucesso:
            print(f"  Cobertura total: {dados['total']:.2f}% [{dados['classificacao']}]")
        else:
            print("  Cobertura: indisponível (sem testes ou Maven ausente)")

        return dados
