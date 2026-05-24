import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


class RelatorioAuditoria:
    """
    Modulo IV - Relatorio de qualidade ISO/IEC 25010.
    Gera PDF e HTML com visual simples e legivel.
    """

    PRETO  = colors.HexColor("#1a1a1a")
    CINZA  = colors.HexColor("#555555")
    CLARO  = colors.HexColor("#f5f5f5")
    BORDA  = colors.HexColor("#cccccc")
    BRANCO = colors.white

    def __init__(self, dados: dict):
        self.dados = dados
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()

    def _configurar_estilos(self):
        self.titulo = ParagraphStyle(
            "Titulo",
            parent=self.styles["Normal"],
            fontSize=16,
            fontName="Helvetica-Bold",
            textColor=self.PRETO,
            spaceAfter=4,
        )
        self.subtitulo = ParagraphStyle(
            "Subtitulo",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=self.CINZA,
            spaceAfter=16,
        )
        self.secao = ParagraphStyle(
            "Secao",
            parent=self.styles["Normal"],
            fontSize=12,
            fontName="Helvetica-Bold",
            textColor=self.PRETO,
            spaceBefore=16,
            spaceAfter=6,
        )
        self.corpo = ParagraphStyle(
            "Corpo",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=self.PRETO,
            leading=14,
            spaceAfter=4,
        )
        self.status_ok = ParagraphStyle(
            "StatusOk",
            parent=self.styles["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#2e7d32"),
            spaceBefore=8,
            spaceAfter=8,
        )
        self.status_nok = ParagraphStyle(
            "StatusNok",
            parent=self.styles["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#b71c1c"),
            spaceBefore=8,
            spaceAfter=8,
        )

    def _tabela(self, cabecalho: list, linhas: list, col_widths=None) -> Table:
        dados = [cabecalho] + linhas
        t = Table(dados, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  self.CLARO),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("TEXTCOLOR",     (0, 0), (-1, -1), self.PRETO),
            ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",          (0, 0), (-1, -1), 0.5, self.BORDA),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        return t

    def _secao_cabecalho(self, story):
        repo = self.dados.get("repositorio", "Nao informado")
        data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        story.append(Paragraph("Relatorio de Analise de Qualidade", self.titulo))
        story.append(Paragraph("ISO/IEC 25010", self.subtitulo))
        story.append(Paragraph(f"Repositorio: {repo}", self.corpo))
        story.append(Paragraph(f"Data: {data}", self.corpo))
        story.append(Spacer(1, 0.5 * cm))

    def _secao_visao_geral(self, story):
        mod1 = self.dados.get("modulo_I", {}).get("resumo", {})
        mod3 = self.dados.get("modulo_III", {})

        cobertura    = mod3.get("total", 0.0)
        cls_cobertura = mod3.get("classificacao", "SEM_TESTES")
        cls_complexidade = mod1.get("classificacao_complexidade", "N/A")
        cls_cbo      = mod1.get("classificacao_cbo", "N/A")
        blocos_dup   = mod1.get("blocos_duplicados", 0)

        reprovado = (
            cls_cobertura in ("BAIXA", "SEM_TESTES") or
            cls_complexidade == "ALTO" or
            cls_cbo == "ALTO"
        )
        status = "REPROVADO" if reprovado else "APROVADO"

        story.append(Paragraph("Visao Geral", self.secao))

        linhas = [
            ["Cobertura de testes",        f"{cobertura:.1f}%",                      cls_cobertura],
            ["Complexidade ciclomatica",   str(mod1.get("complexidade_media", "N/A")), cls_complexidade],
            ["Acoplamento (CBO)",          str(mod1.get("cbo_medio", "N/A")),          cls_cbo],
            ["Blocos de codigo duplicados", str(blocos_dup),                           "-"],
        ]
        story.append(self._tabela(
            ["Metrica", "Valor", "Classificacao"],
            linhas,
            col_widths=[7 * cm, 4 * cm, 4 * cm]
        ))
        story.append(Spacer(1, 0.3 * cm))

        estilo = self.status_ok if status == "APROVADO" else self.status_nok
        story.append(Paragraph(f"Status: {status}", estilo))

        # Observacoes
        obs = self._gerar_observacoes(mod1, mod3)
        for o in obs:
            story.append(Paragraph(f"- {o}", self.corpo))

    def _gerar_observacoes(self, mod1: dict, mod3: dict) -> list:
        obs = []
        cobertura = mod3.get("total", 0.0)
        cls_cob   = mod3.get("classificacao", "SEM_TESTES")

        if cls_cob == "SEM_TESTES":
            obs.append("Nenhum teste unitario foi detectado no projeto.")
        elif cls_cob == "BAIXA":
            obs.append(f"Cobertura de testes baixa ({cobertura:.1f}%). Recomenda-se adicionar testes unitarios.")
        elif cls_cob == "MEDIA":
            obs.append(f"Cobertura de testes media ({cobertura:.1f}%). Recomenda-se superar 80%.")
        else:
            obs.append(f"Cobertura de testes satisfatoria ({cobertura:.1f}%).")

        cls_c  = mod1.get("classificacao_complexidade", "N/A")
        media_c = mod1.get("complexidade_media", 0)
        if cls_c == "ALTO":
            obs.append(f"Complexidade ciclomatica alta (media {media_c}). Metodos com muitas ramificacoes dificultam manutencao e testes.")
        elif cls_c == "MEDIO":
            obs.append(f"Complexidade ciclomatica media ({media_c}). Revisar metodos com complexidade acima de 10.")
        else:
            obs.append(f"Complexidade ciclomatica dentro do esperado (media {media_c}).")

        cls_cbo = mod1.get("classificacao_cbo", "N/A")
        cbo     = mod1.get("cbo_medio", 0)
        if cls_cbo == "ALTO":
            obs.append(f"Acoplamento alto (CBO medio {cbo}). Alta dependencia entre classes dificulta evolucao do sistema.")
        elif cls_cbo == "MEDIO":
            obs.append(f"Acoplamento moderado (CBO medio {cbo}). Considere reduzir dependencias entre modulos.")
        else:
            obs.append(f"Acoplamento dentro do aceitavel (CBO medio {cbo}).")

        dup = mod1.get("blocos_duplicados", 0)
        if dup > 3:
            obs.append(f"{dup} blocos de codigo duplicados encontrados. Recomenda-se extrair logica repetida para metodos reutilizaveis.")
        else:
            obs.append(f"Duplicacao de codigo baixa ({dup} blocos).")

        return obs

    def _secao_modulo1(self, story):
        story.append(Paragraph("Modulo I - Manutenibilidade", self.secao))
        por_arquivo = self.dados.get("modulo_I", {}).get("por_arquivo", {})

        if not por_arquivo:
            story.append(Paragraph("Nenhum arquivo Java encontrado.", self.corpo))
            return

        linhas = []
        for arq, m in por_arquivo.items():
            linhas.append([
                arq,
                str(m.get("complexidade_maxima", 0)),
                str(m.get("complexidade_media", 0)),
                m.get("classificacao_complexidade", "N/A"),
                str(m.get("cbo", 0)),
                m.get("classificacao_cbo", "N/A"),
            ])

        story.append(self._tabela(
            ["Arquivo", "CC max", "CC media", "Class. CC", "CBO", "Class. CBO"],
            linhas,
            col_widths=[5.5 * cm, 1.8 * cm, 1.8 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm]
        ))

        duplicatas = self.dados.get("modulo_I", {}).get("duplicatas", [])
        if duplicatas:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f"Blocos de codigo duplicados ({len(duplicatas)}):", self.corpo))
            for d in duplicatas[:10]:
                story.append(Paragraph(
                    f"  {d['arquivo_a']}  x  {d['arquivo_b']}  ({d['tamanho']} linhas)",
                    self.corpo
                ))

    def _secao_modulo2(self, story):
        story.append(Paragraph("Modulo II - Eficiencia de Desempenho", self.secao))
        mod2 = self.dados.get("modulo_II", {})

        if mod2.get("status") != "ok":
            story.append(Paragraph(
                "Analise de desempenho nao executada. A aplicacao nao iniciou ou Maven nao esta disponivel.",
                self.corpo
            ))
            return

        benchmark = mod2.get("benchmark", {})
        if benchmark:
            story.append(Paragraph("Tempo de resposta por rota:", self.corpo))
            linhas = []
            for rota, dados in benchmark.items():
                if "erro" in dados:
                    linhas.append([rota, "-", "-", "-", "Erro"])
                else:
                    linhas.append([
                        rota,
                        f"{dados.get('tempo_min_ms', 0)}ms",
                        f"{dados.get('tempo_mediano_ms', 0)}ms",
                        f"{dados.get('tempo_max_ms', 0)}ms",
                        str(dados.get("amostras", 0))
                    ])
            story.append(self._tabela(
                ["Rota", "Min", "Mediana", "Max", "Amostras"],
                linhas,
                col_widths=[6 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2 * cm]
            ))

        latencia = mod2.get("latencia", {})
        if latencia:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph("Variacao de latencia por carga:", self.corpo))
            linhas = []
            for carga, dados in latencia.items():
                aumento = dados.get("aumento_pct")
                aumento_str = f"+{aumento}%" if aumento is not None else "-"
                linhas.append([str(carga), f"{dados.get('latencia_ms', 0)}ms", aumento_str])
            story.append(self._tabela(
                ["Requisicoes", "Latencia media", "Aumento vs 100 req"],
                linhas,
                col_widths=[4 * cm, 5 * cm, 6 * cm]
            ))

    def _secao_modulo3(self, story):
        story.append(Paragraph("Modulo III - Cobertura de Testes", self.secao))
        mod3 = self.dados.get("modulo_III", {})
        total = mod3.get("total", 0.0)
        cls   = mod3.get("classificacao", "SEM_TESTES")

        story.append(Paragraph(f"Cobertura total de linhas: {total:.2f}% ({cls})", self.corpo))

        arquivos = mod3.get("arquivos", {})
        if arquivos:
            story.append(Spacer(1, 0.2 * cm))
            linhas = [[arq, f"{cob:.2f}%"] for arq, cob in sorted(arquivos.items())]
            story.append(self._tabela(
                ["Arquivo", "Cobertura"],
                linhas,
                col_widths=[11 * cm, 4.5 * cm]
            ))
        else:
            story.append(Paragraph("Detalhamento por arquivo nao disponivel.", self.corpo))

    def gerar_pdf(self, nome_arquivo: str = "relatorio_iso25010.pdf"):
        doc = SimpleDocTemplate(
            nome_arquivo,
            pagesize=A4,
            leftMargin=2.5 * cm,
            rightMargin=2.5 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
            title="Relatorio ISO/IEC 25010"
        )

        story = []
        self._secao_cabecalho(story)
        self._secao_visao_geral(story)
        story.append(PageBreak())
        self._secao_modulo1(story)
        story.append(Spacer(1, 0.5 * cm))
        self._secao_modulo2(story)
        story.append(Spacer(1, 0.5 * cm))
        self._secao_modulo3(story)

        doc.build(story)
        print(f"\n[Modulo IV] Relatorio gerado: {nome_arquivo}")
        return nome_arquivo

    def gerar_html(self, nome_arquivo: str = "relatorio_iso25010.html"):
        mod1 = self.dados.get("modulo_I", {}).get("resumo", {})
        mod3 = self.dados.get("modulo_III", {})
        cobertura = mod3.get("total", 0.0)
        cls_cob   = mod3.get("classificacao", "SEM_TESTES")
        cls_c     = mod1.get("classificacao_complexidade", "N/A")
        cls_cbo   = mod1.get("classificacao_cbo", "N/A")
        blocos    = mod1.get("blocos_duplicados", 0)
        repo      = self.dados.get("repositorio", "N/A")
        data      = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        reprovado = cls_cob in ("BAIXA", "SEM_TESTES") or cls_c == "ALTO" or cls_cbo == "ALTO"
        status    = "REPROVADO" if reprovado else "APROVADO"
        cor_status = "#b71c1c" if reprovado else "#2e7d32"

        obs = self._gerar_observacoes(mod1, mod3)
        obs_html = "".join(f"<li>{o}</li>" for o in obs)

        linhas_mod1 = ""
        for arq, m in self.dados.get("modulo_I", {}).get("por_arquivo", {}).items():
            linhas_mod1 += f"""<tr>
                <td>{arq}</td>
                <td>{m.get('complexidade_maxima', 0)}</td>
                <td>{m.get('complexidade_media', 0)}</td>
                <td>{m.get('classificacao_complexidade', 'N/A')}</td>
                <td>{m.get('cbo', 0)}</td>
                <td>{m.get('classificacao_cbo', 'N/A')}</td>
            </tr>"""

        linhas_mod3 = ""
        for arq, cob in self.dados.get("modulo_III", {}).get("arquivos", {}).items():
            linhas_mod3 += f"<tr><td>{arq}</td><td>{cob:.2f}%</td></tr>"

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatorio ISO/IEC 25010</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 960px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; background: #fff; }}
  h1   {{ font-size: 1.6em; font-weight: bold; margin-bottom: 2px; }}
  h2   {{ font-size: 1.1em; margin-top: 32px; margin-bottom: 8px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
  p    {{ font-size: 0.9em; margin: 4px 0; color: #444; }}
  ul   {{ font-size: 0.9em; color: #444; padding-left: 20px; }}
  li   {{ margin: 3px 0; }}
  .status {{ font-size: 1.1em; font-weight: bold; color: {cor_status}; margin: 12px 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 0.85em; }}
  th    {{ background: #f0f0f0; text-align: left; padding: 6px 8px; border: 1px solid #ccc; font-weight: bold; }}
  td    {{ padding: 5px 8px; border: 1px solid #ddd; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  .rodape {{ margin-top: 40px; font-size: 0.75em; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
</style>
</head>
<body>

<h1>Relatorio de Analise de Qualidade</h1>
<p>ISO/IEC 25010</p>
<p>Repositorio: {repo}</p>
<p>Data: {data}</p>

<h2>Visao Geral</h2>
<table>
  <tr><th>Metrica</th><th>Valor</th><th>Classificacao</th></tr>
  <tr><td>Cobertura de testes</td><td>{cobertura:.1f}%</td><td>{cls_cob}</td></tr>
  <tr><td>Complexidade ciclomatica media</td><td>{mod1.get('complexidade_media','N/A')}</td><td>{cls_c}</td></tr>
  <tr><td>Acoplamento (CBO medio)</td><td>{mod1.get('cbo_medio','N/A')}</td><td>{cls_cbo}</td></tr>
  <tr><td>Blocos de codigo duplicados</td><td>{blocos}</td><td>-</td></tr>
</table>

<p class="status">Status: {status}</p>
<ul>{obs_html}</ul>

<h2>Modulo I - Manutenibilidade</h2>
<table>
  <tr><th>Arquivo</th><th>CC max</th><th>CC media</th><th>Class. CC</th><th>CBO</th><th>Class. CBO</th></tr>
  {linhas_mod1}
</table>

<h2>Modulo III - Cobertura de Testes</h2>
<table>
  <tr><th>Arquivo</th><th>Cobertura</th></tr>
  {linhas_mod3 if linhas_mod3 else '<tr><td colspan="2">Nao disponivel</td></tr>'}
</table>

<p class="rodape">Gerado em {data}</p>
</body>
</html>"""

        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Modulo IV] Relatorio HTML gerado: {nome_arquivo}")
        return nome_arquivo
