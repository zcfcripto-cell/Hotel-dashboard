import pandas as pd
import plotly.express as px
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

st.title("Hotel Alísios — Dashboard Dinâmico de Satisfação")
st.markdown("Análise interativa dos inquéritos de satisfação dos clientes com base nos dados oficiais.")

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros de Segmentação")

# Filtro de Ano
anos = sorted(df["Ano"].dropna().unique())
ano_selecionado = st.sidebar.selectbox("Selecionar Ano", ["Todos"] + list(anos))

if ano_selecionado != "Todos":
    df_filtered = df[df["Ano"] == ano_selecionado]
else:
    df_filtered = df

# Filtro de Mês
meses = sorted(df_filtered["Mês"].dropna().unique())
mes_selecionado = st.sidebar.selectbox("Selecionar Mês", ["Todos"] + list(meses))

if mes_selecionado != "Todos":
    df_filtered = df_filtered[df_filtered["Mês"] == mes_selecionado]

# --- MÉTRICAS PRINCIPAIS (KPIs) ---
col1, col2, col3 = st.columns(3)

total_inqueritos = len(df_filtered)
satisfacao_geral = df_filtered["Geral_Pct"].mean() * 100 if not df_filtered.empty else 0

col1.metric("Inquéritos Visíveis", f"{total_inqueritos}")
col2.metric("Satisfação Geral Média", f"{satisfacao_geral:.1f}%")

if "Nacionalidade" in df_filtered.columns:
    nacionalidades_unicas = df_filtered["Nacionalidade"].nunique()
    col3.metric("Nacionalidades Diferentes", f"{nacionalidades_unicas}")

st.markdown("---")

# --- GRÁFICOS E ANÁLISES ---
st.subheader("Desempenho por Categoria Principal")

colunas_pct = ["FO_Pct", "Quarto_Pct", "PA_Pct", "Rest_Pct"]
nomes_pct = {
    "FO_Pct": "Front-Office",
    "Quarto_Pct": "Quarto",
    "PA_Pct": "Pequeno-Almoço",
    "Rest_Pct": "Restaurante/Bar"
}

medias_secções = []
for col in colunas_pct:
    if col in df_filtered.columns:
        media = df_filtered[col].mean() * 100
        medias_secções.append({"Secção": nomes_pct.get(col, col), "Satisfação (%)": media})

df_secções = pd.DataFrame(medias_secções)

if not df_secções.empty:
    fig = px.bar(
        df_secções,
        x="Secção",
        y="Satisfação (%)",
        text="Satisfação (%)",
        color="Secção",
        title="Média de Satisfação por Departamento"
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(yaxis=dict(range=[0, 100]), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# --- TABELA DE DADOS DETALHADA ---
with st.expander("Ver dados detalhados filtrados"):
    st.dataframe(df_filtered)
