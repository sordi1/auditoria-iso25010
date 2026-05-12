import subprocess
import os
import xml.etree.ElementTree as ET

class Confiabilidade:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def executar_testes(self):
        print("--- Rodando Testes e JaCoCo no projeto alvo ---")
        # Executa mvn test e gera o relatório xml do jacoco
        try:
            subprocess.run(
                ["mvn", "clean", "test", "jacoco:report"],
                cwd=self.repo_path,
                check=True,
                shell=True
            )
            return True
        except subprocess.CalledProcessError:
            print("Erro ao executar Maven no repositório alvo.")
            return False

    def extrair_cobertura(self):
        """
        Extrai a cobertura total e por arquivo do relatório JaCoCo.
        Retorna um dicionário:
        {
            'total': float,  # cobertura total em %
            'arquivos': { 'Caminho/Arquivo.java': cobertura_em_% }
        }
        """
        xml_path = os.path.join(self.repo_path, "target/site/jacoco/jacoco.xml")
        if not os.path.exists(xml_path):
            return {'total': 0.0, 'arquivos': {}}

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Cobertura total
        total_cobertura = 0.0
        for counter in root.findall('counter'):
            if counter.get('type') == 'LINE':
                covered = int(counter.get('covered'))
                missed = int(counter.get('missed'))
                total = covered + missed
                if total > 0:
                    total_cobertura = (covered / total) * 100
                break

        # Cobertura por arquivo
        arquivos_cobertura = {}
        for package in root.findall('package'):
            for sourcefile in package.findall('sourcefile'):
                nome_arquivo = sourcefile.get('name')
                for counter in sourcefile.findall('counter'):
                    if counter.get('type') == 'LINE':
                        covered = int(counter.get('covered'))
                        missed = int(counter.get('missed'))
                        total = covered + missed
                        if total > 0:
                            cobertura = (covered / total) * 100
                        else:
                            cobertura = 0.0
                        arquivos_cobertura[nome_arquivo] = cobertura
                        break

        return {'total': total_cobertura, 'arquivos': arquivos_cobertura}