import streamlit as st
import pandas as pd

st.title("Dashboard de Força e Hipertrofia")
st.write("Evolução da 1RM (Press Peito Horizontal)")

# 1. Carregar os dados
df = pd.read_csv('hevy_export.csv')

# 2. Mapear o nome exato que está no seu CSV
mapeamento_exercicios = {
    'Chest Press (Machine)': 'Press Peito Horizontal'
}

# 3. Aplicar o mapeamento (coluna 'exercise_title')
df['Exercicio_Unificado'] = df['exercise_title'].replace(mapeamento_exercicios)

# 4. Calcular a 1RM (colunas 'weight_kg' e 'reps')
df['1RM_Estimada'] = df['weight_kg'] * (1 + (df['reps'] / 30))

# 5. Filtrar apenas o Press Peito Horizontal
df_press = df[df['Exercicio_Unificado'] == 'Press Peito Horizontal'].copy()

# 6. Limpar as datas e desenhar o gráfico
if not df_press.empty:
    # Converter a coluna 'start_time' para data
    df_press['Date'] = pd.to_datetime(df_press['start_time'], format='%d %b %Y, %H:%M', errors='coerce')
    
    # Remover as horas para agrupar apenas por dia
    df_press['Date'] = df_press['Date'].dt.date
    
    # Isolar a melhor marca (1RM máxima) de cada dia
    progresso_diario = df_press.groupby('Date')['1RM_Estimada'].max().reset_index()
    
    # Desenhar o gráfico de linha
    st.line_chart(data=progresso_diario, x='Date', y='1RM_Estimada')
else:
    st.warning("Não foram encontrados dados para o exercício especificado. Verifique o mapeamento.")
