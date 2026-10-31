import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Satisfação - Hotel Alísios",
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

# Todas as colunas de rubricas para os gráficos
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

st.title("Hotel Alísios — Dashboard Dinâmico de Satisfação")
st.markdown(
    "Indicadores de gestão com seleção múltipla de datas e análises"
    " operacionais focadas."
)

# --- BARRA LATERAL (FILTROS MÚLTIPLOS) ---
st.sidebar.header("Filtros de Segmentação")

# Filtro de Anos (Seleção Múltipla)
anos_disponiveis = sorted(df["Ano"].dropna().unique())
anos_selecionados = st.sidebar.multiselect(
    "Selecionar Anos", options=anos_disponiveis, default=anos_disponiveis
)

if anos_selecionados:
  df_filtered = df[df["Ano"].isin(anos_selecionados)]
else:
  df_filtered = df

# Filtro de Meses (Seleção Múltipla)
meses_disponiveis = sorted(df_filtered["Mês"].dropna().unique())
meses_selecionados = st.sidebar.multiselect(
    "Selecionar Meses", options=meses_disponiveis, default=meses_disponiveis
)

if meses_selecionados:
  df_filtered = df_filtered[df_filtered["Mês"].isin(meses_selecionados)]

# --- MÉTRICAS PRINCIPAIS & CONTA-ROTAÇÕES ---
st.subheader("Indicador Global (Conta-Rotações)")

total_inqueritos = len(df_filtered)
satisfacao_geral = (
    df_filtered["Geral_Pct"].mean() * 100
    if not df_filtered.empty
    else 0
)

col1, col2 = st.columns([1, 2])

col1.metric("Inquéritos Analisados", f"{total_inqueritos}")
if "Nacionalidade" in df_filtered.columns:
  col1.metric(
      "Nacionalidades Diferentes", f"{df_filtered['Nacionalidade'].nunique()}"
  )

# Gráfico de Velocímetro (Gauge / Conta-Rotações)
fig_gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=satisfacao_geral,
        title={
            "text": "Média de Satisfação Global (%)",
            "font": {"size": 20},
        },
        number={"suffix": "%", "font": {"size": 30}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#1f77b4"},
            "steps": [
                {"range": [0, 75], "color": "#ff9999"},
                {"range": [75, 90], "color": "#ffcc99"},
                {"range": [90, 100], "color": "#99ff99"},
            ],
            "threshold": {
                "line": {"color": "darkgreen", "width": 4},
                "thickness": 0.75,
                "value": 95,
            },
        },
    )
)
fig_gauge.update_layout(height=240, margin=dict(t=30, b=10, l=30, r=30))
col2.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")

# --- CONCLUSÕES AUTOMÁTICAS E DIAGNÓSTICO DE GESTÃO (Excluindo Apresentação nas Análises) ---
st.subheader("Conclusões Automatizadas & Análise de Gestão")

if not df_filtered.empty:
  # Filtrar rubricas que NÃO são de apresentação para as conclusões textuais
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

  # Caixa de Diagnóstico Geral
  with st.info("Diagnóstico Executivo do Período Selecionado"):
    if satisfacao_geral >= 95:
      nivel = "Excelente desempenho operacional."
    elif satisfacao_geral >= 90:
      nivel = "Bom desempenho com margem para otimização."
    else:
      nivel = (
          "Desempenho a necessitar de intervenção direta nos pontos críticos."
      )

    fo_m = df_filtered["FO_Pct"].mean() * 100
    quarto_m = df_filtered["Quarto_Pct"].mean() * 100
    pa_m = df_filtered["PA_Pct"].mean() * 100
    rest_m = df_filtered["Rest_Pct"].mean() * 100

    st.write(f"""
        * **Estado Geral:** O hotel regista **{satisfacao_geral:.1f}%** de satisfação ponderada — *{nivel}*
        * **Resumo por Departamentos:** Front-Office ({fo_m:.1f}%), Quartos ({quarto_m:.1f}%), Pequeno-Almoço ({pa_m:.1f}%), Restaurante/Bar ({rest_m:.1f}%).
        * **Recomendação Principal:** Focar os planos de melhoria operacional na rubrica **{bottom_3.iloc[0]['Rubrica']}** ({bottom_3.iloc[0]['Media']:.1f}%).
        """)
else:
  st.warning("Sem dados disponíveis para a seleção efetuada.")

st.markdown("---")

# --- GRÁFICO DE VALORES MÉDIOS DE TODOS OS INDICADORES (Com todas as rubricas) ---
st.subheader("Valores Médios de Todos os Indicadores por Rubrica")

medias_rubricas_grafico = []
for col in item_cols:
  val_g = df_filtered[col + "_Pct"].mean()
  if not pd.isna(val_g):
    medias_rubricas_grafico.append(
        {"Rubrica": col.replace("_Pct", ""), "Media": val_g}
    )

if not df_filtered.empty and len(medias_rubricas_grafico) > 0:
  df_plot = pd.DataFrame(medias_rubricas_grafico).sort_values(
      by="Media", ascending=True
  )
  fig_rubricas = px.bar(
      df_plot,
      x="Media",
      y="Rubrica",
      orientation="h",
      text="Media",
      title=(
          "Média de Satisfação por Rubrica (Incluindo Todas as Rubricas)"
      ),
      color="Media",
      color_continuous_scale="RdYlGn",
  )
  fig_rubricas.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
  fig_rubricas.update_layout(
      xaxis=dict(range=[0, 115]),
      height=700,
      yaxis=dict(dtick=1),
      coloraxis_showscale=False,
  )
  st.plotly_chart(fig_rubricas, use_container_width=True)

# --- TABELA DE DADOS DETALHADA ---
with st.expander("Ver dados detalhados filtrados"):
  st.dataframe(df_filtered)
