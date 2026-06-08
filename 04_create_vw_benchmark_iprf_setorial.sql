DROP VIEW IF EXISTS "layer_03_gold"."vw_benchmark_iprf_setorial";

CREATE OR REPLACE VIEW "layer_03_gold"."vw_benchmark_iprf_setorial" AS
WITH base AS (
    SELECT *
    FROM "layer_03_gold"."vw_iprf_empresas_anual"
    WHERE "SCORE_IPRF" IS NOT NULL
),
medianas AS (
    SELECT
        "ANO_FISCAL",
        "SETOR",
        percentile_cont(0.5) WITHIN GROUP (ORDER BY "SCORE_IPRF") AS "MEDIANA_IPRF_SETOR_ANO"
    FROM base
    GROUP BY 1, 2
)
SELECT
    b."CNPJ_CIA",
    b."DENOM_CIA",
    b."SETOR",
    b."ANO_FISCAL",
    b."SCORE_IPRF",
    b."FAIXA_IPRF",
    m."MEDIANA_IPRF_SETOR_ANO",
    DENSE_RANK() OVER (
        PARTITION BY b."ANO_FISCAL", b."SETOR"
        ORDER BY b."SCORE_IPRF" DESC NULLS LAST
    ) AS "RANK_IPRF_SETOR_ANO",
    ROUND(
        (100 * PERCENT_RANK() OVER (
            PARTITION BY b."ANO_FISCAL", b."SETOR"
            ORDER BY b."SCORE_IPRF"
        ))::numeric,
        2
    ) AS "PERCENTIL_IPRF_SETOR_ANO"
FROM base b
LEFT JOIN medianas m
  ON m."ANO_FISCAL" = b."ANO_FISCAL"
 AND m."SETOR" = b."SETOR";
