import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from constants import (
    COSAN_COLORS,
    IPRF_DIMENSION_SCORES,
    IPRF_INDICATORS,
    INDICATOR_META,
    PRIORITY_INDICATORS,
)
from database import (
    get_available_years,
    get_cosan_reference,
    get_indicator_benchmark,
    get_indicator_detail_table,
    get_iprf_history,
    get_iprf_sector_benchmark,
    get_iprf_sector_peers,
    get_iprf_year_detail,
    get_overview_history,
    get_overview_snapshot,
    get_priority_indicator_history,
    get_sector_indicator_ranking,
    get_statement_data,
    get_statement_highlights,
)


STATEMENT_TITLES = {
    "BP": "Balanco Patrimonial",
    "DRE": "Demonstracao do Resultado",
    "DFC": "Demonstracao do Fluxo de Caixa",
}

HIGHLIGHT_LABELS = {
    "1": "Ativo Total",
    "1.01": "Ativo Circulante",
    "1.02": "Ativo Nao Circulante",
    "2": "Passivo Total",
    "2.01": "Passivo Circulante",
    "2.02": "Passivo Nao Circulante",
    "2.03": "Patrimonio Liquido",
    "3.01": "Receita Liquida",
    "3.03": "Lucro Bruto",
    "3.05": "EBIT",
    "3.11": "Lucro Liquido",
    "6.01": "Caixa Operacional",
    "6.02": "Caixa de Investimentos",
    "6.03": "Caixa de Financiamentos",
    "6.05.02": "Saldo Final de Caixa",
}


def _inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(180deg, {COSAN_COLORS['bg']} 0%, #0f2740 100%);
            color: {COSAN_COLORS['text']};
        }}
        [data-testid="stSidebar"] {{
            background: #071320;
        }}
        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }}
        .cosan-hero {{
            background: linear-gradient(135deg, {COSAN_COLORS['card']} 0%, {COSAN_COLORS['card_alt']} 100%);
            border: 1px solid {COSAN_COLORS['line']};
            border-radius: 18px;
            padding: 20px 22px;
            margin-bottom: 1rem;
        }}
        .cosan-kpi {{
            background: {COSAN_COLORS['card']};
            border: 1px solid {COSAN_COLORS['line']};
            border-radius: 16px;
            padding: 16px 18px;
            min-height: 112px;
        }}
        .cosan-kpi-label {{
            color: {COSAN_COLORS['muted']};
            font-size: 0.78rem;
            letter-spacing: 0.04rem;
            text-transform: uppercase;
        }}
        .cosan-kpi-value {{
            color: {COSAN_COLORS['text']};
            font-size: 1.7rem;
            font-weight: 700;
            margin-top: 0.4rem;
        }}
        .cosan-kpi-sub {{
            color: {COSAN_COLORS['muted']};
            font-size: 0.82rem;
            margin-top: 0.45rem;
        }}
        .cosan-section-card {{
            background: {COSAN_COLORS['card']};
            border: 1px solid {COSAN_COLORS['line']};
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 1rem;
        }}
        .cosan-pill {{
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            margin-top: 0.6rem;
        }}
        .cosan-note {{
            color: {COSAN_COLORS['muted']};
            font-size: 0.9rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_currency(value: float | int | None, short: bool = False) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    abs_value = abs(float(value))
    if short:
        if abs_value >= 1_000_000_000:
            return f"R$ {value / 1_000_000_000:.1f} bi"
        if abs_value >= 1_000_000:
            return f"R$ {value / 1_000_000:.1f} mi"
        if abs_value >= 1_000:
            return f"R$ {value / 1_000:.1f} mil"
    return f"R$ {value:,.0f}".replace(",", ".")


def _format_percent(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value * 100:.1f}%"


def _format_ratio(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value:.2f}x"


def _format_days(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value:.0f} dias"


def _format_score(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value:.1f}"


def format_value(value, value_format: str, short: bool = False) -> str:
    if value_format == "currency":
        return _format_currency(value, short=short)
    if value_format == "pct":
        return _format_percent(value)
    if value_format == "ratio":
        return _format_ratio(value)
    if value_format == "days":
        return _format_days(value)
    if value_format == "score":
        return _format_score(value)
    return "-" if value is None else str(value)


def _badge_for_risk(faixa: str | None) -> tuple[str, str]:
    faixa = (faixa or "").upper()
    if "SAUD" in faixa:
        return ("rgba(52, 211, 153, 0.13)", COSAN_COLORS["green"])
    if "MODER" in faixa:
        return ("rgba(245, 158, 11, 0.13)", COSAN_COLORS["amber"])
    if "ALERTA" in faixa:
        return ("rgba(251, 146, 60, 0.13)", "#FB923C")
    return ("rgba(239, 68, 68, 0.13)", COSAN_COLORS["red"])


def _statement_pivot(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    pivot = (
        df.pivot_table(
            index=["CD_CONTA", "DS_CONTA"],
            columns="ANO_FISCAL",
            values="VL_CONTA_TRATADO",
            aggfunc="first",
        )
        .reset_index()
        .sort_values("CD_CONTA")
    )
    pivot.columns = [str(col) if isinstance(col, int) else col for col in pivot.columns]
    return pivot


def _statement_download(df: pd.DataFrame, filename: str):
    if df.empty:
        return
    st.download_button(
        "Baixar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def _render_kpi_card(label: str, value: str, subtext: str = ""):
    st.markdown(
        f"""
        <div class="cosan-kpi">
            <div class="cosan-kpi-label">{label}</div>
            <div class="cosan-kpi-value">{value}</div>
            <div class="cosan-kpi-sub">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_overview(tab, selected_year: int):
    history = get_overview_history()
    snapshot = get_overview_snapshot(selected_year)
    benchmark = get_iprf_sector_benchmark(selected_year)
    referencia = get_cosan_reference()

    with tab:
        st.markdown(
            f"""
            <div class="cosan-hero">
                <h2 style="margin:0;">{referencia['nome']}</h2>
                <div class="cosan-note">
                    Painel executivo anual com demonstrativos, benchmark por mediana e IPRF.
                </div>
                <div class="cosan-note" style="margin-top:0.5rem;">
                    CNPJ: {referencia['cnpj']} | Setor: {referencia['setor']} | Ano fiscal selecionado: {selected_year}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            _render_kpi_card(
                "Receita Liquida",
                _format_currency(snapshot.get("REC_LIQ"), short=True),
                f"Ano fiscal {selected_year}",
            )
        with col2:
            _render_kpi_card(
                "EBITDA",
                _format_currency(snapshot.get("EBITDA"), short=True),
                "Proxy anual para analise executiva",
            )
        with col3:
            _render_kpi_card(
                "Lucro Liquido",
                _format_currency(snapshot.get("LUCRO_LIQ"), short=True),
                "Resultado consolidado",
            )
        with col4:
            _render_kpi_card(
                "Score IPRF",
                _format_score(snapshot.get("SCORE_IPRF")),
                f"Faixa: {snapshot.get('FAIXA_IPRF', '-')}",
            )

        chart_col, side_col = st.columns([2.2, 1])
        with chart_col:
            if not history.empty:
                plot_df = history.copy()
                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=plot_df["ANO_FISCAL"],
                        y=plot_df["REC_LIQ"],
                        name="Receita Liquida",
                        marker_color=COSAN_COLORS["lime"],
                        opacity=0.65,
                        yaxis="y1",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=plot_df["ANO_FISCAL"],
                        y=plot_df["EBITDA"],
                        name="EBITDA",
                        mode="lines+markers",
                        line={"color": COSAN_COLORS["teal"], "width": 3},
                        yaxis="y1",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=plot_df["ANO_FISCAL"],
                        y=plot_df["SCORE_IPRF"],
                        name="IPRF Cosan",
                        mode="lines+markers",
                        line={"color": COSAN_COLORS["amber"], "width": 2},
                        yaxis="y2",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=plot_df["ANO_FISCAL"],
                        y=plot_df["MEDIANA_IPRF_SETOR_ANO"],
                        name="Mediana IPRF Setor",
                        mode="lines+markers",
                        line={"color": COSAN_COLORS["violet"], "width": 2, "dash": "dash"},
                        yaxis="y2",
                    )
                )
                fig.update_layout(
                    title="Historico anual: desempenho financeiro e IPRF",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend={"orientation": "h", "y": 1.08},
                    yaxis={"title": "R$"},
                    yaxis2={
                        "title": "Score IPRF",
                        "overlaying": "y",
                        "side": "right",
                        "range": [0, 10],
                    },
                    font={"color": COSAN_COLORS["text"]},
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Historico anual indisponivel. Rode as queries da camada gold antes de abrir o dashboard.")

        with side_col:
            bg, color = _badge_for_risk(snapshot.get("FAIXA_IPRF"))
            st.markdown(
                f"""
                <div class="cosan-section-card">
                    <div class="cosan-kpi-label">Classificacao IPRF</div>
                    <div class="cosan-kpi-value">{_format_score(snapshot.get("SCORE_IPRF"))}</div>
                    <span class="cosan-pill" style="background:{bg}; color:{color};">
                        {snapshot.get("FAIXA_IPRF", "Sem faixa")}
                    </span>
                    <div class="cosan-note" style="margin-top:0.8rem;">
                        Mediana setorial: {_format_score(benchmark.get("MEDIANA_IPRF_SETOR_ANO"))}
                    </div>
                    <div class="cosan-note">
                        Rank no setor: {benchmark.get("RANK_IPRF_SETOR_ANO", "-")}
                    </div>
                    <div class="cosan-note">
                        Percentil setorial: {benchmark.get("PERCENTIL_IPRF_SETOR_ANO", "-")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_statement_tab(tab, statement_type: str, selected_year: int, max_level: int):
    statement_df = get_statement_data(statement_type, max_level=max_level)
    highlights_df = get_statement_highlights(statement_type)

    with tab:
        st.subheader(STATEMENT_TITLES[statement_type])
        st.caption(f"Tabela anual da {STATEMENT_TITLES[statement_type]} para a Cosan, filtrada ate o nivel {max_level}.")

        if statement_df.empty:
            st.info("Sem dados disponiveis para este demonstrativo.")
            return

        pivot = _statement_pivot(statement_df)
        numeric_cols = [col for col in pivot.columns if col not in ["CD_CONTA", "DS_CONTA"]]
        styled = pivot.copy()
        for col in numeric_cols:
            styled[col] = styled[col].map(lambda value: _format_currency(value))

        table_col, chart_col = st.columns([1.3, 1])
        with table_col:
            st.dataframe(styled, use_container_width=True, hide_index=True, height=560)
            _statement_download(pivot, f"cosan_{statement_type.lower()}_anual.csv")

        with chart_col:
            if not highlights_df.empty:
                chart_df = highlights_df.copy()
                chart_df["LABEL"] = chart_df["CD_CONTA"].map(HIGHLIGHT_LABELS).fillna(chart_df["DS_CONTA"])
                fig = px.line(
                    chart_df,
                    x="ANO_FISCAL",
                    y="VL_CONTA_TRATADO",
                    color="LABEL",
                    markers=True,
                    title=f"Evolucao anual - {STATEMENT_TITLES[statement_type]}",
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": COSAN_COLORS["text"]},
                    legend_title_text="Conta",
                )
                st.plotly_chart(fig, use_container_width=True)

                selected_cols = chart_df[chart_df["ANO_FISCAL"] == selected_year].copy()
                if not selected_cols.empty:
                    selected_cols["ABS"] = selected_cols["VL_CONTA_TRATADO"].abs()
                    selected_cols = selected_cols.sort_values("ABS", ascending=False).head(6)
                    fig_bar = px.bar(
                        selected_cols,
                        x="LABEL",
                        y="VL_CONTA_TRATADO",
                        color="LABEL",
                        title=f"Composicao principal em {selected_year}",
                    )
                    fig_bar.update_layout(
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font={"color": COSAN_COLORS["text"]},
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)


def _prepare_indicator_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    meta_df = pd.DataFrame(PRIORITY_INDICATORS)
    merged = meta_df.merge(df, left_on="code", right_on="COD_INDICADOR", how="left")
    return merged


def _render_indicator_cards(df: pd.DataFrame):
    cols = st.columns(3)
    for idx, row in df.reset_index(drop=True).iterrows():
        col = cols[idx % 3]
        with col:
            st.markdown(
                f"""
                <div class="cosan-kpi">
                    <div class="cosan-kpi-label">{row['label']}</div>
                    <div class="cosan-kpi-value">{format_value(row.get('VL_INDICADOR'), row['format'])}</div>
                    <div class="cosan-kpi-sub">
                        Setor: {format_value(row.get('MEDIANA_SETOR_ANO'), row['format'])} |
                        Geral: {format_value(row.get('MEDIANA_GERAL_ANO'), row['format'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_indicator_group_chart(df: pd.DataFrame):
    if df.empty:
        return
    chart_df = pd.DataFrame(
        {
            "Indicador": df["label"],
            "Cosan": df["VL_INDICADOR"],
            "Mediana Setor": df["MEDIANA_SETOR_ANO"],
            "Mediana Geral": df["MEDIANA_GERAL_ANO"],
        }
    ).melt(id_vars="Indicador", var_name="Serie", value_name="Valor")
    fig = px.bar(
        chart_df,
        x="Indicador",
        y="Valor",
        color="Serie",
        barmode="group",
        color_discrete_map={
            "Cosan": COSAN_COLORS["lime"],
            "Mediana Setor": COSAN_COLORS["teal"],
            "Mediana Geral": COSAN_COLORS["violet"],
        },
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COSAN_COLORS["text"]},
        legend={"orientation": "h", "y": 1.1},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_sector_ranking(year: int, indicator_code: str):
    indicator = INDICATOR_META[indicator_code]
    ranking_df = get_sector_indicator_ranking(year, indicator_code)
    if ranking_df.empty:
        st.info("Ranking setorial indisponivel.")
        return

    ascending = indicator["direction"] == "lower_better"
    ranking_df = ranking_df.sort_values("VL_INDICADOR", ascending=ascending).reset_index(drop=True)
    ranking_df["rank"] = ranking_df.index + 1
    ranking_df["cor"] = ranking_df["DENOM_CIA"].apply(
        lambda value: COSAN_COLORS["amber"] if value == "COSAN S.A." else COSAN_COLORS["line"]
    )

    fig = px.bar(
        ranking_df.head(15),
        x="VL_INDICADOR",
        y="DENOM_CIA",
        orientation="h",
        color="DENOM_CIA",
        color_discrete_map={name: color for name, color in zip(ranking_df["DENOM_CIA"], ranking_df["cor"])},
        title=f"Ranking setorial - {indicator['label']} ({year})",
    )
    fig.update_layout(
        showlegend=False,
        yaxis={"autorange": "reversed"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COSAN_COLORS["text"]},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_indicators(tab, selected_year: int):
    benchmark_df = get_indicator_benchmark(selected_year)
    detail_df = get_indicator_detail_table(selected_year)
    history_df = get_priority_indicator_history()

    with tab:
        st.subheader("Indicadores classicos e benchmark por mediana")
        st.caption(
            "Comparacao anual da Cosan contra a mediana de todas as empresas e a mediana do setor Agricultura (Acucar, Alcool e Cana)."
        )

        if benchmark_df.empty:
            st.info("Benchmark indisponivel. Execute as views da camada gold para habilitar esta secao.")
            return

        priority_snapshot = _prepare_indicator_snapshot(benchmark_df)
        selected_group = st.selectbox(
            "Grupo prioritario",
            options=list(dict.fromkeys(item["group"] for item in PRIORITY_INDICATORS)),
        )

        selected_group_df = priority_snapshot[priority_snapshot["group"] == selected_group].copy()
        _render_indicator_cards(selected_group_df)

        chart_col, rank_col = st.columns([1.4, 1])
        with chart_col:
            _render_indicator_group_chart(selected_group_df)
        with rank_col:
            selected_indicator = st.selectbox(
                "Indicador para ranking setorial",
                options=selected_group_df["code"].tolist(),
                format_func=lambda code: INDICATOR_META[code]["label"],
            )
            _render_sector_ranking(selected_year, selected_indicator)

        st.markdown("#### Historico dos indicadores prioritarios")
        if not history_df.empty:
            history_plot = history_df.merge(
                pd.DataFrame(PRIORITY_INDICATORS),
                left_on="COD_INDICADOR",
                right_on="code",
                how="left",
            )
            history_plot = history_plot[history_plot["group"] == selected_group]
            fig = px.line(
                history_plot,
                x="ANO_FISCAL",
                y="VL_INDICADOR",
                color="label",
                markers=True,
                title=f"Historico anual - {selected_group}",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": COSAN_COLORS["text"]},
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Tabela detalhada")
        if not detail_df.empty:
            detail_df = detail_df.copy()
            detail_df["Indicador"] = detail_df["COD_INDICADOR"]
            detail_df["Valor Cosan"] = detail_df["VL_INDICADOR"]
            detail_df["Mediana Geral"] = detail_df["MEDIANA_GERAL_ANO"]
            detail_df["Mediana Setor"] = detail_df["MEDIANA_SETOR_ANO"]
            detail_df["Delta Geral"] = detail_df["DELTA_VS_GERAL"]
            detail_df["Delta Setor"] = detail_df["DELTA_VS_SETOR"]
            st.dataframe(
                detail_df[
                    [
                        "Indicador",
                        "Valor Cosan",
                        "Mediana Geral",
                        "Mediana Setor",
                        "Delta Geral",
                        "Delta Setor",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                height=480,
            )
            _statement_download(detail_df, "cosan_benchmark_indicadores.csv")


def _render_iprf_gauge(score: float | None, sector_median: float | None):
    value = score if score is not None else 0
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            delta={"reference": sector_median or 0, "increasing": {"color": COSAN_COLORS["green"]}},
            gauge={
                "axis": {"range": [0, 10]},
                "bar": {"color": COSAN_COLORS["amber"]},
                "steps": [
                    {"range": [0, 3], "color": "rgba(239, 68, 68, 0.19)"},
                    {"range": [3, 5], "color": "rgba(251, 146, 60, 0.15)"},
                    {"range": [5, 7], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [7, 10], "color": "rgba(52, 211, 153, 0.15)"},
                ],
                "threshold": {"line": {"color": COSAN_COLORS["lime"], "width": 4}, "value": sector_median or 0},
            },
            title={"text": "Score IPRF"},
        )
    )
    fig.update_layout(
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": COSAN_COLORS["text"]},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_iprf_dimensions(detail: dict):
    rows = []
    for score_code, label in IPRF_DIMENSION_SCORES:
        rows.append({"Dimensao": label, "Score": detail.get(score_code)})
    df = pd.DataFrame(rows)
    fig = px.bar(
        df,
        x="Score",
        y="Dimensao",
        orientation="h",
        color="Dimensao",
        color_discrete_sequence=[
            COSAN_COLORS["teal"],
            COSAN_COLORS["violet"],
            COSAN_COLORS["amber"],
            COSAN_COLORS["lime"],
            COSAN_COLORS["green"],
        ],
        range_x=[0, 10],
    )
    fig.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COSAN_COLORS["text"]},
        yaxis={"autorange": "reversed"},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_iprf_indicator_table(detail: dict):
    rows = []
    for item in IPRF_INDICATORS:
        rows.append(
            {
                "Dimensao": item["dimension"],
                "Indicador": item["label"],
                "Valor Base": format_value(detail.get(item["code"]), item["format"]),
                "Nota 0-10": format_value(detail.get(item["note_code"]), "score"),
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=460)


def _render_iprf_peers(peers_df: pd.DataFrame):
    if peers_df.empty:
        st.info("Comparativo setorial do IPRF indisponivel.")
        return

    peers_df = peers_df.copy()
    peers_df["Cor"] = peers_df["DENOM_CIA"].apply(
        lambda value: COSAN_COLORS["amber"] if value == "COSAN S.A." else COSAN_COLORS["line"]
    )
    fig = px.bar(
        peers_df.head(20),
        x="SCORE_IPRF",
        y="DENOM_CIA",
        orientation="h",
        color="DENOM_CIA",
        color_discrete_map={name: color for name, color in zip(peers_df["DENOM_CIA"], peers_df["Cor"])},
        title="Comparativo setorial do IPRF",
    )
    fig.update_layout(
        showlegend=False,
        yaxis={"autorange": "reversed"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COSAN_COLORS["text"]},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_iprf(tab, selected_year: int):
    history_df = get_iprf_history()
    detail = get_iprf_year_detail(selected_year)
    benchmark = get_iprf_sector_benchmark(selected_year)
    peers_df = get_iprf_sector_peers(selected_year)

    with tab:
        st.subheader("Indice de Prevencao ao Risco Financeiro")
        st.caption(
            "Score anual da Cosan comparado apenas com empresas do mesmo setor. As notas 0-10 estao em configuracao provisoria ate a definicao final das faixas."
        )

        if not detail:
            st.info("IPRF indisponivel. Rode a view anual do IPRF na camada gold.")
            return

        top_col, side_col = st.columns([1.3, 1])
        with top_col:
            _render_iprf_gauge(detail.get("SCORE_IPRF"), benchmark.get("MEDIANA_IPRF_SETOR_ANO"))
        with side_col:
            bg, color = _badge_for_risk(detail.get("FAIXA_IPRF"))
            st.markdown(
                f"""
                <div class="cosan-section-card">
                    <div class="cosan-kpi-label">Classificacao</div>
                    <div class="cosan-kpi-value">{format_value(detail.get('SCORE_IPRF'), 'score')}</div>
                    <span class="cosan-pill" style="background:{bg}; color:{color};">
                        {detail.get('FAIXA_IPRF', '-')}
                    </span>
                    <div class="cosan-note" style="margin-top:0.8rem;">
                        Mediana do setor: {format_value(benchmark.get('MEDIANA_IPRF_SETOR_ANO'), 'score')}
                    </div>
                    <div class="cosan-note">
                        Rank setorial: {benchmark.get('RANK_IPRF_SETOR_ANO', '-')}
                    </div>
                    <div class="cosan-note">
                        Percentil setorial: {benchmark.get('PERCENTIL_IPRF_SETOR_ANO', '-')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        dim_col, peers_col = st.columns([1, 1.2])
        with dim_col:
            st.markdown("#### Scores por dimensao")
            _render_iprf_dimensions(detail)
        with peers_col:
            _render_iprf_peers(peers_df)

        history_col, table_col = st.columns([1, 1.1])
        with history_col:
            if not history_df.empty:
                fig = px.line(
                    history_df,
                    x="ANO_FISCAL",
                    y=["SCORE_IPRF", "SCORE_LIQUIDEZ", "SCORE_RENTABILIDADE", "SCORE_SOLVENCIA"],
                    markers=True,
                    title="Historico do IPRF e dimensoes",
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": COSAN_COLORS["text"]},
                    yaxis={"range": [0, 10]},
                )
                st.plotly_chart(fig, use_container_width=True)
        with table_col:
            st.markdown("#### Notas dos 13 indicadores")
            _render_iprf_indicator_table(detail)


def render_executive_dashboard():
    _inject_css()
    referencia = get_cosan_reference()
    years = get_available_years()

    with st.sidebar:
        st.title("Cosan Executive Dashboard")
        st.caption("Projeto final - DFP anual, benchmark por mediana e IPRF")
        st.markdown("---")
        st.write(f"**Empresa:** {referencia['nome']}")
        st.write(f"**CNPJ:** {referencia['cnpj']}")
        st.write(f"**Setor:** {referencia['setor']}")
        st.markdown("---")

        if years:
            selected_year = st.selectbox("Ano fiscal", options=years, index=0)
        else:
            selected_year = None
        max_level = st.slider("Nivel de detalhe dos demonstrativos", 1, 5, 3)

    st.title("Dashboard Final Cosan + Benchmark + IPRF")
    st.caption(
        "Painel anual da Cosan com demonstrativos, indicadores classicos e comparativos com a base completa e com o setor agricola."
    )

    if selected_year is None:
        st.warning("Nenhum ano fiscal encontrado na camada gold. Execute as consultas do schema layer_03_gold e recarregue o app.")
        return

    tabs = st.tabs(["Visao Geral", "BP", "DRE", "DFC", "Indicadores", "IPRF"])
    _render_overview(tabs[0], selected_year)
    _render_statement_tab(tabs[1], "BP", selected_year, max_level)
    _render_statement_tab(tabs[2], "DRE", selected_year, max_level)
    _render_statement_tab(tabs[3], "DFC", selected_year, max_level)
    _render_indicators(tabs[4], selected_year)
    _render_iprf(tabs[5], selected_year)
