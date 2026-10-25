import streamlit as st
import pandas as pd

st.title("Dashboard de Força e Hipertrofia")
st.write("Evolução da 1RM (Press Peito Horizontal)")

# Carregar e limpar dados
df = pd.read_csv('hevy_export.csv')

# Mapear máquinas (ajuste com os nomes exatos do seu CSV)
mapeamento_exercicios = {
    'Chest Press Machine': 'Press Peito Horizontal',
    'Convergent Chest Press': 'Press Peito Horizontal'
}
df['Exercicio_Unificado'] = df['Exercise Name'].replace(mapeamento_exercicios)

# Calcular 1RM e filtrar
df['1RM_Estimada'] = df['Weight (kg)'] * (1 + (df['Reps'] / 30))
df_press = df[df['Exercicio_Unificado'] == 'Press Peito Horizontal'].copy()

# Formatar datas e desenhar gráfico
if not df_press.empty:
    df_press['Date'] = pd.to_datetime(df_press['Date'])
    progresso_diario = df_press.groupby('Date')['1RM_Estimada'].max().reset_index()
    st.line_chart(data=progresso_diario, x='Date', y='1RM_Estimada')
else:
    st.warning("Verifique os nomes das máquinas no dicionário, não foram encontrados dados correspondentes.")
