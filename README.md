# Auditoria ISO/IEC 25010

Ferramenta de análise estática e dinâmica de projetos Java, gerando um parecer de conformidade baseado na norma **ISO/IEC 25010**.

## Módulos

| Módulo | Característica ISO 25010 | O que mede |
|--------|--------------------------|-----------|
| I | Manutenibilidade | Complexidade Ciclomática (McCabe), Acoplamento (CBO), Duplicação de Código |
| II | Eficiência de Desempenho | Benchmarking de rotas HTTP, Análise de Latência por carga |
| III | Confiabilidade | Cobertura de testes (JaCoCo), por arquivo e total |
| IV | Relatório | PDF + HTML com sumário executivo e parecer de conformidade |

## Pontuação das Métricas

**Complexidade Ciclomática (CC)**
- 1–10 → BAIXO ✅
- 11–20 → MÉDIO ⚠️
- >20 → ALTO ❌

**Acoplamento (CBO)**
- ≤5 → BAIXO ✅
- 6–10 → MÉDIO ⚠️
- >10 → ALTO ❌

**Cobertura de Testes**
- ≥80% → ALTA ✅
- 50–79% → MÉDIA ⚠️
- <50% → BAIXA ❌

## Requisitos

- Python 3.8+
- Java 11+ e Maven 3.6+ (para Módulos II e III)
- Git

## Instalação

```bash
git clone https://github.com/sordi1/auditoria-iso25010.git
cd auditoria-iso25010
pip install -r requirements.txt
```

## Uso

```bash
# Análise completa (inclui benchmark dinâmico)
python main.py https://github.com/usuario/projeto-java

# Apenas análise estática + cobertura (sem subir a aplicação)
python main.py https://github.com/usuario/projeto-java --sem-dinamico
```

## Saída

Ao final da execução são gerados:
- `relatorio_iso25010.pdf` — relatório completo em PDF
- `relatorio_iso25010.html` — versão HTML do relatório
- Status no terminal com parecer de conformidade

## Exemplo de saída no terminal

```
============================================================
  RESULTADO FINAL – ISO/IEC 25010
============================================================
  Cobertura de testes  : 34.5%  [BAIXA]
  Complexidade média   : 7.2    [BAIXO]
  Acoplamento (CBO)    : 4.1    [BAIXO]
  Blocos duplicados    : 2
------------------------------------------------------------
  STATUS: REPROVADO

  ⚠  Este código falha na ISO 25010: cobertura insuficiente (34.5%).
============================================================
```
