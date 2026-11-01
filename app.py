import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
        # Exclusão estrita da Coluna1 em todas as circunstâncias
        if "Coluna1" in df.columns:
            df = df.drop(columns=["Coluna1"])

        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df["Ano"] = df["Data"].dt.year
            meses_pt = [
                "Janeiro",
                "Fevereiro",
                "Março",
                "Abril",
                "Maio",
                "Junho",
                "Julho",
                "Agosto",
                "Setembro",
                "Outubro",
                "Novembro",
                "Dezembro",
            ]
            df["Mês"] = df["Data"].dt.month.map(
                lambda x: meses_pt[x - 1] if pd.notna(x) and 1 <= x <= 12 else ""
            )

    return df


df = load_data(uploaded_file)

if df is not None and not df.empty:
    # 1. Colunas de Controlo / Metadados
    meta_cols = [
        "Data",
        "Ano",
        "Mês",
        "Inq. Nº",
        "Distribuídos",
        "Nacionalidade",
        "Quarto",
        "FO",
        "Geral",
    ]

    # 2. Colunas de Resposta Binária / Motivos
    binary_cols = [
        "Localização ",
        "Preço",
        "Qualidade",
        "Comentários online",
        "Outros",
        "Recomendaria",
        "Tenciona Voltar",
    ]

    # 3. Rubricas de Avaliação genuínas (Escala de 1 a 5, inclui Preocupações Ambientais)
    item_cols = [
        c
        for c in df.columns
        if c not in meta_cols
        and c not in binary_cols
        and not c.endswith("_Pct")
    ]

    # Limpeza estrita: força tudo o que não seja número de 1 a 5 a pd.NA (ignorando "N", texto, etc.)
    for col in item_cols:
        df[col] = pd.to_numeric(
            pd.to_numeric(df[col], errors="coerce"), errors="coerce"
        )
        df.loc[(df[col] < 1) | (df[col] > 5), col] = pd.NA

        pct_col_name = f"{col}_Pct"
        df[pct_col_name] = df[col] * 20.0

    pct_rubric_cols = [f"{c}_Pct" for c in item_cols]

    # ---------------------------------------------------------
    # CÁLCULO DA TAXA DE RESPOSTA POR DATA
    # ---------------------------------------------------------
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
                (df["Data"].dt.date >= start_date)
                & (df["Data"].dt.date <= end_date)
            ].copy()
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()

    anos_disponiveis = sorted(
        [int(a) for a in df_filtered["Ano"].dropna().unique()]
    )
    anos_selecionados = st.sidebar.multiselect(
        "Selecionar Anos", options=anos_disponiveis, default=anos_disponiveis
    )
    if anos_selecionados:
        df_filtered = df_filtered[df_filtered["Ano"].isin(anos_selecionados)]

    meses_ordem = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    meses_disponiveis = sorted(
        df_filtered["Mês"].dropna().unique(),
        key=lambda x: meses_ordem.index(x) if x in meses_ordem else 99,
    )
    meses_selecionados = st.sidebar.multiselect(
        "Selecionar Meses", options=meses_disponiveis, default=meses_disponiveis
    )
    if meses_selecionados:
        df_filtered = df_filtered[df_filtered["Mês"].isin(meses_selecionados)]

    nacionalidades_disponiveis = sorted(
        [str(n) for n in df_filtered["Nacionalidade"].dropna().unique()]
    )
    nacionalidades_selecionadas = st.sidebar.multiselect(
        "Selecionar Nacionalidades",
        options=nacionalidades_disponiveis,
        default=nacionalidades_disponiveis,
    )
    if nacionalidades_selecionadas:
        df_filtered = df_filtered[
            df_filtered["Nacionalidade"]
            .astype(str)
            .isin(nacionalidades_selecionadas)
        ]

    if "Quarto" in df_filtered.columns:
        quartos_disponiveis = sorted([
            str(q) for q in df_filtered["Quarto"].dropna().unique()
        ])
        quartos_selecionados = st.sidebar.multiselect(
            "Filtrar por Quarto", options=quartos_disponiveis
        )
        if quartos_selecionados:
            df_filtered = df_filtered[
                df_filtered["Quarto"].astype(str).isin(quartos_selecionados)
            ]

    # ---------------------------------------------------------
    # GESTÃO DE OBJECTIVOS
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Gestão de Objetivos (%)")

    if "objetivo_geral" not in st.session_state:
        st.session_state.objetivo_geral = 90.0
    if "objetivo_taxa_resp" not in st.session_state:
        st.session_state.objetivo_taxa_resp = 75.0

    st.sidebar.slider(
        "Objetivo Global de Satisfação (%)",
        50.0,
        100.0,
        key="objetivo_geral",
        step=1.0,
    )
    st.sidebar.slider(
        "Objetivo de Taxa de Resposta (%)",
        50.0,
        100.0,
        key="objetivo_taxa_resp",
        step=1.0,
    )

    st.sidebar.markdown("### Objetivos por Rubrica")
    objetivos_especificos = {}
    for col in item_cols:
        nome_limpo = col.replace("_Pct", "")
        if nome_limpo not in st.session_state:
            st.session_state[nome_limpo] = 90.0
        objetivos_especificos[nome_limpo] = st.sidebar.slider(
            f"Meta: {nome_limpo[:25]}...", 50.0, 100.0, key=nome_limpo, step=1.0
        )

    anos_str = (
        ", ".join(map(str, anos_selecionados))
        if anos_selecionados
        else "Todos"
    )
    meses_str = ", ".join(meses_selecionados) if meses_selecionados else "Todos"
    st.info(
        f"📅 **Período Selecionado:** Anos: `{anos_str}` | Meses: `{meses_str}`"
    )

    total_inqueritos = len(df_filtered)
    
    # Cálculo rigoroso da Satisfação Geral (idêntico ao Excel: média de todos os pontos de escala válidos x 20)
    if not df_filtered.empty and item_cols:
        valores_validos_escala = df_filtered[item_cols].values.flatten()
        valores_validos_escala = valores_validos_escala[~pd.isna(valores_validos_escala)]
        
        if len(valores_validos_escala) > 0:
            satisfacao_geral = float(valores_validos_escala.mean() * 20.0)
        else:
            satisfacao_geral = 0.0
            
        taxa_resposta_media = df_filtered["Taxa_Resposta_Inquerito"].mean()
    else:
        satisfacao_geral = 0.0
        taxa_resposta_media = 0.0

    # ---------------------------------------------------------
    # MÉTRICAS E INDICADORES (GAUGES)
    # ---------------------------------------------------------
    col_metricas, col_gauge1, col_gauge2 = st.columns([1, 1.5, 1.5])

    with col_metricas:
        st.metric("Inquéritos Analisados", f"{total_inqueritos}")
        if "Nacionalidade" in df_filtered.columns:
            st.metric(
                "Nacionalidades", f"{df_filtered['Nacionalidade'].nunique()}"
            )

    with col_gauge1:
        fig_gauge_sat = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=satisfacao_geral,
                delta={
                    "reference": st.session_state.objetivo_geral,
                    "relative": False,
                    "valueformat": "+.1f",
                },
                title={"text": "Satisfação Geral (%)", "font": {"size": 16}},
                number={"suffix": "%", "font": {"size": 24}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#1f77b4"},
                    "steps": [
                        {
                            "range": [0, st.session_state.objetivo_geral],
                            "color": "#ffcccc",
                        },
                        {
                            "range": [st.session_state.objetivo_geral, 100],
                            "color": "#c6efce",
                        },
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.8,
                        "value": st.session_state.objetivo_geral,
                    },
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
                delta={
                    "reference": st.session_state.objetivo_taxa_resp,
                    "relative": False,
                    "valueformat": "+.1f",
                },
                title={"text": "Taxa de Resposta Média (%)", "font": {"size": 16}},
                number={"suffix": "%", "font": {"size": 24}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#2ca02c"},
                    "steps": [
                        {
                            "range": [0, st.session_state.objetivo_taxa_resp],
                            "color": "#ffcccc",
                        },
                        {
                            "range": [st.session_state.objetivo_taxa_resp, 100],
                            "color": "#c6efce",
                        },
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.8,
                        "value": st.session_state.objetivo_taxa_resp,
                    },
                },
            )
        )
        fig_gauge_resp.update_layout(height=230, margin=dict(t=65, b=10, l=20, r=20))
        st.plotly_chart(fig_gauge_resp, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # EVOLUÇÃO TEMPORAL
    # ---------------------------------------------------------
    st.subheader("📈 Evolução Temporal de Indicadores")
    if not df_filtered.empty and "Data" in df_filtered.columns:
        # Criar coluna auxiliar para a evolução temporal mensal da Satisfação Geral
        df_filtered["Geral_Pct_Row"] = df_filtered[pct_rubric_cols].mean(axis=1)
        
        temporal_options = ["Geral_Pct_Row"] + pct_rubric_cols
        indicador_selecionado = st.selectbox(
            "Selecione o Indicador para Análise Temporal:",
            options=temporal_options,
            format_func=lambda x: "Satisfação Global (%)"
            if x == "Geral_Pct_Row"
            else x.replace("_Pct", ""),
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
        
        fig_temp.add_hline(
            y=obj_atual,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Objetivo ({obj_atual:.0f}%)",
        )
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
                    val_g = serie_valida.mean()
                    obj_val = st.session_state.get(col_original, 90.0)
                    delta_calc = (val_g / obj_val) - 1
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
            rows = [
                df_sec.iloc[i : i + cols_per_row]
                for i in range(0, len(df_sec), cols_per_row)
            ]

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
                            delta={
                                "reference": obj_m,
                                "relative": True,
                                "valueformat": "+.1%",
                            },
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
                                    {
                                        "range": [obj_m, 100],
                                        "color": "#c6efce",
                                    },
                                ],
                                "threshold": {
                                    "line": {"color": "red", "width": 3},
                                    "thickness": 0.8,
                                    "value": obj_m,
                                },
                            },
                        )
                    )
                    fig_ind.update_layout(
                        height=230, margin=dict(t=65, b=10, l=15, r=15)
                    )
                    grid_cols[i].plotly_chart(
                        fig_ind, use_container_width=True
                    )
        st.markdown("---")


    seccoes = {
        "Front-Office": [
            c for c in item_cols if c.startswith("Front-Office -")
        ],
        "Quartos": [c for c in item_cols if c.startswith("Quarto -")],
        "Pequeno-Almoço": [
            c for c in item_cols if c.startswith("Pequeno-Almoço -")
        ],
        "Restaurante / Bar": [
            c for c in item_cols if c.startswith("Restaurante / Bar -")
        ],
        "Outros Serviços e Instalações": [
            c
            for c in item_cols
            if not c.startswith(
                (
                    "Front-Office -",
                    "Quarto -",
                    "Pequeno-Almoço -",
                    "Restaurante / Bar -",
                )
            )
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

    # 1. Motivos de Escolha (Gráfico de Barras Horizontais)
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
            df_motivos = pd.DataFrame(dados_motivos).sort_values(
                by="Percentagem", ascending=True
            )
            fig_motivos = px.bar(
                df_motivos,
                x="Percentagem",
                y="Motivo",
                orientation="h",
                text=df_motivos["Percentagem"].apply(lambda v: f"{v:.1f}%"),
                labels={"Percentagem": "Taxa de Indicação (%)", "Motivo": ""},
            )
            fig_motivos.update_layout(
                xaxis=dict(range=[0, 100]),
                height=300,
                margin=dict(l=0, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_motivos, use_container_width=True)
        else:
            st.info("Colunas de motivos de escolha não encontradas.")

    # 2. Fidelização (Métricas)
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
                    st.metric(
                        label=col_name.strip(), value=f"{taxa:.1f}%"
                    )
                else:
                    st.metric(label=col_name.strip(), value="N/D")

    st.markdown("---")

    # ---------------------------------------------------------
    # EXPORTAÇÃO E TABELA DETALHADA
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("📥 Exportar Relatório")
    csv_data = df_filtered.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        label="Descarregar Dados Filtrados (CSV)",
        data=csv_data,
        file_name="relatorio_satisfacao_hotel_alisios.csv",
        mime="text/csv",
    )

    with st.expander("Ver dados detalhados filtrados"):
        st.dataframe(df_filtered)

else:
    st.warning(
        "Por favor, faça o upload do seu ficheiro Excel (`.xlsx`) na barra"
        " lateral para carregar o dashboard."
    )
