from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class RelatorioAuditoria:
    def __init__(self, dados_metricas):
        self.dados = dados_metricas # Dicionário vindo dos outros módulos

    def gerar_pdf(self, nome_arquivo="relatorio_final.pdf"):
        c = canvas.Canvas(nome_arquivo, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "Relatório de Auditoria ISO/IEC 25010")

        y = 720
        c.setFont("Helvetica-Bold", 13)
        c.drawString(100, y, "Sumário Executivo das Características Avaliadas:")
        y -= 20
        c.setFont("Helvetica", 11)
        c.drawString(100, y, "- Confiabilidade: Cobertura de testes unitários (JaCoCo)")
        y -= 15
        c.drawString(100, y, "- Manutenibilidade: Complexidade Ciclomática, Acoplamento, Duplicação")
        y -= 15
        c.drawString(100, y, "- Eficiência de Desempenho: (Benchmarking, Latência - não implementado neste relatório)")
        y -= 25

        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y, "Cobertura Total de Testes:")
        c.setFont("Helvetica", 12)
        cobertura_total = self.dados.get('cobertura_total', 0.0)
        y -= 20
        c.drawString(120, y, f"Cobertura Total: {cobertura_total:.2f}%")
        y -= 20

        # Cobertura por arquivo
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y, "Cobertura por Arquivo:")
        y -= 18
        c.setFont("Helvetica", 11)
        cobertura_arquivos = self.dados.get('cobertura_arquivos', {})
        if cobertura_arquivos:
            for arquivo, cobertura in cobertura_arquivos.items():
                c.drawString(120, y, f"{arquivo}: {cobertura:.2f}%")
                y -= 15
        else:
            c.drawString(120, y, "Não disponível.")
            y -= 15

        # Complexidade por arquivo
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y, "Complexidade Ciclomática por Arquivo:")
        y -= 18
        c.setFont("Helvetica", 11)
        complexidade_arquivos = self.dados.get('complexidade_arquivos', {})
        if complexidade_arquivos:
            for arquivo, complexidade in complexidade_arquivos.items():
                c.drawString(120, y, f"{arquivo}: {complexidade}")
                y -= 15
        else:
            c.drawString(120, y, "Não disponível.")
            y -= 15

        # Lógica de Decisão
        y -= 10
        c.setFont("Helvetica-Bold", 14)
        status = "APROVADO" if cobertura_total > 70 else "REPROVADO"
        c.drawString(100, y, f"STATUS FINAL: {status}")

        c.save()
        print(f"Relatório {nome_arquivo} gerado com sucesso!")