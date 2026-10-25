import streamlit as st
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Dashboard B2B")

st.title("Dashboard de Desempenho B2B")

# 1. BARRA LATERAL (Sidebar)
with st.sidebar:
    st.header("⚙️ Configurações")
    ficheiro_carregado = st.file_uploader("Upload CSV (Hevy)", type=["csv"])

if ficheiro_carregado is not None:
    df = pd.read_csv(ficheiro_carregado)
    
    # Processar Datas logo no início para podermos filtrar
    df['Data_Completa'] = pd.to_datetime(df['start_time'], format='%d %b %Y, %H:%M', errors='coerce')
    df['Data'] = df['Data_Completa'].dt.date
    df['Semana'] = df['Data_Completa'].dt.to_period('W').apply(lambda r: r.start_time).dt.date
    
    # NOVO: Filtro de Datas na Barra Lateral
    with st.sidebar:
        st.divider()
        st.subheader("📅 Período de Análise")
        data_min = df['Data'].min()
        data_max = df['Data'].max()
        datas_selecionadas = st.date_input(
            "Selecione o intervalo:",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )
    
    # Garantir que o utilizador escolheu as duas datas antes de filtrar
    if len(datas_selecionadas) == 2:
        data_inicio, data_fim = datas_selecionadas
        # Filtrar o DataFrame base consoante as datas escolhidas
        df = df[(df['Data'] >= data_inicio) & (df['Data'] <= data_fim)].copy()
    
    # Cálculos Base e Mapeamento
    df['1RM_Estimada'] = df['weight_kg'] * (1 + (df['reps'] / 30))
    df['Volume_Serie'] = df['weight_kg'] * df['reps']
    
    def mapear_musculo(nome):
        nome = str(nome).lower()
        if any(x in nome for x in ['chest', 'pec', 'press', 'fly', 'pushdown']): return 'Peito/Ombros/Tríceps'
        if any(x in nome for x in ['squat', 'leg', 'deadlift', 'calf']): return 'Pernas'
        if any(x in nome for x in ['row', 'pull', 'lat', 'curl']): return 'Costas/Bíceps'
        if any(x in nome for x in ['crunch', 'core']): return 'Core'
        return 'Outros'
        
    df['Grupo_Muscular'] = df['exercise_title'].apply(mapear_musculo)
    
    # NOVO: Definir a Zona de Treino baseada nas repetições
    def zona_treino(reps):
        if reps <= 5: return 'Força (1-5)'
        elif reps <= 12: return 'Hipertrofia (6-12)'
        else: return 'Resistência (13+)'
        
    df['Zona_Foco'] = df['reps'].apply(zona_treino)

    # Filtro de Exercício na Sidebar
    with st.sidebar:
        st.divider()
        exercicios = df['exercise_title'].dropna().unique()
        exercicios.sort()
        exercicio_selecionado = st.selectbox("Análise Individual:", options=exercicios)
    
    # 2. MÉTRICAS DE TOPO (KPIs)
    st.subheader(f"Análise: {exercicio_selecionado}")
    df_ex = df[df['exercise_title'] == exercicio_selecionado].copy()
    
    if not df_ex.empty:
        max_1rm = df_ex['1RM_Estimada'].max()
        max_vol = df_ex.groupby('Data')['Volume_Serie'].sum().max()
        treinos_totais = df_ex['Data'].nunique()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🏆 Recorde 1RM", f"{max_1rm:.1f} kg")
        col2.metric("📦 Máx Volume/Sessão", f"{max_vol:.0f} kg")
        col3.metric("📅 Treinos Registados", treinos_totais)
        
        progresso_forca = df_ex.groupby('Data')['1RM_Estimada'].max().reset_index()
        st.line_chart(data=progresso_forca, x='Data', y='1RM_Estimada', height=300)
    else:
        st.warning("Sem dados para este exercício no período selecionado.")
    
    st.divider()
    
    # 3. VISÃO GERAL DO TREINADOR (Volume e Zonas)
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Volume Semanal por Músculo")
        volume_semanal = df.groupby(['Semana', 'Grupo_Muscular'])['Volume_Serie'].sum().reset_index()
        df_pivot = volume_semanal.pivot(index='Semana', columns='Grupo_Muscular', values='Volume_Serie').fillna(0)
        st.bar_chart(df_pivot, height=350)
        
    with colB:
        st.subheader("Distribuição do Foco de Treino")
        st.write("Em qual zona o cliente passa mais tempo (Nº de Séries)?")
        # Contar quantas séries foram feitas em cada zona
        distribuicao_zonas = df['Zona_Foco'].value_counts().reset_index()
        distribuicao_zonas.columns = ['Zona', 'Séries Totais']
        # Desenhar um gráfico de barras horizontal (Streamlit novo)
        st.bar_chart(data=distribuicao_zonas.set_index('Zona'), height=315)
    
else:
    st.info("👆 Abra a barra lateral à esquerda para carregar o ficheiro CSV do cliente.")
