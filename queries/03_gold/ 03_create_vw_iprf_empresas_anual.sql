DROP VIEW IF EXISTS "layer_03_gold"."vw_iprf_empresas_anual";

CREATE OR REPLACE VIEW "layer_03_gold"."vw_iprf_empresas_anual" AS
WITH base AS (
    SELECT
        m."CNPJ_CIA",
        m."RAZAO_SOCIAL" AS "DENOM_CIA",
        m."SETOR",
        m."ANO_FISCAL",
        m."LIQ_CORRENTE",
        m."LIQ_SECA_AJUSTADA",
        m."COB_CAIXA_OPERACIONAL",
        m."MARGEM_EBITDA",
        m."MARGEM_LIQUIDA",
        m."ROA",
        m."DL_EBITDA",
        m."GRAU_ENDIVIDAMENTO",
        m."CCC",
        m."GIRO_ATIVO_TOTAL",
        m."MARGEM_CAIXA_OPERACIONAL",
        m."COBERTURA_DIVIDA_CAIXA",
        m."INTENSIDADE_REINVESTIMENTO"
    FROM "layer_03_gold"."mart_indicadores_financeiros" m
    WHERE m."ANO_FISCAL" IS NOT NULL
),
notas AS (
    SELECT
        b.*,
        CASE
            WHEN b."LIQ_CORRENTE" IS NULL THEN NULL
            WHEN b."LIQ_CORRENTE" <= 0.8 THEN 0.0
            WHEN b."LIQ_CORRENTE" >= 2.0 THEN 10.0
            ELSE ROUND((10.0 * (b."LIQ_CORRENTE" - 0.8) / 1.2)::numeric, 4)
        END AS "NOTA_LIQ_CORRENTE",
        CASE
            WHEN b."LIQ_SECA_AJUSTADA" IS NULL THEN NULL
            WHEN b."LIQ_SECA_AJUSTADA" <= 0.6 THEN 0.0
            WHEN b."LIQ_SECA_AJUSTADA" >= 1.5 THEN 10.0
            ELSE ROUND((10.0 * (b."LIQ_SECA_AJUSTADA" - 0.6) / 0.9)::numeric, 4)
        END AS "NOTA_LIQ_SECA",
        CASE
            WHEN b."COB_CAIXA_OPERACIONAL" IS NULL THEN NULL
            WHEN b."COB_CAIXA_OPERACIONAL" <= 0.05 THEN 0.0
            WHEN b."COB_CAIXA_OPERACIONAL" >= 0.40 THEN 10.0
            ELSE ROUND((10.0 * (b."COB_CAIXA_OPERACIONAL" - 0.05) / 0.35)::numeric, 4)
        END AS "NOTA_COB_CAIXA_OPERACIONAL",
        CASE
            WHEN b."MARGEM_EBITDA" IS NULL THEN NULL
            WHEN b."MARGEM_EBITDA" <= 0.05 THEN 0.0
            WHEN b."MARGEM_EBITDA" >= 0.35 THEN 10.0
            ELSE ROUND((10.0 * (b."MARGEM_EBITDA" - 0.05) / 0.30)::numeric, 4)
        END AS "NOTA_MARGEM_EBITDA",
        CASE
            WHEN b."MARGEM_LIQUIDA" IS NULL THEN NULL
            WHEN b."MARGEM_LIQUIDA" <= 0.00 THEN 0.0
            WHEN b."MARGEM_LIQUIDA" >= 0.20 THEN 10.0
            ELSE ROUND((10.0 * b."MARGEM_LIQUIDA" / 0.20)::numeric, 4)
        END AS "NOTA_MARGEM_LIQUIDA",
        CASE
            WHEN b."ROA" IS NULL THEN NULL
            WHEN b."ROA" <= 0.00 THEN 0.0
            WHEN b."ROA" >= 0.15 THEN 10.0
            ELSE ROUND((10.0 * b."ROA" / 0.15)::numeric, 4)
        END AS "NOTA_ROA",
        CASE
            WHEN b."DL_EBITDA" IS NULL THEN NULL
            WHEN b."DL_EBITDA" >= 5.0 THEN 0.0
            WHEN b."DL_EBITDA" <= 0.5 THEN 10.0
            ELSE ROUND((10.0 * (5.0 - b."DL_EBITDA") / 4.5)::numeric, 4)
        END AS "NOTA_DL_EBITDA",
        CASE
            WHEN b."GRAU_ENDIVIDAMENTO" IS NULL THEN NULL
            WHEN b."GRAU_ENDIVIDAMENTO" >= 0.90 THEN 0.0
            WHEN b."GRAU_ENDIVIDAMENTO" <= 0.30 THEN 10.0
            ELSE ROUND((10.0 * (0.90 - b."GRAU_ENDIVIDAMENTO") / 0.60)::numeric, 4)
        END AS "NOTA_GRAU_ENDIVIDAMENTO",
        CASE
            WHEN b."CCC" IS NULL THEN NULL
            WHEN b."CCC" >= 180.0 THEN 0.0
            WHEN b."CCC" <= 0.0 THEN 10.0
            ELSE ROUND((10.0 * (180.0 - b."CCC") / 180.0)::numeric, 4)
        END AS "NOTA_CCC",
        CASE
            WHEN b."GIRO_ATIVO_TOTAL" IS NULL THEN NULL
            WHEN b."GIRO_ATIVO_TOTAL" <= 0.20 THEN 0.0
            WHEN b."GIRO_ATIVO_TOTAL" >= 1.20 THEN 10.0
            ELSE ROUND((10.0 * (b."GIRO_ATIVO_TOTAL" - 0.20) / 1.00)::numeric, 4)
        END AS "NOTA_GIRO_ATIVO_TOTAL",
        CASE
            WHEN b."MARGEM_CAIXA_OPERACIONAL" IS NULL THEN NULL
            WHEN b."MARGEM_CAIXA_OPERACIONAL" <= 0.03 THEN 0.0
            WHEN b."MARGEM_CAIXA_OPERACIONAL" >= 0.25 THEN 10.0
            ELSE ROUND((10.0 * (b."MARGEM_CAIXA_OPERACIONAL" - 0.03) / 0.22)::numeric, 4)
        END AS "NOTA_MARGEM_CAIXA_OPERACIONAL",
        CASE
            WHEN b."COBERTURA_DIVIDA_CAIXA" IS NULL THEN NULL
            WHEN b."COBERTURA_DIVIDA_CAIXA" <= 0.05 THEN 0.0
            WHEN b."COBERTURA_DIVIDA_CAIXA" >= 0.40 THEN 10.0
            ELSE ROUND((10.0 * (b."COBERTURA_DIVIDA_CAIXA" - 0.05) / 0.35)::numeric, 4)
        END AS "NOTA_COBERTURA_DIVIDA_CAIXA",
        CASE
            WHEN b."INTENSIDADE_REINVESTIMENTO" IS NULL THEN NULL
            WHEN b."INTENSIDADE_REINVESTIMENTO" < 0 THEN 0.0
            ELSE ROUND(
                GREATEST(
                    0.0,
                    10.0 - ABS(b."INTENSIDADE_REINVESTIMENTO" - 0.30) * (10.0 / 0.30)
                )::numeric,
                4
            )
        END AS "NOTA_INTENSIDADE_REINVESTIMENTO"
    FROM base b
),
dimensoes AS (
    SELECT
        n.*,
        (
            COALESCE(n."NOTA_LIQ_CORRENTE", 0)
            + COALESCE(n."NOTA_LIQ_SECA", 0)
            + COALESCE(n."NOTA_COB_CAIXA_OPERACIONAL", 0)
        ) / NULLIF(
            (CASE WHEN n."NOTA_LIQ_CORRENTE" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_LIQ_SECA" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_COB_CAIXA_OPERACIONAL" IS NOT NULL THEN 1 ELSE 0 END),
            0
        ) AS "SCORE_LIQUIDEZ",
        (
            COALESCE(n."NOTA_MARGEM_EBITDA", 0)
            + COALESCE(n."NOTA_MARGEM_LIQUIDA", 0)
            + COALESCE(n."NOTA_ROA", 0)
        ) / NULLIF(
            (CASE WHEN n."NOTA_MARGEM_EBITDA" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_MARGEM_LIQUIDA" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_ROA" IS NOT NULL THEN 1 ELSE 0 END),
            0
        ) AS "SCORE_RENTABILIDADE",
        (
            COALESCE(n."NOTA_DL_EBITDA", 0)
            + COALESCE(n."NOTA_GRAU_ENDIVIDAMENTO", 0)
        ) / NULLIF(
            (CASE WHEN n."NOTA_DL_EBITDA" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_GRAU_ENDIVIDAMENTO" IS NOT NULL THEN 1 ELSE 0 END),
            0
        ) AS "SCORE_SOLVENCIA",
        (
            COALESCE(n."NOTA_CCC", 0)
            + COALESCE(n."NOTA_GIRO_ATIVO_TOTAL", 0)
        ) / NULLIF(
            (CASE WHEN n."NOTA_CCC" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_GIRO_ATIVO_TOTAL" IS NOT NULL THEN 1 ELSE 0 END),
            0
        ) AS "SCORE_EFICIENCIA",
        (
            COALESCE(n."NOTA_MARGEM_CAIXA_OPERACIONAL", 0)
            + COALESCE(n."NOTA_COBERTURA_DIVIDA_CAIXA", 0)
            + COALESCE(n."NOTA_INTENSIDADE_REINVESTIMENTO", 0)
        ) / NULLIF(
            (CASE WHEN n."NOTA_MARGEM_CAIXA_OPERACIONAL" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_COBERTURA_DIVIDA_CAIXA" IS NOT NULL THEN 1 ELSE 0 END)
            + (CASE WHEN n."NOTA_INTENSIDADE_REINVESTIMENTO" IS NOT NULL THEN 1 ELSE 0 END),
            0
        ) AS "SCORE_GERACAO_CAIXA"
    FROM notas n
),
iprf_final AS (
    SELECT
        d.*,
        (
            COALESCE(0.25 * d."SCORE_LIQUIDEZ", 0)
            + COALESCE(0.25 * d."SCORE_RENTABILIDADE", 0)
            + COALESCE(0.20 * d."SCORE_SOLVENCIA", 0)
            + COALESCE(0.15 * d."SCORE_EFICIENCIA", 0)
            + COALESCE(0.15 * d."SCORE_GERACAO_CAIXA", 0)
        ) / NULLIF(
            (CASE WHEN d."SCORE_LIQUIDEZ" IS NOT NULL THEN 0.25 ELSE 0 END)
            + (CASE WHEN d."SCORE_RENTABILIDADE" IS NOT NULL THEN 0.25 ELSE 0 END)
            + (CASE WHEN d."SCORE_SOLVENCIA" IS NOT NULL THEN 0.20 ELSE 0 END)
            + (CASE WHEN d."SCORE_EFICIENCIA" IS NOT NULL THEN 0.15 ELSE 0 END)
            + (CASE WHEN d."SCORE_GERACAO_CAIXA" IS NOT NULL THEN 0.15 ELSE 0 END),
            0
        ) AS "SCORE_IPRF"
    FROM dimensoes d
)
SELECT
    i.*,
    CASE
        WHEN i."SCORE_IPRF" >= 7 THEN 'Saudavel'
        WHEN i."SCORE_IPRF" >= 5 THEN 'Moderado'
        WHEN i."SCORE_IPRF" >= 3 THEN 'Alerta'
        WHEN i."SCORE_IPRF" IS NULL THEN NULL
        ELSE 'Critico'
    END AS "FAIXA_IPRF"
FROM iprf_final i;
