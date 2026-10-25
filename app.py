import streamlit as st
import pandas as pd

# Configuração da página para formato panorâmico
st.set_page_config(layout="wide", page_title="Dashboard B2B")

st.title("Dashboard de Desempenho B2B")

# 1. BARRA LATERAL (Sidebar)
with st.sidebar:
    st.header("⚙️ Configurações")
    ficheiro_carregado = st.file_uploader("Upload CSV (Hevy)", type=["csv"])

if ficheiro_carregado is not None:
    df = pd.read_csv(ficheiro_carregado)
    
    # Cálculos Base
    df['1RM_Estimada'] = df['weight_kg'] * (1 + (df['reps'] / 30))
    df['Volume_Serie'] = df['weight_kg'] * df['reps']
    
    # Função para mapear músculos automaticamente pelas palavras no nome
    def mapear_musculo(nome):
        nome = str(nome).lower()
        if any(x in nome for x in ['chest', 'pec', 'press', 'fly']): return 'Peito/Ombros'
        if any(x in nome for x in ['squat', 'leg', 'deadlift']): return 'Pernas'
        if any(x in nome for x in ['row', 'pull', 'lat']): return 'Costas'
        if any(x in nome for x in ['curl', 'tricep', 'arm', 'extension', 'pushdown']): return 'Braços'
        return 'Outros'
        
    df['Grupo_Muscular'] = df['exercise_title'].apply(mapear_musculo)
    
    # Processar Datas para encontrar as Semanas
    df['Data'] = pd.to_datetime(df['start_time'], format='%d %b %Y, %H:%M', errors='coerce')
    df['Semana'] = df['Data'].dt.to_period('W').apply(lambda r: r.start_time).dt.date
    
    # Filtro de Exercício na Sidebar
    with st.sidebar:
        exercicios = df['exercise_title'].dropna().unique()
        exercicios.sort()
        exercicio_selecionado = st.selectbox("Análise Individual:", options=exercicios)
    
    # 2. MÉTRICAS DE TOPO (KPIs)
    st.subheader(f"Resumo: {exercicio_selecionado}")
    df_ex = df[df['exercise_title'] == exercicio_selecionado].copy()
    
    if not df_ex.empty:
        df_ex['Dia'] = df_ex['Data'].dt.date
        max_1rm = df_ex['1RM_Estimada'].max()
        max_vol = df_ex.groupby('Dia')['Volume_Serie'].sum().max()
        treinos_totais = df_ex['Dia'].nunique()
        
        # Criar 3 cartões lado a lado
        col1, col2, col3 = st.columns(3)
        col1.metric("🏆 Recorde 1RM", f"{max_1rm:.1f} kg")
        col2.metric("📦 Máx Volume/Sessão", f"{max_vol:.0f} kg")
        col3.metric("📅 Treinos Registados", treinos_totais)
        
        # Gráfico Individual de Força
        progresso_forca = df_ex.groupby('Dia')['1RM_Estimada'].max().reset_index()
        st.line_chart(data=progresso_forca, x='Dia', y='1RM_Estimada', height=300)
    
    st.divider()
    
    # 3. VOLUME SEMANAL POR GRUPO MUSCULAR (Ouro para Hipertrofia)
    st.subheader("Volume Semanal por Grupo Muscular")
    volume_semanal = df.groupby(['Semana', 'Grupo_Muscular'])['Volume_Serie'].sum().reset_index()
    
    # Pivotar a tabela para desenhar barras empilhadas por cores
    df_pivot = volume_semanal.pivot(index='Semana', columns='Grupo_Muscular', values='Volume_Serie').fillna(0)
    st.bar_chart(df_pivot, height=400)
    
else:
    st.info("👆 Abra a barra lateral à esquerda para carregar o ficheiro CSV.")
