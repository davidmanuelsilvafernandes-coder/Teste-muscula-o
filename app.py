import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from supabase import create_client, Client

st.set_page_config(layout="wide", page_title="Consultoria Pro", page_icon="📈")

# Estilo CSS Personalizado
st.markdown("""
    <style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Ligar à BD
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
                    
                    # Verificar perfil na BD
                    perfil_res = supabase.table("perfis").select("*").eq("email", email_login).execute()
                    
                    if not perfil_res.data:
                        # Criar perfil de segurança caso não exista
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
                    st.warning("Por favor, preencha todos os campos.")
                else:
                    try:
                        # 1. Criar utilizador na Autenticação Supabase
                        auth_res = supabase.auth.sign_up({"email": email_reg, "password": pass_reg})
                        
                        # 2. Registar o perfil correspondente na tabela 'perfis' como treinador
                        supabase.table("perfis").insert({
                            "email": email_reg, 
                            "role": "treinador", 
                            "nome": nome_reg
                        }).execute()
                        
                        st.success("✅ Conta criada com sucesso! Já pode ir ao separador 'Iniciar Sessão' para entrar.")
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
        
        st.subheader("Tarefas Prioritárias")
        if checkins_res.data and len(checkins_res.data) > 0:
            st.warning(f"Tem {len(checkins_res.data)} check-ins de clientes à espera de revisão.")
        else:
            st.success("Toda a consultoria está em dia! Bom trabalho.")

    elif menu == "👥 Gerir Clientes":
        st.title("Gestão de Clientes")
        tab_lista, tab_novo = st.tabs(["Lista de Clientes", "Adicionar Novo Cliente"])
        
        with tab_novo:
            st.subheader("Registar novo atleta na plataforma")
            novo_email = st.text_input("Email do Cliente:")
            novo_nome = st.text_input("Nome Completo do Atleta:")
            if st.button("Criar Acesso ao Cliente"):
                try:
                    supabase.table("perfis").insert({
                        "email": novo_email, 
                        "role": "cliente", 
                        "nome": novo_nome, 
                        "treinador_email": email_atual
                    }).execute()
                    st.success(f"Cliente {novo_nome} adicionado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao adicionar cliente: {e}")

        with tab_lista:
            clientes_res = supabase.table("perfis").select("*").eq("treinador_email", email_atual).execute()
            df_clientes = pd.DataFrame(clientes_res.data)
            if not df_clientes.empty:
                st.dataframe(df_clientes[['nome', 'email']], use_container_width=True, hide_index=True)
                
                st.subheader("Área de Consultoria Individual")
                cliente_sel = st.selectbox("Selecione um cliente para intervir:", df_clientes['email'])
                
                c1, c2, c3 = st.columns(3)
                c1.button("Ver Histórico de Treinos", use_container_width=True)
                c2.button("Ajustar Nutrição", use_container_width=True)
                
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
                    pdf.multi_cell(0, 8, "Evolucao consistente ao longo do periodo avaliado. Bons indices de forca e adesao estavel.")
                    
                    st.download_button("Baixar Relatório PDF", data=bytes(pdf.output()), file_name=f"Relatorio_{cliente_sel}.pdf", mime="application/pdf")
            else:
                st.info("Ainda não tem clientes registados. Adicione o seu primeiro cliente no separador ao lado.")

    elif menu == "🏋️‍♂️ Construtor de Planos":
        st.title("Construtor de Treino Prescrito")
        st.write("Crie blocos de treino estruturados para os seus clientes.")
        
        clientes = pd.DataFrame(supabase.table("perfis").select("email").eq("treinador_email", email_atual).execute().data)
        if not clientes.empty:
            cli_plano = st.selectbox("Para quem é o plano?", clientes['email'])
            nome_plano = st.text_input("Nome da Rotina (ex: Push/Pull/Legs)")
            
            c1, c2, c3, c4 = st.columns(4)
            exercicio = c1.text_input("Exercício")
            series = c2.number_input("Séries", min_value=1, value=3)
            reps = c3.text_input("Reps")
            rir = c4.text_input("RIR/RPE")
            
            if st.button("Guardar Bloco de Treino"):
                st.success(f"Plano atribuído a {cli_plano} com sucesso!")
        else:
            st.info("Adicione clientes na aba de gestão antes de criar planos.")

    elif menu == "📬 Analisar Check-ins":
        st.title("Acompanhamento Periódico")
        checkins = supabase.table("checkins").select("*").eq("visto_treinador", False).execute()
        df_checks = pd.DataFrame(checkins.data)
        
        if not df_checks.empty:
            for index, row in df_checks.iterrows():
                with st.expander(f"📩 Check-in de {row['cliente_email']} ({row['data_checkin']})"):
                    st.write(f"**Peso:** {row['peso_atual']} kg")
                    st.write(f"**Adesão:** {row['adesao_treino']}")
                    st.write(f"**Qualidade do Sono:** {row['recuperacao_sono']}/10")
                    st.write(f"**Feedback:** {row['feedback_livre']}")
                    if st.button(f"Marcar como Analisado", key=f"btn_{row['id']}"):
                        supabase.table("checkins").update({"visto_treinador": True}).eq("id", row['id']).execute()
                        st.rerun()
        else:
            st.info("Não há novos check-ins pendentes.")
            
    elif menu == "📚 Biblioteca Educativa":
        st.title("Biblioteca de Recursos e Guias")
        st.info("Espaço reservado para organizar os seus materiais pedagógicos, vídeos de execução e diretrizes de treino.")

# =====================================================================
# ÁREA DO CLIENTE
# =====================================================================
elif role_atual == "cliente":
    menu = st.sidebar.radio("O Meu Perfil:", ["📅 Treino de Hoje", "📝 Submeter Check-in"])
    
    if menu == "📅 Treino de Hoje":
        st.title("O Meu Plano de Treino")
        st.info("Consulte aqui os exercícios prescritos pelo seu treinador e registe o seu progresso.")
        
        st.markdown("### Treino Ativo - Bloco A")
        with st.container():
            st.markdown("**(1) Supino Reto com Barra** - 3 Séries | 8-10 Reps | RIR 2")
            c1, c2, c3 = st.columns(3)
            c1.number_input("Carga (kg)", key="c1")
            c2.number_input("Reps Feitas", key="r1")
            c3.button("Concluir Série", key="b1")
            
    elif menu == "📝 Submeter Check-in":
        st.title("Check-in de Acompanhamento Periódico")
        st.write("Partilhe os seus dados da semana para o treinador avaliar a evolução.")
        
        with st.form("form_checkin"):
            peso = st.number_input("Peso Atual (kg)", min_value=30.0, max_value=200.0, value=75.0)
            ades
