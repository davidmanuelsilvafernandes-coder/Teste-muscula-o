import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
from supabase import create_client, Client

st.set_page_config(layout="wide", page_title="Dashboard B2B Pro")
st.title("Dashboard de Desempenho Desportivo (B2B)")

# Ligar à Base de Dados
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

with st.sidebar:
    st.header("👥 Gestão de Clientes")
    
    # 1. Obter lista de clientes únicos da BD
    resposta = supabase.table("treinos").select("cliente").execute()
    df_bd = pd.DataFrame(resposta.data)
    clientes_existentes = df_bd['cliente'].unique().tolist() if not df_bd.empty else []
    
    cliente_selecionado = st.selectbox("Selecione o Cliente:", ["Adicionar Novo Cliente..."] + clientes_existentes)
    
    st.divider()
    
    # 2. Lógica para carregar novos ficheiros para a BD
    if cliente_selecionado == "Adicionar Novo Cliente...":
        nome_novo = st.text_input("Nome do novo cliente:")
        ficheiro_carregado = st.file_uploader("Upload CSV (Hevy)", type=["csv"])
        
        if st.button("Guardar Perfil na Base de Dados") and ficheiro_carregado and nome_novo:
            df_novo = pd.read_csv(ficheiro_carregado)
            # Ficar apenas com as colunas necessárias para poupar espaço
            df_limpo = df_novo[['start_time', 'exercise_title', 'weight_kg', 'reps']].copy()
            df_limpo['cliente'] = nome_novo
            
            # Enviar para o Supabase (formato dicionário)
            supabase.table("treinos").insert(df_limpo.to_dict(orient="records")).execute()
            st.success(f"✅ Dados de {nome_novo} guardados com sucesso! Atualize a página.")
            st.stop()

# 3. Mostrar o Dashboard se um cliente válido for selecionado
if cliente_selecionado != "Adicionar Novo Cliente...":
    # Ir buscar apenas os dados deste cliente à BD
    dados_cliente = supabase.table("treinos").select("*").eq("cliente", cliente_selecionado).execute()
    df = pd.DataFrame(dados_cliente.data)
    
    df['Data_Completa'] = pd.to_datetime(df['start_time'], format='%d %b %Y, %H:%M', errors='coerce')
    df['Data'] = df['Data_Completa'].dt.date
    df['Semana'] = df['Data_Completa'].dt.to_period('W').apply(lambda r: r.start_time).dt.date
    df['1RM_Estimada'] = df['weight_kg'] * (1 + (df['reps'] / 30))
    df['Volume_Serie'] = df['weight_kg'] * df['reps']
    
    def categorizar_exercicio(nome):
        nome = str(nome).lower()
        if any(x in nome for x in ['chest', 'pec', 'press', 'fly', 'pushdown', 'dip']): return 'Peito/Ombros/Tríceps', 'Push'
        if any(x in nome for x in ['row', 'pull', 'lat', 'curl', 'bicep']): return 'Costas/Bíceps', 'Pull'
        if any(x in nome for x in ['squat', 'leg', 'deadlift', 'calf']): return 'Pernas', 'Legs'
        return 'Core/Outros', 'Outro'
        
    df[['Grupo_Muscular', 'Movimento']] = df.apply(lambda x: pd.Series(categorizar_exercicio(x['exercise_title'])), axis=1)

    tab1, tab2, tab3 = st.tabs(["📊 Performance & Progressão", "🧬 Saúde, Fadiga e Simetria", "📋 Relatório Automático"])
    
    with tab1:
        st.subheader("Análise de Sobrecarga Progressiva")
        exercicios = df['exercise_title'].dropna().unique()
        exercicios.sort()
        exercicio = st.selectbox("Selecione o Exercício:", options=exercicios)
        
        df_ex = df[df['exercise_title'] == exercicio].copy()
        if not df_ex.empty:
            df_agrupado = df_ex.groupby('Data')['1RM_Estimada'].max().reset_index()
            df_agrupado['Dias'] = (pd.to_datetime(df_agrupado['Data']) - pd.to_datetime(df_agrupado['Data'].min())).dt.days
            
            if len(df_agrupado) > 1:
                z = np.polyfit(df_agrupado['Dias'], df_agrupado['1RM_Estimada'], 1)
                p = np.poly1d(z)
                df_agrupado['Projeção Futura'] = p(df_agrupado['Dias'])
                dados_grafico = df_agrupado.set_index('Data')[['1RM_Estimada', 'Projeção Futura']]
            else:
                dados_grafico = df_agrupado.set_index('Data')[['1RM_Estimada']]
                
            col1, col2, col3 = st.columns(3)
            col1.metric("🏆 Recorde 1RM", f"{df_ex['1RM_Estimada'].max():.1f} kg")
            col2.metric("📦 Máx Volume/Sessão", f"{df_ex.groupby('Data')['Volume_Serie'].sum().max():.0f} kg")
            col3.metric("📅 Treinos", df_ex['Data'].nunique())
            
            st.line_chart(dados_grafico, height=350)
            
            st.subheader("Volume Histórico Semanal")
            vol_semanal = df.groupby(['Semana', 'Grupo_Muscular'])['Volume_Serie'].sum().reset_index()
            st.bar_chart(vol_semanal.pivot(index='Semana', columns='Grupo_Muscular', values='Volume_Serie').fillna(0), height=300)

    with tab2:
        st.subheader("Monitorização de Carga Científica")
        colA, colB = st.columns(2)
        
        with colA:
            st.markdown("**Simetria Muscular (Radar)**")
            radar_df = df.groupby('Grupo_Muscular')['Volume_Serie'].sum().reset_index()
            if not radar_df.empty:
                fig = px.line_polar(radar_df, r='Volume_Serie', theta='Grupo_Muscular', line_close=True,
                                    color_discrete_sequence=['#00e676'], template='plotly_dark')
                fig.update_traces(fill='toself')
                st.plotly_chart(fig, use_container_width=True)
                
        with colB:
            st.markdown("**ACWR (Risco de Fadiga/Lesão)**")
            diario = df.groupby('Data')['Volume_Serie'].sum().reset_index()
            diario['Data'] = pd.to_datetime(diario['Data'])
            idx = pd.date_range(diario['Data'].min(), diario['Data'].max())
            diario = diario.set_index('Data').reindex(idx).fillna(0)
            
            diario['Carga_Aguda_7d'] = diario['Volume_Serie'].rolling(window=7, min_periods=1).sum()
            diario['Carga_Cronica_28d'] = diario['Volume_Serie'].rolling(window=28, min_periods=1).sum() / 4
            diario['ACWR'] = diario['Carga_Aguda_7d'] / diario['Carga_Cronica_28d'].replace(0, 1)
            
            acwr_atual = diario['ACWR'].iloc[-1]
            st.metric("Índice ACWR Atual", f"{acwr_atual:.2f}")
            st.line_chart(diario['ACWR'].tail(30), height=200)

    with tab3:
        st.subheader("Geração de Resumo Executivo")
        vol_total = df['Volume_Serie'].sum()
        ex_monitorizados = df['exercise_title'].nunique()
        musculo_top = radar_df.loc[radar_df['Volume_Serie'].idxmax()]['Grupo_Muscular'] if not radar_df.empty else "N/A"
        
        st.write(f"**🏋️‍♂️ Volume Total Acumulado:** {vol_total:.0f} kg")
        
        def criar_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, f"Relatorio de Desempenho - {cliente_selecionado}", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(10)
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 10, f"Volume Total Acumulado: {vol_total:.0f} kg", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 10, f"Exercicios Monitorizados: {ex_monitorizados}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 10, f"Musculo mais trabalhado: {musculo_top}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 10, f"Indice de Seguranca (ACWR): {acwr_atual:.2f}", new_x="LMARGIN", new_y="NEXT")
            return bytes(pdf.output())

        st.download_button(label="📄 Descarregar Relatório PDF", data=criar_pdf(), file_name=f"relatorio_{cliente_selecionado}.pdf", mime="application/pdf")
