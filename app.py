import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
from supabase import create_client, Client
import tempfile
import os

st.set_page_config(layout="wide", page_title="App Consultoria B2B")

# Ligar à BD
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ---------------- SISTEMA DE LOGIN ----------------
if 'pt_email' not in st.session_state:
    st.title("🔐 Login - Plataforma B2B para Personal Trainers")
    st.write("Aceda à sua área de gestão de clientes.")
    
    tab_login, tab_registo = st.tabs(["Iniciar Sessão", "Criar Conta Gratuita"])
    
    with tab_login:
        email_login = st.text_input("Email", key="login_email")
        pass_login = st.text_input("Palavra-passe", type="password", key="login_pass")
        if st.button("Entrar", type="primary"):
            try:
                resposta = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                st.session_state['pt_email'] = resposta.user.email
                st.rerun()
            except Exception as e:
                st.error("Erro no login. Verifique as suas credenciais.")
                
    with tab_registo:
        email_reg = st.text_input("Email", key="reg_email")
        pass_reg = st.text_input("Palavra-passe (Mínimo 6 caracteres)", type="password", key="reg_pass")
        if st.button("Registar", type="primary"):
            try:
                resposta = supabase.auth.sign_up({"email": email_reg, "password": pass_reg})
                st.success("Conta criada com sucesso! Pode iniciar sessão no separador ao lado.")
            except Exception as e:
                st.error(f"Erro ao registar: {e}")
                
    st.stop() # Bloqueia o resto do código se não houver login

# ---------------- DASHBOARD PRINCIPAL ----------------
st.title("Plataforma de Consultoria Desportiva (B2B)")
pt_atual = st.session_state['pt_email']

with st.sidebar:
    st.success(f"👤 Treinador: {pt_atual}")
    if st.button("Terminar Sessão"):
        del st.session_state['pt_email']
        st.rerun()
        
    st.divider()
    
    # FUNCIONALIDADE WHITE-LABEL (Branding)
    st.header("🎨 Branding")
    logo_upload = st.file_uploader("Carregue o seu Logótipo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
    if logo_upload:
        st.image(logo_upload, caption="Logótipo Ativo", use_container_width=True)
    
    st.divider()
    st.header("👥 Gestão de Clientes")
    
    # Mostrar APENAS os clientes deste PT
    resposta = supabase.table("treinos").select("cliente").eq("pt_email", pt_atual).execute()
    df_bd = pd.DataFrame(resposta.data)
    clientes_existentes = df_bd['cliente'].unique().tolist() if not df_bd.empty else []
    
    cliente_selecionado = st.selectbox("Selecione o Cliente:", ["Adicionar Novo Cliente..."] + clientes_existentes)
    
    st.divider()
    
    if cliente_selecionado == "Adicionar Novo Cliente...":
        nome_novo = st.text_input("Nome do novo cliente:")
        ficheiro_carregado = st.file_uploader("Upload CSV (Hevy)", type=["csv"])
        
        if st.button("Guardar Perfil na BD") and ficheiro_carregado and nome_novo:
            df_novo = pd.read_csv(ficheiro_carregado)
            df_limpo = df_novo[['start_time', 'exercise_title', 'weight_kg', 'reps']].copy()
            df_limpo['cliente'] = nome_novo
            df_limpo['pt_email'] = pt_atual # Associar ao PT logado
            df_limpo = df_limpo.fillna(0)
            
            supabase.table("treinos").insert(df_limpo.to_dict(orient="records")).execute()
            st.success(f"✅ {nome_novo} guardado! Atualize a página.")
            st.stop()
    else:
        st.write("Ações:")
        if st.button(f"🗑️ Eliminar {cliente_selecionado}", type="primary"):
            supabase.table("treinos").delete().eq("cliente", cliente_selecionado).eq("pt_email", pt_atual).execute()
            st.warning("Perfil eliminado. Atualize a página.")
            st.stop()

if cliente_selecionado != "Adicionar Novo Cliente...":
    dados_cliente = supabase.table("treinos").select("*").eq("cliente", cliente_selecionado).eq("pt_email", pt_atual).execute()
    df = pd.DataFrame(dados_cliente.data)
    
    if not df.empty:
        df['weight_kg'] = pd.to_numeric(df['weight_kg'], errors='coerce').fillna(0)
        df['reps'] = pd.to_numeric(df['reps'], errors='coerce').fillna(0)
        
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

        tab1, tab2, tab3 = st.tabs(["📊 Performance & Progressão", "🧬 Saúde e Simetria", "📋 Relatório com Logótipo"])
        
        with tab1:
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
                col2.metric("📦 Máx Volume", f"{df_ex.groupby('Data')['Volume_Serie'].sum().max():.0f} kg")
                col3.metric("📅 Treinos", df_ex['Data'].nunique())
                st.line_chart(dados_grafico, height=350)
                
        with tab2:
            colA, colB = st.columns(2)
            with colA:
                radar_df = df.groupby('Grupo_Muscular')['Volume_Serie'].sum().reset_index()
                if not radar_df.empty:
                    fig = px.line_polar(radar_df, r='Volume_Serie', theta='Grupo_Muscular', line_close=True, color_discrete_sequence=['#00e676'], template='plotly_dark')
                    fig.update_traces(fill='toself')
                    st.plotly_chart(fig, use_container_width=True)
            with colB:
                diario = df.groupby('Data')['Volume_Serie'].sum().reset_index()
                diario['Data'] = pd.to_datetime(diario['Data'])
                idx = pd.date_range(diario['Data'].min(), diario['Data'].max())
                diario = diario.set_index('Data').reindex(idx).fillna(0)
                diario['Carga_Aguda_7d'] = diario['Volume_Serie'].rolling(window=7, min_periods=1).sum()
                diario['Carga_Cronica_28d'] = diario['Volume_Serie'].rolling(window=28, min_periods=1).sum() / 4
                diario['ACWR'] = diario['Carga_Aguda_7d'] / diario['Carga_Cronica_28d'].replace(0, 1)
                st.metric("Índice ACWR (Risco)", f"{diario['ACWR'].iloc[-1]:.2f}")
                st.line_chart(diario['ACWR'].tail(30), height=200)

        with tab3:
            vol_total = df['Volume_Serie'].sum()
            musculo_top = radar_df.loc[radar_df['Volume_Serie'].idxmax()]['Grupo_Muscular'] if not radar_df.empty else "N/A"
            
            st.write("Exporte o relatório com a identidade visual da sua marca.")
            
            def criar_pdf_personalizado():
                pdf = FPDF()
                pdf.add_page()
                
                # Inserir logótipo se existir
                if logo_upload is not None:
                    # Guardar a imagem temporariamente para o FPDF a conseguir ler
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(logo_upload.getvalue())
                        tmp_path = tmp.name
                    pdf.image(tmp_path, x=85, y=10, w=40)
                    pdf.ln(45)
                    os.remove(tmp_path)
                
                pdf.set_font("helvetica", "B", 18)
                pdf.cell(0, 15, "Relatorio de Consultoria Desportiva", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.set_font("helvetica", "I", 14)
                pdf.cell(0, 10, f"Atleta: {cliente_selecionado}", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.ln(10)
                
                pdf.set_font("helvetica", "", 12)
                pdf.cell(0, 10, f"Volume Total: {vol_total:,.0f} kg", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 10, f"Musculo Principal: {musculo_top}", new_x="LMARGIN", new_y="NEXT")
                return bytes(pdf.output())

            st.download_button(label="📄 Exportar Relatório em PDF", data=criar_pdf_personalizado(), file_name=f"Relatorio_{cliente_selecionado}.pdf", mime="application/pdf")
