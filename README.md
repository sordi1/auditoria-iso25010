# Auditoria ISO/IEC 25010

Ferramenta de analise estatica e dinamica de projetos Java, gerando um parecer de conformidade baseado na norma **ISO/IEC 25010**.

## Modulos

| Modulo | Caracteristica ISO 25010 | O que mede |
|--------|--------------------------|-----------|
| I | Manutenibilidade | Complexidade Ciclomatica (McCabe), Acoplamento (CBO), Duplicacao de Codigo |
| II | Eficiencia de Desempenho | Benchmarking de rotas HTTP, Analise de Latencia por carga |
| III | Confiabilidade | Cobertura de testes (JaCoCo), por arquivo e total |
| IV | Relatorio | PDF + HTML com sumario executivo e parecer de conformidade |

## Pontuacao das Metricas

**Complexidade Ciclomatica (CC)**
- 1 a 10: BAIXO
- 11 a 20: MEDIO
- acima de 20: ALTO

**Acoplamento (CBO)**
- ate 5: BAIXO
- 6 a 10: MEDIO
- acima de 10: ALTO

**Cobertura de Testes**
- 80% ou mais: ALTA
- 50% a 79%: MEDIA
- abaixo de 50%: BAIXA

## Pre-requisitos

| Ferramenta | Versao minima | Para que serve |
|------------|---------------|----------------|
| Python | 3.8+ | Executar a ferramenta |
| Git | qualquer | Clonar o repositorio alvo |
| Java | 11+ | Modulos II e III (compilar e testar o projeto alvo) |
| Maven | 3.6+ | Modulos II e III (rodar testes e benchmark) |

> **Observacao:** Java e Maven sao necessarios apenas para os Modulos II (benchmark) e III (cobertura de testes).
> Se o repositorio analisado nao usar Maven (ex: so tem codigo sem build system), ou se Maven nao estiver instalado,
> a ferramenta continua funcionando e entrega o Modulo I (analise estatica) e o relatorio normalmente.
> Use a flag `--sem-dinamico` para pular os Modulos II e III intencionalmente.

## Instalacao

```bash
git clone https://github.com/sordi1/auditoria-iso25010.git
cd auditoria-iso25010
pip install -r requirements.txt
```

## Uso

```bash
# Analise completa (inclui benchmark e cobertura de testes)
python main.py https://github.com/usuario/projeto-java

# Apenas analise estatica (sem subir a aplicacao, sem Maven)
python main.py https://github.com/usuario/projeto-java --sem-dinamico
```

## Saida

Ao final da execucao sao gerados:
- `relatorio_iso25010.pdf` — relatorio completo em PDF
- `relatorio_iso25010.html` — versao HTML do relatorio
- Status no terminal com parecer de conformidade
