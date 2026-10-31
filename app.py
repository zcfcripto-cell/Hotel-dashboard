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

# Converter todas as rubricas de 1-5 para percentagem (0-100%)
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
for col in item_cols:
  df[col + "_Pct"] = (df[col] / 5.0) * 100

st.title("Hotel Alísios — Dashboard Dinâmico de Satisfação")
st.markdown(
    "Indicadores de gestão com seleção múltipla de datas e escalas (0-100%)."
)

# --- BARRA LATERAL (FILTROS MÚLTIPLOS) ---
st.sidebar.header("Filtros de Segmentação (Múltiplos)")

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

# --- MÉTRICAS PRINCIPAIS & CONTA-ROTAÇÕES (GAUGE) ---
st.subheader("Indicador Global (Conta-Rotações)")

total_inqueritos = len(df_filtered)
satisfacao_geral = (
    df_filtered["Geral_Pct"].mean() * 100
    if not df_filtered.empty
    else 0
)

col1, col2 = st.columns([1, 2])

col1.metric("Inquéritos Visíveis", f"{total_inqueritos}")
if "Nacionalidade" in df_filtered.columns:
  col1.metric(
      "Nacionalidades Diferentes", f"{df_filtered['Nacionalidade'].nunique()}"
  )

# Criar Gráfico de Velocímetro (Gauge / Conta-Rotações)
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
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 60], "color": "#ff9999"},
                {"range": [60, 80], "color": "#ffcc99"},
                {"range": [80, 100], "color": "#99ff99"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 90,
            },
        },
    )
)
fig_gauge.update_layout(height=250, margin=dict(t=30, b=10, l=30, r=30))
col2.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")

# --- GRÁFICO DE VALORES MÉDIOS DE TODOS OS INDICADORES POR RUBRICA ---
st.subheader("Valores Médios de Todos os Indicadores por Rubrica")

medias_rubricas = []
for col in item_cols:
  if col + "_Pct" in df_filtered.columns:
    media_val = df_filtered[col + "_Pct"].mean()
    medias_rubricas.append(
        {
            "Rubrica": col.replace("_Pct", ""),
            "Satisfação Média (%)": (
                media_val if not pd.isna(media_val) else 0
            ),
        }
    )

df_rubricas = pd.DataFrame(medias_rubricas).sort_values(
    by="Satisfação Média (%)", ascending=True
)

if not df_rubricas.empty:
  fig_rubricas = px.bar(
      df_rubricas,
      x="Satisfação Média (%)",
      y="Rubrica",
      orientation="h",
      text="Satisfação Média (%)",
      title=(
          "Média de Satisfação por Rubrica (Filtrado por Anos/Meses"
          " Selecionados)"
      ),
  )
  fig_rubricas.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
  fig_rubricas.update_layout(
      xaxis=dict(range=[0, 115]), height=700, yaxis=dict(dtick=1)
  )
  st.plotly_chart(fig_rubricas, use_container_width=True)

# --- TABELA DE DADOS DETALHADA ---
with st.expander("Ver dados detalhados filtrados"):
  st.dataframe(df_filtered)
