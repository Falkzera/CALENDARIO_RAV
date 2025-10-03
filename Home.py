import streamlit as st
from utils.utils import img_pag_icon, padrao_importacao_page, titulos_pagina, rodape_desenvolvedor
from src.google_sheets import read_data


def fazer_login(usuario, senha):
    """
    Faz o login validando NOME e SENHA na planilha do Google Sheets (calendario_rav > usuarios_rav).

    Parâmetros:
    - usuario (str): O NOME do usuário.
    - senha (str): A senha do usuário.
    """
    with st.spinner('Verificando Autenticação...'):
        df_usuarios = read_data("calendario_rav", "usuarios_rav")
        usuario_encontrado = None
        for _, row in df_usuarios.iterrows():
            nome_planilha = str(row.get('NOME', '')).strip()
            senha_planilha = str(row.get('SENHA', '')).strip()
            if nome_planilha == str(usuario).strip() and senha_planilha == str(senha).strip():
                usuario_encontrado = nome_planilha
                break
        if usuario_encontrado:
            st.session_state.logged_in = True
            st.session_state.usuario_atual = usuario_encontrado
            st.success("Login bem-sucedido!")
        else:
            st.error("Usuário ou senha inválidos.")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    
    with st.form("login_form", border=True):

        st.set_page_config(
        page_title="Sistema de Login", 
        page_icon=img_pag_icon(), 
        layout="centered", 
        initial_sidebar_state="expanded"
    )
        
        titulos_pagina("SIREGOV", font_size="1.9em", text_color="#3064AD")
        
        usuario = st.text_input("Nome", help="Informe seu NOME")
        senha = st.text_input("Senha", type="password", help="Informe sua SENHA")
        submitted = st.form_submit_button("ACESSAR", use_container_width=True, type="primary")

        if submitted:
            if usuario and senha:
                fazer_login(usuario, senha)
                st.rerun()
            else:
                st.error("⚠️ Por favor, preencha todos os campos!")
    st.stop()

if st.session_state.logged_in:

    padrao_importacao_page()

    from src.google_sheets import get_dados_usuarios, get_dados_motorista
    df_usuarios = get_dados_usuarios()
    st.session_state.df_usuarios = df_usuarios
    df_motorista = get_dados_motorista()
    st.session_state.df_motoristas = df_motorista


    titulos_pagina("Navegação", font_size="1.9em", text_color="#3064AD", icon='' )

rodape_desenvolvedor()