# Contexto para o Codex — Criação da Tabela Gold de Indicadores Financeiros CVM

## 1. Objetivo do projeto

Este projeto faz parte de um pipeline de Engenharia de Dados Financeiros usando dados públicos da CVM, especialmente o dataset de DFP de companhias abertas:

- Fonte: https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp
- Banco: PostgreSQL
- Arquitetura: Medallion Architecture
  - Bronze: dados brutos da CVM
  - Silver: dados tratados, normalizados e validados
  - Gold: indicadores financeiros e tabelas prontas para análise

O objetivo desta etapa é criar uma tabela Gold com indicadores financeiros clássicos de análise de demonstrações financeiras, calculados a partir das três tabelas Silver já existentes:

- Balanço Patrimonial: `layer_02_silver.n1_dfp_cia_aberta_bp`
- Demonstração do Resultado: `layer_02_silver.n1_dfp_cia_aberta_dre`
- Demonstração do Fluxo de Caixa: `layer_02_silver.n1_dfp_cia_aberta_dfc`

A análise final do projeto irá comparar uma empresa específica com o seu setor e também com outros setores.

Empresa escolhida:

- Empresa: `COSAN S.A.`
- CNPJ: `50.746.577/0001-15`
- Setor: `Agricultura (Açúcar, Álcool e Cana)`

Regra importante para este setor/empresa:

- A conta `1.01.05 - ATIVOS BIOLÓGICOS` deve ser considerada nos cálculos operacionais, principalmente nos indicadores de atividade, ciclos e necessidade de capital de giro.
- Para empresas agrícolas, ativos biológicos são parte relevante da operação, com comportamento próximo de estoques operacionais.

---

## 2. Estrutura geral do projeto

Estrutura base esperada do repositório:

```text
bigdata_for_finance/
├── notebooks/
│   ├── 01_bronze/
│   ├── 02_silver/
│   └── 03_gold/
│
├── queries/
│
├── dashboard/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   └── views/
│
├── .env
├── requirements.txt
└── README.md
```

Schemas no PostgreSQL:

```sql
CREATE SCHEMA IF NOT EXISTS layer_01_bronze;
CREATE SCHEMA IF NOT EXISTS layer_02_silver;
CREATE SCHEMA IF NOT EXISTS layer_03_gold;
```

---

## 3. Estrutura das tabelas Silver

As três tabelas Silver possuem a mesma estrutura principal, com colunas em maiúsculo. Por isso, no PostgreSQL, usar sempre aspas duplas nos nomes das colunas.

Tabelas:

```sql
layer_02_silver.n1_dfp_cia_aberta_bp
layer_02_silver.n1_dfp_cia_aberta_dre
layer_02_silver.n1_dfp_cia_aberta_dfc
```

Colunas disponíveis:

```text
CNPJ_CIA
SETOR_ATIV
DT_REFER
DT_REFER_TRATADO
DT_REFER_ANO
VERSAO
DENOM_CIA
CD_CVM
GRUPO_DFP_TRATADO
DT_FIM_EXERC_TRATADO
DT_FIM_EXERC_ANO
CD_CONTA
CD_CONTA_QTD_DIGITOS
DS_CONTA
DS_CONTA_REPORTADA
FLAG_NORMALIZACAO
FLAG_RECONSTRUCAO
STATUS_MATH
CONTA_NOME_COMPLETO
VL_CONTA_TRATADO
ST_CONTA_FIXA
ST_CONTA_FIXA_REPORTADA
IS_LEAF
DS_NIVEL_1
DS_NIVEL_2
DS_NIVEL_3
DS_NIVEL_4
DS_NIVEL_5
_origem_tabela
```

Coluna de valor:

```sql
"VL_CONTA_TRATADO"
```

Coluna de código da conta:

```sql
"CD_CONTA"
```

Colunas principais de identificação da empresa:

```sql
"CNPJ_CIA"
"CD_CVM"
"DENOM_CIA"
"SETOR_ATIV"
```

Colunas principais de período:

```sql
"DT_REFER"
"DT_REFER_TRATADO"
"DT_REFER_ANO"
"DT_FIM_EXERC_TRATADO"
"DT_FIM_EXERC_ANO"
```

Para DFP anual, preferir usar:

```sql
"DT_FIM_EXERC_ANO"
```

---

## 4. Regras importantes do projeto

### 4.1. Colunas em maiúsculo

As consultas precisam usar aspas duplas:

```sql
SELECT "CD_CONTA", "DS_CONTA", "VL_CONTA_TRATADO"
FROM layer_02_silver.n1_dfp_cia_aberta_bp;
```

Não usar:

```sql
SELECT cd_conta, ds_conta, vl_conta_tratado
FROM layer_02_silver.n1_dfp_cia_aberta_bp;
```

### 4.2. Uso do `IS_LEAF`

A regra geral do projeto diz que, para somatórios analíticos, deve-se usar `"IS_LEAF" = TRUE` para evitar dupla contagem.

Porém, para cálculo de indicadores financeiros usando contas sintéticas já consolidadas da CVM, como `1`, `1.01`, `2.01`, `3.01`, etc., NÃO filtrar obrigatoriamente `IS_LEAF = TRUE`, porque essas contas são justamente as contas consolidadas que representam o total do grupo.

Exemplo: para Liquidez Corrente, usar diretamente:

- Ativo Circulante: `CD_CONTA = '1.01'`
- Passivo Circulante: `CD_CONTA = '2.01'`

### 4.3. Valores da DRE podem vir negativos

Na DRE, custos, despesas e impostos normalmente aparecem negativos. Para indicadores como margem bruta, margem operacional e margem líquida, usar diretamente os valores consolidados:

- Receita líquida: `3.01`
- Resultado bruto: `3.03`
- Resultado operacional: `3.05`
- Lucro líquido: `3.11`

Para indicadores que usam CPV no denominador ou numerador operacional, como giro de estoques e PMRE, usar `ABS(cpv)` quando necessário, pois `3.02` pode vir negativo.

---

## 5. Mapeamento de contas principais por demonstrativo

### 5.1. BP — Balanço Patrimonial

| Conceito | CD_CONTA | DS_CONTA |
|---|---|---|
| Ativo Total | `1` | ATIVO TOTAL |
| Ativo Circulante | `1.01` | ATIVO CIRCULANTE |
| Caixa e Equivalentes | `1.01.01` | CAIXA E EQUIVALENTES DE CAIXA |
| Aplicações Financeiras | `1.01.02` | APLICAÇÕES FINANCEIRAS |
| Contas a Receber / Clientes | `1.01.03` | CONTAS A RECEBER |
| Estoques | `1.01.04` | ESTOQUES |
| Ativos Biológicos | `1.01.05` | ATIVOS BIOLÓGICOS |
| Tributos a Recuperar | `1.01.06` | TRIBUTOS A RECUPERAR |
| Despesas Antecipadas | `1.01.07` | DESPESAS ANTECIPADAS |
| Outros Ativos Circulantes | `1.01.08` | OUTROS ATIVOS CIRCULANTES |
| Ativo Não Circulante | `1.02` | ATIVO NÃO CIRCULANTE |
| Realizável a Longo Prazo | `1.02.01` | ATIVO REALIZÁVEL A LONGO PRAZO |
| Investimentos | `1.02.02` | INVESTIMENTOS |
| Imobilizado | `1.02.03` | IMOBILIZADO |
| Intangível | `1.02.04` | INTANGÍVEL |
| Passivo Total | `2` | PASSIVO TOTAL |
| Passivo Circulante | `2.01` | PASSIVO CIRCULANTE |
| Obrigações Sociais e Trabalhistas | `2.01.01` | OBRIGAÇÕES SOCIAIS E TRABALHISTAS |
| Fornecedores | `2.01.02` | FORNECEDORES |
| Obrigações Fiscais | `2.01.03` | OBRIGAÇÕES FISCAIS |
| Empréstimos e Financiamentos CP | `2.01.04` | EMPRÉSTIMOS E FINANCIAMENTOS |
| Outras Obrigações | `2.01.05` | OUTRAS OBRIGAÇÕES |
| Provisões | `2.01.06` | PROVISÕES |
| Passivo Não Circulante | `2.02` | PASSIVO NÃO CIRCULANTE |
| Empréstimos e Financiamentos LP | `2.02.01` | EMPRÉSTIMOS E FINANCIAMENTOS |
| Patrimônio Líquido | `2.03` | PATRIMÔNIO LÍQUIDO CONSOLIDADO |

### 5.2. DRE — Demonstração do Resultado

| Conceito | CD_CONTA | DS_CONTA |
|---|---|---|
| Receita Líquida | `3.01` | RECEITA DE VENDA DE BENS E/OU SERVIÇOS |
| Receita Bruta | `3.01.01` | RECEITA BRUTA DE VENDAS E/OU SERVIÇOS |
| Custo dos Bens/Serviços Vendidos | `3.02` | CUSTO DOS BENS E/OU SERVIÇOS VENDIDOS |
| Resultado Bruto / Lucro Bruto | `3.03` | RESULTADO BRUTO |
| Despesas/Receitas Operacionais | `3.04` | DESPESAS/RECEITAS OPERACIONAIS |
| Resultado Operacional | `3.05` | RESULTADO ANTES DO RESULTADO FINANCEIRO E DOS TRIBUTOS |
| Resultado Financeiro | `3.06` | RESULTADO FINANCEIRO |
| Receitas Financeiras | `3.06.01` | RECEITAS FINANCEIRAS |
| Despesas Financeiras | `3.06.02` | DESPESAS FINANCEIRAS |
| Resultado Antes dos Tributos | `3.07` | RESULTADO ANTES DOS TRIBUTOS SOBRE O LUCRO |
| IR e CSLL | `3.08` | IMPOSTO DE RENDA E CONTRIBUIÇÃO SOCIAL SOBRE O LUCRO |
| Resultado Líquido Operações Continuadas | `3.09` | RESULTADO LÍQUIDO DAS OPERAÇÕES CONTINUADAS |
| Resultado Líquido Operações Descontinuadas | `3.10` | RESULTADO LÍQUIDO DE OPERAÇÕES DESCONTINUADAS |
| Lucro/Prejuízo Consolidado | `3.11` | LUCRO/PREJUÍZO CONSOLIDADO DO PERÍODO |
| Lucro por Ação reportado | `3.99` | LUCRO POR AÇÃO - (REAIS / AÇÃO) |

### 5.3. DFC — Demonstração do Fluxo de Caixa

| Conceito | CD_CONTA | DS_CONTA |
|---|---|---|
| Caixa Líquido das Atividades Operacionais | `6.01` | CAIXA LÍQUIDO ATIVIDADES OPERACIONAIS |
| Caixa Gerado nas Operações | `6.01.01` | CAIXA GERADO NAS OPERAÇÕES |
| Variações nos Ativos e Passivos | `6.01.02` | VARIAÇÕES NOS ATIVOS E PASSIVOS |
| Caixa Líquido de Investimento | `6.02` | CAIXA LÍQUIDO ATIVIDADES DE INVESTIMENTO |
| Caixa Líquido de Financiamento | `6.03` | CAIXA LÍQUIDO ATIVIDADES DE FINANCIAMENTO |
| Variação Cambial sobre Caixa | `6.04` | VARIAÇÃO CAMBIAL SOBRE CAIXA E EQUIVALENTES |
| Aumento/Redução de Caixa | `6.05` | AUMENTO (REDUÇÃO) DE CAIXA E EQUIVALENTES |
| Saldo Inicial de Caixa | `6.05.01` | SALDO INICIAL DE CAIXA E EQUIVALENTES |
| Saldo Final de Caixa | `6.05.02` | SALDO FINAL DE CAIXA E EQUIVALENTES |

---

## 6. Indicadores a calcular

Os indicadores vêm de um guia de indicadores financeiros clássicos, organizado em sete grupos:

1. Liquidez
2. Endividamento e estrutura de capital
3. Margens de lucro
4. Rentabilidade
5. Atividade: giros e prazos
6. Ciclos
7. Recursos financeiros / Modelo Fleuriet

### 6.1. Liquidez

| Código | Indicador | Fórmula | Contas |
|---|---|---|---|
| `LIQ_GERAL` | Liquidez Geral | `(AC + RLP) / (PC + PNC)` | `1.01`, `1.02.01`, `2.01`, `2.02` |
| `LIQ_CORRENTE` | Liquidez Corrente | `AC / PC` | `1.01`, `2.01` |
| `LIQ_SECA` | Liquidez Seca | `(AC - Estoques - Ativos Biológicos) / PC` | `1.01`, `1.01.04`, `1.01.05`, `2.01` |
| `LIQ_IMEDIATA` | Liquidez Imediata | `(Caixa + Aplicações Financeiras) / PC` | `1.01.01`, `1.01.02`, `2.01` |

Observação sobre a COSAN/setor agrícola:

- Para Liquidez Seca, remover também `1.01.05 - ATIVOS BIOLÓGICOS`, além dos estoques.
- Justificativa: ativos biológicos não são disponibilidade imediata e têm realização operacional mais lenta.

### 6.2. Endividamento

| Código | Indicador | Fórmula | Contas |
|---|---|---|---|
| `END_CT_CP` | Capital de Terceiros / Capital Próprio | `(PC + PNC) / PL` | `2.01`, `2.02`, `2.03` |
| `END_CT_AT` | Capital de Terceiros / Ativo Total | `(PC + PNC) / AT` | `2.01`, `2.02`, `1` |
| `END_GARANTIA_CP_CT` | Garantia de Capital Próprio ao Capital de Terceiros | `PL / (PC + PNC)` | `2.03`, `2.01`, `2.02` |
| `END_COMPOSICAO` | Composição do Endividamento | `PC / (PC + PNC)` | `2.01`, `2.02` |
| `END_IMOB_CP` | Imobilização do Capital Próprio | `Imobilizado / PL` | `1.02.03`, `2.03` |
| `END_IMOB_AT` | Imobilização do Ativo Total | `Imobilizado / AT` | `1.02.03`, `1` |

### 6.3. Margens de lucro

| Código | Indicador | Fórmula | Contas |
|---|---|---|---|
| `MARG_BRUTA` | Margem Bruta | `Resultado Bruto / Receita Líquida` | `3.03`, `3.01` |
| `MARG_OPERACIONAL` | Margem Operacional | `Resultado Operacional / Receita Líquida` | `3.05`, `3.01` |
| `MARG_LIQUIDA` | Margem Líquida | `Lucro Líquido / Receita Líquida` | `3.11`, `3.01` |
| `LPA_REPORTADO` | Lucro por Ação reportado | valor direto do `3.99` | `3.99` |

Observação:

- O LPA clássico é `Lucro Líquido / Número de Ações`, mas o número de ações não está disponível nas três tabelas atuais.
- Portanto, por enquanto, usar o valor reportado em `3.99`, se existir.

### 6.4. Rentabilidade

| Código | Indicador | Fórmula | Contas |
|---|---|---|---|
| `RENT_ROA` | ROA | `Lucro Líquido / Ativo Total` | `3.11`, `1` |
| `RENT_ROE` | ROE | `Lucro Líquido / PL` | `3.11`, `2.03` |
| `RENT_ROI` | ROI | `Lucro Líquido / (Empréstimos CP + Empréstimos LP + PL)` | `3.11`, `2.01.04`, `2.02.01`, `2.03` |

### 6.5. Atividade: giros e prazos

| Código | Indicador | Fórmula | Contas |
|---|---|---|---|
| `ATIV_GIRO_ESTOQUES` | Giro dos Estoques Ajustado | `ABS(CPV) / (Estoques + Ativos Biológicos)` | `3.02`, `1.01.04`, `1.01.05` |
| `ATIV_GIRO_RECEBER` | Giro de Contas a Receber | `Receita Líquida / Contas a Receber` | `3.01`, `1.01.03` |
| `ATIV_GIRO_PAGAR` | Giro de Contas a Pagar | `ABS(CPV) / Fornecedores` | `3.02`, `2.01.02` |
| `ATIV_GIRO_AC` | Giro do Ativo Circulante | `Receita Líquida / AC` | `3.01`, `1.01` |
| `ATIV_PMRE` | PMRE Ajustado | `(Estoques + Ativos Biológicos) * 360 / ABS(CPV)` | `1.01.04`, `1.01.05`, `3.02` |
| `ATIV_PMRV` | PMRV | `Contas a Receber * 360 / Receita Líquida` | `1.01.03`, `3.01` |
| `ATIV_PMPC` | PMPC | `Fornecedores * 360 / ABS(CPV)` | `2.01.02`, `3.02` |
| `ATIV_PMRAC` | PMRAC | `AC * 360 / Receita Líquida` | `1.01`, `3.01` |

Observação sobre a COSAN/setor agrícola:

- Para o giro dos estoques e PMRE, usar `Estoques + Ativos Biológicos`.
- Nomear estes indicadores como ajustados para deixar claro que foi feita adaptação setorial.

### 6.6. Ciclos

| Código | Indicador | Fórmula |
|---|---|---|
| `CICLO_ECONOMICO` | Ciclo Econômico | `PMRE + PMRV` |
| `CICLO_FINANCEIRO` | Ciclo Financeiro | `PMRE + PMRV - PMPC` |

Usar o PMRE ajustado com ativos biológicos.

### 6.7. Recursos financeiros / Modelo Fleuriet

| Código | Indicador | Fórmula | Contas |
|---|---|---|---|
| `FLEURIET_CGL` | Capital de Giro Líquido / CCL | `AC - PC` | `1.01`, `2.01` |
| `FLEURIET_NCG` | Necessidade de Capital de Giro Ajustada | `ACO - PCO` | classificação operacional |
| `FLEURIET_ST` | Saldo de Tesouraria | `ACF - PCF` | classificação financeira |
| `DFC_SALDO_FINAL_CAIXA` | Saldo Final de Caixa DFC | valor direto do `6.05.02` | `6.05.02` |

Classificação inicial sugerida:

ACO — Ativo Circulante Operacional:

```text
1.01.03 - Contas a Receber
1.01.04 - Estoques
1.01.05 - Ativos Biológicos
1.01.06 - Tributos a Recuperar
1.01.07 - Despesas Antecipadas
1.01.08 - Outros Ativos Circulantes
```

ACF — Ativo Circulante Financeiro:

```text
1.01.01 - Caixa e Equivalentes de Caixa
1.01.02 - Aplicações Financeiras
```

PCO — Passivo Circulante Operacional:

```text
2.01.01 - Obrigações Sociais e Trabalhistas
2.01.02 - Fornecedores
2.01.03 - Obrigações Fiscais
2.01.05 - Outras Obrigações
2.01.06 - Provisões
```

PCF — Passivo Circulante Financeiro:

```text
2.01.04 - Empréstimos e Financiamentos
```

---

## 7. Estrutura recomendada para a camada Gold

Criar uma view/tabela intermediária com os saldos base por empresa e ano:

```sql
layer_03_gold.vw_saldos_base_indicadores
```

Essa view deve gerar uma linha por empresa, setor e ano, contendo colunas como:

```text
CNPJ_CIA
CD_CVM
DENOM_CIA
SETOR_ATIV
DT_FIM_EXERC_ANO
ativo_total
ativo_circulante
caixa_equivalentes
aplicacoes_financeiras
contas_receber
estoques
ativos_biologicos
ativo_operacional_circulante
ativo_financeiro_circulante
ativo_nao_circulante
realizavel_longo_prazo
imobilizado
passivo_total
passivo_circulante
obrigacoes_sociais_trabalhistas
fornecedores
obrigacoes_fiscais
emprestimos_financiamentos_cp
outras_obrigacoes
provisoes
passivo_operacional_circulante
passivo_financeiro_circulante
passivo_nao_circulante
emprestimos_financiamentos_lp
patrimonio_liquido
receita_liquida
cpv
lucro_bruto
resultado_operacional
lucro_liquido
lpa_reportado
caixa_operacional
saldo_final_caixa_dfc
```

Depois, criar a tabela final de indicadores:

```sql
layer_03_gold.indicadores_financeiros
```

Estrutura sugerida:

```sql
CREATE TABLE IF NOT EXISTS layer_03_gold.indicadores_financeiros (
    "CNPJ_CIA" TEXT,
    "CD_CVM" INTEGER,
    "DENOM_CIA" TEXT,
    "SETOR_ATIV" TEXT,
    "DT_FIM_EXERC_ANO" INTEGER,
    "GRUPO_INDICADOR" TEXT,
    "COD_INDICADOR" TEXT,
    "NOME_INDICADOR" TEXT,
    "VL_NUMERADOR" NUMERIC,
    "VL_DENOMINADOR" NUMERIC,
    "VL_INDICADOR" NUMERIC,
    "UNIDADE" TEXT,
    "INTERPRETACAO" TEXT,
    "STATUS_CALCULO" TEXT,
    "OBSERVACAO" TEXT,
    "DT_CRIACAO" TIMESTAMP DEFAULT NOW()
);
```

Regras de cálculo:

- Usar `NULLIF(denominador, 0)` para evitar divisão por zero.
- Quando o denominador for nulo ou zero, preencher `STATUS_CALCULO = 'DENOMINADOR_ZERO_OU_NULO'`.
- Quando alguma conta essencial estiver ausente, preencher `STATUS_CALCULO = 'CONTA_AUSENTE'`.
- Quando o cálculo for realizado, preencher `STATUS_CALCULO = 'OK'`.
- Usar `ABS(cpv)` para indicadores de atividade e prazos que usam CPV.
- Para indicadores percentuais, manter valor em decimal, por exemplo `0.25` para 25%, ou decidir padrão único e documentar. Recomendação: manter decimal e formatar no BI.

---

## 8. SQL base sugerido para a view de saldos

Este é um esqueleto inicial. O Codex deve adaptar, testar e corrigir conforme o projeto real.

```sql
CREATE OR REPLACE VIEW layer_03_gold.vw_saldos_base_indicadores AS
WITH bp AS (
    SELECT
        "CNPJ_CIA",
        "CD_CVM",
        "DENOM_CIA",
        "SETOR_ATIV",
        "DT_FIM_EXERC_ANO",
        SUM(CASE WHEN "CD_CONTA" = '1' THEN "VL_CONTA_TRATADO" END) AS ativo_total,
        SUM(CASE WHEN "CD_CONTA" = '1.01' THEN "VL_CONTA_TRATADO" END) AS ativo_circulante,
        SUM(CASE WHEN "CD_CONTA" = '1.01.01' THEN "VL_CONTA_TRATADO" END) AS caixa_equivalentes,
        SUM(CASE WHEN "CD_CONTA" = '1.01.02' THEN "VL_CONTA_TRATADO" END) AS aplicacoes_financeiras,
        SUM(CASE WHEN "CD_CONTA" = '1.01.03' THEN "VL_CONTA_TRATADO" END) AS contas_receber,
        SUM(CASE WHEN "CD_CONTA" = '1.01.04' THEN "VL_CONTA_TRATADO" END) AS estoques,
        SUM(CASE WHEN "CD_CONTA" = '1.01.05' THEN "VL_CONTA_TRATADO" END) AS ativos_biologicos,
        SUM(CASE WHEN "CD_CONTA" = '1.01.06' THEN "VL_CONTA_TRATADO" END) AS tributos_recuperar,
        SUM(CASE WHEN "CD_CONTA" = '1.01.07' THEN "VL_CONTA_TRATADO" END) AS despesas_antecipadas,
        SUM(CASE WHEN "CD_CONTA" = '1.01.08' THEN "VL_CONTA_TRATADO" END) AS outros_ativos_circulantes,
        SUM(CASE WHEN "CD_CONTA" = '1.02' THEN "VL_CONTA_TRATADO" END) AS ativo_nao_circulante,
        SUM(CASE WHEN "CD_CONTA" = '1.02.01' THEN "VL_CONTA_TRATADO" END) AS realizavel_longo_prazo,
        SUM(CASE WHEN "CD_CONTA" = '1.02.03' THEN "VL_CONTA_TRATADO" END) AS imobilizado,
        SUM(CASE WHEN "CD_CONTA" = '2' THEN "VL_CONTA_TRATADO" END) AS passivo_total,
        SUM(CASE WHEN "CD_CONTA" = '2.01' THEN "VL_CONTA_TRATADO" END) AS passivo_circulante,
        SUM(CASE WHEN "CD_CONTA" = '2.01.01' THEN "VL_CONTA_TRATADO" END) AS obrigacoes_sociais_trabalhistas,
        SUM(CASE WHEN "CD_CONTA" = '2.01.02' THEN "VL_CONTA_TRATADO" END) AS fornecedores,
        SUM(CASE WHEN "CD_CONTA" = '2.01.03' THEN "VL_CONTA_TRATADO" END) AS obrigacoes_fiscais,
        SUM(CASE WHEN "CD_CONTA" = '2.01.04' THEN "VL_CONTA_TRATADO" END) AS emprestimos_financiamentos_cp,
        SUM(CASE WHEN "CD_CONTA" = '2.01.05' THEN "VL_CONTA_TRATADO" END) AS outras_obrigacoes,
        SUM(CASE WHEN "CD_CONTA" = '2.01.06' THEN "VL_CONTA_TRATADO" END) AS provisoes,
        SUM(CASE WHEN "CD_CONTA" = '2.02' THEN "VL_CONTA_TRATADO" END) AS passivo_nao_circulante,
        SUM(CASE WHEN "CD_CONTA" = '2.02.01' THEN "VL_CONTA_TRATADO" END) AS emprestimos_financiamentos_lp,
        SUM(CASE WHEN "CD_CONTA" = '2.03' THEN "VL_CONTA_TRATADO" END) AS patrimonio_liquido
    FROM layer_02_silver.n1_dfp_cia_aberta_bp
    GROUP BY
        "CNPJ_CIA",
        "CD_CVM",
        "DENOM_CIA",
        "SETOR_ATIV",
        "DT_FIM_EXERC_ANO"
),
dre AS (
    SELECT
        "CNPJ_CIA",
        "CD_CVM",
        "DT_FIM_EXERC_ANO",
        SUM(CASE WHEN "CD_CONTA" = '3.01' THEN "VL_CONTA_TRATADO" END) AS receita_liquida,
        SUM(CASE WHEN "CD_CONTA" = '3.02' THEN "VL_CONTA_TRATADO" END) AS cpv,
        SUM(CASE WHEN "CD_CONTA" = '3.03' THEN "VL_CONTA_TRATADO" END) AS lucro_bruto,
        SUM(CASE WHEN "CD_CONTA" = '3.05' THEN "VL_CONTA_TRATADO" END) AS resultado_operacional,
        SUM(CASE WHEN "CD_CONTA" = '3.11' THEN "VL_CONTA_TRATADO" END) AS lucro_liquido,
        SUM(CASE WHEN "CD_CONTA" = '3.99' THEN "VL_CONTA_TRATADO" END) AS lpa_reportado
    FROM layer_02_silver.n1_dfp_cia_aberta_dre
    GROUP BY
        "CNPJ_CIA",
        "CD_CVM",
        "DT_FIM_EXERC_ANO"
),
dfc AS (
    SELECT
        "CNPJ_CIA",
        "CD_CVM",
        "DT_FIM_EXERC_ANO",
        SUM(CASE WHEN "CD_CONTA" = '6.01' THEN "VL_CONTA_TRATADO" END) AS caixa_operacional,
        SUM(CASE WHEN "CD_CONTA" = '6.05.02' THEN "VL_CONTA_TRATADO" END) AS saldo_final_caixa_dfc
    FROM layer_02_silver.n1_dfp_cia_aberta_dfc
    GROUP BY
        "CNPJ_CIA",
        "CD_CVM",
        "DT_FIM_EXERC_ANO"
)
SELECT
    bp.*,
    dre.receita_liquida,
    dre.cpv,
    dre.lucro_bruto,
    dre.resultado_operacional,
    dre.lucro_liquido,
    dre.lpa_reportado,
    dfc.caixa_operacional,
    dfc.saldo_final_caixa_dfc,
    COALESCE(bp.contas_receber, 0)
        + COALESCE(bp.estoques, 0)
        + COALESCE(bp.ativos_biologicos, 0)
        + COALESCE(bp.tributos_recuperar, 0)
        + COALESCE(bp.despesas_antecipadas, 0)
        + COALESCE(bp.outros_ativos_circulantes, 0) AS ativo_operacional_circulante,
    COALESCE(bp.caixa_equivalentes, 0)
        + COALESCE(bp.aplicacoes_financeiras, 0) AS ativo_financeiro_circulante,
    COALESCE(bp.obrigacoes_sociais_trabalhistas, 0)
        + COALESCE(bp.fornecedores, 0)
        + COALESCE(bp.obrigacoes_fiscais, 0)
        + COALESCE(bp.outras_obrigacoes, 0)
        + COALESCE(bp.provisoes, 0) AS passivo_operacional_circulante,
    COALESCE(bp.emprestimos_financiamentos_cp, 0) AS passivo_financeiro_circulante
FROM bp
LEFT JOIN dre
    ON dre."CNPJ_CIA" = bp."CNPJ_CIA"
   AND dre."CD_CVM" = bp."CD_CVM"
   AND dre."DT_FIM_EXERC_ANO" = bp."DT_FIM_EXERC_ANO"
LEFT JOIN dfc
    ON dfc."CNPJ_CIA" = bp."CNPJ_CIA"
   AND dfc."CD_CVM" = bp."CD_CVM"
   AND dfc."DT_FIM_EXERC_ANO" = bp."DT_FIM_EXERC_ANO";
```

---

## 9. Validações recomendadas

Após criar a view de saldos, validar a COSAN:

```sql
SELECT *
FROM layer_03_gold.vw_saldos_base_indicadores
WHERE "CNPJ_CIA" = '50.746.577/0001-15'
ORDER BY "DT_FIM_EXERC_ANO";
```

Validar se ativos biológicos existem para a COSAN:

```sql
SELECT
    "CNPJ_CIA",
    "DENOM_CIA",
    "SETOR_ATIV",
    "DT_FIM_EXERC_ANO",
    "CD_CONTA",
    "DS_CONTA",
    "VL_CONTA_TRATADO"
FROM layer_02_silver.n1_dfp_cia_aberta_bp
WHERE "CNPJ_CIA" = '50.746.577/0001-15'
  AND "CD_CONTA" = '1.01.05'
ORDER BY "DT_FIM_EXERC_ANO";
```

Validar empresas do setor:

```sql
SELECT DISTINCT
    "CNPJ_CIA",
    "DENOM_CIA",
    "SETOR_ATIV"
FROM layer_02_silver.n1_dfp_cia_aberta_bp
WHERE "SETOR_ATIV" = 'Agricultura (Açúcar, Álcool e Cana)'
ORDER BY "DENOM_CIA";
```

Comparação COSAN vs setor:

```sql
SELECT
    "DT_FIM_EXERC_ANO",
    "COD_INDICADOR",
    "NOME_INDICADOR",
    AVG("VL_INDICADOR") FILTER (WHERE "SETOR_ATIV" = 'Agricultura (Açúcar, Álcool e Cana)') AS media_setor,
    MAX("VL_INDICADOR") FILTER (WHERE "CNPJ_CIA" = '50.746.577/0001-15') AS cosan
FROM layer_03_gold.indicadores_financeiros
WHERE "COD_INDICADOR" IN (
    'LIQ_CORRENTE',
    'LIQ_SECA',
    'MARG_LIQUIDA',
    'RENT_ROE',
    'ATIV_PMRE',
    'CICLO_FINANCEIRO',
    'FLEURIET_NCG',
    'FLEURIET_ST'
)
GROUP BY
    "DT_FIM_EXERC_ANO",
    "COD_INDICADOR",
    "NOME_INDICADOR"
ORDER BY
    "DT_FIM_EXERC_ANO",
    "COD_INDICADOR";
```

---

## 10. Entregáveis esperados para o Codex

Criar preferencialmente os seguintes arquivos:

```text
queries/03_gold/01_create_vw_saldos_base_indicadores.sql
queries/03_gold/02_create_indicadores_financeiros.sql
queries/03_gold/03_insert_indicadores_financeiros.sql
queries/03_gold/04_validacoes_indicadores_cosan.sql
notebooks/03_gold/01_indicadores_financeiros.ipynb
```

Se a pasta `queries/03_gold/` não existir, criar.

---

## 11. Boas práticas

- Usar CTEs para legibilidade.
- Usar aspas duplas nas colunas em maiúsculo.
- Não alterar tabelas Silver.
- Criar tudo na camada `layer_03_gold`.
- Usar `NULLIF` para evitar divisão por zero.
- Documentar adaptações setoriais, especialmente uso de `1.01.05 - ATIVOS BIOLÓGICOS`.
- Validar primeiro a COSAN, depois o setor, depois todos os setores.
- Não fazer alterações destrutivas sem necessidade.
- Criar scripts idempotentes quando possível (`CREATE OR REPLACE VIEW`, `CREATE TABLE IF NOT EXISTS`, `TRUNCATE + INSERT` ou `DROP TABLE IF EXISTS + CREATE TABLE` com cuidado).

---

# Prompts recomendados para continuar no Codex

## Prompt 1 — Criar a estrutura Gold de saldos base

```text
Leia o arquivo `contexto_codex_indicadores_cvm.md` e implemente a primeira etapa da camada Gold.

Objetivo:
Criar o arquivo `queries/03_gold/01_create_vw_saldos_base_indicadores.sql` com uma view chamada `layer_03_gold.vw_saldos_base_indicadores`.

Regras:
- Usar as tabelas Silver:
  - `layer_02_silver.n1_dfp_cia_aberta_bp`
  - `layer_02_silver.n1_dfp_cia_aberta_dre`
  - `layer_02_silver.n1_dfp_cia_aberta_dfc`
- Usar `"CD_CONTA"` e `"VL_CONTA_TRATADO"`.
- Usar aspas duplas nos nomes das colunas.
- Criar uma linha por empresa e ano.
- Incluir as contas necessárias para calcular liquidez, endividamento, margens, rentabilidade, atividade, ciclos e Fleuriet.
- Incluir `1.01.05 - ATIVOS BIOLÓGICOS` como coluna própria e também dentro do ativo operacional circulante.
- Não filtrar `IS_LEAF` para contas sintéticas principais.

Depois de criar o SQL, revise se ele está sintaticamente correto para PostgreSQL.
```

## Prompt 2 — Criar tabela final de indicadores

```text
Com base no arquivo `contexto_codex_indicadores_cvm.md` e na view `layer_03_gold.vw_saldos_base_indicadores`, crie o arquivo `queries/03_gold/02_create_indicadores_financeiros.sql`.

Objetivo:
Criar a tabela `layer_03_gold.indicadores_financeiros` com os campos:
- `CNPJ_CIA`
- `CD_CVM`
- `DENOM_CIA`
- `SETOR_ATIV`
- `DT_FIM_EXERC_ANO`
- `GRUPO_INDICADOR`
- `COD_INDICADOR`
- `NOME_INDICADOR`
- `VL_NUMERADOR`
- `VL_DENOMINADOR`
- `VL_INDICADOR`
- `UNIDADE`
- `INTERPRETACAO`
- `STATUS_CALCULO`
- `OBSERVACAO`
- `DT_CRIACAO`

Use tipos adequados para PostgreSQL. O script deve ser idempotente.
```

## Prompt 3 — Inserir todos os indicadores

```text
Agora crie o arquivo `queries/03_gold/03_insert_indicadores_financeiros.sql`.

Objetivo:
Preencher `layer_03_gold.indicadores_financeiros` a partir da view `layer_03_gold.vw_saldos_base_indicadores`.

Indicadores obrigatórios:
1. Liquidez Geral
2. Liquidez Corrente
3. Liquidez Seca ajustada, removendo Estoques e Ativos Biológicos
4. Liquidez Imediata
5. Capital de Terceiros / Capital Próprio
6. Capital de Terceiros / Ativo Total
7. Garantia de Capital Próprio ao Capital de Terceiros
8. Composição do Endividamento
9. Imobilização do Capital Próprio
10. Imobilização do Ativo Total
11. Margem Bruta
12. Margem Operacional
13. Margem Líquida
14. LPA reportado, usando `3.99` quando existir
15. ROA
16. ROE
17. ROI
18. Giro dos Estoques Ajustado, usando Estoques + Ativos Biológicos
19. Giro de Contas a Receber
20. Giro de Contas a Pagar
21. Giro do Ativo Circulante
22. PMRE Ajustado, usando Estoques + Ativos Biológicos
23. PMRV
24. PMPC
25. PMRAC
26. Ciclo Econômico
27. Ciclo Financeiro
28. CGL/CCL
29. NCG ajustada
30. Saldo de Tesouraria
31. Saldo Final de Caixa DFC

Regras:
- Usar `NULLIF(denominador, 0)`.
- Usar `ABS(cpv)` nos indicadores de atividade que dependem de CPV.
- Quando denominador for nulo ou zero, preencher `STATUS_CALCULO = 'DENOMINADOR_ZERO_OU_NULO'`.
- Quando cálculo for possível, preencher `STATUS_CALCULO = 'OK'`.
- Manter percentuais em formato decimal, por exemplo `0.25` para 25%.
- Fazer `TRUNCATE layer_03_gold.indicadores_financeiros` antes do insert, se a tabela já existir.
- Usar CTEs para organizar os cálculos.
```

## Prompt 4 — Validar COSAN e setor agrícola

```text
Crie o arquivo `queries/03_gold/04_validacoes_indicadores_cosan.sql`.

Objetivo:
Criar consultas de validação para a empresa `COSAN S.A.`, CNPJ `50.746.577/0001-15`, setor `Agricultura (Açúcar, Álcool e Cana)`.

As validações devem incluir:
1. Conferir se a COSAN aparece na view de saldos base.
2. Conferir se existe valor para `1.01.05 - ATIVOS BIOLÓGICOS` por ano.
3. Conferir os indicadores da COSAN por ano.
4. Comparar COSAN vs média do setor por ano e indicador.
5. Comparar COSAN vs média geral dos demais setores por ano e indicador.
6. Listar indicadores com `STATUS_CALCULO` diferente de `OK`.
7. Verificar anos faltantes em BP, DRE e DFC para a COSAN.

Use SQL PostgreSQL com CTEs e aspas duplas nas colunas.
```

## Prompt 5 — Criar notebook de execução e documentação

```text
Crie o notebook `notebooks/03_gold/01_indicadores_financeiros.ipynb` para documentar e executar a criação da camada Gold de indicadores financeiros.

O notebook deve conter:
1. Explicação do objetivo da Gold de indicadores.
2. Conexão com PostgreSQL usando `.env` e SQLAlchemy.
3. Execução dos scripts SQL:
   - `queries/03_gold/01_create_vw_saldos_base_indicadores.sql`
   - `queries/03_gold/02_create_indicadores_financeiros.sql`
   - `queries/03_gold/03_insert_indicadores_financeiros.sql`
   - `queries/03_gold/04_validacoes_indicadores_cosan.sql`
4. Consultas de validação em DataFrames pandas.
5. Análise específica da COSAN S.A.
6. Comparação COSAN vs setor `Agricultura (Açúcar, Álcool e Cana)`.
7. Destaque documentado para a regra dos Ativos Biológicos (`1.01.05`).

Use prints com emojis seguindo o padrão do projeto.
```

## Prompt 6 — Revisão final de qualidade

```text
Revise todos os arquivos criados para a camada Gold de indicadores financeiros.

Checklist:
- As tabelas Silver não podem ser alteradas.
- Todos os objetos novos devem ficar em `layer_03_gold`.
- Colunas em maiúsculo devem estar com aspas duplas.
- `1.01.05 - ATIVOS BIOLÓGICOS` deve estar incluído nos cálculos ajustados para COSAN/setor agrícola.
- `LIQ_SECA` deve remover estoques e ativos biológicos.
- `PMRE` e `Giro dos Estoques` devem usar estoques + ativos biológicos.
- NCG deve incluir ativos biológicos no ativo operacional circulante.
- Indicadores com divisão devem usar `NULLIF`.
- Deve existir tratamento de `STATUS_CALCULO`.
- Deve haver consultas de validação para COSAN, setor e demais setores.

Depois, gere um resumo do que foi criado e a ordem correta de execução dos scripts.
```
