import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF
import tempfile
import os

st.set_page_config(
    page_title="Análise de Inquéritos de Satisfação - Hotel Alísios",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Análise de Inquéritos de Satisfação")
st.markdown(
    "Hotel Alísios — Gestão dinâmica de inquéritos, objetivos, evolução"
    " temporal detalhada e análise por secção."
)

# ---------------------------------------------------------
# CARREGAMENTO E TRATAMENTO DOS DADOS
# ---------------------------------------------------------
st.sidebar.header("📁 Gestão de Dados")
uploaded_file = st.sidebar.file_uploader(
    "Carregar / Atualizar Ficheiro Excel", type=["xlsx", "xls"]
)


@st.cache_data
def load_data(file):
    if file is not None:
        df = pd.read_excel(file, sheet_name="BD_Inquéritos", header=3)
    else:
        try:
            df = pd.read_excel(
                "BD Satisfação Cliente.xlsx", sheet_name="BD_Inquéritos", header=3
            )
        except Exception:
            return None

    if df is not None:
        if "Coluna1" in df.columns:
            df = df.drop(columns=["Coluna1"])

        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df["Ano"] = df["Data"].dt.year
            meses_pt = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]
            df["Mês"] = df["Data"].dt.month.map(
                lambda x: meses_pt[x - 1] if pd.notna(x) and 1 <= x <= 12 else ""
            )

    return df


df = load_data(uploaded_file)

if df is not None and not df.empty:
    meta_cols = [
        "Data", "Ano", "Mês", "Inq. Nº", "Distribuídos",
        "Nacionalidade", "Quarto", "FO", "Geral"
    ]

    binary_cols = [
        "Localização ", "Preço", "Qualidade",
        "Comentários online", "Outros", "Recomendaria", "Tenciona Voltar"
    ]

    item_cols = [
        c for c in df.columns
        if c not in meta_cols and c not in binary_cols and not c.endswith("_Pct")
    ]

    # Limpeza estrita para escala 1-5 convertida a percentagem (x 20)
    for col in item_cols:
        df[col] = pd.to_numeric(pd.to_numeric(df[col], errors="coerce"), errors="coerce")
        df.loc[(df[col] < 1) | (df[col] > 5), col] = pd.NA
        df[f"{col}_Pct"] = df[col] * 20.0

    pct_rubric_cols = [f"{c}_Pct" for c in item_cols]

    if "Geral" in df.columns:
        df["Geral_Clean"] = pd.to_numeric(pd.to_numeric(df["Geral"], errors="coerce"), errors="coerce")
        df["Geral_Excel_Pct"] = df["Geral_Clean"].apply(
            lambda x: x * 20.0 if pd.notna(x) and x <= 5 else x
        )
    else:
        df["Geral_Excel_Pct"] = pd.NA

    if "Distribuídos" in df.columns and "Data" in df.columns:
        df["Distribuídos"] = pd.to_numeric(df["Distribuídos"], errors="coerce")
        contagem_por_data = df.groupby("Data")["Inq. Nº"].transform("count")
        df["Taxa_Resposta_Inquerito"] = (
            contagem_por_data / df["Distribuídos"].replace(0, pd.NA)
        ) * 100.0
        df["Taxa_Resposta_Inquerito"] = df["Taxa_Resposta_Inquerito"].fillna(0)
    else:
        df["Taxa_Resposta_Inquerito"] = 0.0

    # ---------------------------------------------------------
    # FILTROS DE SEGMENTAÇÃO (BARRA LATERAL)
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("Filtros de Segmentação")

    if "Data" in df.columns and not df["Data"].dropna().empty:
        min_date = df["Data"].min().date()
        max_date = df["Data"].max().date()
        date_range = st.sidebar.date_input(
            "Selecionar Intervalo de Datas",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df[
                (df["Data"].dt.date >= start_date) & (df["Data"].dt.date <= end_date)
            ].copy()
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()

    anos_disponiveis = sorted([int(a) for a in df_filtered["Ano"].dropna().unique()])
    anos_selecionados = st.sidebar.multiselect("Selecionar Anos", options=anos_disponiveis, default=anos_disponiveis)
    if anos_selecionados:
        df_filtered = df_filtered[df_filtered["Ano"].isin(anos_selecionados)]

    meses_ordem = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    meses_disponiveis = sorted(
        df_filtered["Mês"].dropna().unique(),
        key=lambda x: meses_ordem.index(x) if x in meses_ordem else 99,
    )
    meses_selecionados = st.sidebar.multiselect("Selecionar Meses", options=meses_disponiveis, default=meses_disponiveis)
    if meses_selecionados:
        df_filtered = df_filtered[df_filtered["Mês"].isin(meses_selecionados)]

    nacionalidades_disponiveis = sorted([str(n) for n in df_filtered["Nacionalidade"].dropna().unique()])
    nacionalidades_selecionadas = st.sidebar.multiselect("Selecionar Nacionalidades", options=nacionalidades_disponiveis, default=nacionalidades_disponiveis)
    if nacionalidades_selecionadas:
        df_filtered = df_filtered[df_filtered["Nacionalidade"].astype(str).isin(nacionalidades_selecionadas)]

    if "Quarto" in df_filtered.columns:
        quartos_disponiveis = sorted([str(q) for q in df_filtered["Quarto"].dropna().unique()])
        quartos_selecionados = st.sidebar.multiselect("Filtrar por Quarto", options=quartos_disponiveis)
        if quartos_selecionados:
            df_filtered = df_filtered[df_filtered["Quarto"].astype(str).isin(quartos_selecionados)]

    # ---------------------------------------------------------
    # GESTÃO DE OBJETIVOS E CÁLCULO
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Gestão de Objetivos & Cálculo")

    metodo_calculo_geral = st.sidebar.selectbox(
        "Método de Cálculo da Satisfação Geral",
        options=["Média global (Método das Linhas)", "Coluna 'Geral' original do Excel"],
        index=0
    )

    if "objetivo_geral" not in st.session_state:
        st.session_state.objetivo_geral = 90.0
    if "objetivo_taxa_resp" not in st.session_state:
        st.session_state.objetivo_taxa_resp = 75.0

    st.sidebar.slider("Objetivo Global de Satisfação (%)", 50.0, 100.0, key="objetivo_geral", step=1.0)
    st.sidebar.slider("Objetivo de Taxa de Resposta (%)", 50.0, 100.0, key="objetivo_taxa_resp", step=1.0)

    st.sidebar.markdown("### Objetivos por Rubrica")
    objetivos_especificos = {}
    for col in item_cols:
        nome_limpo = col.replace("_Pct", "")
        if nome_limpo not in st.session_state:
            st.session_state[nome_limpo] = 90.0
        objetivos_especificos[nome_limpo] = st.sidebar.slider(
            f"Meta: {nome_limpo[:25]}...", 50.0, 100.0, key=nome_limpo, step=1.0
        )

    anos_str = ", ".join(map(str, anos_selecionados)) if anos_selecionados else "Todos"
    meses_str = ", ".join(meses_selecionados) if meses_selecionados else "Todos"
    st.info(f"📅 **Período Selecionado:** Anos: `{anos_str}` | Meses: `{meses_str}`")

    total_inqueritos = len(df_filtered)
    
    if not df_filtered.empty:
        if metodo_calculo_geral == "Coluna 'Geral' original do Excel" and "Geral_Excel_Pct" in df_filtered.columns:
            vals_geral = df_filtered["Geral_Excel_Pct"].dropna()
            satisfacao_geral = float(vals_geral.mean()) if len(vals_geral) > 0 else 0.0
        else:
            row_means = df_filtered[pct_rubric_cols].mean(axis=1, skipna=True)
            row_means_clean = row_means.dropna()
            satisfacao_geral = float(row_means_clean.mean()) if not row_means_clean.empty else 0.0
            
        taxa_resposta_media = df_filtered["Taxa_Resposta_Inquerito"].mean()
    else:
        satisfacao_geral = 0.0
        taxa_resposta_media = 0.0

    # ---------------------------------------------------------
    # CÁLCULO DE COMPARAÇÃO HOMÓLOGA (MoM & YoY)
    # ---------------------------------------------------------
    satisfacao_mom_diff = 0.0
    satisfacao_yoy_diff = 0.0

    if not df_filtered.empty and "Data" in df_filtered.columns and not df.empty:
        df_sorted = df_filtered.sort_values("Data")
        max_date = df_sorted["Data"].max()
        
        if pd.notna(max_date):
            current_year = max_date.year
            current_month = max_date.month

            prev_month = current_month - 1 if current_month > 1 else 12
            prev_year = current_year if current_month > 1 else current_year - 1

            df_current_m = df[(df["Data"].dt.year == current_year) & (df["Data"].dt.month == current_month)]
            df_prev_m = df[(df["Data"].dt.year == prev_year) & (df["Data"].dt.month == prev_month)]

            curr_val = satisfacao_geral
            if not df_current_m.empty:
                curr_means = df_current_m[pct_rubric_cols].mean(axis=1, skipna=True).dropna()
                curr_val = float(curr_means.mean()) if not curr_means.empty else satisfacao_geral

            if not df_prev_m.empty:
                prev_means = df_prev_m[pct_rubric_cols].mean(axis=1, skipna=True).dropna()
                prev_val = float(prev_means.mean()) if not prev_means.empty else 0.0
                satisfacao_mom_diff = curr_val - prev_val

            prev_y_year = current_year - 1
            df_yoy_m = df[(df["Data"].dt.year == prev_y_year) & (df["Data"].dt.month == current_month)]

            if not df_yoy_m.empty:
                yoy_means = df_yoy_m[pct_rubric_cols].mean(axis=1, skipna=True).dropna()
                yoy_val = float(yoy_means.mean()) if not yoy_means.empty else 0.0
                satisfacao_yoy_diff = curr_val - yoy_val

    # ---------------------------------------------------------
    # MÉTRICAS E INDICADORES (GAUGES)
    # ---------------------------------------------------------
    col_metricas, col_gauge1, col_gauge2 = st.columns([1, 1.5, 1.5])

    with col_metricas:
        st.metric("Inquéritos Analisados", f"{total_inqueritos}")
        if "Nacionalidade" in df_filtered.columns:
            st.metric("Nacionalidades", f"{df_filtered['Nacionalidade'].nunique()}")

    with col_gauge1:
        fig_gauge_sat = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=satisfacao_geral,
                delta={"reference": st.session_state.objetivo_geral, "relative": False, "valueformat": "+.1f"},
                title={"text": "Satisfação Geral (%)", "font": {"size": 16}},
                number={"suffix": "%", "font": {"size": 24}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#1f77b4"},
                    "steps": [
                        {"range": [0, st.session_state.objetivo_geral], "color": "#ffcccc"},
                        {"range": [st.session_state.objetivo_geral, 100], "color": "#c6efce"},
                    ],
                    "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.8, "value": st.session_state.objetivo_geral},
                },
            )
        )
        fig_gauge_sat.update_layout(height=230, margin=dict(t=65, b=10, l=20, r=20))
        st.plotly_chart(fig_gauge_sat, use_container_width=True)

    with col_gauge2:
        fig_gauge_resp = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=taxa_resposta_media,
                delta={"reference": st.session_state.objetivo_taxa_resp, "relative": False, "valueformat": "+.1f"},
                title={"text": "Taxa de Resposta Média (%)", "font": {"size": 16}},
                number={"suffix": "%", "font": {"size": 24}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#2ca02c"},
                    "steps": [
                        {"range": [0, st.session_state.objetivo_taxa_resp], "color": "#ffcccc"},
                        {"range": [st.session_state.objetivo_taxa_resp, 100], "color": "#c6efce"},
                    ],
                    "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.8, "value": st.session_state.objetivo_taxa_resp},
                },
            )
        )
        fig_gauge_resp.update_layout(height=230, margin=dict(t=65, b=10, l=20, r=20))
        st.plotly_chart(fig_gauge_resp, use_container_width=True)

    # ---------------------------------------------------------
    # SECÇÃO DE COMPARAÇÃO HOMÓLOGA (MoM & YoY)
    # ---------------------------------------------------------
    st.markdown("### 📊 Análise de Tendência Homóloga (MoM & YoY)")
    col_mom, col_yoy = st.columns(2)

    with col_mom:
        st.metric(
            label="🔄 Variação Face ao Mês Anterior (MoM)",
            value=f"{satisfacao_geral:.2f}%",
            delta=f"{satisfacao_mom_diff:+.2f}% vs mês anterior"
        )

    with col_yoy:
        st.metric(
            label="📅 Variação Homóloga (YoY - Face ao Ano Transato)",
            value=f"{satisfacao_geral:.2f}%",
            delta=f"{satisfacao_yoy_diff:+.2f}% vs mesmo mês do ano anterior",
            delta_color="normal"
        )

    # ---------------------------------------------------------
    # PAINEL DE DESTAQUES (TOP & FLOPS)
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("🏆 Painel de Destaques Operacionais")

    resumo_rubricas = []
    for col in item_cols:
        pct_col = f"{col}_Pct"
        if pct_col in df_filtered.columns:
            s_val = df_filtered[pct_col].dropna()
            if not s_val.empty:
                resumo_rubricas.append({"Rubrica": col, "Média": float(s_val.mean())})

    if resumo_rubricas:
        df_resumo = pd.DataFrame(resumo_rubricas).sort_values(by="Média", ascending=False)
        top_item = df_resumo.iloc[0]
        flop_item = df_resumo.iloc[-1]

        col_top, col_flop = st.columns(2)
        with col_top:
            st.success(f"🌟 **Ponto Forte (Top Performance):**\n\n `{top_item['Rubrica']}` com **{top_item['Média']:.2f}%** de satisfação.")
        with col_flop:
            st.warning(f"⚠️ **Ponto Crítico (Área de Atenção):**\n\n `{flop_item['Rubrica']}` com **{flop_item['Média']:.2f}%** de satisfação.")

    st.markdown("---")

    # ---------------------------------------------------------
    # EVOLUÇÃO TEMPORAL
    # ---------------------------------------------------------
    st.subheader("📈 Evolução Temporal de Indicadores")
    if not df_filtered.empty and "Data" in df_filtered.columns:
        df_filtered["Geral_Pct_Row"] = df_filtered[pct_rubric_cols].mean(axis=1, skipna=True)
        
        temporal_options = ["Geral_Pct_Row"] + pct_rubric_cols
        indicador_selecionado = st.selectbox(
            "Selecione o Indicador para Análise Temporal:",
            options=temporal_options,
            format_func=lambda x: "Satisfação Global (%)" if x == "Geral_Pct_Row" else x.replace("_Pct", ""),
        )

        df_temp = (
            df_filtered.set_index("Data")
            .resample("ME")[indicador_selecionado]
            .mean()
            .dropna()
            .reset_index()
        )
        df_temp["Media (%)"] = df_temp[indicador_selecionado]

        fig_temp = px.line(
            df_temp,
            x="Data",
            y="Media (%)",
            markers=True,
            title=f"Evolução Mensal: {'Satisfação Global (%)' if indicador_selecionado == 'Geral_Pct_Row' else indicador_selecionado.replace('_Pct', '')}",
            line_shape="spline",
        )

        nome_limpo = indicador_selecionado.replace("_Pct", "")
        obj_atual = (
            st.session_state.objetivo_geral
            if indicador_selecionado == "Geral_Pct_Row"
            else st.session_state.get(nome_limpo, 90.0)
        )
        
        fig_temp.add_hline(y=obj_atual, line_dash="dash", line_color="red", annotation_text=f"Objetivo ({obj_atual:.0f}%)")
        fig_temp.update_layout(height=300, yaxis=dict(range=[50, 105]))
        st.plotly_chart(fig_temp, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # ANÁLISE POR SECÇÃO
    # ---------------------------------------------------------
    st.subheader("Análise por Secção")

    def render_gauge_grid(cols_list, seccao_titulo):
        st.markdown(f"### 🏨 Secção: {seccao_titulo}")
        valid_cols = []
        for col in cols_list:
            col_original = col
            pct_col_name = f"{col}_Pct"
            if pct_col_name in df_filtered.columns:
                serie_valida = df_filtered[pct_col_name].dropna()
                n_respostas = len(serie_valida)
                
                if n_respostas > 0:
                    val_g = float(serie_valida.mean())
                    obj_val = st.session_state.get(col_original, 90.0)
                    delta_calc = (val_g / obj_val) - 1 if obj_val > 0 else 0.0
                    valid_cols.append({
                        "Rubrica": col_original,
                        "Media": val_g,
                        "Objetivo": obj_val,
                        "Delta": delta_calc,
                        "N": n_respostas,
                    })

        if valid_cols:
            df_sec = pd.DataFrame(valid_cols)
            cols_per_row = 2
            rows = [df_sec.iloc[i : i + cols_per_row] for i in range(0, len(df_sec), cols_per_row)]

            for row_df in rows:
                grid_cols = st.columns(len(row_df))
                for i, (_, row_item) in enumerate(row_df.iterrows()):
                    rubrica_nome = row_item["Rubrica"]
                    valor_m = row_item["Media"]
                    obj_m = row_item["Objetivo"]
                    n_resp = int(row_item["N"])

                    fig_ind = go.Figure(
                        go.Indicator(
                            mode="gauge+number+delta",
                            value=valor_m,
                            delta={"reference": obj_m, "relative": True, "valueformat": "+.1%"},
                            title={
                                "text": f"{rubrica_nome}<br><span style='font-size:11px;color:gray;'>Objetivo: {obj_m:.0f}% | Respostas: {n_resp}</span>",
                                "font": {"size": 13},
                            },
                            number={"suffix": "%", "font": {"size": 20}},
                            gauge={
                                "axis": {"range": [0, 100], "tickwidth": 1},
                                "bar": {"color": "#1f77b4"},
                                "steps": [
                                    {"range": [0, obj_m], "color": "#ffcccc"},
                                    {"range": [obj_m, 100], "color": "#c6efce"},
                                ],
                                "threshold": {"line": {"color": "red", "width": 3}, "thickness": 0.8, "value": obj_m},
                            },
                        )
                    )
                    fig_ind.update_layout(height=230, margin=dict(t=65, b=10, l=15, r=15))
                    grid_cols[i].plotly_chart(fig_ind, use_container_width=True)
        st.markdown("---")

    seccoes = {
        "Front-Office": [c for c in item_cols if c.startswith("Front-Office -")],
        "Quartos": [c for c in item_cols if c.startswith("Quarto -")],
        "Pequeno-Almoço": [c for c in item_cols if c.startswith("Pequeno-Almoço -")],
        "Restaurante / Bar": [c for c in item_cols if c.startswith("Restaurante / Bar -")],
        "Outros Serviços e Instalações": [
            c for c in item_cols
            if not c.startswith(("Front-Office -", "Quarto -", "Pequeno-Almoço -", "Restaurante / Bar -"))
        ],
    }

    for sec_nome, sec_colunas in seccoes.items():
        if sec_colunas:
            render_gauge_grid(sec_colunas, sec_nome)

    # ---------------------------------------------------------
    # ANÁLISE DE VARIÁVEIS DE RESPOSTA 0 E 1
    # ---------------------------------------------------------
    st.subheader("🎯 Análise de Motivos de Escolha e Fidelização")

    def clean_binary(series):
        return pd.to_numeric(series, errors="coerce").fillna(0)

    col_bin1, col_bin2 = st.columns(2)

    motivos_cols = ["Localização ", "Preço", "Qualidade", "Comentários online", "Outros"]

    with col_bin1:
        st.markdown("#### Motivos de Escolha do Hotel (%)")
        dados_motivos = []
        for col in motivos_cols:
            if col in df_filtered.columns:
                s_bin = clean_binary(df_filtered[col])
                pct = (s_bin > 0).mean() * 100
                dados_motivos.append({"Motivo": col.strip(), "Percentagem": pct})

        if dados_motivos:
            df_motivos = pd.DataFrame(dados_motivos).sort_values(by="Percentagem", ascending=True)
            fig_motivos = px.bar(
                df_motivos,
                x="Percentagem",
                y="Motivo",
                orientation="h",
                text=df_motivos["Percentagem"].apply(lambda v: f"{v:.1f}%"),
                labels={"Percentagem": "Taxa de Indicação (%)", "Motivo": ""},
            )
            fig_motivos.update_layout(xaxis=dict(range=[0, 100]), height=300, margin=dict(l=0, r=10, t=10, b=10))
            st.plotly_chart(fig_motivos, use_container_width=True)
        else:
            st.info("Colunas de motivos de escolha não encontradas.")

    loyalty_cols = ["Recomendaria", "Tenciona Voltar"]

    with col_bin2:
        st.markdown("#### Fidelização e Recomendação")
        st.write("Proporção de respostas afirmativas no período selecionado:")

        cols_metricas_bin = st.columns(len(loyalty_cols))
        for idx, col_name in enumerate(loyalty_cols):
            with cols_metricas_bin[idx]:
                if col_name in df_filtered.columns:
                    s_bin = clean_binary(df_filtered[col_name])
                    taxa = (s_bin > 0).mean() * 100
                    st.metric(label=col_name.strip(), value=f"{taxa:.1f}%")
                else:
                    st.metric(label=col_name.strip(), value="N/D")

    st.markdown("---")

    # ---------------------------------------------------------
    # GERAÇÃO DE RELATÓRIO EXECUTIVO EM PDF
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("📥 Exportar Relatórios")

    class PDFReport(FPDF):
        def header(self):
            self.set_font('helvetica', 'B', 14)
            self.cell(0, 10, 'Relatório Executivo de Satisfação - Hotel Alísios', 0, 1, 'C')
            self.set_font('helvetica', 'I', 9)
            self.cell(0, 6, f'Filtros: Anos: {anos_str} | Meses: {meses_str}', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('helvetica', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def generate_pdf():
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font('helvetica', '', 10)

        # Resumo de Indicadores Principais
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, '1. Indicadores Globais', 0, 1)
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 6, f'- Total de Inquéritos Analisados: {total_inqueritos}', 0, 1)
        pdf.cell(0, 6, f'- Satisfação Geral: {satisfacao_geral:.2f}% (Objetivo: {st.session_state.objetivo_geral:.1f}%)', 0, 1)
        pdf.cell(0, 6, f'- Taxa de Resposta Média: {taxa_resposta_media:.2f}% (Objetivo: {st.session_state.objetivo_taxa_resp:.1f}%)', 0, 1)
        pdf.ln(5)

        # Tabela de Rubricas
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, '2. Desempenho por Rubrica', 0, 1)
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(130, 7, 'Rubrica', 1)
        pdf.cell(30, 7, 'Média (%)', 1, 0, 'C')
        pdf.cell(30, 7, 'Respostas (N)', 1, 1, 'C')

        pdf.set_font('helvetica', '', 9)
        for r in resumo_rubricas:
            nome_rub = r['Rubrica'][:65]
            med_val = f"{r['Média']:.2f}%"
            n_val = str(len(df_filtered[f"{r['Rubrica']}_Pct"].dropna()))
            pdf.cell(130, 6, nome_rub, 1)
            pdf.cell(30, 6, med_val, 1, 0, 'C')
            pdf.cell(30, 6, n_val, 1, 1, 'C')

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)
        return temp_file.name

    if st.sidebar.button("📄 Gerar Relatório Executivo (PDF)"):
        pdf_path = generate_pdf()
        with open(pdf_path, "rb") as pdf_file:
            st.sidebar.download_button(
                label="⬇️ Descarregar PDF Gerado",
                data=pdf_file,
                file_name="relatorio_executivo_hotel_alisios.pdf",
                mime="application/pdf",
            )
        os.unlink(pdf_path)

    csv_data = df_filtered.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        label="📥 Descarregar Dados Filtrados (CSV)",
        data=csv_data,
        file_name="relatorio_satisfacao_hotel_alisios.csv",
        mime="text/csv",
    )

    with st.expander("Ver dados detalhados filtrados"):
        st.dataframe(df_filtered)

else:
    st.warning("Por favor, faça o upload do seu ficheiro Excel (`.xlsx`) na barra lateral para carregar o dashboard.")
