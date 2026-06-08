DROP VIEW IF EXISTS "layer_03_gold"."vw_benchmark_indicadores_anual";

CREATE OR REPLACE VIEW "layer_03_gold"."vw_benchmark_indicadores_anual" AS
WITH base_long AS (
    SELECT
        m."CNPJ_CIA",
        m."RAZAO_SOCIAL" AS "DENOM_CIA",
        m."SETOR",
        m."ANO_FISCAL",
        ind."COD_INDICADOR",
        ind."VL_INDICADOR"
    FROM "layer_03_gold"."mart_indicadores_financeiros" m
    CROSS JOIN LATERAL (
        VALUES
            ('LIQ_GERAL', m."LIQ_GERAL"),
            ('LIQ_CORRENTE', m."LIQ_CORRENTE"),
            ('LIQ_SECA_AJUSTADA', m."LIQ_SECA_AJUSTADA"),
            ('LIQ_IMEDIATA', m."LIQ_IMEDIATA"),
            ('ENDIV_CP', m."ENDIV_CP"),
            ('ENDIV_TOTAL', m."ENDIV_TOTAL"),
            ('GARANTIA_CP_CT', m."GARANTIA_CP_CT"),
            ('COMPOSICAO_ENDIV', m."COMPOSICAO_ENDIV"),
            ('IMOB_PL', m."IMOB_PL"),
            ('IMOB_AT', m."IMOB_AT"),
            ('MARGEM_BRUTA', m."MARGEM_BRUTA"),
            ('MARGEM_OPERACIONAL', m."MARGEM_OPERACIONAL"),
            ('MARGEM_LIQUIDA', m."MARGEM_LIQUIDA"),
            ('LPA', m."LPA"),
            ('ROA', m."ROA"),
            ('ROE', m."ROE"),
            ('ROI', m."ROI"),
            ('GIRO_ESTOQUES_AJUSTADO', m."GIRO_ESTOQUES_AJUSTADO"),
            ('GIRO_CLIENTES', m."GIRO_CLIENTES"),
            ('GIRO_FORNECEDORES', m."GIRO_FORNECEDORES"),
            ('GIRO_AC', m."GIRO_AC"),
            ('PMRE_AJUSTADO', m."PMRE_AJUSTADO"),
            ('PMRV', m."PMRV"),
            ('PMPC', m."PMPC"),
            ('PMRAC', m."PMRAC"),
            ('CICLO_ECONOMICO', m."CICLO_ECONOMICO"),
            ('CICLO_FINANCEIRO', m."CICLO_FINANCEIRO"),
            ('NCG', m."NCG"),
            ('ST', m."ST"),
            ('CGL', m."CGL")
    ) ind("COD_INDICADOR", "VL_INDICADOR")
    WHERE m."ANO_FISCAL" IS NOT NULL
      AND ind."VL_INDICADOR" IS NOT NULL
),
mediana_geral AS (
    SELECT
        "ANO_FISCAL",
        "COD_INDICADOR",
        percentile_cont(0.5) WITHIN GROUP (ORDER BY "VL_INDICADOR") AS "MEDIANA_GERAL_ANO"
    FROM base_long
    GROUP BY 1, 2
),
mediana_setorial AS (
    SELECT
        "ANO_FISCAL",
        "SETOR",
        "COD_INDICADOR",
        percentile_cont(0.5) WITHIN GROUP (ORDER BY "VL_INDICADOR") AS "MEDIANA_SETOR_ANO"
    FROM base_long
    GROUP BY 1, 2, 3
)
SELECT
    b."CNPJ_CIA",
    b."DENOM_CIA",
    b."SETOR",
    b."ANO_FISCAL",
    b."COD_INDICADOR",
    b."VL_INDICADOR",
    g."MEDIANA_GERAL_ANO",
    s."MEDIANA_SETOR_ANO",
    b."VL_INDICADOR" - g."MEDIANA_GERAL_ANO" AS "DELTA_VS_GERAL",
    b."VL_INDICADOR" - s."MEDIANA_SETOR_ANO" AS "DELTA_VS_SETOR"
FROM base_long b
LEFT JOIN mediana_geral g
  ON g."ANO_FISCAL" = b."ANO_FISCAL"
 AND g."COD_INDICADOR" = b."COD_INDICADOR"
LEFT JOIN mediana_setorial s
  ON s."ANO_FISCAL" = b."ANO_FISCAL"
 AND s."SETOR" = b."SETOR"
 AND s."COD_INDICADOR" = b."COD_INDICADOR";
