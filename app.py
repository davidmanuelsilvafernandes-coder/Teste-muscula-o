import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from supabase import create_client, Client

st.set_page_config(layout="wide", page_title="Consultoria Pro", page_icon="📈")

st.markdown("""
    <style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ---------------- SISTEMA DE AUTENTICAÇÃO E REGISTO ----------------
if 'user_email' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>Plataforma de Consultoria B2B</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Gestão de Treino e Acompanhamento Físico</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.divider()
        tab_login, tab_registo = st.tabs(["🔐 Iniciar Sessão", "📝 Criar Conta de Treinador"])
        
        with tab_login:
            email_login = st.text_input("Email", key="l_email")
            pass_login = st.text_input("Palavra-passe", type="password", key="l_pass")
            
            if st.button("Entrar na Plataforma", use_container_width=True, type="primary"):
                try:
                    auth_res = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                    perfil_res = supabase.table("perfis").select("*").eq("email", email_login).execute()
                    
                    if not perfil_res.data:
                        supabase.table("perfis").insert({"email": email_login, "role": "treinador", "nome": "Treinador"}).execute()
                        role = "treinador"
                    else:
                        role = perfil_res.data[0]['role']

                    st.session_state['user_email'] = email_login
                    st.session_state['role'] = role
                    st.rerun()
                except Exception as e:
                    st.error("Erro no login. Verifique os seus dados.")
                    
        with tab_registo:
            nome_reg = st.text_input("Nome Completo", key="r_nome")
            email_reg = st.text_input("Email", key="r_email")
            pass_reg = st.text_input("Palavra-passe (Mínimo 6 caracteres)", type="password", key="r_pass")
            
            if st.button("Registar Nova Conta", use_container_width=True, type="primary"):
                if not nome_reg or not email_reg or not pass_reg:
                    st.warning("Preencha todos os campos.")
                else:
                    try:
                        supabase.auth.sign_up({"email": email_reg, "password": pass_reg})
                        supabase.table("perfis").insert({"email": email_reg, "role": "treinador", "nome": nome_reg}).execute()
                        st.success("✅ Conta criada com sucesso! Vá ao separador 'Iniciar Sessão'.")
                    except Exception as e:
                        st.error(f"Erro ao registar: {e}")
                        
    st.stop()

email_atual = st.session_state['user_email']
role_atual = st.session_state['role']

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2936/2936886.png", width=50)
    st.write(f"**Sessão:** {'Treinador' if role_atual == 'treinador' else 'Atleta'}")
    st.write(f"👤 {email_atual}")
    if st.button("Terminar Sessão"):
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
        clientes_res = supabase.table("perfis").select("*").eq("treinador_email", email_atual).execute()
        checkins_res = supabase.table("checkins").select("*").eq("visto_treinador", False).execute()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Clientes Ativos", len(clientes_res.data) if clientes_res.data else 0)
        col2.metric("Check-ins Pendentes", len(checkins_res.data) if checkins_res.data else 0)
        col3.metric("Novas Avaliações", "0")
        col4.metric("Planos Ativos", "0")

    elif menu == "👥 Gerir Clientes":
        st.title("Gestão de Clientes")
        tab_lista, tab_novo = st.tabs(["Lista de Clientes", "Adicionar Novo Cliente"])
        
        with tab_novo:
            novo_email = st.text_input("Email do Cliente:")
            novo_nome = st.text_input("Nome Completo do Atleta:")
            if st.button("Criar Acesso ao Cliente"):
                supabase.table("perfis").insert({"email": novo_email, "role": "cliente", "nome": novo_nome, "treinador_email": email_atual}).execute()
                st.success(f"Cliente {novo_nome} adicionado com sucesso!")

        with tab_lista:
            clientes_res = supabase.table("perfis").select("*").eq("treinador_email", email_atual).execute()
            df_clientes = pd.DataFrame(clientes_res.data)
            if not df_clientes.empty:
                st.dataframe(df_clientes[['nome', 'email']], use_container_width=True, hide_index=True)
                
                cliente_sel = st.selectbox("Selecionar Atleta para ver Histórico:", df_clientes['email'])
                
                # Ver os registos estilo Hevy enviados pelo atleta
                st.subheader(f"Registo de Treinos de: {cliente_sel}")
                registos_cli = supabase.table("registos_treino").select("*").eq("cliente_email", cliente_sel).execute()
                df_reg = pd.DataFrame(registos_cli.data)
                
                if not df_reg.empty:
                    st.dataframe(df_reg[['data_registo', 'exercicio', 'serie_num', 'peso', 'reps']], use_container_width=True, hide_index=True)
                else:
                    st.info("Este atleta ainda não registou treinos na plataforma.")

    elif menu == "🏋️‍♂️ Construtor de Planos":
        st.title("Construtor de Treino Prescrito")
        st.info("Ferramenta de criação de blocos de treino.")

    elif menu == "📬 Analisar Check-ins":
        st.title("Acompanhamento Periódico")
        checkins = supabase.table("checkins").select("*").eq("visto_treinador", False).execute()
        df_checks = pd.DataFrame(checkins.data)
        
        if not df_checks.empty:
            for index, row in df_checks.iterrows():
                with st.expander(f"📩 Check-in de {row['cliente_email']} ({row['data_checkin']})"):
                    st.write(f"**Peso:** {row['peso_atual']} kg | **Adesão:** {row['adesao_treino']}")
                    st.write(f"**Feedback:** {row['feedback_livre']}")
                    if st.button(f"Marcar como Analisado", key=f"btn_{row['id']}"):
                        supabase.table("checkins").update({"visto_treinador": True}).eq("id", row['id']).execute()
                        st.rerun()
        else:
            st.info("Sem check-ins pendentes.")
            
    elif menu == "📚 Biblioteca Educativa":
        st.title("Biblioteca de Recursos")

# =====================================================================
# ÁREA DO CLIENTE (ESTILO HEVY INTEGRADO)
# =====================================================================
elif role_atual == "cliente":
    menu = st.sidebar.radio("O Meu Perfil:", ["🏋️‍♂️ Registar Treino (Hevy Mode)", "📝 Submeter Check-in"])
    
    if menu == "🏋️‍♂️ Registar Treino (Hevy Mode)":
        st.title("Registo de Treino em Directo")
        st.write("Registe os seus exercícios, cargas e repetições tal como numa aplicação de musculação.")
        
        with st.form("form_registo_treino", clear_on_submit=True):
            data_hoje = str(datetime.now().date())
            st.write(f"**Data da Sessão:** {data_hoje}")
            
            exercicio_nome = st.selectbox("Escolher Exercício:", ["Supino Reto com Barra", "Agachamento Livre", "Puxada Vertical", "Elevação Lateral", "Curl de Bíceps", "Tríceps Corda", "Leg Press"])
            
            col1, col2, col3 = st.columns(3)
            serie_id = col1.number_input("Número da Série", min_value=1, max_value=10, value=1)
            peso_kg = col2.number_input("Carga (kg)", min_value=0.0, max_value=300.0, step=2.5)
            reps_feitas = col3.number_input("Repetições", min_value=0, max_value=100, value=10)
            
            if st.form_submit_button("💾 Registar Série", type="primary"):
                supabase.table("registos_treino").insert({
                    "cliente_email": email_atual,
                    "exercicio": exercicio_nome,
                    "serie_num": int(serie_id),
                    "peso": float(peso_kg),
                    "reps": int(reps_feitas),
                    "data_registo": data_hoje
                }).execute()
                st.success(f"Série guardada com sucesso: {exercicio_nome} - {peso_kg}kg x {reps_feitas} reps!")
                
        # Mostrar o histórico recente do próprio atleta na sessão
        st.subheader("📜 Os seus registos recentes")
        meus_registos = supabase.table("registos_treino").select("*").eq("cliente_email", email_atual).execute()
        df_meus = pd.DataFrame(meus_registos.data)
        if not df_meus.empty:
            st.dataframe(df_meus[['data_registo', 'exercicio', 'serie_num', 'peso', 'reps']], use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não registou nenhum exercício hoje.")
            
    elif menu == "📝 Submeter Check-in":
        st.title("Check-in de Acompanhamento")
        with st.form("form_checkin"):
            peso = st.number_input("Peso Atual (kg)", min_value=30.0, max_value=200.0, value=75.0)
            adesao = st.select_slider("Adesão ao plano:", options=["Muito Má", "Razoável", "Boa", "Perfeita"])
            sono = st.slider("Qualidade do Sono (0-10)", 0, 10, 7)
            feedback = st.text_area("Comentários / Dificuldades:")
            
            if st.form_submit_button("Enviar Check-in", type="primary"):
                supabase.table("checkins").insert({
                    "cliente_email": email_atual,
                    "data_checkin": str(datetime.now().date()),
                    "peso_atual": peso,
                    "adesao_treino": adesao,
                    "recuperacao_sono": sono,
                    "feedback_livre": feedback
                }).execute()
                st.success("Check-in enviado com sucesso!")
