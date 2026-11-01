import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Hotel Alísios - Dashboard de Satisfação",
    page_icon="🏨",
    layout="wide"
)

st.title("🏨 Hotel Alísios — Análise de Satisfação de Clientes")
st.markdown("---")

# -----------------------------------------------------------------------------
# CARREGAMENTO E PIPELINE DE DADOS
# -----------------------------------------------------------------------------
@st.cache_data
def load_survey_data(file):
    # Lê a folha BD_Inquéritos com o cabeçalho na linha 4 (índice 3)
    df = pd.read_excel(file, sheet_name="BD_Inquéritos", header=3)
    return df

st.sidebar.header("📁 Gestão de Dados")
uploaded_file = st.sidebar.file_uploader("Carregar Ficheiro Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    df_raw = load_survey_data(uploaded_file)
else:
    try:
        df_raw = load_survey_data("BD Satisfação Cliente.xlsx")
    except Exception:
        st.sidebar.warning("Carrega o ficheiro Excel para iniciar a análise.")
        st.stop()

# Cópia de trabalho e aplicação estrita das regras de exclusão
df = df_raw.copy()

# Exclusão estrita da Coluna1 em todas as circunstâncias
if 'Coluna1' in df.columns:
    df = df.drop(columns=['Coluna1'])

# Tratamento da coluna de Data para permitir filtros temporais
if 'Data' in df.columns:
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

# -----------------------------------------------------------------------------
# FILTROS NA BARRA LATERAL
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros Dinâmicos")

# 1. Filtro por Data
if 'Data' in df.columns and not df['Data'].dropna().empty:
    min_date = df['Data'].min().date()
    max_date = df['Data'].max().date()
    
    date_filter = st.sidebar.date_input(
        "Selecione o Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if isinstance(date_filter, tuple) and len(date_filter) == 2:
        start_date, end_date = date_filter
        df = df[(df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)]

# 2. Filtro por Tipo de Quarto / Alojamento
if 'Quarto' in df.columns:
    quartos_disponiveis = ['Todos'] + list(df['Quarto'].dropna().unique())
    selected_quarto = st.sidebar.selectbox("Tipo de Quarto", quartos_disponiveis)
    if selected_quarto != 'Todos':
        df = df[df['Quarto'] == selected_quarto]

# 3. Filtro por Motivo de Viagem
if 'Motivo Viagem' in df.columns:
    motivos_disponiveis = ['Todos'] + list(df['Motivo Viagem'].dropna().unique())
    selected_motivo = st.sidebar.selectbox("Motivo da Viagem", motivos_disponiveis)
    if selected_motivo != 'Todos':
        df = df[df['Motivo Viagem'] == selected_motivo]

# -----------------------------------------------------------------------------
# SECÇÃO 1: MÉTRICAS GLOBAIS E TAXA DE RESPOSTA
# -----------------------------------------------------------------------------
st.subheader("📈 Resumo Operacional")

total_recolhidos = len(df)
total_distribuidos = df['Distribuídos'].sum() if 'Distribuídos' in df.columns else 0

if total_distribuidos > 0:
    taxa_resposta = (total_recolhidos / total_distribuidos) * 100
else:
    taxa_resposta = 0.0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Inquéritos Recolhidos", f"{total_recolhidos}")
kpi2.metric("Inquéritos Distribuídos", f"{int(total_distribuidos)}")
kpi3.metric("Taxa de Resposta Global", f"{taxa_resposta:.1f}%")

st.markdown("---")

# -----------------------------------------------------------------------------
# SECÇÃO 2: AVALIAÇÃO DAS RUBRICAS PRINCIPAIS (1 A 5) E AMBIENTAL
# -----------------------------------------------------------------------------
st.subheader("⭐ Avaliação Média por Rubrica")

rubricas_escala = [
    '1. Acolhimento e Receção',
    '2. Instalações e Serviços',
    '3. Restauração e Bar',
    '4. Limpeza e Arrumação',
    '5. Qualidade / Preço',
    'Preocupações Ambientais'
]

rubricas_presentes = [r for r in rubricas_escala if r in df.columns]

if rubricas_presentes:
    cols_metrics = st.columns(min(len(rubricas_presentes), 3))
    
    for idx, rubrica in enumerate(rubricas_presentes):
        serie_valores = pd.to_numeric(df[rubrica], errors='coerce')
        media_rubrica = serie_valores.mean()
        
        col_target = cols_metrics[idx % 3]
        with col_target:
            if pd.notnull(media_rubrica):
                # Representação em Gauge para leitura imediata
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=media_rubrica,
                    title={'text': rubrica, 'font': {'size': 13}},
                    gauge={
                        'axis': {'range': [1, 5], 'tickwidth': 1},
                        'bar': {'color': "#2b5c8f"},
                        'steps': [
                            {'range': [1, 3], 'color': "#f8d7da"},
                            {'range': [3, 4], 'color': "#fff3cd"},
                            {'range': [4, 5], 'color': "#d4edda"}
                        ]
                    }
                ))
                fig_g.update_layout(height=210, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_g, use_container_width=True)
            else:
                st.info(f"Sem dados suficientes para {rubrica}")

st.markdown("---")

# -----------------------------------------------------------------------------
# SECÇÃO 3: VARIÁVEIS BINÁRIAS — MOTIVOS DE ESCOLHA E FIDELIZAÇÃO (NOVO)
# -----------------------------------------------------------------------------
st.subheader("🎯 Análise de Motivos de Escolha e Fidelização")

def converter_binario(series):
    """Converte e limpa colunas binárias/proporcionais para lógica 0/1"""
    return pd.to_numeric(series, errors='coerce').fillna(0)

col_esquerda, col_direita = st.columns(2)

# 3.1. Gráfico de Barras para Motivos de Escolha
binary_choice_cols = ['Localização ', 'Preço', 'Qualidade', 'Comentários online', 'Outros']

with col_esquerda:
    st.markdown("#### Motivos de Escolha do Hotel")
    dados_escolha = []
    
    for col in binary_choice_cols:
        if col in df.columns:
            s_bin = converter_binario(df[col])
            percentual = (s_bin > 0).mean() * 100
            dados_escolha.append({"Motivo": col.strip(), "Percentagem": percentual})
            
    if dados_escolha:
        df_motivos = pd.DataFrame(dados_escolha).sort_values(by="Percentagem", ascending=True)
        
        fig_bar = px.bar(
            df_motivos,
            x="Percentagem",
            y="Motivo",
            orientation="h",
            text=df_motivos["Percentagem"].apply(lambda val: f"{val:.1f}%"),
            labels={"Percentagem": "Taxa de Indicação (%)", "Motivo": ""}
        )
        fig_bar.update_layout(
            xaxis=dict(range=[0, 100]),
            height=300,
            margin=dict(l=0, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Colunas de motivos de escolha não identificadas na tabela.")

# 3.2. Métricas de Fidelização e Recomendação
loyalty_cols = ['Recomendaria', 'Tenciona Voltar']

with col_direita:
    st.markdown("#### Fidelização e Recomendação")
    st.markdown("Proporção de respostas afirmativas dos clientes inquiridos:")
    
    col_f1, col_f2 = st.columns(2)
    
    fid_containers = [col_f1, col_f2]
    for idx, col_name in enumerate(loyalty_cols):
        with fid_containers[idx]:
            if col_name in df.columns:
                s_fid = converter_binario(df[col_name])
                taxa_fid = (s_fid > 0).mean() * 100
                st.metric(label=f"Taxa de {col_name}", value=f"{taxa_fid:.1f}%")
            else:
                st.metric(label=f"{col_name}", value="N/D")

st.markdown("---")

# -----------------------------------------------------------------------------
# SECÇÃO 4: VISUALIZAÇÃO DETALHADA DA TABELA DE DADOS (COM EXCLUSÃO DE COLUNA1)
# -----------------------------------------------------------------------------
with st.expander("🔍 Ver Tabela de Dados Filtrada"):
    st.dataframe(df, use_container_width=True)

st.markdown("---")
st.caption("Hotel Alísios — Sistema Automatizado de Business Intelligence e Inquéritos de Satisfação.")
