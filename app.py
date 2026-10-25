import streamlit as st
import pandas as pd

st.title("Dashboard de Força e Hipertrofia B2B")
st.write("Ferramenta de análise de desempenho para Personal Trainers.")

# 1. Botão para o utilizador carregar o seu próprio ficheiro CSV
ficheiro_carregado = st.file_uploader("Carregue o ficheiro de exportação do Hevy (.csv)", type=["csv"])

if ficheiro_carregado is not None:
    # Ler os dados do ficheiro que foi carregado na página
    df = pd.read_csv(ficheiro_carregado)
    
    # 2. Calcular as duas métricas principais
    df['1RM_Estimada'] = df['weight_kg'] * (1 + (df['reps'] / 30)) # Força
    df['Volume_Serie'] = df['weight_kg'] * df['reps']              # Hipertrofia
    
    # 3. Criar o menu interativo com os exercícios encontrados no ficheiro
    exercicios_disponiveis = df['exercise_title'].dropna().unique()
    exercicios_disponiveis.sort()
    
    index_padrao = list(exercicios_disponiveis).index('Chest Press (Machine)') if 'Chest Press (Machine)' in exercicios_disponiveis else 0
    
    exercicio_selecionado = st.selectbox(
        "Selecione o exercício a analisar:", 
        options=exercicios_disponiveis,
        index=index_padrao
    )
    
    # 4. Filtrar e formatar as datas
    df_filtrado = df[df['exercise_title'] == exercicio_selecionado].copy()
    
    if not df_filtrado.empty:
        df_filtrado['Date'] = pd.to_datetime(df_filtrado['start_time'], format='%d %b %Y, %H:%M', errors='coerce').dt.date
        
        # --- GRÁFICO 1: FORÇA PURA ---
        st.subheader(f"Evolução da 1RM: {exercicio_selecionado}")
        progresso_forca = df_filtrado.groupby('Date')['1RM_Estimada'].max().reset_index()
        st.line_chart(data=progresso_forca, x='Date', y='1RM_Estimada')
        
        # --- GRÁFICO 2: HIPERTROFIA (Volume) ---
        st.subheader("Volume Total de Carga (Kg x Reps)")
        progresso_volume = df_filtrado.groupby('Date')['Volume_Serie'].sum().reset_index()
        st.bar_chart(data=progresso_volume, x='Date', y='Volume_Serie')
        
    else:
        st.warning("Não há dados suficientes para desenhar os gráficos deste exercício.")
else:
    st.info("👆 Por favor, faça o upload de um ficheiro CSV do Hevy para começar.")
