"""
Ferramenta de Auditoria de Qualidade - ISO/IEC 25010
=====================================================
Uso:
    python main.py <url-do-repositorio-git> [--sem-dinamico]

Exemplos:
    python main.py https://github.com/usuario/projeto-java
    python main.py https://github.com/usuario/projeto-java --sem-dinamico

Flags:
    --sem-dinamico   Pula o Modulo II (nao tenta subir a aplicacao).
                     Util quando Maven/Java nao estao no PATH da maquina.
"""

import sys
import os

from modules.cloner          import clonar_repositorio, listar_arquivos_java
from modules.maintainability import rodar_analise as analise_modulo1
from modules.modulo_II       import EficienciaDesempenho
from modules.modulo_III      import Confiabilidade
from modules.modulo_IV       import RelatorioAuditoria


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: python main.py <url-do-repositorio> [--sem-dinamico]")
        sys.exit(1)

    repo_url      = args[0]
    executar_mod2 = "--sem-dinamico" not in args

    destino = "repo_auditado"
    print("AUDITORIA DE QUALIDADE - ISO/IEC 25010")
    print(f"Repositorio : {repo_url}")
    print(f"Modulo II   : {'ativado' if executar_mod2 else 'desativado (--sem-dinamico)'}\n")

    # Clonagem
    try:
        repo_path = clonar_repositorio(repo_url, destino)
    except Exception as e:
        print(f"[ERRO] Falha ao clonar repositorio: {e}")
        sys.exit(1)

    java_files = listar_arquivos_java(repo_path)
    if not java_files:
        print("[AVISO] Nenhum arquivo .java encontrado. Verifique se e um projeto Java.")

    # Modulo I - Manutenibilidade
    resultado_mod1 = analise_modulo1(java_files) if java_files else {
        "por_arquivo": {}, "duplicatas": [], "resumo": {}
    }

    # Modulo II - Eficiencia de Desempenho
    resultado_mod2 = {"status": "desativado"}
    if executar_mod2:
        mod2 = EficienciaDesempenho(repo_path)
        resultado_mod2 = mod2.rodar_analise()
    else:
        print("\n[Modulo II] Pulado (--sem-dinamico).")

    # Modulo III - Confiabilidade
    mod3 = Confiabilidade(repo_path)
    resultado_mod3 = mod3.rodar_analise()

    # Modulo IV - Relatorio
    dados_relatorio = {
        "repositorio": repo_url,
        "modulo_I":    resultado_mod1,
        "modulo_II":   resultado_mod2,
        "modulo_III":  resultado_mod3,
    }

    relatorio = RelatorioAuditoria(dados_relatorio)
    nome_base = "relatorio_iso25010"
    relatorio.gerar_pdf(f"{nome_base}.pdf")
    relatorio.gerar_html(f"{nome_base}.html")

    _imprimir_status_final(resultado_mod1, resultado_mod3)


def _imprimir_status_final(mod1: dict, mod3: dict):
    resumo    = mod1.get("resumo", {})
    cobertura = mod3.get("total", 0.0)
    cls_cob   = mod3.get("classificacao", "SEM_TESTES")
    cls_c     = resumo.get("classificacao_complexidade", "N/A")
    cls_cbo   = resumo.get("classificacao_cbo", "N/A")

    reprovado = (
        cls_cob in ("BAIXA", "SEM_TESTES") or
        cls_c == "ALTO" or
        cls_cbo == "ALTO"
    )
    status = "REPROVADO" if reprovado else "APROVADO"

    print("\nRESULTADO FINAL - ISO/IEC 25010")
    print(f"  Cobertura de testes  : {cobertura:.1f}%  [{cls_cob}]")
    print(f"  Complexidade media   : {resumo.get('complexidade_media', 'N/A')}  [{cls_c}]")
    print(f"  Acoplamento (CBO)    : {resumo.get('cbo_medio', 'N/A')}  [{cls_cbo}]")
    print(f"  Blocos duplicados    : {resumo.get('blocos_duplicados', 'N/A')}")
    print(f"\n  STATUS: {status}")

    if reprovado:
        motivos = []
        if cls_cob in ("BAIXA", "SEM_TESTES"):
            motivos.append(f"cobertura insuficiente ({cobertura:.1f}%)")
        if cls_c == "ALTO":
            motivos.append("complexidade ciclomatica ALTA")
        if cls_cbo == "ALTO":
            motivos.append("acoplamento (CBO) ALTO")
        print(f"\n  Este codigo falha na ISO 25010: {', '.join(motivos)}.")
    else:
        print("\n  O projeto esta em conformidade com os criterios avaliados.")
    print()


if __name__ == "__main__":
    main()
