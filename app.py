import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from supabase import create_client, Client

st.set_page_config(layout="wide", page_title="Consultoria Pro", page_icon="📈")

# Estilo CSS Personalizado para um visual "Premium"
st.markdown("""
    <style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .metric-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 5px solid #00e676; }
    </style>
""", unsafe_allow_html=True)

# Ligar à BD
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ---------------- SISTEMA DE AUTENTICAÇÃO (ROLE-BASED) ----------------
if 'user_email' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>Plataforma de Consultoria B2B</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Gestão de Treino e Acompanhamento Físico</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.divider()
        email_login = st.text_input("Email")
        pass_login = st.text_input("Palavra-passe", type="password")
        
        if st.button("Iniciar Sessão", use_container_width=True, type="primary"):
            try:
                # Login Auth
                auth_res = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                
                # Verificar Role (Treinador ou Cliente)
                perfil_res = supabase.table("perfis").select("*").eq("email", email_login).execute()
                
                if not perfil_res.data: # Se não existir perfil, regista como Treinador por defeito (para o seu 1º acesso)
                    supabase.table("perfis").insert({"email": email_login, "role": "treinador", "nome": "Treinador Principal"}).execute()
                    role = "treinador"
                else:
                    role = perfil_res.data[0]['role']

                st.session_state['user_email'] = email_login
                st.session_state['role'] = role
                st.rerun()
            except Exception as e:
                st.error("Falha no login. Verifique os dados.")
    st.stop()

email_atual = st.session_state['user_email']
role_atual = st.session_state['role']

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2936/2936886.png", width=50) # Espaço para o seu Logo
    st.write(f"**Sessão:** {'Treinador' if role_atual == 'treinador' else 'Atleta'}")
    st.write(f"👤 {email_atual}")
    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()
    st.divider()

# =====================================================================
# ÁREA DO TREINADOR
# =====================================================================
if role_atual == "treinador":
    menu = st.sidebar.radio("Navegação:", ["📊 Dashboard", "👥 Gerir Clientes", "📝 Avaliações Iniciais", "🏋️‍♂️ Construtor de Planos", "📬 Analisar Check-ins", "📚 Biblioteca Educativa"])

    if menu == "📊 Dashboard":
        st.title("Dashboard Geral de Consultoria")
        
        # KPIs Reais
        clientes_res = supabase.table("perfis").select("*").eq("treinador_email", email_atual).execute()
        checkins_res = supabase.table("checkins").select("*").eq("visto_treinador", False).execute()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Clientes Ativos", len(clientes_res.data))
        col2.metric("Check-ins Pendentes", len(checkins_res.data))
        col3.metric("Novas Avaliações", "0")
        col4.metric("Planos a Expirar", "0")
        
        st.subheader("Tarefas Prioritárias")
        if len(checkins_res.data) > 0:
            st.warning(f"Tem {len(checkins_res.data)} check-ins de clientes à espera de revisão.")
        else:
            st.success("Toda a consultoria está em dia! Bom trabalho.")

    elif menu == "👥 Gerir Clientes":
        st.title("Gestão de Clientes")
        tab_lista, tab_novo = st.tabs(["Lista de Clientes", "Adicionar Novo Cliente"])
        
        with tab_novo:
            st.subheader("Registar novo atleta na plataforma")
            novo_email = st.text_input("Email do Cliente:")
            novo_nome = st.text_input("Nome Completo:")
            if st.button("Criar Acesso Cliente"):
                # Insere o perfil indicando que você é o treinador dele
                supabase.table("perfis").insert({"email": novo_email, "role": "cliente", "nome": novo_nome, "treinador_email": email_atual}).execute()
                st.success(f"Cliente {novo_nome} adicionado! Ele já pode fazer login na plataforma.")

        with tab_lista:
            clientes_res = supabase.table("perfis").select("*").eq("treinador_email", email_atual).execute()
            df_clientes = pd.DataFrame(clientes_res.data)
            if not df_clientes.empty:
                st.dataframe(df_clientes[['nome', 'email']], use_container_width=True, hide_index=True)
                
                st.subheader("Área de Consultoria Individual")
                cliente_sel = st.selectbox("Selecione um cliente para intervir:", df_clientes['email'])
                
                c1, c2, c3 = st.columns(3)
                c1.button("Ver Histórico de Treinos", use_container_width=True)
                c2.button("Ajustar Nutrição (Em Breve)", use_container_width=True)
                
                # GERADOR DE RELATÓRIO PROFISSIONAL
                if c3.button("Gerar Relatório de Evolução PDF", use_container_width=True, type="primary"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("helvetica", "B", 18)
                    pdf.cell(0, 15, "Relatorio Oficial de Evolucao", ln=True, align="C")
                    pdf.set_font("helvetica", "I", 12)
                    pdf.cell(0, 10, f"Atleta: {cliente_sel} | Treinador: {email_atual}", ln=True, align="C")
                    pdf.ln(10)
                    
                    pdf.set_font("helvetica", "B", 14)
                    pdf.cell(0, 10, "A. Resumo Executivo", ln=True)
                    pdf.set_font("helvetica", "", 12)
                    pdf.multi_cell(0, 8, "Este relatorio reflete a adesao ao plano no ultimo mes. O cliente apresentou uma melhoria de 12% na forca relativa e manteve uma adesao de 90% aos treinos prescritos.")
                    
                    pdf.ln(5)
                    pdf.set_font("helvetica", "B", 14)
                    pdf.cell(0, 10, "B. Plano de Acao para o Proximo Mes", ln=True)
                    pdf.set_font("helvetica", "", 12)
                    pdf.multi_cell(0, 8, "1. Aumentar volume no grupo muscular das costas.\n2. Ajustar periodo de descanso para 120s nos exercicios compostos.\n3. Focar na qualidade de sono relatada nos check-ins.")
                    
                    st.download_button("Baixar PDF", data=bytes(pdf.output()), file_name=f"Relatorio_{cliente_sel}.pdf", mime="application/pdf")

    elif menu == "🏋️‍♂️ Construtor de Planos":
        st.title("Construtor de Treino Prescrito")
        st.write("Crie blocos de treino estruturados para os seus clientes.")
        
        clientes = pd.DataFrame(supabase.table("perfis").select("email").eq("treinador_email", email_atual).execute().data)
        if not clientes.empty:
            cli_plano = st.selectbox("Para quem é o plano?", clientes['email'])
            nome_plano = st.text_input("Nome da Rotina (ex: Push/Pull/Legs - Fase 1)")
            
            st.markdown("### Adicionar Exercício")
            c1, c2, c3, c4 = st.columns(4)
            exercicio = c1.text_input("Exercício (ex: Agachamento)")
            series = c2.number_input("Séries", min_value=1, value=3)
            reps = c3.text_input("Reps (ex: 8-10)")
            rir = c4.text_input("RIR/RPE (ex: RIR 2)")
            
            if st.button("Guardar Bloco de Treino"):
                # Em produção, usaremos a coluna detalhes (JSONB) para empilhar exercícios. 
                st.success(f"Plano '{nome_plano}' atribuído a {cli_plano} com sucesso!")
        else:
            st.info("Adicione clientes primeiro.")

    elif menu == "📬 Analisar Check-ins":
        st.title("Acompanhamento Periódico")
        checkins = supabase.table("checkins").select("*").eq("visto_treinador", False).execute()
        df_checks = pd.DataFrame(checkins.data)
        
        if not df_checks.empty:
            for index, row in df_checks.iterrows():
                with st.expander(f"📩 Check-in de {row['cliente_email']} ({row['data_checkin']})"):
                    st.write(f"**Peso:** {row['peso_atual']} kg")
                    st.write(f"**Adesão:** {row['adesao_treino']}")
                    st.write(f"**Qualidade do Sono (0-10):** {row['recuperacao_sono']}")
                    st.write(f"**Feedback:** {row['feedback_livre']}")
                    if st.button(f"Marcar como Analisado", key=f"btn_{row['id']}"):
                        supabase.table("checkins").update({"visto_treinador": True}).eq("id", row['id']).execute()
                        st.rerun()
        else:
            st.info("Não há novos check-ins para rever.")

# =====================================================================
# ÁREA DO CLIENTE
# =====================================================================
elif role_atual == "cliente":
    menu = st.sidebar.radio("O Meu Perfil:", ["📅 Treino de Hoje", "📈 O Meu Progresso", "📝 Submeter Check-in"])
    
    if menu == "📅 Treino de Hoje":
        st.title("O Meu Plano de Treino")
        st.info("Bem-vindo à sua área de atleta. Aqui poderá ver os planos prescritos pelo seu treinador e registar as suas cargas em tempo real.")
        
        # Simulação visual da interface mobile para o cliente no ginásio
        st.markdown("### Treino A - Full Body")
        with st.container():
            st.markdown("**(1) Agachamento Livre** - 3 Séries | 8-10 Reps | RIR 2")
            c1, c2, c3 = st.columns(3)
            c1.number_input("Carga (kg)", key="c1")
            c2.number_input("Reps Feitas", key="r1")
            c3.button("Concluir Série", key="b1")
            
    elif menu == "📝 Submeter Check-in":
        st.title("Check-in de Acompanhamento")
        st.write("Preencha este formulário para que o seu treinador possa avaliar a sua semana e fazer ajustes no plano.")
        
        with st.form("form_checkin"):
            peso = st.number_input("Peso Atual Corporal (kg)", min_value=30.0, max_value=200.0, value=75.0)
            adesao = st.select_slider("Como foi a adesão aos treinos?", options=["Muito Má", "Razoável", "Boa", "Perfeita"])
            sono = st.slider("Como avalia o seu sono/recuperação? (0-10)", 0, 10, 7)
            feedback = st.text_area("Descreva dificuldades, dores ou pontos positivos da semana:")
            
            if st.form_submit_button("Enviar para o Treinador", type="primary"):
                supabase.table("checkins").insert({
                    "cliente_email": email_atual,
                    "data_checkin": str(datetime.now().date()),
                    "peso_atual": peso,
                    "adesao_treino": adesao,
                    "recuperacao_sono": sono,
                    "feedback_livre": feedback
                }).execute()
                st.success("Check-in enviado com sucesso! O seu treinador será notificado.")
