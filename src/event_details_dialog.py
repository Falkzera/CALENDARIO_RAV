import streamlit as st
from datetime import datetime


def show_event_details(event):
    """
    Exibe os detalhes do evento selecionado diretamente na página.
    
    Args:
        event (dict): Dicionário contendo os dados do evento
    """
    # Container principal com título
    st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); 
                   border-radius: 15px; margin-bottom: 25px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <h1 style='margin: 0; font-size: 2rem;'>📋 Detalhes do Evento</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Verificar se é feriado ou evento da agenda
    is_feriado = event.get('extendedProps', {}).get('isFeriado', False)
    
    if is_feriado:
        # Layout para feriados
        st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       border-radius: 15px; margin-bottom: 20px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                <h1 style='margin: 0; font-size: 2.5rem;'>🎉</h1>
                <h2 style='margin: 10px 0; color: white;'>{}</h2>
                <p style='margin: 5px 0; opacity: 0.9; font-size: 1.1rem;'>Feriado {}</p>
            </div>
        """.format(
            event.get('extendedProps', {}).get('nome', 'Feriado'),
            event.get('extendedProps', {}).get('tipo', '')
        ), unsafe_allow_html=True)
        
        # Informações do feriado
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #667eea; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #667eea; margin-top: 0;'>📅 Data</h4>
                    <p style='margin: 0; font-size: 1.1rem; font-weight: 500;'>{}</p>
                </div>
            """.format(
                datetime.strptime(event['start'], '%Y-%m-%d').strftime('%d/%m/%Y')
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #764ba2; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #764ba2; margin-top: 0;'>🏛️ Tipo</h4>
                    <p style='margin: 0; font-size: 1.1rem; font-weight: 500;'>{}</p>
                </div>
            """.format(event.get('extendedProps', {}).get('tipo', 'Feriado')), unsafe_allow_html=True)
    
    else:
        # Layout para eventos da agenda
        st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #1f77b4 0%, #0d5aa7 100%); 
                       border-radius: 15px; margin-bottom: 20px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                <h1 style='margin: 0; font-size: 2.5rem;'>🎯</h1>
                <h2 style='margin: 10px 0; color: white;'>{}</h2>
                <p style='margin: 5px 0; opacity: 0.9; font-size: 1.1rem;'>Evento da Agenda RAV</p>
            </div>
        """.format(event.get('evento', event.get('title', 'Evento'))), unsafe_allow_html=True)
        
        # Informações do evento em cards
        col1, col2 = st.columns(2)
        
        with col1:
            # Data e Horário
            start_datetime = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))
            
            st.markdown("""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #1f77b4; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #1f77b4; margin-top: 0;'>📅 Data e Horário</h4>
                    <p style='margin: 5px 0; font-size: 1.1rem;'><strong>Data:</strong> {}</p>
                    <p style='margin: 5px 0; font-size: 1.1rem;'><strong>Horário:</strong> {} às {}</p>
                </div>
            """.format(
                start_datetime.strftime('%d/%m/%Y'),
                start_datetime.strftime('%H:%M'),
                end_datetime.strftime('%H:%M')
            ), unsafe_allow_html=True)
            
            # Condutor
            st.markdown("""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #28a745; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #28a745; margin-top: 0;'>🚗 Condutor/Motorista</h4>
                    <p style='margin: 0; font-size: 1.1rem; font-weight: 500;'>{}</p>
                </div>
            """.format(event.get('condutor', 'Não informado')), unsafe_allow_html=True)
        
        with col2:
            # Equipe
            st.markdown("""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #fd7e14; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #fd7e14; margin-top: 0;'>👥 Equipe</h4>
                    <p style='margin: 0; font-size: 1.1rem; font-weight: 500;'>{}</p>
                </div>
            """.format(event.get('equipe', 'Não informado')), unsafe_allow_html=True)
            
            # Local
            st.markdown("""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #dc3545; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #dc3545; margin-top: 0;'>📍 Local</h4>
                    <p style='margin: 0; font-size: 1.1rem; font-weight: 500;'>{}</p>
                </div>
            """.format(event.get('local', 'Não informado')), unsafe_allow_html=True)
        
        # Descrição completa
        if event.get('evento'):
            st.markdown("""
                <div style='background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #6f42c1; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #6f42c1; margin-top: 0;'>📝 Descrição Completa</h4>
                    <p style='margin: 0; font-size: 1.1rem; line-height: 1.6;'>{}</p>
                </div>
            """.format(event.get('evento', '')), unsafe_allow_html=True)
    
    # Botões de ação
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔙 Voltar ao Calendário", type="secondary", use_container_width=True):
            st.session_state.show_event_details = False
            st.session_state.selected_event = None
            st.rerun()
    
    with col2:
        if st.button("🔄 Atualizar", type="secondary", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("✅ Fechar", type="primary", use_container_width=True):
            st.session_state.show_event_details = False
            st.session_state.selected_event = None
            st.rerun()


def handle_event_click(calendar_result, filtered_feriados, events):
    """
    Gerencia o clique em eventos do calendário e define o evento selecionado.
    
    Args:
        calendar_result (dict): Resultado do componente calendar
        filtered_feriados (list): Lista de feriados filtrados
        events (list): Lista de eventos da agenda
    """
    if calendar_result.get("eventClick"):
        event_clicked = calendar_result["eventClick"]["event"]
        event_id = event_clicked.get("id", "")
        
        # Encontrar o evento completo nos dados
        selected_event = None
        
        # Procurar nos eventos da agenda
        for event in events:
            if event.get("id") == event_id:
                selected_event = event
                break
        
        # Se não encontrou, procurar nos feriados
        if not selected_event:
            for event in filtered_feriados:
                if event.get("id") == event_id:
                    selected_event = event
                    break
        
        if selected_event:
            st.session_state.selected_event = selected_event
            st.session_state.show_event_details = True