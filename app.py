import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E CARREGAMENTO DE DADOS
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard - Hotel Alísios", layout="wide")

st.title("Dashboard de Operações - Hotel Alísios")

@st.cache_data
def carregar_dados():
    # Substitua "dados_satisfacao.csv" pelo nome exato do seu ficheiro de dados se for diferente
    try:
        return Dashboard_Satisfacao_Cliente_Corrigido.xlsx
    except FileNotFoundError:
        return None

df = carregar_dados()

if df is not None:
    # ---------------------------------------------------------
    # 2. OUTRAS SECÇÕES DO SEU DASHBOARD (Exemplo)
    # ---------------------------------------------------------
    st.header("Visão Geral dos Inquéritos")
    st.write(f"Total de registos carregados: {len(df)}")
    
    # ---------------------------------------------------------
    # 3. MATRIZ DE CORRELAÇÃO (RUBRICAS DE 1 A 5)
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("Matriz de Correlação das Rubricas (Escala de 1 a 5)")
    st.write("Análise de correlação entre as rubricas avaliadas no inquérito.")

    # Filtra apenas as colunas das rubricas (ex: que contêm '_Pct' ou ajuste conforme o seu dataset)
    colunas_rubricas = [col for col in df.columns if '_Pct' in col]
    
    # Se preferir filtrar por colunas específicas, comente a linha acima e descomente a linha abaixo colocando os nomes exatos:
    # colunas_rubricas = ['Nome_Coluna_1', 'Nome_Coluna_2', 'Nome_Coluna_3']

    df_filtrado = df[colunas_rubricas].select_dtypes(include=['float64', 'int64'])
    
    if not df_filtrado.empty:
        # Calcular a matriz de correlação
        corr = df_filtrado.corr()
        
        # Configurar o tamanho do gráfico para ficar legível
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Gerar o mapa de calor (sem os números `annot=False` para evitar sobreposição)
        sns.heatmap(
            corr, 
            annot=False,         # Desativado para o gráfico não ficar amontoado
            cmap='coolwarm', 
            ax=ax, 
            linewidths=0.5,
            vmin=-1, vmax=1,     # Escala fixa de correlação de -1 a 1
            cbar_kws={'label': 'Nível de Correlação'}
        )
        
        # Ajustar a rotação e o tamanho das legendas dos eixos
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        
        # Garantir que o layout não corta nenhuma etiqueta
        plt.tight_layout()
        
        # Apresentar o gráfico no Streamlit
        st.pyplot(fig)
    else:
        st.warning("Não foram encontradas colunas numéricas suficientes correspondentes às rubricas para calcular a correlação.")

else:
    st.error("O ficheiro de dados não foi encontrado. Por favor, verifique se o ficheiro CSV está na pasta correta do projeto no GitHub.")
