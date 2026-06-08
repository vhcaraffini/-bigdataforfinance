# Premissas Setor Agricultura Acucar Alcool e Cana

## Cabecalho

| Campo | Valor |
|---|---|
| Setor | Agricultura (Acucar, Alcool e Cana) |
| Squad | GABRIELA ANTASZCZYSZYN, MILENA JULIANE FERRAZ DE ARAUJO RODRIGUES, RENAN DOBRIANSKY DA SILVA, VICTOR HUGO MORAIS CARAFFINI |
| Data | 2026-05-23 |
| Base de dados | `layer_02_silver.n1_dfp_cia_aberta_bp`, `layer_02_silver.n1_dfp_cia_aberta_dre`, `layer_02_silver.n1_dfp_cia_aberta_dfc` |
| Escopo | Contrato setorial da camada gold para os indicadores classicos, alinhado ao racional atual do projeto e ao caso COSAN |
| Status | Atualizado com regras de ativos biologicos, LPA via leaves de `3.99` e query da mart para todas as empresas |

## Notas Gerais Obrigatorias

### N1. Caixa para indicadores: quando usar BP e quando usar DFC

| Indicador | Conta correta | Conta incorreta | Motivo |
|---|---|---|---|
| Liquidez Imediata | `1.01.01` + `1.01.02` do BP | `6.05.02` da DFC | O indicador e definido sobre disponibilidades do balanco |
| Ativo Circulante Financeiro Fleuriet | `1.01.01` + `1.01.02` do BP | `6.05.02` da DFC | O modelo Fleuriet e estruturalmente baseado no balanco |
| Divida Liquida e EV | `6.05.02` da DFC | `1.01.01` isolado | A DFC captura equivalentes de caixa e efeitos de `CPC 03` e `CPC 31` |

### N2. Estoques ausentes

Regra:
- Usar `COALESCE(estoques, 0)` para `Liquidez Seca`.
- Para `Giro de Estoques`, `PMRE`, `Ciclo Economico` e `Ciclo Financeiro`, exibir `N/A` quando a empresa nao tiver base operacional de estoque.
- No setor agricola, a ausencia de `1.01.04` nao implica ausencia de ativo operacional de giro, porque a empresa pode reportar `1.01.05 - ATIVOS BIOLOGICOS`.

### N3. LPA: usar leaves originais da familia 3.99

Regra:
- Nao usar o pai `3.99` como primeira opcao analitica.
- Prioridade operacional: `3.99.02.01` `LPA Diluido ON`.
- Fallback: `3.99.01.01` `LPA Basico ON`.
- So usar `3.99` quando o objetivo for reproduzir exatamente o valor reportado na estrutura original, e isso deve ser documentado como excecao.

### N4. ST_CONTA_FIXA: como interpretar

Regra:
- `S`: conta padronizada da taxonomia CVM; preferencia maxima.
- `N`: conta livre da companhia; usar apenas quando a taxonomia padronizada nao fecha o conceito.
- `A validar`: familia candidata ainda nao validada no recorte setorial.
- Variaveis derivadas ficam com `N/A`.

### N5. Ativos Biologicos sao operacionais neste setor

Regra:
- `1.01.05 - ATIVOS BIOLOGICOS` deve ser tratado como ativo operacional de giro para empresas agricolas.
- `Liquidez Seca` deve remover `Estoques + Ativos Biologicos`.
- `Giro dos Estoques` e `PMRE` devem usar `Estoques + Ativos Biologicos`.
- `Ciclo Economico` e `Ciclo Financeiro` devem herdar o `PMRE` ajustado.
- Em `NCG`, os ativos biologicos entram do lado operacional, seja explicitamente em `ACO`, seja implicitamente via `AC - ACF`, dependendo da implementacao da mart.

### N6. CPV na DRE pode vir negativo

Regra:
- O valor de `3.02` deve ser usado com `ABS(CPV)` nos indicadores de atividade e prazos.
- Para margens, usar os saldos consolidados de `3.03`, `3.05` e `3.11` diretamente.

## Fichas de Variaveis

### V01. Ativo Total

| Campo | Valor |
|---|---|
| CD_CONTA | `1` |
| DS_CONTA | ATIVO TOTAL |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `PCT/AT`, `ROA`, `Imobilizacao do AT` |
| Atencao | Conta sintetica consolidada; nao exigir `IS_LEAF = TRUE` |

### V02. Ativo Circulante

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01` |
| DS_CONTA | ATIVO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Liquidez Corrente`, `Liquidez Seca`, `Giro AC`, `PMRAC`, `CGL`, `NCG` |
| Atencao | Base principal do capital de giro |

### V03. Ativo Nao Circulante

| Campo | Valor |
|---|---|
| CD_CONTA | `1.02` |
| DS_CONTA | ATIVO NAO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | Reconciliacao do BP e formula alternativa de `CGL` |
| Atencao | Variavel de suporte, nao entra sozinha na maior parte dos indicadores |

### V04. Realizavel a Longo Prazo

| Campo | Valor |
|---|---|
| CD_CONTA | `1.02.01` |
| DS_CONTA | ATIVO REALIZAVEL A LONGO PRAZO |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Liquidez Geral` |
| Atencao | Representa o conceito correto de realizavel fora do circulante |

### V05. Imobilizado

| Campo | Valor |
|---|---|
| CD_CONTA | `1.02.03` |
| DS_CONTA | IMOBILIZADO |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Imobilizacao CP`, `Imobilizacao AT` |
| Atencao | Valor liquido apos depreciacao acumulada |

### V06. Estoques

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.04` |
| DS_CONTA | ESTOQUES |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| COALESCE? | Sim, apenas nos casos definidos em N2 |
| Usado em | `Liquidez Seca`, `Giro Estoques`, `PMRE`, `Ciclos`, `NCG` |
| Atencao | No setor agricola deve ser lido junto com `V06B` |

### V06B. Ativos Biologicos

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.05` |
| DS_CONTA | ATIVOS BIOLOGICOS |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| COALESCE? | Sim, tratar como `0` quando ausente fora das empresas agricolas |
| Usado em | `Liquidez Seca`, `Giro Estoques Ajustado`, `PMRE Ajustado`, `Ciclo Economico`, `Ciclo Financeiro`, `NCG` |
| Atencao | Variavel setorial critica; deve entrar como estoque operacional, nao como disponibilidade |

### V07. Contas a Receber CP

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.03` |
| DS_CONTA | CONTAS A RECEBER |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Giro Contas a Receber`, `PMRV`, `NCG` |
| Atencao | Para a mart atual, o proxy padrao e curto prazo; recebiveis LP nao sao obrigatorios no indicador |

### V08. Clientes LP

| Campo | Valor |
|---|---|
| CD_CONTA | Subcontas livres de `1.02.01` |
| DS_CONTA | Variavel por empresa |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `N` |
| Usado em | Nao usado na mart padrao |
| Atencao | Desconsiderado por baixa padronizacao e baixa materialidade media |

### V09. Fornecedores

| Campo | Valor |
|---|---|
| CD_CONTA | `2.01.02` |
| DS_CONTA | FORNECEDORES |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Giro Contas a Pagar`, `PMPC`, `NCG` |
| Atencao | Proxy principal do passivo operacional de compras |

### V10. Passivo Circulante

| Campo | Valor |
|---|---|
| CD_CONTA | `2.01` |
| DS_CONTA | PASSIVO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Liquidez`, `Endividamento`, `CGL`, `Fleuriet` |
| Atencao | Conta sintetica consolidada |

### V11. Passivo Nao Circulante

| Campo | Valor |
|---|---|
| CD_CONTA | `2.02` |
| DS_CONTA | PASSIVO NAO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Liquidez Geral`, `PCT/CP`, `PCT/AT`, `Garantia`, `Composicao do Endividamento` |
| Atencao | Equivale ao conceito classico de `ELP` |

### V12. Patrimonio Liquido

| Campo | Valor |
|---|---|
| CD_CONTA | `2.03` |
| DS_CONTA | PATRIMONIO LIQUIDO CONSOLIDADO |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `ROE`, `ROI`, `PCT/CP`, `Garantia`, `Imobilizacao CP` |
| Atencao | Pode ser negativo; interpretar com cuidado no dashboard |

### V13. Emprestimos e Financiamentos CP

| Campo | Valor |
|---|---|
| CD_CONTA | `2.01.04` |
| DS_CONTA | EMPRESTIMOS E FINANCIAMENTOS |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| COALESCE? | Sim, quando a empresa nao tiver divida CP |
| Usado em | `ROI`, `PCF Fleuriet`, `ST` |
| Atencao | Passivo financeiro de curto prazo |

### V14. Emprestimos e Financiamentos LP

| Campo | Valor |
|---|---|
| CD_CONTA | `2.02.01` |
| DS_CONTA | EMPRESTIMOS E FINANCIAMENTOS |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| COALESCE? | Sim, quando a empresa nao tiver divida LP |
| Usado em | `ROI` |
| Atencao | Passivo oneroso de longo prazo |

### V15. Aplicacoes Financeiras

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.02` |
| DS_CONTA | APLICACOES FINANCEIRAS |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| COALESCE? | Sim |
| Usado em | `Liquidez Imediata`, `ACF`, `ST` |
| Atencao | Junto com `V22`, fecha disponibilidades do BP |

### V16. PCF Fleuriet

| Campo | Valor |
|---|---|
| CD_CONTA | `V13` |
| DS_CONTA | DERIVADA A PARTIR DE EMPRESTIMOS CP |
| Tabela Silver | DERIVADA |
| ST_CONTA_FIXA | `N/A` |
| Usado em | `ST`, `Efeito Tesoura` |
| Atencao | Na implementacao atual, `PCF = Emprestimos CP` |

### V17. Receita Liquida de Vendas

| Campo | Valor |
|---|---|
| CD_CONTA | `3.01` |
| DS_CONTA | RECEITA DE VENDA DE BENS E/OU SERVICOS |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Margens`, `Giros`, `PMRV`, `PMRAC` |
| Atencao | Ja e receita liquida na taxonomia CVM |

### V18. CPV CMV COGS

| Campo | Valor |
|---|---|
| CD_CONTA | `3.02` |
| DS_CONTA | CUSTO DOS BENS E/OU SERVICOS VENDIDOS |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Giro Estoques`, `Giro Fornecedores`, `PMRE`, `PMPC` |
| Atencao | Usar `ABS(CPV)` para indicadores de atividade |

### V19. Lucro Bruto

| Campo | Valor |
|---|---|
| CD_CONTA | `3.03` |
| DS_CONTA | RESULTADO BRUTO |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Margem Bruta` |
| Atencao | Preferir a conta consolidada em vez de recalcular |

### V20. EBIT Resultado Operacional

| Campo | Valor |
|---|---|
| CD_CONTA | `3.05` |
| DS_CONTA | RESULTADO ANTES DO RESULTADO FINANCEIRO E DOS TRIBUTOS |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Margem Operacional`, `EBITDA` |
| Atencao | Nao usar `3.07` para margem operacional |

### V21. Lucro Liquido do Exercicio

| Campo | Valor |
|---|---|
| CD_CONTA | `3.11` |
| DS_CONTA | LUCRO/PREJUIZO CONSOLIDADO DO PERIODO |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Margem Liquida`, `ROA`, `ROE`, `ROI` |
| Atencao | Base consolidada padrao do contrato |

### V22. Caixa e Equivalentes BP

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.01` |
| DS_CONTA | CAIXA E EQUIVALENTES DE CAIXA |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` |
| Usado em | `Liquidez Imediata`, `ACF`, `ST` |
| Atencao | Para liquidez, usar BP; nao substituir por DFC |

### V23. Caixa Liquido das Atividades Operacionais

| Campo | Valor |
|---|---|
| CD_CONTA | `6.01` |
| DS_CONTA | CAIXA LIQUIDO ATIVIDADES OPERACIONAIS |
| Tabela Silver | `n1_dfp_cia_aberta_dfc` |
| ST_CONTA_FIXA | `S` |
| Usado em | Analise complementar |
| Atencao | Nao entra diretamente nos indicadores classicos principais da mart atual |

### V24. Saldo Final de Caixa DFC

| Campo | Valor |
|---|---|
| CD_CONTA | `6.05.02` |
| DS_CONTA | SALDO FINAL DE CAIXA E EQUIVALENTES |
| Tabela Silver | `n1_dfp_cia_aberta_dfc` |
| ST_CONTA_FIXA | `S` |
| Usado em | Divida Liquida e EV futuros |
| Atencao | Caixa economico correto para analise de divida liquida |

### V25. LPA Basico ON

| Campo | Valor |
|---|---|
| CD_CONTA | `3.99.01.01` |
| DS_CONTA | LUCRO BASICO POR ACAO ORDINARIA |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `N` |
| Usado em | `LPA` por fallback |
| Atencao | Nao usar pai reconstruido de `3.99` como primeira opcao |

### V26. LPA Diluido ON

| Campo | Valor |
|---|---|
| CD_CONTA | `3.99.02.01` |
| DS_CONTA | LUCRO DILUIDO POR ACAO ORDINARIA |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `N` |
| Usado em | `LPA` por prioridade |
| Atencao | Estrategia operacional: `COALESCE(V26, V25)` |

### V27. Divida Bruta

| Campo | Valor |
|---|---|
| CD_CONTA | `V13 + V14` |
| DS_CONTA | DERIVADA |
| Tabela Silver | DERIVADA |
| ST_CONTA_FIXA | `N/A` |
| Usado em | `Divida Liquida` futura |
| Atencao | Passivo oneroso total |

### V28. Divida Liquida

| Campo | Valor |
|---|---|
| CD_CONTA | `V27 - V24` |
| DS_CONTA | DERIVADA |
| Tabela Silver | DERIVADA |
| ST_CONTA_FIXA | `N/A` |
| Usado em | Analises futuras de capital |
| Atencao | Nao e usada no ROI da mart atual |

### V29. Capital Investido

| Campo | Valor |
|---|---|
| CD_CONTA | `V12 + V13 + V14` |
| DS_CONTA | DERIVADA |
| Tabela Silver | DERIVADA |
| ST_CONTA_FIXA | `N/A` |
| Usado em | `ROI` |
| Atencao | A premissa atual do projeto usa `PL + Emprestimos CP + Emprestimos LP` |

## Mapa Rapido Indicador para Variaveis

| Indicador | Formula | Variaveis necessarias |
|---|---|---|
| Liquidez Geral | `(AC + RLP) / (PC + ELP)` | `V02`, `V04`, `V10`, `V11` |
| Liquidez Corrente | `AC / PC` | `V02`, `V10` |
| Liquidez Seca Ajustada | `(AC - Estoques - Ativos Biologicos) / PC` | `V02`, `V06`, `V06B`, `V10` |
| Liquidez Imediata | `(Caixa + Aplicacoes) / PC` | `V22`, `V15`, `V10` |
| PCT/CP | `(PC + ELP) / PL` | `V10`, `V11`, `V12` |
| PCT/AT | `(PC + ELP) / AT` | `V10`, `V11`, `V01` |
| Garantia CP/CT | `PL / (PC + ELP)` | `V12`, `V10`, `V11` |
| Composicao de Endividamento | `PC / (PC + ELP)` | `V10`, `V11` |
| Imobilizacao do CP | `Imobilizado / PL` | `V05`, `V12` |
| Imobilizacao do AT | `Imobilizado / AT` | `V05`, `V01` |
| Margem Bruta | `Lucro Bruto / Receita Liquida` | `V19`, `V17` |
| Margem Operacional | `EBIT / Receita Liquida` | `V20`, `V17` |
| Margem Liquida | `Lucro Liquido / Receita Liquida` | `V21`, `V17` |
| LPA | `COALESCE(LPA Diluido ON, LPA Basico ON)` | `V26`, `V25` |
| ROA | `Lucro Liquido / Ativo Total` | `V21`, `V01` |
| ROE | `Lucro Liquido / PL` | `V21`, `V12` |
| ROI | `Lucro Liquido / (PL + Emprestimos CP + Emprestimos LP)` | `V21`, `V12`, `V13`, `V14` |
| Giro dos Estoques Ajustado | `ABS(CPV) / (Estoques + Ativos Biologicos)` | `V18`, `V06`, `V06B` |
| Giro de Contas a Receber | `Receita Liquida / Contas a Receber` | `V17`, `V07` |
| Giro de Contas a Pagar | `ABS(CPV) / Fornecedores` | `V18`, `V09` |
| Giro do Ativo Circulante | `Receita Liquida / AC` | `V17`, `V02` |
| PMRE Ajustado | `((Estoques + Ativos Biologicos) * 360) / ABS(CPV)` | `V06`, `V06B`, `V18` |
| PMRV | `(Contas a Receber * 360) / Receita Liquida` | `V07`, `V17` |
| PMPC | `(Fornecedores * 360) / ABS(CPV)` | `V09`, `V18` |
| PMRAC | `(AC * 360) / Receita Liquida` | `V02`, `V17` |
| Ciclo Economico | `PMRE + PMRV` | `V06`, `V06B`, `V07`, `V17`, `V18` |
| Ciclo Financeiro | `PMRE + PMRV - PMPC` | `V06`, `V06B`, `V07`, `V09`, `V17`, `V18` |
| CGL CCL | `AC - PC` | `V02`, `V10` |
| NCG | `ACO - PCO` ou, na mart atual, `(AC - ACF) - (PC - PCF)` | `V02`, `V10`, `V22`, `V15`, `V13`, com `V06B` embutido no componente operacional do setor |
| Saldo de Tesouraria | `ACF - PCF` | `V22`, `V15`, `V13` |
| Efeito Tesoura | `ST negativo e piorando em sequencia` | Serie temporal de `ST` |

## Empresas-anomalia identificadas

Nenhuma empresa foi listada nominalmente ainda nesta versao.

Pendencias para preencher esta secao:
- empresas do setor com `1.01.05` material e sem `1.01.04`
- empresas com `PL` negativo
- empresas com `LPA` ausente mesmo tendo `3.11`
- empresas com divergencia relevante entre `1.01.01 + 1.01.02` e `6.05.02`

## Checklist de aderencia deste rascunho

- A regra setorial de `1.01.05 - ATIVOS BIOLOGICOS` foi incorporada.
- `Liquidez Seca`, `Giro dos Estoques`, `PMRE` e ciclos foram atualizados para a adaptacao agricola.
- `LPA` foi realinhado para `3.99.02.01` com fallback em `3.99.01.01`.
- `ROI` foi atualizado para `PL + Emprestimos CP + Emprestimos LP`.
- O racional de `Fleuriet` foi alinhado ao uso de `ACF`, `PCF`, `NCG` e `ST`.
- Ainda falta validacao empirica do recorte setorial para cobertura, materialidade e lista nominal de anomalias.
