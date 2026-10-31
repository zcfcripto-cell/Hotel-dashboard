import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Análise de Inquéritos de Satisfação - Hotel Alísios",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Carregar dados
@st.cache_data
def load_data():
  file_path = "Dashboard_Satisfacao_Cliente_Corrigido.xlsx"
  df = pd.read_excel(file_path, sheet_name="Base de Dados", header=2)
  return df


df = load_data()

# Todas as colunas de rubricas
item_cols = [
    c
    for c in df.columns
    if c
    not in [
        "Data",
        "Ano",
        "Mês",
        "Inq. Nº",
        "Nacionalidade",
        "Quarto",
        "FO_Pct",
        "Quarto_Pct",
        "PA_Pct",
        "Rest_Pct",
        "Geral_Pct",
    ]
]

# Converter todas as rubricas de 1-5 para percentagem (0-100%)
for col in item_cols:
  df[col + "_Pct"] = (df[col] / 5.0) * 100

# Taxa de resposta por inquérito
df["Taxa_Resposta_Inquerito"] = df[item_cols].notnull().mean(axis=1) * 100

# Título Principal
st.title("Análise de Inquéritos de Satisfação")
st.markdown("Hotel Alísios — Gestão dinâmica de inquéritos e desempenho.")

# --- BARRA LATERAL (FILTROS MÚLTIPLOS E OBJETIVO) ---
st.sidebar.header("Filtros de Segmentação")

# Filtro de Anos
anos_disponiveis = sorted(df["Ano"].dropna().unique())
anos_selecionados = st.sidebar.multiselect(
    "Selecionar Anos", options=anos_disponiveis, default=anos_disponiveis
)
df_filtered = (
    df[df["Ano"].isin(anos_selecionados)] if anos_selecionados else df
)

# Filtro de Meses
meses_disponiveis = sorted(df_filtered["Mês"].dropna().unique())
meses_selecionados = st.sidebar.multiselect(
    "Selecionar Meses", options=meses_disponiveis, default=meses_selecionados
)
if meses_selecionados:
  df_filtered = df_filtered[df_filtered["Mês"].isin(meses_selecionados)]

# Filtro de Nacionalidade
nacionalidades_disponiveis = sorted(
    df_filtered["Nacionalidade"].dropna().unique()
)
nacionalidades_selecionadas = st.sidebar.multiselect(
    "Selecionar Nacionalidades",
    options=nacionalidades_disponiveis,
    default=nacionalidades_disponiveis,
)
if nacionalidades_selecionadas:
  df_filtered = df_filtered[
      df_filtered["Nacionalidade"].isin(nacionalidades_selecionadas)
  ]

st.sidebar.markdown("---")
st.sidebar.header("Meta / Objetivo de Satisfação")
objetivo_global = st.sidebar.slider(
    "Objetivo a Atingir (%)",
    min_value=50.0,
    max_value=100.0,
    value=90.0,
    step=1.0,
)

# --- CARTÃO COM ANOS E MESES FILTRADOS ---
anos_str = (
    ", ".join(map(str, anos_selecionados))
    if anos_selecionados
    else "Todos"
)
meses_str = ", ".join(meses_selecionados) if meses_selecionados else "Todos"
st.info(
    f"📅 **Período Selecionado:** Anos: `{anos_str}` | Meses: `{meses_str}`"
)

# --- CONTA-ROTAÇÕES GLOBAIS ---
total_inqueritos = len(df_filtered)
satisfacao_geral = (
    df_filtered["Geral_Pct"].mean() * 100
    if not df_filtered.empty
    else 0
)
taxa_resposta_media = (
    df_filtered["Taxa_Resposta_Inquerito"].mean()
    if not df_filtered.empty
    else 0
)

col_metricas, col_gauge1, col_gauge2 = st.columns([1, 1.5, 1.5])

with col_metricas:
  st.metric("Inquéritos Analisados", f"{total_inqueritos}")
  if "Nacionalidade" in df_filtered.columns:
    st.metric(
        "Nacionalidades", f"{df_filtered['Nacionalidade'].nunique()}"
    )

# 1º Conta-Rotações: Satisfação Geral
fig_gauge_sat = go.Figure(
    go.Indicator(
        mode="gauge+number+delta",
        value=satisfacao_geral,
        delta={"reference": objetivo_global, "relative": False},
        title={"text": "Satisfação Geral (%)", "font": {"size": 16}},
        number={"suffix": "%", "font": {"size": 24}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#1f77b4"},
            "steps": [
                {"range": [0, objetivo_global], "color": "#ffcccc"},
                {"range": [objetivo_global, 100], "color": "#c6efce"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.8,
                "value": objetivo_global,
            },
        },
    )
)
fig_gauge_sat.update_layout(height=220, margin=dict(t=30, b=10, l=20, r=20))
col_gauge1.plotly_chart(fig_gauge_sat, use_container_width=True)

# 2º Conta-Rotações: Taxa de Resposta
fig_gauge_resp = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=taxa_resposta_media,
        title={"text": "Taxa de Resposta Média (%)", "font": {"size": 16}},
        number={"suffix": "%", "font": {"size": 24}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#2ca02c"},
            "steps": [
                {"range": [0, 50], "color": "#ff9999"},
                {"range": [50, 75], "color": "#ffcc99"},
                {"range": [75, 100], "color": "#99ff99"},
            ],
        },
    )
)
fig_gauge_resp.update_layout(height=220, margin=dict(t=30, b=10, l=20, r=20))
col_gauge2.plotly_chart(fig_gauge_resp, use_container_width=True)

st.markdown("---")

# --- CONCLUSÕES AUTOMÁTICAS E DIAGNÓSTICO DE GESTÃO ---
st.subheader("Conclusões Automatizadas & Análise de Gestão")

if not df_filtered.empty:
  item_cols_analise = [
      c
      for c in item_cols
      if "apresentação" not in c.lower() and "apresentacao" not in c.lower()
  ]

  medias_rubricas_analise = []
  for col in item_cols_analise:
    val = df_filtered[col + "_Pct"].mean()
    if not pd.isna(val):
      medias_rubricas_analise.append(
          {"Rubrica": col.replace("_Pct", ""), "Media": val}
      )

  df_rank = pd.DataFrame(medias_rubricas_analise).sort_values(
      by="Media", ascending=False
  )

  top_3 = df_rank.head(3)
  bottom_3 = df_rank.tail(3).iloc[::-1]

  col_a, col_b = st.columns(2)

  with col_a:
    st.markdown("### Pontos Fortes (Análise Operacional)")
    for idx, row in top_3.iterrows():
      st.success(f"**{row['Rubrica']}**: {row['Media']:.1f}% de satisfação")

  with col_b:
    st.markdown("### Oportunidades de Melhoria (Análise Operacional)")
    for idx, row in bottom_3.iterrows():
      st.warning(f"**{row['Rubrica']}**: {row['Media']:.1f}% de satisfação")

  if satisfacao_geral >= 95:
    nivel = "Excelente desempenho operacional."
  elif satisfacao_geral >= 90:
    nivel = "Bom desempenho com margem para otimização."
  else:
    nivel = "Desempenho a necessitar de intervenção direta nos pontos críticos."

  fo_m = df_filtered["FO_Pct"].mean() * 100
  quarto_m = df_filtered["Quarto_Pct"].mean() * 100
  pa_m = df_filtered["PA_Pct"].mean() * 100
  rest_m = df_filtered["Rest_Pct"].mean() * 100

  st.info(f"""
        **Diagnóstico Executivo do Período Selecionado:**
        * **Estado Geral:** O hotel regista **{satisfacao_geral:.1f}%** de satisfação ponderada e uma **taxa de resposta média de {taxa_resposta_media:.1f}%** — *{nivel}*
        * **Resumo por Departamentos:** Front-Office ({fo_m:.1f}%), Quartos ({quarto_m:.1f}%), Pequeno-Almoço ({pa_m:.1f}%), Restaurante/Bar ({rest_m:.1f}%).
        * **Recomendação Principal:** Focar os planos de melhoria operacional na rubrica **{bottom_3.iloc[0]['Rubrica']}** ({bottom_3.iloc[0]['Media']:.1f}%).
        """)
else:
  st.warning("Sem dados disponíveis para a seleção efetuada.")

st.markdown("---")

# --- PAINEL COMPLETO DE CONTA-ROTAÇÕES DE TODOS OS INDICADORES VISÍVEIS ---
st.subheader(
    f"Painel de Conta-Rotações de Todos os Indicadores (Objetivo:"
    f" {objetivo_global:.0f}%)"
)

medias_rubricas_grafico = []
for col in item_cols:
  val_g = df_filtered[col + "_Pct"].mean()
  if not pd.isna(val_g):
    medias_rubricas_grafico.append(
        {"Rubrica": col.replace("_Pct", ""), "Media": val_g}
    )

if not df_filtered.empty and len(medias_rubricas_grafico) > 0:
  df_plot = pd.DataFrame(medias_rubricas_grafico).sort_values(
      by="Media", ascending=False
  )

  cols_per_row = 2
  rows = [
      df_plot.iloc[i : i + cols_per_row]
      for i in range(0, len(df_plot), cols_per_row)
  ]

  for row_df in rows:
    grid_cols = st.columns(len(row_df))
    for i, (_, row_item) in enumerate(row_df.iterrows()):
      rubrica_nome = row_item["Rubrica"]
      valor_m = row_item["Media"]

      fig_ind = go.Figure(
          go.Indicator(
              mode="gauge+number+delta",
              value=valor_m,
              delta={"reference": objetivo_global, "relative": False},
              title={"text": rubrica_nome, "font": {"size": 14}},
              number={"suffix": "%", "font": {"size": 22}},
              gauge={
                  "axis": {"range": [0, 100], "tickwidth": 1},
                  "bar": {"color": "#1f77b4"},
                  "steps": [
                      {"range": [0, objetivo_global], "color": "#ffcccc"},
                      {
                          "range": [objetivo_global, 100],
                          "color": "#c6efce",
                      },
                  ],
                  "threshold": {
                      "line": {"color": "red", "width": 3},
                      "thickness": 0.8,
                      "value": objetivo_global,
                  },
              },
          )
      )
      fig_ind.update_layout(
          height=200, margin=dict(t=35, b=10, l=15, r=15)
      )
      grid_cols[i].plotly_chart(fig_ind, use_container_width=True)

st.markdown("---")

# --- TABELA DE DADOS DETALHADA ---
with st.expander("Ver dados detalhados filtrados"):
  st.dataframe(df_filtered)
