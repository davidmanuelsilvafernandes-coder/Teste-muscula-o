import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Dashboard B2B")
st.title("Dashboard de Desempenho B2B")

with st.sidebar:
    st.header("⚙️ Configurações")
    ficheiro_carregado = st.file_uploader("Upload CSV (Hevy)", type=["csv"])

if ficheiro_carregado is not None:
    df = pd.read_csv(ficheiro_carregado)
    
    df['Data_Completa'] = pd.to_datetime(df['start_time'], format='%d %b %Y, %H:%M', errors='coerce')
    df['Data'] = df['Data_Completa'].dt.date
    df['Semana'] = df['Data_Completa'].dt.to_period('W').apply(lambda r: r.start_time).dt.date
    
    with st.sidebar:
        st.divider()
        st.subheader("📅 Período de Análise")
        data_min = df['Data'].min()
        data_max = df['Data'].max()
        datas = st.date_input("Selecione o intervalo:", value=(data_min, data_max), min_value=data_min, max_value=data_max)
    
    if len(datas) == 2:
        df = df[(df['Data'] >= datas[0]) & (df['Data'] <= datas[1])].copy()
    
    df['1RM_Estimada'] = df['weight_kg'] * (1 + (df['reps'] / 30))
    df['Volume_Serie'] = df['weight_kg'] * df['reps']
    
    # Categorizar Músculos e Tipo de Movimento (Push vs Pull)
    def categorizar_exercicio(nome):
        nome = str(nome).lower()
        if any(x in nome for x in ['chest', 'pec', 'press', 'fly', 'pushdown', 'dip']): 
            return pd.Series(['Peito/Ombros/Tríceps', 'Push (Empurrar)'])
        elif any(x in nome for x in ['row', 'pull', 'lat', 'curl', 'bicep', 'chin']): 
            return pd.Series(['Costas/Bíceps', 'Pull (Puxar)'])
        elif any(x in nome for x in ['squat', 'leg', 'deadlift', 'calf', 'lunge']): 
            return pd.Series(['Pernas', 'Pernas'])
        return pd.Series(['Core/Outros', 'Outro'])
        
    df[['Grupo_Muscular', 'Movimento']] = df['exercise_title'].apply(categorizar_exercicio)
    df['Zona_Foco'] = df['reps'].apply(lambda r: 'Força' if r <= 5 else ('Hipertrofia' if r <= 12 else 'Resistência'))

    with st.sidebar:
        st.divider()
        exercicios = df['exercise_title'].dropna().unique()
        exercicios.sort()
        exercicio = st.selectbox("Análise Individual:", options=exercicios)
    
    st.subheader(f"Análise e Projeção: {exercicio}")
    df_ex = df[df['exercise_title'] == exercicio].copy()
    
    if not df_ex.empty:
        df_agrupado = df_ex.groupby('Data')['1RM_Estimada'].max().reset_index()
        
        # Regressão Linear para Linha de Tendência Predita
        df_agrupado['Dias'] = (pd.to_datetime(df_agrupado['Data']) - pd.to_datetime(df_agrupado['Data'].min())).dt.days
        if len(df_agrupado) > 1:
            z = np.polyfit(df_agrupado['Dias'], df_agrupado['1RM_Estimada'], 1)
            p = np.poly1d(z)
            df_agrupado['Projeção Futura'] = p(df_agrupado['Dias'])
            dados_grafico = df_agrupado.set_index('Data')[['1RM_Estimada', 'Projeção Futura']]
        else:
            dados_grafico = df_agrupado.set_index('Data')[['1RM_Estimada']]
            
        max_1rm = df_ex['1RM_Estimada'].max()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🏆 Recorde 1RM", f"{max_1rm:.1f} kg")
        col2.metric("📦 Máx Volume/Sessão", f"{df_ex.groupby('Data')['Volume_Serie'].sum().max():.0f} kg")
        col3.metric("📅 Treinos Registados", df_ex['Data'].nunique())
        
        st.line_chart(dados_grafico, height=300)
    
    st.divider()
    
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Volume Semanal por Músculo")
        vol_semanal = df.groupby(['Semana', 'Grupo_Muscular'])['Volume_Serie'].sum().reset_index()
        st.bar_chart(vol_semanal.pivot(index='Semana', columns='Grupo_Muscular', values='Volume_Serie').fillna(0), height=300)
        
    with colB:
        st.subheader("Rácio Prevenção de Lesões")
        vol_push = df[df['Movimento'] == 'Push (Empurrar)']['Volume_Serie'].sum()
        vol_pull = df[df['Movimento'] == 'Pull (Puxar)']['Volume_Serie'].sum()
        
        if vol_push > 0 or vol_pull > 0:
            st.bar_chart(pd.DataFrame({'Volume Total': [vol_push, vol_pull]}, index=['Push', 'Pull']), height=200)
            racio = vol_push / vol_pull if vol_pull > 0 else float('inf')
            if racio > 1.5:
                st.error(f"⚠️ Alerta: Volume Push é {racio:.1f}x superior ao Pull. Risco de lesão no ombro e má postura.")
            elif racio < 0.6:
                st.warning("⚠️ Atenção: Volume Pull é desproporcionalmente maior.")
            else:
                st.success("✅ Rácio equilibrado! Excelente gestão de carga.")
    
    st.divider()
    with st.expander("📋 Gerar Relatório para o Cliente (WhatsApp / Print)"):
        st.subheader("Resumo do Ciclo de Treino")
        st.write(f"**Período:** {datas[0]} até {datas[1]}")
        st.write(f"**Volume Total Movimentado:** {df['Volume_Serie'].sum():.0f} kg")
        st.write(f"**Melhor Marca ({exercicio}):** {max_1rm:.1f} kg")
        st.write(f"**Foco Predominante:** {df['Zona_Foco'].mode()[0]}")
        st.info("💡 Tire uma captura de ecrã desta área para partilhar as vitórias com o cliente.")

else:
    st.info("👆 Abra a barra lateral para carregar o ficheiro CSV.")
