import streamlit as st
import pandas as pd

st.title("Dashboard de Força e Hipertrofia")

# 1. Carregar os dados
df = pd.read_csv('hevy_export.csv')

# 2. Calcular a 1RM para todos os treinos de uma vez
df['1RM_Estimada'] = df['weight_kg'] * (1 + (df['reps'] / 30))

# 3. Obter a lista de todos os exercícios que existem no seu ficheiro
# Removemos os vazios e ordenamos alfabeticamente
exercicios_disponiveis = df['exercise_title'].dropna().unique()
exercicios_disponiveis.sort()

# 4. Criar o menu interativo na página
# Definimos o Chest Press como padrão se existir, senão escolhe o primeiro da lista
index_padrao = list(exercicios_disponiveis).index('Chest Press (Machine)') if 'Chest Press (Machine)' in exercicios_disponiveis else 0

exercicio_selecionado = st.selectbox(
    "Escolha o exercício que pretende analisar:", 
    options=exercicios_disponiveis,
    index=index_padrao
)

st.write(f"Evolução da 1RM: **{exercicio_selecionado}**")

# 5. Filtrar os dados com base na escolha do utilizador
df_filtrado = df[df['exercise_title'] == exercicio_selecionado].copy()

# 6. Limpar datas e desenhar o gráfico
if not df_filtrado.empty:
    df_filtrado['Date'] = pd.to_datetime(df_filtrado['start_time'], format='%d %b %Y, %H:%M', errors='coerce')
    df_filtrado['Date'] = df_filtrado['Date'].dt.date
    
    progresso_diario = df_filtrado.groupby('Date')['1RM_Estimada'].max().reset_index()
    
    st.line_chart(data=progresso_diario, x='Date', y='1RM_Estimada')
else:
    st.warning("Não há dados suficientes para desenhar o gráfico deste exercício.")
