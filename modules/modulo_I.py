import os
import javalang


def analisar_complexidade(source: str) -> dict:
    """
    Conta if/else em cada método (Complexidade Ciclomática McCabe simplificada).
    Começa em 1, +1 por ramificação (if, else-if, else).
    Pontuação: 1-10 BAIXO | 11-20 MEDIO | >20 ALTO
    """
    resultados = {}
    try:
        tree = javalang.parse.parse(source)
    except Exception:
        return resultados

    for _, classe in tree.filter(javalang.tree.ClassDeclaration):
        for metodo in classe.methods:
            nome = f"{classe.name}.{metodo.name}"
            complexidade = 1
            for _, node in metodo.filter(javalang.tree.IfStatement):
                complexidade += 1           # +1 pelo if
                if node.else_statement:
                    complexidade += 1       # +1 pelo else / else-if
            resultados[nome] = complexidade

    return resultados


def analisar_cbo(source: str) -> int:
    """
    Conta quantas classes únicas o arquivo importa (Acoplamento entre Objetos).
    Cada import que não seja wildcard conta 1 ponto.
    Pontuação: <=5 BAIXO | <=10 MEDIO | >10 ALTO
    """
    try:
        tree = javalang.parse.parse(source)
    except Exception:
        return 0

    imports = set()
    for imp in (tree.imports or []):
        classe = imp.path.split(".")[-1]
        if classe != "*":
            imports.add(classe)

    return len(imports)


def encontrar_duplicatas(java_files: list, min_linhas: int = 5) -> list:
    """
    Encontra blocos de código idênticos (≥ 5 linhas consecutivas) entre arquivos.
    Cada bloco repetido conta 1 ponto de penalidade.
    """
    blocos_por_arquivo = {}

    for filepath in java_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                linhas = [
                    l.strip() for l in f.readlines()
                    if l.strip() and not l.strip().startswith(("//", "*", "@"))
                ]
            blocos = [tuple(linhas[i:i+min_linhas]) for i in range(len(linhas) - min_linhas + 1)]
            blocos_por_arquivo[filepath] = set(blocos)
        except Exception:
            continue

    duplicatas = []
    arquivos = list(blocos_por_arquivo.keys())

    for i in range(len(arquivos)):
        for j in range(i + 1, len(arquivos)):
            comuns = blocos_por_arquivo[arquivos[i]] & blocos_por_arquivo[arquivos[j]]
            for bloco in comuns:
                duplicatas.append({
                    "arquivo_a": os.path.basename(arquivos[i]),
                    "arquivo_b": os.path.basename(arquivos[j]),
                    "tamanho": len(bloco)
                })

    return duplicatas


def classificar(valor: int, limites: tuple) -> str:
    """Classifica um valor em BAIXO, MEDIO ou ALTO."""
    baixo, medio = limites
    if valor <= baixo:
        return "BAIXO"
    elif valor <= medio:
        return "MEDIO"
    return "ALTO"


def rodar_analise(java_files: list) -> dict:
    """Função principal – analisa todos os arquivos e retorna o resultado."""
    print("\n[Módulo I] Iniciando análise de manutenibilidade...")

    por_arquivo = {}

    for filepath in java_files:
        nome = os.path.basename(filepath)
        print(f"  Analisando: {nome}")

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        complexidade = analisar_complexidade(source)
        cbo = analisar_cbo(source)

        valores_c = list(complexidade.values())
        max_c = max(valores_c) if valores_c else 0
        media_c = round(sum(valores_c) / len(valores_c), 2) if valores_c else 0

        por_arquivo[nome] = {
            "complexidade_maxima": max_c,
            "complexidade_media": media_c,
            "classificacao_complexidade": classificar(max_c, (10, 20)),
            "cbo": cbo,
            "classificacao_cbo": classificar(cbo, (5, 10)),
            "metodos": complexidade
        }

    duplicatas = encontrar_duplicatas(java_files)

    todas_medias = [v["complexidade_media"] for v in por_arquivo.values()]
    todos_cbos   = [v["cbo"] for v in por_arquivo.values()]

    media_geral_c   = round(sum(todas_medias) / len(todas_medias), 2) if todas_medias else 0
    media_geral_cbo = round(sum(todos_cbos)   / len(todos_cbos),   2) if todos_cbos   else 0

    resumo = {
        "total_arquivos": len(java_files),
        "complexidade_media": media_geral_c,
        "classificacao_complexidade": classificar(media_geral_c, (10, 20)),
        "cbo_medio": media_geral_cbo,
        "classificacao_cbo": classificar(media_geral_cbo, (5, 10)),
        "blocos_duplicados": len(duplicatas)
    }

    print(f"\n  Complexidade média : {resumo['complexidade_media']} [{resumo['classificacao_complexidade']}]")
    print(f"  CBO médio          : {resumo['cbo_medio']} [{resumo['classificacao_cbo']}]")
    print(f"  Blocos duplicados  : {resumo['blocos_duplicados']}")

    return {"por_arquivo": por_arquivo, "duplicatas": duplicatas, "resumo": resumo}
