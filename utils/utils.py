import streamlit as st

def padrao_importacao_page():
    """
    Define o padrão de importação e configuração para páginas do Streamlit.
    
    Esta função configura o ambiente padrão para páginas internas do sistema,
    incluindo verificação de autenticação, configuração da página, modo desenvolvedor
    e navegação por ranking. Redireciona usuários não autenticados para a página inicial.
    
    A função executa as seguintes operações:
    1. Verifica e inicializa o estado de login do usuário
    2. Redireciona para Home.py se o usuário não estiver logado
    3. Configura a página do Streamlit com título, ícone e layout
    4. Carrega a imagem do topo
    5. Ativa o modo desenvolvedor se necessário
    6. Exibe informações do usuário na sidebar
    7. Configura a navegação baseada em permissões
    8. Adiciona estilos CSS do Font Awesome
    
    Returns:
        None: A função não retorna valores, apenas configura a interface.
    """
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in is False:
        st.switch_page("Home.py")
    
    st.set_page_config(
        page_title="Sistema de Gerenciamento", 
        page_icon=img_pag_icon(), 
        layout="wide", 
        initial_sidebar_state="expanded"
    )

    # imagem_topo()
    exibir_info_usuario_sidebar()
    menu_navegacao_sidebar()

    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" integrity="sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg==" crossorigin="anonymous" referrerpolicy="no-referrer" />',
        unsafe_allow_html=True
    )

def menu_navegacao_sidebar():
    """
    Constrói um menu de navegação na barra lateral com botões para as páginas:
    1_agenda.py, 2_kpi.py e um botão de SAIR que limpa todo o cache.
    """

    # Botão para página de Agenda
    if st.sidebar.button("Agenda", key="btn_agenda", use_container_width=True, type='primary'):
        st.switch_page("pages/1_agenda.py")

    # Botão para página de KPIs
    if st.sidebar.button("Indicadores", key="btn_kpi", use_container_width=True, type='primary'):
        st.switch_page("pages/2_kpi.py")

    st.sidebar.markdown("---")

    # Botão de Sair que limpa o cache
    if st.sidebar.button("Sair", key="btn_sair", use_container_width=True, type='primary'):
        # Limpa todos os dados do session_state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.cache_data.clear()
        st.cache_resource.clear()
        st.switch_page("Home.py")

# Importar a função dentro do padrão_importacao_page
# Adicionar a chamada da função no final de padrao_importacao_page


def img_pag_icon():
    """Retorna o caminho do ícone de página do governo."""
    # Preferir arquivo servido via pasta static para evitar MediaFileStorageError
    return 'static/rav.png'

def imagem_topo():
    """
    Exibe o logo de ALAGOAS e um separador visual na barra lateral.
    """
    try:
        st.sidebar.image("static/rav.png")
    except Exception:
        st.sidebar.image("assets/image/rav.png")
    st.sidebar.caption('---')

def configurar_cabecalho_principal():
    """
    Exibe o título principal e o logo da SEPLAG na área principal.
    """
    # col1, col2 = st.columns([2, 1.2])

    st.markdown(
        """
        <div style='
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 0 !important; 
            padding-top: 0 !important; 
            margin-bottom: 0 !important; 
            padding-bottom: 0 !important;
        '>
            <div style='
                border: 4px solid #EAEDF1;
                border-radius: 40px;
                padding: 24px 32px;
                background: #F0F2F9;  /* Cinza mais forte */
                display: flex;
                align-items: center;
                justify-content: center;
                box-sizing: border-box;
                width: 100%;
                max-width: 10000px;
            '>
                <h1 style='
                    text-align: center; 
                    color: #3064AD; 
                    font-weight: bold; 
                    margin: 0; 
                    padding: 0;
                    font-size: 3.1em;
                '>
                    <b>Governo de Alagoas</b>
                </h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def titulos_pagina(
    text,
    font_size="3.1em",
    text_color="#3064ad",
    centralizado=True,
    icon=None
):
    """
    Cria um cabeçalho estilizado com texto, tamanho de fonte e ícone HTML personalizáveis.

    Parâmetros:
    - text (str): O texto a ser exibido no cabeçalho
    - font_size (str): Tamanho da fonte (padrão: "3.1em")
    - text_color (str): Cor do texto (padrão: "#3064AD")
    - bg_color (str): Cor de fundo (padrão: "#F0F2F9")
    - centralizado (bool): Se True, o texto será centralizado (padrão: True)
    - border_color (str): Cor da borda (padrão: "#EAEDF1")
    - icon_html (str): HTML do ícone (ex: '<i class="fas fa-balance-scale"></i>') a ser exibido antes do texto
    """
    icon_part = f"{icon} " if icon else ""
    st.markdown(
        f"""
        <h1 style='
            text-align: {'center' if centralizado else 'left'};
            color: {text_color};
            font-weight: bold;
            margin: 0;
            padding: 0;
            font-size: {font_size};
            white-space: pre-line;
        '>
            {icon_part}<b>{text}</b>
        </h1>
        """,
        unsafe_allow_html=True
    )

def exibir_info_usuario_sidebar():
    """
    Exibe o nome do usuário em uma caixa estilizada na barra lateral, se disponível.
    """
    if "usuario_atual" in st.session_state:
        st.sidebar.markdown(f"""
        <style>
        .caixa-info-usuario {{
            background: #EAEDF1;
            color: #3064AD;
            border-radius: 10px;
            padding: 18px 12px 14px 12px;
            margin-bottom: 10px;
            font-size: 1.05em;
            font-weight: 500;
            box-shadow: 0 2px 8px rgba(48,100,173,0.08);
            text-align: center;
        }}
        .caixa-info-usuario a {{
            color: #3064AD;
            text-decoration: underline;
            font-weight: bold;
        }}
        .caixa-info-usuario a:hover {{
            color: #18325e;
            text-decoration: underline;
        }}
        </style>
        <div class="caixa-info-usuario">
            Olá, {st.session_state.usuario_atual.title()}
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.markdown("<br>", unsafe_allow_html=True)

def rodape_desenvolvedor():
    """
    Exibe o rodapé padrão do sistema com identidade visual e separador na barra lateral.
    """
    st.write("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>🏛️ <strong>SIREGOV - Sistema de Governança</strong></p>
            <p>Desenvolvido para otimizar a gestão governamental</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")