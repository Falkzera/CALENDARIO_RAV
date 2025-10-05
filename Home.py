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
        
        titulos_pagina("Sistema de Login", font_size="1.9em", text_color="#3064AD")
        
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


    guia_agenda, guia_exportar = st.tabs(["Instruções: Agenda", "Instruções: Exportar Resumo Mensal"]) 

    with guia_agenda:
        with st.container(border=True):
            titulos_pagina("Agenda de Eventos — Guia de Operação", font_size="1.3em", text_color="#3064AD")
            st.markdown(
                """
                <div style=\"font-size: 0.98em; line-height: 1.6; color: #24354A; background:#f7fbff; border:1px solid #e1ecfa; border-radius:14px; padding:18px;\">
                  <div style=\"display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px;\">
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">🗓️ Navegar</span>
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">➕ Criar</span>
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">👁️ Ver detalhes</span>
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">✏️ Editar</span>
                    <span style=\"background:#ffecec; color:#b3212f; padding:6px 10px; border-radius:10px;\">🗑️ Excluir</span>
                  </div>
                  
                  <h4 style=\"margin: 12px 0 6px; color:#3064AD;\">Como navegar</h4>
                  <ul>
                    <li>Use as setas para avançar/voltar e alterne entre as visões <em>Mês</em>, <em>Semana</em> e <em>Dia</em>.</li>
                    <li>Clique em um dia ou arraste para selecionar um período no calendário.</li>
                  </ul>
                  
                  <h4 style=\"margin: 12px 0 6px; color:#3064AD;\">Como criar um evento</h4>
                  <ol>
                    <li>Clique em um <strong>dia futuro</strong> para exibir o botão “➕ Criar Evento para: DD/MM/AAAA”, ou selecione um <strong>período</strong> para criar no intervalo escolhido.</li>
                    <li>No formulário, preencha:
                      <ul>
                        <li><strong>Título*</strong> (obrigatório).</li>
                        <li><strong>Dia inteiro</strong> ou defina <em>Início</em> e <em>Fim</em> com horários válidos.</li>
                        <li><strong>Equipe</strong> e <strong>Motorista</strong> selecionando na lista.</li>
                        <li><strong>Local</strong> (opcional) e <strong>Descrição</strong> (opcional).</li>
                      </ul>
                    </li>
                    <li>Clique em <strong>Salvar</strong> para adicionar o evento à agenda. Use <strong>Cancelar</strong> para fechar sem mudanças.</li>
                  </ol>
                  
                  <h4 style=\"margin: 12px 0 6px; color:#3064AD;\">Como ver detalhes</h4>
                  <ol>
                    <li>Clique em um evento para abrir o painel de detalhes.</li>
                    <li>Use o botão <strong>“Abrir no Google Agenda”</strong> para visualizar no navegador, se desejar.</li>
                  </ol>
                  
                  <h4 style=\"margin: 12px 0 6px; color:#3064AD;\">Como editar</h4>
                  <ol>
                    <li>Em eventos futuros, clique em <strong>“✏️ Editar Evento”</strong>.</li>
                    <li>Altere título, período (dia inteiro ou horários), equipe, motorista, local e descrição.</li>
                    <li>Clique em <strong>Salvar</strong> para aplicar as alterações ou <strong>Cancelar</strong> para descartar.</li>
                  </ol>
                  
                  <h4 style=\"margin: 12px 0 6px; color:#3064AD;\">Como excluir</h4>
                  <ol>
                    <li>Clique em <strong>“🗑️ Deletar Evento”</strong> e confirme para remover.</li>
                  </ol>
                  
                  <div style=\"margin-top:10px; padding:10px; background:#f0f7ff; border:1px dashed #cfe1ff; border-radius:10px;\">
                    <strong>Observações rápidas:</strong>
                    <ul style=\"margin:8px 0 0;\">
                      <li>Eventos <em>passados</em> não podem ser editados.</li>
                      <li>Ao salvar ou cancelar, a agenda é atualizada automaticamente.</li>
                    </ul>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    with guia_exportar:
        with st.container(border=True):
            titulos_pagina("Resumo Mensal — Guia de Operação", font_size="1.3em", text_color="#3064AD")
            st.markdown(
                """
                <div style=\"font-size: 0.98em; line-height: 1.6; color: #24354A; background:#f7fbff; border:1px solid #e1ecfa; border-radius:14px; padding:18px;\">
                  <div style=\"display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px;\">
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">🗓️ Selecionar mês/ano</span>
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">👁️ Pré-visualizar</span>
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">⬇️ Baixar HTML</span>
                    <span style=\"background:#eaf2ff; color:#3064AD; padding:6px 10px; border-radius:10px;\">🖨️ Salvar PDF</span>
                  </div>
                  
                  <h4 style=\"margin: 12px 0 6px; color:#3064AD;\">Como exportar o resumo mensal</h4>
                  <ol>
                    <li>Escolha o <strong>Mês</strong> e o <strong>Ano</strong> desejados.</li>
                    <li>Veja a <strong>Pré-visualização</strong> do documento gerado.</li>
                    <li>Clique em <strong>“Baixar como HTML”</strong> para salvar o arquivo.</li>
                    <li>Para gerar PDF, abra o HTML no navegador e use <em>Imprimir</em> → <em>Salvar como PDF</em> (orientação paisagem, margens padrão).</li>
                  </ol>
                  
                  <div style=\"margin-top:10px; padding:10px; background:#f0f7ff; border:1px dashed #cfe1ff; border-radius:10px;\">
                    <strong>Dicas rápidas:</strong>
                    <ul style=\"margin:8px 0 0;\">
                      <li>Os eventos do mês aparecem em cartões com título, período, local e descrição.</li>
                      <li>O calendário mensal exibe “pills” com as cores por tipo de evento.</li>
                    </ul>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )



    

rodape_desenvolvedor()