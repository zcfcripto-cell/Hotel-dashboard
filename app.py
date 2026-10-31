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

# Identificar colunas originais (1-5)
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

# Converter colunas de 1-5 para 0-100%
for col in item_cols:
  df[col + "_Pct"] = (df[col] / 5.0) * 100

df["Taxa_Resposta_Inquerito"] = df[item_cols].notnull().mean(axis=1) * 100

# Título Principal
st.title("Análise de Inquéritos de Satisfação")
st.markdown(
    "Hotel Alísios — Gestão dinâmica de inquéritos, objetivos, evolução"
    " temporal detalhada e análise por secção."
)

# --- BARRA LATERAL (FILTROS E OBJETIVOS) ---
st.sidebar.header("Filtros de Segmentação")

anos_disponiveis = sorted(df["Ano"].dropna().unique())
anos_selecionados = st.sidebar.multiselect(
    "Selecionar Anos", options=anos_disponiveis, default=anos_disponiveis
)
df_filtered = (
    df[df["Ano"].isin(anos_selecionados)] if anos_selecionados else df
)

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

st.sidebar.markdown("---")
st.sidebar.header("🎯 Gestão de Objetivos (%)")
objetivo_geral = st.sidebar.slider(
    "Objetivo Global de Satisfação (%)", 50.0, 100.0, 90.0, 1.0
)
objetivo_taxa_resp = st.sidebar.slider(
    "Objetivo de Taxa de Resposta (%)", 50.0, 100.0, 75.0, 1.0
)

st.sidebar.markdown("### Objetivos por Rubrica")
objetivos_especificos = {}
for col in item_cols:
  nome_limpo = col.replace("_Pct", "")
  objetivos_especificos[nome_limpo] = st.sidebar.slider(
      f"Meta: {nome_limpo[:25]}...", 50.0, 100.0, 90.0, 1.0
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

with col_gauge1:
  fig_gauge_sat = go.Figure(
      go.Indicator(
          mode="gauge+number+delta",
          value=satisfacao_geral,
          delta={
              "reference": objetivo_geral,
              "relative": False,
              "valueformat": "+.1f",
          },
          title={"text": "Satisfação Geral (%)", "font": {"size": 16}},
          number={"suffix": "%", "font": {"size": 24}},
          gauge={
              "axis": {"range": [0, 100], "tickwidth": 1},
              "bar": {"color": "#1f77b4"},
              "steps": [
                  {"range": [0, objetivo_geral], "color": "#ffcccc"},
                  {"range": [objetivo_geral, 100], "color": "#c6efce"},
              ],
              "threshold": {
                  "line": {"color": "red", "width": 4},
                  "thickness": 0.8,
                  "value": objetivo_geral,
              },
          },
      )
  )
  fig_gauge_sat.update_layout(height=220, margin=dict(t=30, b=10, l=20, r=20))
  st.plotly_chart(fig_gauge_sat, use_container_width=True)

with col_gauge2:
  fig_gauge_resp = go.Figure(
      go.Indicator(
          mode="gauge+number+delta",
          value=taxa_resposta_media,
          delta={
              "reference": objetivo_taxa_resp,
              "relative": False,
              "valueformat": "+.1f",
          },
          title={"text": "Taxa de Resposta Média (%)", "font": {"size": 16}},
          number={"suffix": "%", "font": {"size": 24}},
          gauge={
              "axis": {"range": [0, 100], "tickwidth": 1},
              "bar": {"color": "#2ca02c"},
              "steps": [
                  {"range": [0, objetivo_taxa_resp], "color": "#ffcccc"},
                  {"range": [objetivo_taxa_resp, 100], "color": "#c6efce"},
              ],
              "threshold": {
                  "line": {"color": "red", "width": 4},
                  "thickness": 0.8,
                  "value": objetivo_taxa_resp,
              },
          },
      )
  )
  fig_gauge_resp.update_layout(height=220, margin=dict(t=30, b=10, l=20, r=20))
  st.plotly_chart(fig_gauge_resp, use_container_width=True)

st.markdown("---")

# --- ANÁLISE TEMPORAL ---
st.subheader("📈 Evolução Temporal de Indicadores")
if not df_filtered.empty and "Data" in df_filtered.columns:
  indicador_selecionado = st.selectbox(
      "Selecione o Indicador para Análise Temporal:",
      options=["Geral_Pct"] + [c + "_Pct" for c in item_cols],
      format_func=lambda x: "Satisfação Global (%)"
      if x == "Geral_Pct"
      else x.replace("_Pct", ""),
  )

  df_temp = (
      df_filtered.set_index("Data")
      .resample("ME")[indicador_selecionado]
      .mean()
      .dropna()
      .reset_index()
  )
  df_temp["Media (%)"] = df_temp[indicador_selecionado] * 100
  fig_temp = px.line(
      df_temp,
      x="Data",
      y="Media (%)",
      markers=True,
      title=f"Evolução Mensal: {indicador_selecionado.replace('_Pct', '')}",
      line_shape="spline",
  )
  fig_temp.update_layout(height=300, yaxis=dict(range=[50, 105]))
  st.plotly_chart(fig_temp, use_container_width=True)

st.markdown("---")

# --- ANÁLISE POR SECÇÃO ---
st.subheader("Análise por Secção")
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
            ("Front-Office -", "Quarto -", "Pequeno-Almoço -", "Restaurante / Bar -")
        )
    ],
}


def render_gauge_grid(cols_list, seccao_titulo):
  st.markdown(f"### 🏨 Secção: {seccao_titulo}")
  valid_cols = []
  for col in cols_list:
    val_g = df_filtered[col + "_Pct"].mean()
    if not pd.isna(val_g):
      nome_limpo = col.replace("_Pct", "")
      obj_val = objetivos_especificos.get(nome_limpo, 90.0)
      delta_calc = (val_g / obj_val) - 1
      valid_cols.append({
          "Rubrica": nome_limpo,
          "Media": val_g,
          "Objetivo": obj_val,
          "Delta": delta_calc,
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
        delta_m = row_item["Delta"]

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
                    "text": f"{rubrica_nome}<br><span style='font-size:11px;color:gray;'>Objetivo: {obj_m:.0f}%</span>",
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
            height=210, margin=dict(t=45, b=10, l=15, r=15)
        )
        grid_cols[i].plotly_chart(fig_ind, use_container_width=True)
  st.markdown("---")


for sec_nome, sec_colunas in seccoes.items():
  if sec_colunas:
    render_gauge_grid(sec_colunas, sec_nome)
