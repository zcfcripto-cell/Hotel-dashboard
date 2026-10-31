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

# Identificar estritamente as colunas originais de perguntas/rubricas (escala 1-5)
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

# Converter colunas de 1 a 5 para percentagem (0-100%)
for col in item_cols:
  df[col + "_Pct"] = (df[col] / 5.0) * 100

# Taxa de resposta por inquérito
df["Taxa_Resposta_Inquerito"] = df[item_cols].notnull().mean(axis=1) * 100

# Título Principal
st.title("Análise de Inquéritos de Satisfação")
st.markdown(
    "Hotel Alísios — Gestão dinâmica de inquéritos, objetivos, evolução"
    " temporal e análise detalhada."
)

# --- BARRA LATERAL (FILTROS MÚLTIPLOS E CONFIGURAÇÃO DE OBJETIVOS) ---
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
    "Selecionar Meses", options=meses_disponiveis, default=meses_disponiveis
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

# Filtro por Número de Quarto
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
col_gauge1.plotly_chart(fig_gauge_sat, use_container_width=True)

# 2º Conta-Rotações: Taxa de Resposta
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
col_gauge2.plotly_chart(fig_gauge_resp, use_container_width=True)

st.markdown("---")

# EVOLUÇÃO TEMPORAL (Corrigido para 'ME')
st.subheader("📈 Evolução Temporal da Satisfação e Inquéritos")
if not df_filtered.empty and "Data" in df_filtered.columns:
  df_temp = (
      df_filtered.set_index("Data")
      .resample("ME")["Geral_Pct"]
      .mean()
      .reset_index()
  )
  df_temp["Satisfação Geral (%)"] = df_temp["Geral_Pct"] * 100

  fig_temp = px.line(
      df_temp,
      x="Data",
      y="Satisfação Geral (%)",
      markers=True,
      title="Evolução Mensal da Satisfação Geral (%)",
      line_shape="spline",
  )
  fig_temp.add_hline(
      y=objetivo_geral,
      line_dash="dash",
      line_color="red",
      annotation_text=f"Objetivo ({objetivo_geral:.0f}%)",
  )
  fig_temp.update_layout(height=300, yaxis=dict(range=[50, 105]))
  st.plotly_chart(fig_temp, use_container_width=True)

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

# DISTRIBUIÇÃO DE NOTAS (1 a 5)
st.subheader("📊 Distribuição de Avaliações por Nota (1 a 5)")
if not df_filtered.empty:
  notas_data = []
  for col in item_cols:
    counts = df_filtered[col].value_counts()
    for nota in range(1, 6):
      notas_data.append({
          "Rubrica": col,
          "Nota": f"Nota {nota}",
          "Quantidade": counts.get(nota, 0),
      })

  df_dist = pd.DataFrame(notas_data)
  fig_dist = px.bar(
      df_dist,
      x="Quantidade",
      y="Rubrica",
      color="Nota",
      orientation="h",
      title="Proporção de Respostas por Nota (1 a 5)",
      color_discrete_map={
          "Nota 5": "#2ca02c",
          "Nota 4": "#98df8a",
          "Nota 3": "#ffbb78",
          "Nota 2": "#ff7f0e",
          "Nota 1": "#d62728",
      },
  )
  fig_dist.update_layout(height=600, barmode="stack")
  st.plotly_chart(fig_dist, use_container_width=True)

st.markdown("---")

# --- PAINEL DE CONTA-ROTAÇÕES ORGANIZADO POR SECÇÃO ---
st.subheader("Painel de Conta-Rotações Organizado por Secção")

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
      valid_cols.append(
          {"Rubrica": nome_limpo, "Media": val_g, "Objetivo": obj_val}
      )

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

        fig_ind = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=valor_m,
                delta={
                    "reference": obj_m,
                    "relative": False,
                    "valueformat": "+.1f",
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

# EXPORTAÇÃO DE DADOS
st.sidebar.markdown("---")
st.sidebar.header("📥 Exportar Relatório")
csv_data = df_filtered.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label="Descarregar Dados Filtrados (CSV)",
    data=csv_data,
    file_name="relatorio_satisfacao_hotel_alisios.csv",
    mime="text/csv",
)

# --- TABELA DE DADOS DETALHADA ---
with st.expander("Ver dados detalhados filtrados"):
  st.dataframe(df_filtered)
