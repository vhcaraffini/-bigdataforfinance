# Big Data for Finance - Pipeline CVM

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Postgres](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

## Objetivo do Projeto

Este repositório concentra o projeto da disciplina de **Big Data for Finance**. A proposta é construir um pipeline completo de dados financeiros a partir dos dados públicos da **CVM**, saindo do dado bruto até a análise executiva.

O produto final é uma camada `gold` pronta para consumo analítico, com:

- demonstrativos financeiros anuais harmonizados;
- indicadores financeiros clássicos calculados a partir de `BP`, `DRE` e `DFC`;
- benchmarking por mediana anual contra toda a base e contra o setor;
- dashboard executivo em `Streamlit`;
- score de risco financeiro `IPRF`.

## Empresa Analisada

Na fase atual do projeto, a empresa foco é a **COSAN S.A.**

O dashboard final foi desenhado para:

- apresentar os demonstrativos anuais da companhia;
- comparar seus indicadores com a mediana de **todas as empresas da base**;
- comparar seus indicadores com a mediana do setor **Agricultura (Açúcar, Álcool e Cana)**;
- comparar o `IPRF` da Cosan com o das demais empresas do mesmo setor.

## O que é o IPRF

O **IPRF (Índice Preventivo de Risco Financeiro)** é um score sintético de saúde financeira incorporado ao projeto como complemento aos indicadores tradicionais.

Ele resume a situação financeira da empresa a partir de cinco dimensões:

- `Liquidez`
- `Rentabilidade`
- `Solvência`
- `Eficiência Operacional`
- `Geração de Caixa`

No projeto, o `IPRF` é usado para posicionar a `COSAN S.A.` frente aos pares setoriais e enriquecer a leitura executiva do dashboard.

## Contexto: por que isso é difícil?

Os dados da CVM são públicos, mas chegam com problemas reais de engenharia e contabilidade:

| Problema | Como tratamos |
| :--- | :--- |
| Múltiplas versões do mesmo documento | Deduplicação via `ROW_NUMBER()` |
| Empresas não reportam todas as contas | Reconstrução controlada de contas pai |
| Nomes de contas variam entre empresas | Normalização com mapeamento contábil |
| Hierarquia das contas precisa fechar | Validação matemática vertical |
| Demonstrativos podem vir inconsistentes | Regras de auditoria e flags |

## Escopo Analítico Atual

O projeto evoluiu de um pipeline didático para um caso aplicado de análise financeira empresarial. Hoje, o foco está em:

- `COSAN S.A.` como empresa principal do estudo;
- base anual `DFP`;
- comparação com a mediana anual da base completa;
- comparação com a mediana anual do setor `Agricultura (Açúcar, Álcool e Cana)`;
- construção de um painel executivo com indicadores e `IPRF`.

No contexto do setor agrícola, uma premissa importante é o tratamento de **Ativos Biológicos** (`CD_CONTA = 1.01.05`). Quando essa conta existir para a empresa, ela deve ser considerada nos indicadores operacionais apropriados, como liquidez seca ajustada, giro de estoques e ciclos.

## Os Três Demonstrativos Financeiros

### Balanço Patrimonial (BP)

Fotografia da empresa em um instante.

```text
Ativo = Passivo + Patrimônio Líquido
```

### Demonstração do Resultado (DRE)

Mostra o desempenho da empresa ao longo do período.

```text
Receita Líquida - Custos - Despesas = Lucro / Prejuízo
```

### Demonstração dos Fluxos de Caixa (DFC)

Mostra de onde veio e para onde foi o caixa no período.

```text
Saldo final de caixa da DFC ~= disponibilidades reportadas no BP
```

## Taxonomia CVM

Os códigos `CD_CONTA` são hierárquicos. Exemplo:

```text
1
├── 1.01
│   ├── 1.01.01
│   └── 1.01.02
└── 1.02
```

Na prática, isso significa que contas pai e filho precisam respeitar coerência matemática e semântica.

## Arquitetura Medallion

```text
Portal CVM -> Bronze -> Silver -> Gold -> Dashboard
```

### Bronze - `layer_01_bronze`

- ingestão bruta dos arquivos da CVM;
- sem transformação conceitual;
- preservação fiel da origem.

### Silver - `layer_02_silver`

- deduplicação;
- padronização de colunas;
- normalização de nomes de contas;
- validações matemáticas;
- flags de auditoria.

### Gold - `layer_03_gold`

- mart anual de indicadores financeiros;
- views de benchmark por mediana;
- views auxiliares para o dashboard;
- cálculo do `IPRF`;
- consumo final por análises e visualizações.

## Estrutura do Projeto

```text
big_data_for_finance/
├── notebooks/
│   ├── 01_bronze/
│   ├── 02_silver/
│   └── 03_gold/
├── queries/
├── dashboard/
│   ├── app.py
│   ├── config.py
│   ├── constants.py
│   ├── database.py
│   └── views/
├── .env
├── requirements.txt
└── README.md
```

## Camada Silver

As tabelas da `silver` seguem um formato padronizado para permitir empilhamento e auditoria. Entre as colunas mais importantes estão:

- `CD_CONTA`
- `DS_CONTA`
- `VL_CONTA_TRATADO`
- `STATUS_MATH`
- `FLAG_RECONSTRUCAO`
- `FLAG_NORMALIZACAO`
- `IS_LEAF`

Regra importante:

> Nunca some contas em análises finais sem considerar corretamente a granularidade e a hierarquia da taxonomia CVM.

## Camada Gold

A camada `gold` é onde os saldos harmonizados viram artefatos analíticos prontos para uso.

Ela concentra:

- indicadores financeiros clássicos;
- mart anual para comparação entre empresas;
- medianas anuais gerais;
- medianas anuais setoriais;
- score `IPRF` por empresa;
- benchmark setorial do `IPRF`;
- apoio direto ao dashboard executivo da `COSAN S.A.`.

## Fontes de Dados

| Dataset | Descrição | Link |
| :--- | :--- | :---: |
| Cadastro de Cias Abertas | Dados cadastrais | [Link](https://dados.cvm.gov.br/dataset/cia_aberta-cad) |
| DFP | Demonstrativos anuais | [Link](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) |
| ITR | Demonstrativos trimestrais | [Link](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) |
| FRE | Formulário de referência | [Link](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre) |

Diretório geral:

- `http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/`

## Tecnologias Utilizadas

| Categoria | Tecnologia | Uso |
| :--- | :--- | :--- |
| Linguagem | Python 3.10+ | Pipeline, notebooks e app |
| Banco de dados | PostgreSQL | Armazenamento das camadas |
| Notebooks | Jupyter / VS Code | Exploração e desenvolvimento |
| Dashboard | Streamlit + Plotly | Visualização executiva |
| Conexão | SQLAlchemy + psycopg2 | Interface Python e PostgreSQL |
| Dados | pandas | Transformação e análise |
| Configuração | python-dotenv | Credenciais e ambiente |

## Setup do Projeto

### 1. Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- [VS Code](https://code.visualstudio.com/)
- [Git](https://git-scm.com/downloads)

### 2. Estrutura mínima

Crie as pastas:

- `notebooks/01_bronze/`
- `notebooks/02_silver/`
- `notebooks/03_gold/`
- `queries/`
- `dashboard/`

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o `.env`

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bigdata_for_finance
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

Se o código local estiver configurado para `DB_PASS`, mantenha a mesma senha também nessa chave:

```env
DB_PASS=sua_senha
```

### 5. Crie o banco e os schemas

```sql
CREATE DATABASE bigdata_for_finance;

\c bigdata_for_finance

CREATE SCHEMA IF NOT EXISTS layer_01_bronze;
CREATE SCHEMA IF NOT EXISTS layer_02_silver;
CREATE SCHEMA IF NOT EXISTS layer_03_gold;
```

## Como abrir o dashboard

Na raiz do projeto:

```powershell
C:\Users\renan\AppData\Local\Programs\Python\Python312\python.exe -m streamlit run dashboard/app.py
```

Depois abra:

```text
http://localhost:8501
```

## Regras Inegociáveis

1. Não sobrescrever valores originais da CVM sem justificativa contábil clara.
2. Tratar deduplicação antes de qualquer análise.
3. Manter rastreabilidade das transformações.
4. Preferir SQL com CTEs para legibilidade.
5. Validar fórmulas sensíveis com amostras reais antes de publicar resultados.

## Resultado Esperado

Ao final, o projeto entrega:

- pipeline financeiro `Bronze -> Silver -> Gold`;
- benchmarking anual entre empresas;
- painel executivo da `COSAN S.A.`;
- leitura integrada de demonstrativos, indicadores e `IPRF`.

---

Projeto desenvolvido na disciplina de Big Data for Finance pelo Prof. Ivan Ribeiro Mello.
