import streamlit as st
#import mysql.connector
import pymysql
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.graph_objects as go
import plotly.express as px
import bcrypt


st.set_page_config(page_title="Gestão de Engenharia", layout="wide")

#def get_connection():
#    return mysql.connector.connect(
#        host="localhost",
#        user="root",
#        password="0692",
#        database="gestao_engenharia"
#    )

import ssl

def get_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        port=int(st.secrets["mysql"]["port"]),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        ssl=ssl.create_default_context()
    )

# -------------------------------------------------------------------
# FUNÇÕES DE SEGURANÇA E AUTENTICAÇÃO
# -------------------------------------------------------------------
def gerar_hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    try:
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))
    except Exception:
        return False

def garantir_usuario_admin_inicial():
    """ Cria o utilizador admin automaticamente no banco se a tabela estiver vazia """
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) as total FROM usuarios")
        res = cur.fetchone()
        if res['total'] == 0:
            senha_hash = gerar_hash_senha("admin123")
            cur.execute(
                """
                INSERT INTO usuarios (nome, login, senha, email, setor, area, cargo, perfil)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                ('Administrador', 'admin', senha_hash, 'admin@whbbrasil.com.br', 'Engenharia', 'Engenharia de Processos', 'Administrador de Sistema', 'Admin')
            )
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao verificar/criar admin inicial: {e}")

# Executa a verificação inicial
garantir_usuario_admin_inicial()

def autenticar_usuario(login_input, senha_input):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM usuarios WHERE login = %s", (login_input,))
    usr = cur.fetchone()
    cur.close()
    conn.close()

    if usr and usr.get('senha'):
        if verificar_senha(senha_input, usr['senha']):
            return usr
    return None

# Controle de Sessão de Login
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

def tela_login_e_registro():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Acesso ao Sistema de Engenharia")
        
        tab_entrar, tab_cadastrar = st.tabs(["🔑 Entrar", "📝 Criar Novo Utilizador"])

        # ABA 1: LOGIN
        with tab_entrar:
            with st.form("form_login"):
                login_in = st.text_input("Login / Utilizador")
                senha_in = st.text_input("Senha", type="password")
                btn_entrar = st.form_submit_button("Entrar no Sistema", type="primary")

                if btn_entrar:
                    usr = autenticar_usuario(login_in, senha_in)
                    if usr:
                        st.session_state["usuario_logado"] = usr
                        st.success(f"Bem-vindo(a), {usr['nome']}!")
                        st.rerun()
                    else:
                        st.error("❌ Login ou senha incorretos.")

        # ABA 2: AUTOCADASTRO DE NOVO UTILIZADOR
        with tab_cadastrar:
            with st.form("form_autocadastro"):
                st.markdown("##### Preencha os seus dados para criar o seu acesso:")
                novo_nome = st.text_input("Nome Completo")
                novo_login = st.text_input("Login Desejado")
                nova_senha = st.text_input("Senha", type="password")
                novo_email = st.text_input("E-mail Empresarial")
                novo_setor = st.selectbox("Setor Principal", ["Engenharia", "Produção", "Qualidade", "Manutenção", "Outro"])
                nova_area = st.text_input("Área / Sub-setor (ex: Processos, Usinagem)")
                novo_cargo = st.text_input("Cargo (ex: Analista, Operador, Engenheiro)")
                
                btn_cadastrar = st.form_submit_button("Criar a Minha Conta", type="primary")

                if btn_cadastrar:
                    if not novo_nome or not novo_login or not nova_senha or not novo_email:
                        st.error("Por favor, preencha todos os campos obrigatórios (Nome, Login, Senha e E-mail).")
                    else:
                        try:
                            senha_hash = gerar_hash_senha(nova_senha)
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO usuarios (nome, login, senha, email, setor, area, cargo, perfil)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Operador')
                                """,
                                (novo_nome, novo_login, senha_hash, novo_email, novo_setor, nova_area, novo_cargo)
                            )
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success("✅ Conta criada com sucesso! Agora pode aceder na aba 'Entrar'.")
                        except mysql.connector.Error as err:
                            if err.errno == 1062:
                                st.error("❌ O login informado já está em uso. Por favor, escolha outro.")
                            else:
                                st.error(f"Erro ao cadastrar utilizador: {err}")

# Bloqueia a aplicação até o utilizador fazer login
if not st.session_state["usuario_logado"]:
    tela_login_e_registro()
    st.stop()

# Dados do Utilizador Ativo
usr_ativo = st.session_state["usuario_logado"]
usuario_ativo_id = usr_ativo["id"]
usuario_ativo_nome = usr_ativo["nome"]
usuario_ativo_setor = usr_ativo["setor"]
perfil_ativo = usr_ativo["perfil"]
es_admin = (perfil_ativo == "Admin")

# Barra Lateral - Utilizador e Logout
st.sidebar.markdown(f"### 👤 {usuario_ativo_nome}")
st.sidebar.caption(f"**Perfil:** {perfil_ativo} | **Setor:** {usuario_ativo_setor}")
if st.sidebar.button("🚪 Sair / Logout"):
    st.session_state["usuario_logado"] = None
    st.rerun()

st.sidebar.markdown("---")

# -------------------------------------------------------------------
# FUNÇÕES DE ENVIO DE E-MAIL AUTOMÁTICO
# -------------------------------------------------------------------
def enviar_email_generico(destinatarios, assunto, corpo_html):
    SMTP_SERVER = "smtp.office365.com"
    SMTP_PORT = 587
    REMETENTE_EMAIL = "DOCUMENTAOUSI@whbbrasil.com.br"
    REMETENTE_SENHA = "SUA_SENHA_CORRETA_AQUI"

    if not destinatarios:
        return False

    msg = MIMEMultipart()
    msg['From'] = REMETENTE_EMAIL
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(REMETENTE_EMAIL, REMETENTE_SENHA)
        server.sendmail(REMETENTE_EMAIL, destinatarios, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

def enviar_email_notificacao(destinatarios, codigo_solicitacao, linha, num_doc, tipo_acao, solicitante, itens_solicitados):
    if not destinatarios: return
    linhas_itens_html = "".join([f"<tr><td style='text-align: center;'><b>{i+1}</b></td><td>{item['descricao']}</td></tr>" for i, item in enumerate(itens_solicitados)])
    assunto = f"[Engenharia] Nova Solicitação de Revisão na Fila - {codigo_solicitacao}"
    corpo_html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #0056b3;">⚙️ Nova Solicitação de Revisão Documental</h2>
        <p>Nova solicitação disponível na <b>Fila de Trabalho</b> para aceite.</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;"><td><b>Código:</b></td><td>{codigo_solicitacao}</td></tr>
            <tr><td><b>Linha:</b></td><td>{linha}</td></tr>
            <tr style="background-color: #f2f2f2;"><td><b>Nº Doc:</b></td><td>{num_doc}</td></tr>
            <tr><td><b>Solicitante:</b></td><td>{solicitante}</td></tr>
        </table>
        <h3>📋 Ações Requeridas:</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">{linhas_itens_html}</table>
    </body></html>"""
    enviar_email_generico(destinatarios, assunto, corpo_html)

def enviar_email_acao_indicador(destinatarios, codigo_ind, indicador, linha_ou_fabrica, periodo, valor, meta, unidade, setores_cobrados, solicitante):
    if not destinatarios: return
    setores_txt = ", ".join(setores_cobrados)
    assunto = f"[Indicadores] Ação Requerida - {indicador} | {linha_ou_fabrica} ({periodo})"
    corpo_html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #d9534f;">📊 Ação de Melhoria de Indicador Requerida</h2>
        <p>Um novo indicador foi registrado e requer plano de ação para os setores convocados.</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;"><td><b>Código:</b></td><td>{codigo_ind}</td></tr>
            <tr><td><b>Indicador:</b></td><td>{indicador}</td></tr>
            <tr style="background-color: #f2f2f2;"><td><b>Resultado vs Meta:</b></td><td><b>{valor} {unidade}</b> (Meta: {meta} {unidade})</td></tr>
            <tr><td><b>Setores Convocados:</b></td><td><b>{setores_txt}</b></td></tr>
        </table>
    </body></html>"""
    enviar_email_generico(destinatarios, assunto, corpo_html)

def enviar_email_conclusao(destinatarios, codigo_solicitacao, linha, num_doc, descricao, comentario_solucao, executor):
    if not destinatarios: return
    assunto = f"[Engenharia] Ação CONCLUÍDA - {codigo_solicitacao}"
    corpo_html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #28a745;">✅ Ação Concluída com Sucesso</h2>
        <p>Ação finalizada no sistema por {executor}.</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr><td><b>Código:</b></td><td>{codigo_solicitacao}</td></tr>
            <tr><td><b>Linha:</b></td><td>{linha}</td></tr>
            <tr><td><b>Descrição:</b></td><td>{descricao}</td></tr>
            <tr><td><b>Solução:</b></td><td>{comentario_solucao}</td></tr>
        </table>
    </body></html>"""
    enviar_email_generico(destinatarios, assunto, corpo_html)

st.title("⚙️ Sistema de Gestão de Engenharia")

# -------------------------------------------------------------------
# VERIFICAÇÃO VISUAL DE ALERTA NO SISTEMA AO LOGAR
# -------------------------------------------------------------------
conn = get_connection()
cur_chk = conn.cursor(dictionary=True)

semana_atual_str = f"Semana {datetime.now().isocalendar()[1]:02d}"
ano_atual = datetime.now().year

cur_chk.execute("""
    SELECT ic.nome_indicador
    FROM indicadores_cadastro ic
    WHERE ic.periodicidade = 'Semanal' AND ic.setor_responsavel = %s
    AND ic.id NOT IN (
        SELECT DISTINCT ic_sub.id 
        FROM indicadores_cadastro ic_sub
        JOIN tipos_acao ta ON ic_sub.nome_indicador = ta.nome
        JOIN indicadores_registros ir ON ir.tipo_acao_id = ta.id
        WHERE ir.periodo_referencia = %s AND ir.ano = %s
    )
""", (usuario_ativo_setor, semana_atual_str, ano_atual))
ind_pendentes_usuario = cur_chk.fetchall()

cur_chk.execute("""
    SELECT COUNT(*) AS total
    FROM indicador_acoes
    WHERE setor_responsavel = %s AND status IN ('Pendente', 'Em Andamento')
""", (usuario_ativo_setor,))
total_acoes_pendentes_usr = cur_chk.fetchone()['total']

cur_chk.close()
conn.close()

if ind_pendentes_usuario or total_acoes_pendentes_usr > 0:
    st.error(f"🚨 **ALERTAS DE OBRIGATORIEDADE PARA O SEU SETOR ({usuario_ativo_setor.upper()}):**")
    if ind_pendentes_usuario:
        nomes_ind_p = ", ".join([i['nome_indicador'] for i in ind_pendentes_usuario])
        st.warning(f"⚠️ **Indicadores Semanais sem preenchimento na {semana_atual_str}:** {nomes_ind_p}. Vá até a aba '6. Atualização de Indicadores'.")
    if total_acoes_pendentes_usr > 0:
        st.warning(f"⚠️ **Ações Pendentes sem Resposta:** Possui **{total_acoes_pendentes_usr}** plano(s) de ação pendente(s) na aba '8. Plano de Ação - Indicadores'.")

st.sidebar.markdown("---")

opcao = st.sidebar.selectbox(
    "Navegação",
    [
        "1. Usuários", 
        "2. Linhas & Responsáveis", 
        "3. Tipos de Ação", 
        "4. Nova Solicit. (Revisão)",
        "5. Plano de Ação - Revisões",
        "6. Atualização de Indicadores",
        "7. Parametrização de Indicadores",
        "8. Plano de Ação - Indicadores",
        "9. Relatório Geral de Ações"
    ]
)

# -------------------------------------------------------------------
# TELA 1: CADASTRO E GESTÃO COMPLETA DE USUÁRIOS
# -------------------------------------------------------------------
if opcao == "1. Usuários":
    st.header("👤 Gestão de Colaboradores & Utilizadores")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("➕ Criar Utilizador (Admin)")
        if es_admin:
            with st.form("form_usuario", clear_on_submit=True):
                nome = st.text_input("Nome Completo")
                login = st.text_input("Login de Acesso")
                senha = st.text_input("Senha", type="password")
                email = st.text_input("E-mail")
                setor = st.selectbox("Setor Principal", ["Engenharia", "Produção", "Qualidade", "Manutenção", "Outro"])
                area = st.text_input("Área / Sub-setor")
                cargo = st.text_input("Cargo")
                perfil = st.selectbox("Perfil de Acesso", ["Operador", "Admin"])
                
                btn_usr = st.form_submit_button("Salvar Utilizador", type="primary")

                if btn_usr:
                    if not nome or not login or not senha:
                        st.error("Preencha os campos obrigatórios: Nome, Login e Senha.")
                    else:
                        try:
                            senha_hash = gerar_hash_senha(senha)
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO usuarios (nome, login, senha, email, setor, area, cargo, perfil)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (nome, login, senha_hash, email, setor, area, cargo, perfil)
                            )
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"Utilizador '{nome}' cadastrado!")
                            st.rerun()
                        except mysql.connector.Error as err:
                            if err.errno == 1062:
                                st.error("❌ O login informado já está em uso por outro utilizador.")
                            else:
                                st.error(f"Erro ao salvar: {err}")
        else:
            st.info("🔒 Apenas Administradores podem criar utilizadores nesta aba.")

    with col2:
        st.subheader("📋 Utilizadores Registados")
        conn = get_connection()
        df_usr = pd.read_sql("SELECT id, nome AS Nome, login AS Login, email AS Email, setor AS Setor, area AS Area, cargo AS Cargo, perfil AS Perfil FROM usuarios", conn)
        conn.close()

        if es_admin:
            df_editado = st.data_editor(df_usr, num_rows="dynamic", key="editor_usuarios", disabled=["id"])
            if st.button("💾 Salvar Alterações na Tabela"):
                conn = get_connection()
                cursor = conn.cursor()
                for idx, row in df_editado.iterrows():
                    cursor.execute(
                        """
                        UPDATE usuarios 
                        SET nome = %s, login = %s, email = %s, setor = %s, area = %s, cargo = %s, perfil = %s 
                        WHERE id = %s
                        """,
                        (row["Nome"], row["Login"], row["Email"], row["Setor"], row["Area"], row["Cargo"], row["Perfil"], row["id"])
                    )
                conn.commit()
                cursor.close()
                conn.close()
                st.success("Dados atualizados!")
                st.rerun()
        else:
            st.dataframe(df_usr, use_container_width=True)

# -------------------------------------------------------------------
# TELA 2: LINHAS E ASSOCIAÇÃO DE RESPONSÁVEIS
# -------------------------------------------------------------------
elif opcao == "2. Linhas & Responsáveis":
    st.header("📍 Gestão de Linhas de Produção e Equipe")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("1. Cadastrar Linha")
        if es_admin:
            with st.form("form_linha", clear_on_submit=True):
                nome_linha = st.text_input("Nome da Linha")
                codigo_linha = st.text_input("Código da Linha")
                btn_linha = st.form_submit_button("Cadastrar Linha")

                if btn_linha and nome_linha:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO linhas (nome, codigo) VALUES (%s, %s)", (nome_linha, codigo_linha))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"Linha '{nome_linha}' cadastrada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")
        else:
            st.info("🔒 Apenas Administradores podem cadastrar novas linhas.")

    with col2:
        st.subheader("Linhas Cadastradas")
        conn = get_connection()
        df_linhas = pd.read_sql("SELECT id, nome AS 'Nome da Linha', codigo AS 'Código' FROM linhas", conn)
        conn.close()

        if es_admin:
            df_linhas_edit = st.data_editor(df_linhas, num_rows="dynamic", key="editor_linhas")
            if st.button("Salvar Alterações nas Linhas"):
                conn = get_connection()
                cursor = conn.cursor()
                for idx, row in df_linhas_edit.iterrows():
                    cursor.execute(
                        "UPDATE linhas SET nome = %s, codigo = %s WHERE id = %s",
                        (row["Nome da Linha"], row["Código"], row["id"])
                    )
                conn.commit()
                cursor.close()
                conn.close()
                st.success("Linhas atualizadas!")
                st.rerun()
        else:
            st.dataframe(df_linhas, use_container_width=True)

    st.markdown("---")
    st.subheader("2. Associar Responsáveis por Área")

    conn = get_connection()
    df_linhas_raw = pd.read_sql("SELECT id, nome FROM linhas", conn)
    df_usuarios_raw = pd.read_sql("SELECT id, nome FROM usuarios", conn)
    conn.close()

    if df_linhas_raw.empty:
        st.info("Cadastre pelo menos uma linha primeiro.")
    elif df_usuarios_raw.empty:
        st.warning("Nenhum utilizador cadastrado.")
    else:
        lista_usuarios = ["-- Selecionar --"] + df_usuarios_raw["nome"].tolist()

        if es_admin:
            with st.form("form_responsaveis_linha"):
                linha_selecionada = st.selectbox("Selecione a Linha de Produção", df_linhas_raw["nome"].tolist())
                col_a, col_b = st.columns(2)
                with col_a:
                    resp_eng = st.selectbox("Engenharia", lista_usuarios, key="eng")
                    resp_prod = st.selectbox("Produção", lista_usuarios, key="prod")
                with col_b:
                    resp_qual = st.selectbox("Qualidade", lista_usuarios, key="qual")
                    resp_man = st.selectbox("Manutenção", lista_usuarios, key="man")

                btn_salvar_resp = st.form_submit_button("Atualizar Equipe da Linha")

                if btn_salvar_resp:
                    linha_id = int(df_linhas_raw[df_linhas_raw["nome"] == linha_selecionada]["id"].values[0])
                    mapeamento = [("Engenharia", resp_eng), ("Produção", resp_prod), ("Qualidade", resp_qual), ("Manutenção", resp_man)]

                    conn = get_connection()
                    cursor = conn.cursor()
                    for papel, nome_resp in mapeamento:
                        if nome_resp != "-- Selecionar --":
                            usr_id = int(df_usuarios_raw[df_usuarios_raw["nome"] == nome_resp]["id"].values[0])
                            cursor.execute("SELECT id FROM linha_responsaveis WHERE linha_id = %s AND papel = %s", (linha_id, papel))
                            existente = cursor.fetchone()
                            if existente:
                                cursor.execute("UPDATE linha_responsaveis SET usuario_id = %s WHERE id = %s", (usr_id, existente[0]))
                            else:
                                cursor.execute("INSERT INTO linha_responsaveis (linha_id, usuario_id, papel) VALUES (%s, %s, %s)", (linha_id, usr_id, papel))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"Equipe da linha '{linha_selecionada}' atualizada!")
                    st.rerun()

        st.markdown("### Resumo de Responsáveis por Linha")
        conn = get_connection()
        query_resumo = """
            SELECT l.nome AS Linha, lr.papel AS Setor, u.nome AS Responsavel
            FROM linha_responsaveis lr
            JOIN linhas l ON lr.linha_id = l.id
            JOIN usuarios u ON lr.usuario_id = u.id
            ORDER BY l.nome, lr.papel
        """
        df_resumo = pd.read_sql(query_resumo, conn)
        conn.close()
        st.dataframe(df_resumo, use_container_width=True)

# -------------------------------------------------------------------
# TELA 3: CADASTRO DE TIPOS DE AÇÃO
# -------------------------------------------------------------------
elif opcao == "3. Tipos de Ação":
    st.header("📋 Gestão de Tipos de Ação")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Nova Ação")
        if es_admin:
            with st.form("form_acao", clear_on_submit=True):
                nome_acao = st.text_input("Nome da Ação (ex: FMEA, OEE)")
                intervencao = st.selectbox("Tipo de Intervenção", ["Revisar", "Atualizar"])
                
                conn = get_connection()
                df_usuarios = pd.read_sql("SELECT id, nome FROM usuarios", conn)
                conn.close()

                lista_resp = ["Nenhum"] + df_usuarios["nome"].tolist() if not df_usuarios.empty else ["Nenhum"]
                resp_padrao = st.selectbox("Responsável Padrão", lista_resp)
                btn_acao = st.form_submit_button("Cadastrar Ação")

                if btn_acao and nome_acao:
                    resp_id = int(df_usuarios[df_usuarios["nome"] == resp_padrao]["id"].values[0]) if resp_padrao != "Nenhum" else None
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO tipos_acao (nome, tipo_intervencao, responsavel_padrao_id) VALUES (%s, %s, %s)", (nome_acao, intervencao, resp_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"Ação '{nome_acao}' cadastrada!")
                    st.rerun()
        else:
            st.info("🔒 Apenas Administradores podem cadastrar novas ações.")

    with col2:
        st.subheader("Ações Registradas")
        conn = get_connection()
        query = """
            SELECT a.id, a.nome AS Acao, a.tipo_intervencao AS Intervencao, u.nome AS Responsavel_Padrao 
            FROM tipos_acao a 
            LEFT JOIN usuarios u ON a.responsavel_padrao_id = u.id
        """
        df_acoes = pd.read_sql(query, conn)
        conn.close()

        if es_admin:
            df_acoes_edit = st.data_editor(df_acoes, num_rows="dynamic", key="editor_acoes")
            if st.button("Salvar Alterações nas Ações"):
                conn = get_connection()
                cursor = conn.cursor()
                for idx, row in df_acoes_edit.iterrows():
                    cursor.execute("UPDATE tipos_acao SET nome = %s, tipo_intervencao = %s WHERE id = %s", (row["Acao"], row["Intervencao"], row["id"]))
                conn.commit()
                cursor.close()
                conn.close()
                st.success("Ações atualizadas!")
                st.rerun()
        else:
            st.dataframe(df_acoes, use_container_width=True)

# -------------------------------------------------------------------
# TELA 4: SOLICITAÇÃO DE REVISÃO DOCUMENTAL
# -------------------------------------------------------------------
elif opcao == "4. Nova Solicit. (Revisão)":
    st.header("📄 Solicitação de Revisão Documental")

    conn = get_connection()
    df_linhas = pd.read_sql("SELECT id, nome FROM linhas", conn)
    df_acoes_rev = pd.read_sql("SELECT id, nome FROM tipos_acao WHERE tipo_intervencao = 'Revisar'", conn)
    df_usuarios = pd.read_sql("SELECT id, nome, email FROM usuarios", conn)
    conn.close()

    if df_linhas.empty or df_acoes_rev.empty or df_usuarios.empty:
        st.warning("É necessário ter Linhas, Utilizadores e Tipos de Ação do tipo 'Revisar' cadastrados.")
    else:
        st.subheader("1. Dados do Documento")
        c1, c2, c3 = st.columns(3)
        with c1:
            linha_sel = st.selectbox("Linha de Produção", df_linhas["nome"].tolist())
            num_doc = st.text_input("Nº do Documento")
        with c2:
            tipo_rev_sel = st.selectbox("Tipo de Revisão (Documento)", df_acoes_rev["nome"].tolist())
            elaborador_sel = st.selectbox("Elaborador", ["-- Selecionar --"] + df_usuarios["nome"].tolist())
        with c3:
            revisor_sel = st.selectbox("Revisor", ["-- Selecionar --"] + df_usuarios["nome"].tolist())
            aprovador_sel = st.selectbox("Aprovador", ["-- Selecionar --"] + df_usuarios["nome"].tolist())

        st.markdown("---")
        st.subheader("2. Itens / Ações da Solicitação")

        if "itens_solicitacao" not in st.session_state:
            st.session_state["itens_solicitacao"] = []

        with st.form("form_adicionar_item", clear_on_submit=True):
            st.markdown("**Adicionar Solicitação/Alteração para este documento:**")
            desc_item = st.text_area("Descrição detalhada da alteração requerida")
            anexo_item = st.file_uploader("Anexo (Opcional)", type=["pdf", "png", "jpg", "jpeg", "xlsx", "docx"])
            btn_add_item = st.form_submit_button("➕ Adicionar esta ação à lista")

            if btn_add_item and desc_item:
                anexo_bytes = anexo_item.read() if anexo_item else None
                anexo_nome = anexo_item.name if anexo_item else None
                
                st.session_state["itens_solicitacao"].append({
                    "descricao": desc_item,
                    "nome_anexo": anexo_nome,
                    "bytes_anexo": anexo_bytes
                })
                st.success("Ação adicionada à lista!")

        if st.session_state["itens_solicitacao"]:
            st.markdown("#### Lista de Ações a Enviar:")
            for idx, item in enumerate(st.session_state["itens_solicitacao"]):
                anexo_txt = f"📎 Anexo: {item['nome_anexo']}" if item['nome_anexo'] else "Sem anexo"
                st.info(f"**Ação {idx+1}:** {item['descricao']} | *{anexo_txt}*")

            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                if st.button("Limpar Ações"):
                    st.session_state["itens_solicitacao"] = []
                    st.rerun()

            st.markdown("---")
            if st.button("🚀 Finalizar e Enviar Solicitação", type="primary"):
                if not num_doc or elaborador_sel == "-- Selecionar --" or revisor_sel == "-- Selecionar --" or aprovador_sel == "-- Selecionar --":
                    st.error("Por favor, preencha todos os campos obrigatórios.")
                else:
                    try:
                        linha_id = int(df_linhas[df_linhas["nome"] == linha_sel]["id"].values[0])
                        tipo_acao_id = int(df_acoes_rev[df_acoes_rev["nome"] == tipo_rev_sel]["id"].values[0])
                        elab_id = int(df_usuarios[df_usuarios["nome"] == elaborador_sel]["id"].values[0])
                        rev_id = int(df_usuarios[df_usuarios["nome"] == revisor_sel]["id"].values[0])
                        aprov_id = int(df_usuarios[df_usuarios["nome"] == aprovador_sel]["id"].values[0])
                        
                        codigo_gerado = f"REV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

                        conn = get_connection()
                        cursor = conn.cursor()

                        cursor.execute(
                            """
                            INSERT INTO solicitacoes_revisao 
                            (codigo_solicitacao, linha_id, tipo_acao_id, numero_documento, elaborador_id, revisor_id, aprovador_id, solicitante_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (codigo_gerado, linha_id, tipo_acao_id, num_doc, elab_id, rev_id, aprov_id, usuario_ativo_id)
                        )
                        solicitacao_id = cursor.lastrowid

                        for item in st.session_state["itens_solicitacao"]:
                            cursor.execute(
                                """
                                INSERT INTO solicitacao_revisao_itens (solicitacao_id, descricao_solicitacao, nome_anexo, arquivo_anexo)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (solicitacao_id, item["descricao"], item["nome_anexo"], item["bytes_anexo"])
                            )

                        conn.commit()
                        cursor.close()
                        conn.close()

                        emails_destino = [
                            df_usuarios[df_usuarios["nome"] == elaborador_sel]["email"].values[0],
                            df_usuarios[df_usuarios["nome"] == revisor_sel]["email"].values[0],
                            df_usuarios[df_usuarios["nome"] == aprovador_sel]["email"].values[0]
                        ]
                        emails_validos = list(set([email for email in emails_destino if email and "@" in email]))

                        enviar_email_notificacao(
                            destinatarios=emails_validos,
                            codigo_solicitacao=codigo_gerado,
                            linha=linha_sel,
                            num_doc=num_doc,
                            tipo_acao=tipo_rev_sel,
                            solicitante=usuario_ativo_nome,
                            itens_solicitados=st.session_state["itens_solicitacao"]
                        )

                        st.session_state["itens_solicitacao"] = []
                        st.success(f"Solicitação {codigo_gerado} enviada para a fila de revisões!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao guardar solicitação: {e}")

# -------------------------------------------------------------------
# TELA 5: FILA DE REVISÕES E INDICADORES DE LEAD TIME
# -------------------------------------------------------------------
elif opcao == "5. Plano de Ação - Revisões":
    st.header("📄 Fila de Revisões & Indicadores de Lead Time")

    tab_fila, tab_kpi = st.tabs(["📋 Fila de Trabalho & Atendimento", "📊 Indicadores de Lead Time & Performance"])

    with tab_kpi:
        st.subheader("⏱️ Indicadores de Tempo de Resposta e Lead Time")

        conn = get_connection()
        query_lead = """
            SELECT 
                sr.codigo_solicitacao,
                l.nome AS linha,
                ta.nome AS tipo_acao,
                sr.data_abertura,
                i.data_aceite,
                i.data_conclusao,
                i.status,
                u_aceite.nome AS responsavel_aceite
            FROM solicitacao_revisao_itens i
            JOIN solicitacoes_revisao sr ON i.solicitacao_id = sr.id
            JOIN linhas l ON sr.linha_id = l.id
            JOIN tipos_acao ta ON sr.tipo_acao_id = ta.id
            LEFT JOIN usuarios u_aceite ON i.usuario_aceite_id = u_aceite.id
        """
        df_lead = pd.read_sql(query_lead, conn)
        conn.close()

        if df_lead.empty:
            st.info("Nenhuma solicitação registrada para geração de métricas.")
        else:
            df_lead['data_abertura'] = pd.to_datetime(df_lead['data_abertura'])
            df_lead['data_aceite'] = pd.to_datetime(df_lead['data_aceite'])
            df_lead['data_conclusao'] = pd.to_datetime(df_lead['data_conclusao'])

            df_lead['tempo_espera_horas'] = (df_lead['data_aceite'] - df_lead['data_abertura']).dt.total_seconds() / 3600
            df_lead['tempo_execucao_horas'] = (df_lead['data_conclusao'] - df_lead['data_aceite']).dt.total_seconds() / 3600
            df_lead['lead_time_total_horas'] = (df_lead['data_conclusao'] - df_lead['data_abertura']).dt.total_seconds() / 3600

            df_concluidas = df_lead[df_lead['status'] == 'Concluído']

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Solicitado", len(df_lead))
            k2.metric("Revisões Atendidas", len(df_concluidas))
            
            med_espera = round(df_lead['tempo_espera_horas'].mean(), 1) if not df_lead['tempo_espera_horas'].dropna().empty else 0
            med_total = round(df_concluidas['lead_time_total_horas'].mean(), 1) if not df_concluidas['lead_time_total_horas'].dropna().empty else 0

            k3.metric("Tempo Média até Aceite", f"{med_espera} h")
            k4.metric("Lead Time Média Total", f"{med_total} h")

            st.markdown("---")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("#### Lead Time Média por Tipo de Revisão (Horas)")
                if not df_concluidas.empty:
                    df_grp_tipo = df_concluidas.groupby("tipo_acao")[['tempo_espera_horas', 'tempo_execucao_horas']].mean().reset_index()
                    fig_bar = px.bar(
                        df_grp_tipo, 
                        x='tipo_acao', 
                        y=['tempo_espera_horas', 'tempo_execucao_horas'],
                        labels={'value': 'Horas', 'variable': 'Etapa'},
                        title="Espera (Fila) vs Execução por Documento",
                        barmode='stack'
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.caption("Sem revisões concluídas para exibir o gráfico.")

            with col_g2:
                st.markdown("#### Distribuição de Status das Revisões")
                fig_pie = px.pie(df_lead, names='status', title='Status Atual da Fila', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

    with tab_fila:
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            filter_status = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Em Andamento", "Concluído"], key="f_rev_st")
        with col_f2:
            modo_visao = st.radio("Modo de Visão", ["Cards / Galeria Visual 🖼️", "Lista Detalhada 📋"], horizontal=True, key="f_rev_v")

        conn = get_connection()
        
        query = """
            SELECT 
                sr.codigo_solicitacao AS codigo,
                sr.numero_documento AS num_doc,
                l.nome AS linha,
                ta.nome AS tipo_acao,
                u_elab.nome AS elaborador,
                u_aceite.nome AS usuario_aceite,
                sr.data_abertura,
                i.data_aceite,
                i.data_conclusao,
                i.id AS item_id,
                i.descricao_solicitacao AS descricao,
                i.status AS status_item,
                i.nome_anexo,
                i.arquivo_anexo,
                i.comentario_solucao,
                i.nome_evidencia,
                i.arquivo_evidencia
            FROM solicitacoes_revisao sr
            JOIN linhas l ON sr.linha_id = l.id
            JOIN tipos_acao ta ON sr.tipo_acao_id = ta.id
            LEFT JOIN usuarios u_elab ON sr.elaborador_id = u_elab.id
            JOIN solicitacao_revisao_itens i ON sr.id = i.solicitacao_id
            LEFT JOIN usuarios u_aceite ON i.usuario_aceite_id = u_aceite.id
        """
        if filter_status != "Todos":
            query += f" WHERE i.status = '{filter_status}'"
        query += " ORDER BY sr.data_abertura DESC, i.id ASC"
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        itens = cursor.fetchall()
        cursor.close()
        conn.close()

        if not itens:
            st.info("Nenhuma solicitação de revisão documental encontrada.")
        else:
            if modo_visao == "Cards / Galeria Visual 🖼️":
                cols = st.columns(3)
                for idx, item in enumerate(itens):
                    col_atual = cols[idx % 3]
                    with col_atual:
                        cor_status = "🔴" if item['status_item'] == 'Pendente' else ("🟡" if item['status_item'] == 'Em Andamento' else "🟢")
                        
                        with st.container(border=True):
                            st.markdown(f"### {cor_status} {item['codigo']}")
                            st.caption(f"**Linha:** {item['linha']} | **Doc:** {item['num_doc']}")
                            st.write(f"**Tipo:** {item['tipo_acao']}")
                            st.write(f"**Abertura:** {item['data_abertura'].strftime('%d/%m/%Y %H:%M') if item['data_abertura'] else '-'}")
                            
                            if item['usuario_aceite']:
                                st.caption(f"👤 **Pego por:** {item['usuario_aceite']} em {item['data_aceite'].strftime('%d/%m %H:%M') if item['data_aceite'] else ''}")
                            else:
                                st.warning("⏳ Na fila aguardando responsável")

                            st.write(f"**Solicitação:** {item['descricao']}")
                            
                            if item.get('arquivo_anexo') and item.get('nome_anexo'):
                                st.download_button(
                                    label=f"📥 Anexo ({item['nome_anexo']})",
                                    data=item['arquivo_anexo'],
                                    file_name=item['nome_anexo'],
                                    key=f"dl_anexo_rev_{item['item_id']}"
                                )
                            
                            if item['comentario_solucao']:
                                st.info(f"**Solução:** {item['comentario_solucao']}")

                            pode_responder = es_admin or (usuario_ativo_setor.lower() == "engenharia")

                            if pode_responder:
                                if item['status_item'] == 'Pendente' and not item['data_aceite']:
                                    if st.button("✋ Aceitar / Pegar esta Revisão", key=f"btn_aceitar_{item['item_id']}", type="primary"):
                                        conn = get_connection()
                                        cur = conn.cursor()
                                        cur.execute(
                                            "UPDATE solicitacao_revisao_itens SET status='Em Andamento', data_aceite=NOW(), usuario_aceite_id=%s WHERE id=%s",
                                            (usuario_ativo_id, item['item_id'])
                                        )
                                        conn.commit()
                                        cur.close()
                                        conn.close()
                                        st.success("Ação aceita com sucesso e iniciada!")
                                        st.rerun()

                                else:
                                    with st.popover("⚙️ Finalizar / Registrar Solução"):
                                        with st.form(key=f"card_form_rev_{item['item_id']}"):
                                            novo_status = st.selectbox(
                                                "Status", ["Em Andamento", "Concluído"],
                                                index=1 if item["status_item"] == "Concluído" else 0
                                            )
                                            comentario = st.text_area("Descreva a alteração realizada", value=item["comentario_solucao"] or "")
                                            evid_file = st.file_uploader("Anexar Documento Atualizado", type=["png", "jpg", "jpeg", "pdf", "xlsx", "docx"], key=f"up_rev_{item['item_id']}")
                                            
                                            if st.form_submit_button("Salvar Resolução"):
                                                conn = get_connection()
                                                cur = conn.cursor()
                                                evid_bytes = evid_file.read() if evid_file else None
                                                evid_nome = evid_file.name if evid_file else item["nome_evidencia"]

                                                query_up = """
                                                    UPDATE solicitacao_revisao_itens 
                                                    SET status=%s, comentario_solucao=%s, responsavel_execucao_id=%s, 
                                                        data_conclusao = IF(%s = 'Concluído', NOW(), data_conclusao)
                                                """
                                                params = [novo_status, comentario, usuario_ativo_id, novo_status]

                                                if evid_bytes:
                                                    query_up += ", nome_evidencia=%s, arquivo_evidencia=%s"
                                                    params.extend([evid_nome, evid_bytes])

                                                query_up += " WHERE id=%s"
                                                params.append(item['item_id'])

                                                cur.execute(query_up, params)
                                                conn.commit()

                                                if novo_status == "Concluído":
                                                    query_emails = """
                                                        SELECT u_elab.email AS elab, u_rev.email AS rev, u_aprov.email AS aprov, u_solic.email AS solic
                                                        FROM solicitacao_revisao_itens i
                                                        JOIN solicitacoes_revisao sr ON i.solicitacao_id = sr.id
                                                        LEFT JOIN usuarios u_elab ON sr.elaborador_id = u_elab.id
                                                        LEFT JOIN usuarios u_rev ON sr.revisor_id = u_rev.id
                                                        LEFT JOIN usuarios u_aprov ON sr.aprovador_id = u_aprov.id
                                                        LEFT JOIN usuarios u_solic ON sr.solicitante_id = u_solic.id
                                                        WHERE i.id = %s
                                                    """
                                                    cur.execute(query_emails, (item['item_id'],))
                                                    row_em = cur.fetchone()
                                                    emails_dest = [e for e in row_em if e and "@" in e] if row_em else []

                                                    enviar_email_conclusao(
                                                        destinatarios=list(set(emails_dest)),
                                                        codigo_solicitacao=item['codigo'],
                                                        linha=item['linha'],
                                                        num_doc=item['num_doc'],
                                                        descricao=item['descricao'],
                                                        comentario_solucao=comentario,
                                                        executor=usuario_ativo_nome
                                                    )

                                                cur.close()
                                                conn.close()
                                                st.success("Revisão finalizada com sucesso!")
                                                st.rerun()
                            else:
                                st.warning("🔒 Apenas colaboradores do setor Engenharia podem responder esta revisão.")

            else:
                for item in itens:
                    cor_status = "🔴" if item['status_item'] == 'Pendente' else ("🟡" if item['status_item'] == 'Em Andamento' else "🟢")
                    titulo = f"{cor_status} [{item['codigo']}] {item['linha']} - Doc: {item['num_doc']} | Status: {item['status_item']}"
                    with st.expander(titulo):
                        st.write(f"**Descrição:** {item['descricao']}")
                        st.write(f"**Pego por:** {item['usuario_aceite'] or 'Aguardando aceite'}")

# -------------------------------------------------------------------
# TELA 6: ATUALIZAÇÃO E DASHBOARD DE INDICADORES
# -------------------------------------------------------------------
elif opcao == "6. Atualização de Indicadores":
    st.header("📊 Atualização, Ações e Dashboards de Indicadores")

    tab_novo, tab_graficos, tab_historico = st.tabs(["➕ Lancar Indicador & Selecionar Setores", "📈 Dashboard e Gráficos", "📋 Histórico Completo"])

    conn = get_connection()
    df_linhas = pd.read_sql("SELECT id, nome FROM linhas", conn)
    df_ind_cadastrados = pd.read_sql("""
        SELECT 
            ic.id AS param_id, 
            ic.nome_indicador, 
            ic.abrangencia, 
            ic.linha_id, 
            ic.periodicidade, 
            ic.tipo_unidade, 
            ic.meta_padrao, 
            ic.setor_responsavel, 
            COALESCE(l.nome, '-- N/A --') AS linha 
        FROM indicadores_cadastro ic 
        LEFT JOIN linhas l ON ic.linha_id = l.id
    """, conn)
    df_usuarios = pd.read_sql("SELECT id, nome, email, setor FROM usuarios", conn)
    conn.close()

    semanas_ano = [f"Semana {i:02d}" for i in range(1, 53)]
    meses_ano = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    with tab_novo:
        if df_ind_cadastrados.empty:
            st.warning("⚠️ Nenhum indicador cadastrado na aba '7. Parametrização de Indicadores'. Cadastre as metas oficiais primeiro.")
        else:
            st.subheader("1. Métrica do Indicador")
            
            lista_ind_opts = [f"{row['nome_indicador']} ({row['abrangencia']} - {row['linha']})" for idx, row in df_ind_cadastrados.iterrows()]
            ind_sel_idx = st.selectbox("Selecione o Indicador Parametrizado", list(range(len(lista_ind_opts))), format_func=lambda x: lista_ind_opts[x])
            
            ind_info = df_ind_cadastrados.iloc[ind_sel_idx]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.info(f"**Indicador:** {ind_info['nome_indicador']}\n\n**Abrangência:** {ind_info['abrangencia']} ({ind_info['linha']})")
            with c2:
                st.info(f"**Periodicidade:** {ind_info['periodicidade']}\n\n**Formato:** {ind_info['tipo_unidade']}")
                ano_ref = st.number_input("Ano de Referência", min_value=2020, max_value=2030, value=datetime.now().year)
                if ind_info['periodicidade'] == "Semanal":
                    periodo_ref = st.selectbox("Selecione a Semana", semanas_ano, index=datetime.now().isocalendar()[1]-1)
                else:
                    periodo_ref = st.selectbox("Selecione o Mês", meses_ano)
            with c3:
                valor_ind = st.number_input(f"Valor Apurado ({ind_info['tipo_unidade']})", format="%.2f")
                meta_ind = st.number_input(f"Meta Oficial Cadastrada", value=float(ind_info['meta_padrao']), format="%.2f", disabled=True)

            st.markdown("---")
            st.subheader("2. Seleção de Setores Requeridos para Ação")

            c_eng, c_prod, c_qual, c_man = st.columns(4)
            with c_eng:
                chk_eng = st.checkbox("Engenharia", value=(ind_info['setor_responsavel'] == "Engenharia"))
            with c_prod:
                chk_prod = st.checkbox("Produção", value=(ind_info['setor_responsavel'] == "Produção"))
            with c_qual:
                chk_qual = st.checkbox("Qualidade", value=(ind_info['setor_responsavel'] == "Qualidade"))
            with c_man:
                chk_man = st.checkbox("Manutenção", value=(ind_info['setor_responsavel'] == "Manutenção"))

            setores_selecionados = []
            if chk_eng: setores_selecionados.append("Engenharia")
            if chk_prod: setores_selecionados.append("Produção")
            if chk_qual: setores_selecionados.append("Qualidade")
            if chk_man: setores_selecionados.append("Manutenção")

            st.markdown("---")
            if st.button("🚀 Registrar Indicador e Solicitar Plano aos Setores", type="primary"):
                if not setores_selecionados:
                    st.error("Por favor, selecione pelo menos um setor responsável.")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()

                        cursor.execute("SELECT id FROM tipos_acao WHERE nome = %s LIMIT 1", (ind_info['nome_indicador'],))
                        r_ta = cursor.fetchone()
                        tipo_id = r_ta[0] if r_ta else 1

                        linha_id_real = int(ind_info['linha_id']) if pd.notnull(ind_info['linha_id']) and ind_info['linha_id'] != 0 else None
                        cod_ind = f"IND-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

                        cursor.execute(
                            """
                            INSERT INTO indicadores_registros 
                            (codigo_registro, tipo_acao_id, abrangencia, linha_id, periodicidade, tipo_unidade, ano, periodo_referencia, valor_indicador, meta_indicador, responsavel_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (cod_ind, tipo_id, ind_info['abrangencia'], linha_id_real, ind_info['periodicidade'], ind_info['tipo_unidade'], ano_ref, periodo_ref, valor_ind, meta_ind, usuario_ativo_id)
                        )
                        ind_id = cursor.lastrowid

                        emails_para_notificar = []
                        for setor in setores_selecionados:
                            desc_padrao = f"Elaborar plano de ação de melhoria para o indicador {ind_info['nome_indicador']} ({periodo_ref}/{ano_ref}) - Apurado: {valor_ind} vs Meta: {meta_ind}."
                            cursor.execute(
                                """
                                INSERT INTO indicador_acoes (indicador_registro_id, descricao_acao, setor_responsavel)
                                VALUES (%s, %s, %s)
                                """,
                                (ind_id, desc_padrao, setor)
                            )

                            if linha_id_real:
                                query_resp = "SELECT u.email FROM linha_responsaveis lr JOIN usuarios u ON lr.usuario_id = u.id WHERE lr.linha_id = %s AND lr.papel = %s"
                                cursor.execute(query_resp, (linha_id_real, setor))
                                res = cursor.fetchone()
                                if res and res[0] and "@" in res[0]:
                                    emails_para_notificar.append(res[0])

                            if not emails_para_notificar:
                                query_setor_usr = "SELECT email FROM usuarios WHERE setor = %s AND email IS NOT NULL AND email != ''"
                                cursor.execute(query_setor_usr, (setor,))
                                for row_em in cursor.fetchall():
                                    if row_em[0] and "@" in row_em[0]:
                                        emails_para_notificar.append(row_em[0])

                        conn.commit()
                        cursor.close()
                        conn.close()

                        enviar_email_acao_indicador(
                            destinatarios=list(set(emails_para_notificar)),
                            codigo_ind=cod_ind,
                            indicador=ind_info['nome_indicador'],
                            linha_ou_fabrica=ind_info['linha'] if ind_info['linha'] != "-- N/A --" else ind_info['abrangencia'],
                            periodo=f"{periodo_ref}/{ano_ref}",
                            valor=valor_ind,
                            meta=meta_ind,
                            unidade=ind_info['tipo_unidade'],
                            setores_cobrados=setores_selecionados,
                            solicitante=usuario_ativo_nome
                        )

                        st.success(f"Indicador {cod_ind} registrado com sucesso!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao registrar indicador: {e}")

    with tab_graficos:
        st.subheader("📈 Gráficos de Evolução e Metas")

        conn = get_connection()
        query_g = """
            SELECT 
                ta.nome AS Indicador,
                ir.abrangencia AS Abrangência,
                COALESCE(l.nome, ir.abrangencia) AS Local,
                ir.ano AS Ano,
                ir.periodo_referencia AS Referencia,
                ir.valor_indicador AS Valor,
                ir.meta_indicador AS Meta,
                ir.tipo_unidade AS Unidade,
                ir.data_registro
            FROM indicadores_registros ir
            JOIN tipos_acao ta ON ir.tipo_acao_id = ta.id
            LEFT JOIN linhas l ON ir.linha_id = l.id
            ORDER BY ir.data_registro ASC
        """
        df_g = pd.read_sql(query_g, conn)
        conn.close()

        if df_g.empty:
            st.info("Nenhum dado disponível para geração de gráficos.")
        else:
            cg1, cg2 = st.columns(2)
            with cg1:
                ind_filtro = st.selectbox("Selecione o Indicador", df_g["Indicador"].unique())
            with cg2:
                local_filtro = st.selectbox("Selecione o Local / Linha", df_g[df_g["Indicador"] == ind_filtro]["Local"].unique())

            df_filtrado = df_g[(df_g["Indicador"] == ind_filtro) & (df_g["Local"] == local_filtro)].copy()

            if df_filtrado.empty:
                st.warning("Sem dados para o filtro selecionado.")
            else:
                unidade_medida = df_filtrado["Unidade"].values[0]
                df_filtrado['ordem'] = df_filtrado['Referencia'].str.extract(r'(\d+)').astype(float)
                df_filtrado = df_filtrado.sort_values(by=['Ano', 'ordem', 'data_registro'])

                st.markdown(f"#### Evolução do {ind_filtro} - {local_filtro} ({unidade_medida})")

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_filtrado['Referencia'], y=df_filtrado['Valor'],
                    mode='lines+markers+text', name='Valor Apurado',
                    text=[f"{v:.1f}" for v in df_filtrado['Valor']], textposition="top center",
                    line=dict(color='#0056b3', width=3), marker=dict(size=8)
                ))
                fig.add_trace(go.Scatter(
                    x=df_filtrado['Referencia'], y=df_filtrado['Meta'],
                    mode='lines+markers+text', name='Meta Oficial',
                    text=[f"{m:.1f}" for m in df_filtrado['Meta']], textposition="bottom center",
                    line=dict(color='#d9534f', width=2, dash='dash'), marker=dict(size=6, symbol='square')
                ))
                fig.update_layout(xaxis_title="Período de Referência", yaxis_title=f"Valor ({unidade_medida})", hovermode="x unified", height=450)
                st.plotly_chart(fig, use_container_width=True)

    with tab_historico:
        st.subheader("📈 Histórico Completo de Indicadores")
        conn = get_connection()
        query_hist = """
            SELECT 
                ir.codigo_registro AS Código, ta.nome AS Indicador, ir.abrangencia AS Abrangência,
                COALESCE(l.nome, 'Geral/Fábrica') AS Linha, ir.periodicidade AS Período, ir.ano AS Ano,
                ir.periodo_referencia AS Referência, ir.tipo_unidade AS Unidade, ir.valor_indicador AS Valor,
                ir.meta_indicador AS Meta, ia.setor_responsavel AS Setor_Ação, ia.status AS Status_Ação
            FROM indicadores_registros ir
            JOIN tipos_acao ta ON ir.tipo_acao_id = ta.id
            LEFT JOIN linhas l ON ir.linha_id = l.id
            LEFT JOIN indicador_acoes ia ON ir.id = ia.indicador_registro_id
            ORDER BY ir.ano DESC, ir.data_registro DESC
        """
        df_hist = pd.read_sql(query_hist, conn)
        conn.close()
        st.dataframe(df_hist, use_container_width=True)

# -------------------------------------------------------------------
# TELA 7: PARAMETRIZAÇÃO DE INDICADORES
# -------------------------------------------------------------------
elif opcao == "7. Parametrização de Indicadores":
    st.header("🎯 Cadastro e Parametrização de Indicadores e Metas")
    col1, col2 = st.columns([1, 2])

    conn = get_connection()
    df_linhas = pd.read_sql("SELECT id, nome FROM linhas", conn)
    conn.close()

    with col1:
        st.subheader("Cadastrar Novo Indicador")
        if es_admin:
            with st.form("form_cadastrar_indicador_param", clear_on_submit=True):
                nome_ind = st.text_input("Nome do Indicador (ex: OEE, Refugo, TPM, 5S)")
                abrangencia = st.selectbox("Abrangência", ["Linha", "Fábrica 1", "Fábrica 3", "Fábrica Inteira"])
                linha_sel = st.selectbox("Linha (se aplicável)", ["-- N/A --"] + df_linhas["nome"].tolist()) if abrangencia == "Linha" else "-- N/A --"
                periodicidade = st.selectbox("Periodicidade", ["Semanal", "Mensal"])
                tipo_unidade = st.selectbox("Formato da Métrica", ["Percentual (%)", "Número Real"])
                meta_padrao = st.number_input("Meta Oficial Estabelecida", format="%.2f")
                setor_resp = st.selectbox("Setor Responsável Principal", ["Engenharia", "Produção", "Qualidade", "Manutenção"])
                
                btn_salvar_param = st.form_submit_button("💾 Salvar Parametrização")

                if btn_salvar_param and nome_ind:
                    try:
                        linha_id = int(df_linhas[df_linhas["nome"] == linha_sel]["id"].values[0]) if linha_sel != "-- N/A --" and not df_linhas.empty else None
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO indicadores_cadastro (nome_indicador, abrangencia, linha_id, periodicidade, tipo_unidade, meta_padrao, setor_responsavel) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (nome_ind, abrangencia, linha_id, periodicidade, tipo_unidade, meta_padrao, setor_resp)
                        )
                        cursor.execute("SELECT id FROM tipos_acao WHERE nome = %s", (nome_ind,))
                        if not cursor.fetchone():
                            cursor.execute("INSERT INTO tipos_acao (nome, tipo_intervencao) VALUES (%s, 'Atualizar')", (nome_ind,))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"Indicador '{nome_ind}' parametrizado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao parametrizar: {e}")

    with col2:
        st.subheader("Indicadores e Metas Cadastradas")
        conn = get_connection()
        df_params = pd.read_sql("SELECT ic.id, ic.nome_indicador AS Indicador, ic.abrangencia AS Abrangência, COALESCE(l.nome, 'Geral/Fábrica') AS Linha, ic.meta_padrao AS Meta_Oficial, ic.setor_responsavel AS Setor_Resp FROM indicadores_cadastro ic LEFT JOIN linhas l ON ic.linha_id = l.id", conn)
        conn.close()
        st.dataframe(df_params, use_container_width=True)

# -------------------------------------------------------------------
# TELA 8: PLANO DE AÇÃO EXCLUSIVO PARA INDICADORES
# -------------------------------------------------------------------
elif opcao == "8. Plano de Ação - Indicadores":
    st.header("📊 Plano de Ação & Solução (Indicadores)")

    lista_setores_opts = ["Todos", "Engenharia", "Produção", "Qualidade", "Manutenção"]
    
    if not es_admin and usuario_ativo_setor in lista_setores_opts:
        idx_setor_default = lista_setores_opts.index(usuario_ativo_setor)
        travar_filtro_setor = True
    else:
        idx_setor_default = 0
        travar_filtro_setor = False

    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        filter_status = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Em Andamento", "Concluído"], key="f_stat_ind")
    with col_f2:
        filter_setor = st.selectbox("Filtrar por Setor Cobrado", lista_setores_opts, index=idx_setor_default, disabled=travar_filtro_setor, key="f_set_ind")
    with col_f3:
        modo_visao = st.radio("Modo de Visão", ["Cards / Galeria Visual 🖼️", "Lista Detalhada 📋"], horizontal=True, key="f_v_ind")

    conn = get_connection()
    query_ind = """
        SELECT 
            ir.codigo_registro AS codigo,
            CONCAT('Apurado: ', ir.valor_indicador, ' ', ir.tipo_unidade, ' (Meta: ', ir.meta_indicador, ' ', ir.tipo_unidade, ')') AS num_doc,
            COALESCE(l.nome, ir.abrangencia) AS linha, ir.linha_id, ta.nome AS tipo_acao, u.nome AS elaborador,
            ia.id AS item_id, ia.descricao_acao AS descricao, ia.status AS status_item, ia.comentario_solucao,
            ia.nome_evidencia, ia.arquivo_evidencia, ia.setor_responsavel AS setor_resp
        FROM indicadores_registros ir
        JOIN tipos_acao ta ON ir.tipo_acao_id = ta.id
        LEFT JOIN linhas l ON ir.linha_id = l.id
        JOIN usuarios u ON ir.responsavel_id = u.id
        JOIN indicador_acoes ia ON ir.id = ia.indicador_registro_id
        WHERE 1=1
    """
    if filter_status != "Todos": query_ind += f" AND ia.status = '{filter_status}'"
    if filter_setor != "Todos": query_ind += f" AND ia.setor_responsavel = '{filter_setor}'"
    query_ind += " ORDER BY ir.data_registro DESC"

    cursor_ind = conn.cursor(dictionary=True)
    cursor_ind.execute(query_ind)
    itens_ind = cursor_ind.fetchall()
    cursor_ind.close()
    conn.close()

    if not itens_ind:
        st.info("Nenhuma ação de indicador encontrada para os filtros selecionados.")
    else:
        if modo_visao == "Cards / Galeria Visual 🖼️":
            cols = st.columns(3)
            for idx, item in enumerate(itens_ind):
                col_atual = cols[idx % 3]
                with col_atual:
                    cor_status = "🔴" if item['status_item'] == 'Pendente' else ("🟡" if item['status_item'] == 'Em Andamento' else "🟢")
                    
                    with st.container(border=True):
                        st.markdown(f"### {cor_status} {item['codigo']}")
                        st.caption(f"**Local/Linha:** {item['linha']} | **Setor Cobrado:** {item['setor_resp']}")
                        st.write(f"**Indicador:** {item['tipo_acao']}")
                        st.write(f"**Resultado:** {item['num_doc']}")
                        st.info(f"**Solicitação:** {item['descricao']}")
                        
                        if item['arquivo_evidencia'] and item['nome_evidencia']:
                            st.download_button(
                                label=f"📥 Baixar Evidência ({item['nome_evidencia']})",
                                data=item['arquivo_evidencia'], file_name=item['nome_evidencia'],
                                key=f"dl_evid_ind_tab_{item['item_id']}"
                            )

                        if item['comentario_solucao']:
                            st.success(f"**Plano de Solução ({item['setor_resp']}):** {item['comentario_solucao']}")

                        pode_responder = es_admin or (usuario_ativo_setor.lower() == item['setor_resp'].lower())

                        if pode_responder:
                            with st.popover("⚙️ Responder / Registrar Ação"):
                                with st.form(key=f"card_form_ind_tab_{item['item_id']}"):
                                    novo_status = st.selectbox("Status", ["Pendente", "Em Andamento", "Concluído"], index=["Pendente", "Em Andamento", "Concluído"].index(item["status_item"]))
                                    comentario = st.text_area("Descreva a ação de melhoria", value=item["comentario_solucao"] or "")
                                    evid_file = st.file_uploader("Anexar Evidência", type=["png", "jpg", "jpeg", "pdf", "xlsx", "docx"], key=f"up_ind_tab_{item['item_id']}")
                                    
                                    if st.form_submit_button("Salvar Resolução"):
                                        conn = get_connection()
                                        cur = conn.cursor()
                                        evid_bytes = evid_file.read() if evid_file else None
                                        evid_nome = evid_file.name if evid_file else item["nome_evidencia"]

                                        if evid_bytes:
                                            cur.execute("UPDATE indicador_acoes SET status=%s, comentario_solucao=%s, nome_evidencia=%s, arquivo_evidencia=%s, responsavel_execucao_id=%s, data_conclusao=NOW() WHERE id=%s", (novo_status, comentario, evid_nome, evid_bytes, usuario_ativo_id, item['item_id']))
                                        else:
                                            cur.execute("UPDATE indicador_acoes SET status=%s, comentario_solucao=%s, responsavel_execucao_id=%s, data_conclusao=NOW() WHERE id=%s", (novo_status, comentario, usuario_ativo_id, item['item_id']))
                                        conn.commit()

                                        if novo_status == "Concluído":
                                            emails_dest = []
                                            query_em_criador = "SELECT u.email FROM indicador_acoes ia JOIN indicadores_registros ir ON ia.indicador_registro_id = ir.id JOIN usuarios u ON ir.responsavel_id = u.id WHERE ia.id = %s"
                                            cur.execute(query_em_criador, (item['item_id'],))
                                            r_em = cur.fetchone()
                                            if r_em and r_em[0] and "@" in r_em[0]: emails_dest.append(r_em[0])

                                            enviar_email_conclusao(destinatarios=list(set(emails_dest)), codigo_solicitacao=item['codigo'], linha=item['linha'], num_doc=item['num_doc'], descricao=item['descricao'], comentario_solucao=comentario, executor=usuario_ativo_nome)

                                        cur.close()
                                        conn.close()
                                        st.success("Plano de ação atualizado com sucesso!")
                                        st.rerun()
                        else:
                            st.warning(f"🔒 Apenas colaboradores do setor **{item['setor_resp']}** podem responder esta ação.")

# -------------------------------------------------------------------
# TELA 9: RELATÓRIO GERAL E EXPORTAÇÃO DE AÇÕES
# -------------------------------------------------------------------
elif opcao == "9. Relatório Geral de Ações":
    st.header("📋 Relatório Consolidado de Ações & Exportação")

    col_r1, col_r2 = st.columns([2, 4])
    with col_r1:
        origem_filtro = st.selectbox("Origem dos Dados", ["Todas as Ações", "Somente Revisões Documentais", "Somente Planos dos Indicadores"])

    conn = get_connection()

    query_rev = """
        SELECT 
            'Revisão Documental' AS `Origem`,
            l.nome AS `Linha`,
            DATE_FORMAT(sr.data_abertura, '%d/%m/%Y %H:%i') AS `Data Abertura`,
            ta.nome AS `Tipo do Doc / Métrica`,
            i.descricao_solicitacao AS `Solicitação descrição`,
            COALESCE(u_exec.nome, u_aceite.nome, 'Aguardando Atribuição') AS `Executante`,
            COALESCE(i.comentario_solucao, 'Em Aberto') AS `Descrição da Execução`,
            DATE_FORMAT(i.data_conclusao, '%d/%m/%Y %H:%i') AS `Data Finalização`,
            i.status AS `Status`
        FROM solicitacao_revisao_itens i
        JOIN solicitacoes_revisao sr ON i.solicitacao_id = sr.id
        JOIN linhas l ON sr.linha_id = l.id
        JOIN tipos_acao ta ON sr.tipo_acao_id = ta.id
        LEFT JOIN usuarios u_exec ON i.responsavel_execucao_id = u_exec.id
        LEFT JOIN usuarios u_aceite ON i.usuario_aceite_id = u_aceite.id
    """

    query_ind = """
        SELECT 
            'Plano de Indicadores' AS `Origem`,
            COALESCE(l.nome, ir.abrangencia) AS `Linha`,
            DATE_FORMAT(ir.data_registro, '%d/%m/%Y %H:%i') AS `Data Abertura`,
            ta.nome AS `Tipo do Doc / Métrica`,
            ia.descricao_acao AS `Solicitação descrição`,
            COALESCE(u_exec.nome, ia.setor_responsavel) AS `Executante`,
            COALESCE(ia.comentario_solucao, 'Em Aberto') AS `Descrição da Execução`,
            DATE_FORMAT(ia.data_conclusao, '%d/%m/%Y %H:%i') AS `Data Finalização`,
            ia.status AS `Status`
        FROM indicador_acoes ia
        JOIN indicadores_registros ir ON ia.indicador_registro_id = ir.id
        JOIN tipos_acao ta ON ir.tipo_acao_id = ta.id
        LEFT JOIN linhas l ON ir.linha_id = l.id
        LEFT JOIN usuarios u_exec ON ia.responsavel_execucao_id = u_exec.id
    """

    if origem_filtro == "Somente Revisões Documentais":
        query_final = query_rev + " ORDER BY sr.data_abertura DESC"
    elif origem_filtro == "Somente Planos dos Indicadores":
        query_final = query_ind + " ORDER BY ir.data_registro DESC"
    else:
        query_final = f"({query_rev}) UNION ALL ({query_ind}) ORDER BY `Data Abertura` DESC"

    df_relatorio = pd.read_sql(query_final, conn)
    conn.close()

    if df_relatorio.empty:
        st.info("Nenhum dado de ação encontrado para exibição.")
    else:
        st.markdown(f"#### Tabela de Ações Cadastradas ({len(df_relatorio)} registros)")
        st.dataframe(df_relatorio, use_container_width=True)

        st.markdown("---")
        csv_data = df_relatorio.to_csv(index=False, sep=";").encode('utf-8-sig')

        st.download_button(
            label="📥 Baixar Relatório Completo em CSV (Compatível com Excel)",
            data=csv_data,
            file_name=f"relatorio_acoes_engenharia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            type="primary"
        )
