import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class RelatorioAuditoria:
    """
    Módulo IV – Geração de Relatório ISO/IEC 25010 em PDF.

    Recebe os dados de todos os módulos e gera um sumário executivo
    com pontuação e parecer de conformidade.
    """

    VERDE   = colors.HexColor("#2e7d32")
    AMARELO = colors.HexColor("#f9a825")
    VERMELHO= colors.HexColor("#c62828")
    AZUL    = colors.HexColor("#0d47a1")
    CINZA   = colors.HexColor("#546e7a")
    BRANCO  = colors.white
    PRETO   = colors.black

    def __init__(self, dados: dict):
        self.dados = dados
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()

    # ------------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------------

    def _configurar_estilos(self):
        self.estilo_titulo = ParagraphStyle(
            "Titulo",
            parent=self.styles["Title"],
            fontSize=20,
            textColor=self.AZUL,
            spaceAfter=6,
            alignment=TA_CENTER
        )
        self.estilo_subtitulo = ParagraphStyle(
            "Subtitulo",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=self.CINZA,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        self.estilo_secao = ParagraphStyle(
            "Secao",
            parent=self.styles["Heading2"],
            fontSize=13,
            textColor=self.AZUL,
            spaceBefore=14,
            spaceAfter=6,
            borderPad=(0, 0, 2, 0)
        )
        self.estilo_body = ParagraphStyle(
            "Body",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=14,
            spaceAfter=4
        )
        self.estilo_parecer = ParagraphStyle(
            "Parecer",
            parent=self.styles["Normal"],
            fontSize=11,
            leading=16,
            leftIndent=10,
            spaceBefore=4,
            spaceAfter=4
        )

    # ------------------------------------------------------------------
    # Utilitários visuais
    # ------------------------------------------------------------------

    def _cor_classificacao(self, cls: str):
        mapa = {
            "BAIXO": self.VERDE, "ALTA": self.VERDE, "APROVADO": self.VERDE,
            "MEDIO": self.AMARELO, "MEDIA": self.AMARELO,
            "ALTO": self.VERMELHO, "BAIXA": self.VERMELHO,
            "SEM_TESTES": self.VERMELHO, "REPROVADO": self.VERMELHO
        }
        return mapa.get(cls.upper(), self.CINZA)

    def _badge(self, texto: str) -> Table:
        cor = self._cor_classificacao(texto)
        t = Table([[texto]], colWidths=[3*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), cor),
            ("TEXTCOLOR",  (0,0), (-1,-1), self.BRANCO),
            ("FONTNAME",   (0,0), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
            ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
            ("ROUNDEDCORNERS", [4]),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        return t

    def _tabela_estilizada(self, cabecalho: list, linhas: list, col_widths=None) -> Table:
        dados = [cabecalho] + linhas
        t = Table(dados, colWidths=col_widths, repeatRows=1)
        estilo = [
            ("BACKGROUND",  (0,0), (-1,0),  self.AZUL),
            ("TEXTCOLOR",   (0,0), (-1,0),  self.BRANCO),
            ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#cfd8dc")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#eceff1")]),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ]
        t.setStyle(TableStyle(estilo))
        return t

    # ------------------------------------------------------------------
    # Construção das seções
    # ------------------------------------------------------------------

    def _secao_capa(self, story):
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Relatório de Auditoria de Qualidade", self.estilo_titulo))
        story.append(Paragraph("ISO/IEC 25010 – Análise Estática e Dinâmica", self.estilo_subtitulo))
        story.append(HRFlowable(width="100%", thickness=1.5, color=self.AZUL))
        story.append(Spacer(1, 0.3*cm))

        repo = self.dados.get("repositorio", "Não informado")
        data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        story.append(Paragraph(f"<b>Repositório analisado:</b> {repo}", self.estilo_body))
        story.append(Paragraph(f"<b>Data da análise:</b> {data}", self.estilo_body))
        story.append(Spacer(1, 0.5*cm))

    def _secao_resumo_executivo(self, story):
        story.append(Paragraph("Sumário Executivo", self.estilo_secao))

        mod1 = self.dados.get("modulo_I", {}).get("resumo", {})
        mod3 = self.dados.get("modulo_III", {})

        cobertura = mod3.get("total", 0.0)
        cls_cobertura = mod3.get("classificacao", "SEM_TESTES")
        cls_complexidade = mod1.get("classificacao_complexidade", "N/A")
        cls_cbo = mod1.get("classificacao_cbo", "N/A")
        blocos_dup = mod1.get("blocos_duplicados", 0)

        # Determina status geral
        reprovado = (
            cls_cobertura in ("BAIXA", "SEM_TESTES") or
            cls_complexidade == "ALTO" or
            cls_cbo == "ALTO"
        )
        status = "REPROVADO" if reprovado else "APROVADO"

        # Tabela resumo
        linhas = [
            ["Cobertura de Testes",  f"{cobertura:.1f}%",            cls_cobertura],
            ["Complexidade Média",   str(mod1.get("complexidade_media","N/A")), cls_complexidade],
            ["Acoplamento (CBO)",    str(mod1.get("cbo_medio","N/A")), cls_cbo],
            ["Blocos Duplicados",    str(blocos_dup),                 "BAIXO" if blocos_dup <= 3 else "ALTO"],
        ]

        tab = self._tabela_estilizada(
            ["Característica", "Valor", "Classificação"],
            linhas,
            col_widths=[7*cm, 4*cm, 4*cm]
        )
        story.append(tab)
        story.append(Spacer(1, 0.5*cm))

        cor_status = self._cor_classificacao(status)
        story.append(Paragraph(
            f'<font color="{"#2e7d32" if status == "APROVADO" else "#c62828"}"><b>STATUS FINAL: {status}</b></font>',
            ParagraphStyle("StatusFinal", parent=self.estilo_body, fontSize=13, alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 0.3*cm))

        # Parecer descritivo
        pareceres = self._gerar_parecer(mod1, mod3)
        for p in pareceres:
            story.append(Paragraph(f"• {p}", self.estilo_parecer))

    def _gerar_parecer(self, mod1: dict, mod3: dict) -> list:
        pareceres = []
        cobertura = mod3.get("total", 0.0)
        cls_cob = mod3.get("classificacao", "SEM_TESTES")

        if cls_cob == "SEM_TESTES":
            pareceres.append("Confiabilidade: nenhum teste unitário detectado — risco crítico de regressão.")
        elif cls_cob == "BAIXA":
            pareceres.append(f"Confiabilidade BAIXA: cobertura de {cobertura:.1f}% (abaixo de 50%). Recomenda-se adicionar testes.")
        elif cls_cob == "MEDIA":
            pareceres.append(f"Confiabilidade MEDIA: cobertura de {cobertura:.1f}%. Recomenda-se superar 80%.")
        else:
            pareceres.append(f"Confiabilidade ALTA: cobertura de {cobertura:.1f}% — excelente.")

        cls_c = mod1.get("classificacao_complexidade", "N/A")
        media_c = mod1.get("complexidade_media", 0)
        if cls_c == "ALTO":
            pareceres.append(f"Manutenibilidade comprometida: complexidade ciclomática média de {media_c} — métodos difíceis de testar e manter.")
        elif cls_c == "MEDIO":
            pareceres.append(f"Manutenibilidade aceitável: complexidade média de {media_c} — revisar métodos com CC > 10.")
        else:
            pareceres.append(f"Manutenibilidade BOA: complexidade média de {media_c}.")

        cls_cbo = mod1.get("classificacao_cbo", "N/A")
        cbo = mod1.get("cbo_medio", 0)
        if cls_cbo == "ALTO":
            pareceres.append(f"Acoplamento ALTO (CBO médio={cbo}): alta interdependência entre módulos — dificuldade de evolução.")
        elif cls_cbo == "MEDIO":
            pareceres.append(f"Acoplamento MÉDIO (CBO médio={cbo}): considere reduzir dependências.")
        else:
            pareceres.append(f"Acoplamento BAIXO (CBO médio={cbo}) — bem modularizado.")

        dup = mod1.get("blocos_duplicados", 0)
        if dup > 3:
            pareceres.append(f"Duplicação de código: {dup} blocos repetidos encontrados (violação DRY).")
        else:
            pareceres.append(f"Duplicação de código: {dup} blocos repetidos — dentro do aceitável.")

        return pareceres

    def _secao_modulo1(self, story):
        story.append(Paragraph("Módulo I — Manutenibilidade (Análise Estática)", self.estilo_secao))
        por_arquivo = self.dados.get("modulo_I", {}).get("por_arquivo", {})

        if not por_arquivo:
            story.append(Paragraph("Nenhum arquivo Java analisado.", self.estilo_body))
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

        tab = self._tabela_estilizada(
            ["Arquivo", "CC máx", "CC média", "Class. CC", "CBO", "Class. CBO"],
            linhas,
            col_widths=[5.5*cm, 1.8*cm, 1.8*cm, 2.2*cm, 1.8*cm, 2.2*cm]
        )
        story.append(tab)

        # Duplicatas
        duplicatas = self.dados.get("modulo_I", {}).get("duplicatas", [])
        if duplicatas:
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(f"<b>Blocos duplicados ({len(duplicatas)}):</b>", self.estilo_body))
            for d in duplicatas[:10]:
                story.append(Paragraph(
                    f"  {d['arquivo_a']}  ↔  {d['arquivo_b']}  ({d['tamanho']} linhas)",
                    self.estilo_body
                ))

    def _secao_modulo2(self, story):
        story.append(Paragraph("Módulo II — Eficiência de Desempenho", self.estilo_secao))
        mod2 = self.dados.get("modulo_II", {})

        if mod2.get("status") != "ok":
            story.append(Paragraph(
                "Análise de desempenho não executada "
                "(aplicação não iniciou ou Maven indisponível).",
                self.estilo_body
            ))
            return

        benchmark = mod2.get("benchmark", {})
        if benchmark:
            story.append(Paragraph("<b>Benchmarking de Rotas:</b>", self.estilo_body))
            linhas = []
            for rota, dados in benchmark.items():
                if "erro" in dados:
                    linhas.append([rota, "–", "–", "–", "Erro"])
                else:
                    linhas.append([
                        rota,
                        f"{dados.get('tempo_min_ms',0)}ms",
                        f"{dados.get('tempo_mediano_ms',0)}ms",
                        f"{dados.get('tempo_max_ms',0)}ms",
                        str(dados.get("amostras", 0))
                    ])
            tab = self._tabela_estilizada(
                ["Rota", "Mín", "Mediana", "Máx", "Amostras"],
                linhas,
                col_widths=[6*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm]
            )
            story.append(tab)

        latencia = mod2.get("latencia", {})
        if latencia:
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("<b>Análise de Latência por Carga:</b>", self.estilo_body))
            linhas = []
            for carga, dados in latencia.items():
                aumento = dados.get("aumento_pct")
                aumento_str = f"+{aumento}%" if aumento is not None else "–"
                linhas.append([
                    str(carga),
                    f"{dados.get('latencia_ms',0)}ms",
                    aumento_str
                ])
            tab = self._tabela_estilizada(
                ["Carga (req)", "Latência Média", "Aumento vs. 100 req"],
                linhas,
                col_widths=[4*cm, 5*cm, 6*cm]
            )
            story.append(tab)

    def _secao_modulo3(self, story):
        story.append(Paragraph("Módulo III — Confiabilidade (Cobertura de Testes)", self.estilo_secao))
        mod3 = self.dados.get("modulo_III", {})
        total = mod3.get("total", 0.0)
        cls   = mod3.get("classificacao", "SEM_TESTES")

        story.append(Paragraph(
            f"<b>Cobertura total de linhas:</b> {total:.2f}%  [{cls}]",
            self.estilo_body
        ))

        arquivos = mod3.get("arquivos", {})
        if arquivos:
            story.append(Spacer(1, 0.2*cm))
            linhas = [[arq, f"{cob:.2f}%"] for arq, cob in sorted(arquivos.items())]
            tab = self._tabela_estilizada(
                ["Arquivo", "Cobertura"],
                linhas,
                col_widths=[11*cm, 4.5*cm]
            )
            story.append(tab)
        else:
            story.append(Paragraph("Detalhamento por arquivo não disponível.", self.estilo_body))

    # ------------------------------------------------------------------
    # Geração final
    # ------------------------------------------------------------------

    def gerar_pdf(self, nome_arquivo: str = "relatorio_iso25010.pdf"):
        doc = SimpleDocTemplate(
            nome_arquivo,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title="Relatório ISO/IEC 25010"
        )

        story = []
        self._secao_capa(story)
        self._secao_resumo_executivo(story)
        story.append(HRFlowable(width="100%", thickness=0.5, color=self.CINZA))

        story.append(PageBreak())
        self._secao_modulo1(story)

        story.append(Spacer(1, 0.5*cm))
        self._secao_modulo2(story)

        story.append(Spacer(1, 0.5*cm))
        self._secao_modulo3(story)

        doc.build(story)
        print(f"\n[Módulo IV] Relatório gerado: {nome_arquivo}")
        return nome_arquivo

    def gerar_html(self, nome_arquivo: str = "relatorio_iso25010.html"):
        """Versão HTML alternativa ao PDF."""
        mod1 = self.dados.get("modulo_I", {}).get("resumo", {})
        mod3 = self.dados.get("modulo_III", {})
        cobertura = mod3.get("total", 0.0)
        status = "REPROVADO" if (
            mod3.get("classificacao") in ("BAIXA","SEM_TESTES") or
            mod1.get("classificacao_complexidade") == "ALTO"
        ) else "APROVADO"
        cor_status = "#2e7d32" if status == "APROVADO" else "#c62828"
        data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        repo = self.dados.get("repositorio","N/A")

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8">
<title>Relatório ISO/IEC 25010</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; color:#333; }}
  h1   {{ color:#0d47a1; }}
  h2   {{ color:#0d47a1; border-bottom:2px solid #0d47a1; padding-bottom:4px; margin-top:30px; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:4px;
             color:#fff; font-weight:bold; font-size:0.85em; }}
  .alto, .baixa, .sem_testes {{ background:#c62828; }}
  .medio, .media {{ background:#f9a825; color:#333; }}
  .baixo, .alta  {{ background:#2e7d32; }}
  .status {{ font-size:1.5em; font-weight:bold; color:{cor_status}; margin:20px 0; }}
  table {{ border-collapse:collapse; width:100%; margin:10px 0; }}
  th    {{ background:#0d47a1; color:#fff; padding:7px; }}
  td    {{ padding:6px; border:1px solid #cfd8dc; }}
  tr:nth-child(even) {{ background:#eceff1; }}
</style>
</head>
<body>
<h1>Relatório de Auditoria ISO/IEC 25010</h1>
<p><b>Repositório:</b> {repo}<br>
<b>Data:</b> {data}</p>

<h2>Sumário Executivo</h2>
<p class="status">STATUS: {status}</p>

<table>
<tr><th>Característica</th><th>Valor</th><th>Classificação</th></tr>
<tr><td>Cobertura de Testes</td><td>{cobertura:.1f}%</td>
    <td><span class="badge {mod3.get('classificacao','N/A').lower()}">{mod3.get('classificacao','N/A')}</span></td></tr>
<tr><td>Complexidade Ciclomática Média</td><td>{mod1.get('complexidade_media','N/A')}</td>
    <td><span class="badge {mod1.get('classificacao_complexidade','N/A').lower()}">{mod1.get('classificacao_complexidade','N/A')}</span></td></tr>
<tr><td>Acoplamento CBO Médio</td><td>{mod1.get('cbo_medio','N/A')}</td>
    <td><span class="badge {mod1.get('classificacao_cbo','N/A').lower()}">{mod1.get('classificacao_cbo','N/A')}</span></td></tr>
<tr><td>Blocos Duplicados</td><td>{mod1.get('blocos_duplicados','N/A')}</td><td>–</td></tr>
</table>

<h2>Módulo I — Manutenibilidade</h2>
<table>
<tr><th>Arquivo</th><th>CC máx</th><th>CC média</th><th>Class. CC</th><th>CBO</th><th>Class. CBO</th></tr>
"""
        for arq, m in self.dados.get("modulo_I",{}).get("por_arquivo",{}).items():
            html += f"""<tr>
  <td>{arq}</td><td>{m.get('complexidade_maxima',0)}</td>
  <td>{m.get('complexidade_media',0)}</td>
  <td><span class="badge {m.get('classificacao_complexidade','').lower()}">{m.get('classificacao_complexidade','N/A')}</span></td>
  <td>{m.get('cbo',0)}</td>
  <td><span class="badge {m.get('classificacao_cbo','').lower()}">{m.get('classificacao_cbo','N/A')}</span></td>
</tr>"""

        html += """</table>
<h2>Módulo III — Cobertura de Testes</h2>
<table><tr><th>Arquivo</th><th>Cobertura</th></tr>
"""
        for arq, cob in self.dados.get("modulo_III",{}).get("arquivos",{}).items():
            html += f"<tr><td>{arq}</td><td>{cob:.2f}%</td></tr>"

        html += f"""</table>
<p style="margin-top:30px;color:#777;font-size:0.8em">
Gerado automaticamente pela ferramenta auditoria-iso25010.</p>
</body></html>"""

        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Módulo IV] Relatório HTML gerado: {nome_arquivo}")
        return nome_arquivo
