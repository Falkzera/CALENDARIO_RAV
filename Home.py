import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import json
import os
from src.event_details_dialog import show_event_details, handle_event_click

# ==================== CONFIGURAÇÕES ====================
st.set_page_config(
    page_title="Calendário RAV",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)




# Constantes
EVENTS_FILE = "data/events.json"
MOTORISTAS = [
    "A definir", "Everaldo", "Alexandre", "Beronaldo", 
    "Edson", "Fábio", "Holanda", "Marcelo", "Meiber"
]

# ==================== DADOS DE FERIADOS ====================
FERIADOS_BASE = {
    # Feriados Nacionais (fixos)
    "nacionais": {
        "01-01": "Confraternização Universal",
        "04-21": "Tiradentes", 
        "05-01": "Dia Mundial do Trabalho",
        "09-07": "Independência do Brasil",
        "10-12": "Nossa Senhora Aparecida",
        "11-02": "Finados",
        "11-15": "Proclamação da República", 
        "11-20": "Consciência Negra",
        "12-25": "Natal"
    },
    # Feriados Estaduais de Alagoas
    "estaduais": {
        "06-24": "São João",
        "06-29": "São Pedro", 
        "09-16": "Emancipação Política de Alagoas",
        "11-30": "Dia Estadual do Evangélico"
    },
    # Feriados Municipais de Maceió
    "municipais": {
        "04-18": "Sexta-feira da Paixão",
        "06-19": "Corpus Christi",
        "08-27": "Nossa Senhora dos Prazeres", 
        "12-08": "Nossa Senhora da Conceição"
    }
}

# ==================== FUNÇÕES UTILITÁRIAS ====================
def generate_time_options():
    """Gera opções de horário de 07:00 às 19:00 em intervalos de 30 min"""
    times = []
    for hour in range(7, 20):
        for minute in [0, 30]:
            if hour == 19 and minute == 30:
                break
            times.append(f"{hour:02d}:{minute:02d}")
    return times

def get_feriado_info(date_str):
    """Verifica se uma data é feriado e retorna informações"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month_day = date_obj.strftime('%m-%d')
        
        for tipo, feriados in FERIADOS_BASE.items():
            if month_day in feriados:
                return {
                    "nome": feriados[month_day],
                    "tipo": tipo.title(),
                    "color": {
                        "nacionais": "#ff6b6b",
                        "estaduais": "#4ecdc4", 
                        "municipais": "#45b7d1"
                    }[tipo]
                }
    except:
        pass
    return None

def get_feriado_events(view_type="month"):
    """Gera eventos de feriados para o calendário"""
    events = []
    current_year = datetime.now().year
    
    for year in [current_year, current_year + 1]:
        for tipo, feriados in FERIADOS_BASE.items():
            for month_day, nome in feriados.items():
                date_str = f"{year}-{month_day}"
                
                # Título baseado no tipo de visualização
                if view_type == "year":
                    title = "🎉"
                else:
                    title = f"🎉 {nome}"
                
                color = {
                    "nacionais": "#ff6b6b",
                    "estaduais": "#4ecdc4",
                    "municipais": "#45b7d1"
                }[tipo]
                
                events.append({
                    "id": f"feriado_{date_str}",
                    "title": title,
                    "start": date_str,
                    "end": date_str,
                    "allDay": True,
                    "backgroundColor": color,
                    "borderColor": color,
                    "textColor": "white",
                    "extendedProps": {
                        "tipo": tipo.title(),
                        "isFeriado": True,
                        "nome": nome
                    }
                })
    
    return events

def load_events():
    """Carrega eventos do arquivo JSON"""
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_events(events):
    """Salva eventos no arquivo JSON"""
    os.makedirs("data", exist_ok=True)
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def filter_events(events, selected_filters):
    """Filtra eventos baseado nos filtros selecionados"""
    if "Todos" in selected_filters:
        return events
    
    filtered = []
    
    for event in events:
        # Eventos da agenda (não feriados)
        if not event.get('extendedProps', {}).get('isFeriado', False):
            if "Ações da Agenda" in selected_filters:
                filtered.append(event)
        else:
            # Feriados
            tipo = event.get('extendedProps', {}).get('tipo', '').lower()
            if f"Feriados {tipo.title()}" in selected_filters:
                filtered.append(event)
    
    return filtered

def create_year_indicators(events):
    """Cria indicadores para visualização de ano"""
    from collections import defaultdict
    
    events_by_date = defaultdict(int)
    
    # Contar eventos por dia (excluindo feriados)
    for event in events:
        if not event.get('extendedProps', {}).get('isFeriado', False):
            start_date = event.get('start', '').split('T')[0]
            if start_date:
                events_by_date[start_date] += 1
    
    # Criar indicadores
    indicators = []
    for date, count in events_by_date.items():
        if count > 0:
            title = f"🎯 {count}" if count > 1 else "🎯"
            indicators.append({
                "id": f"indicator_{date}",
                "title": title,
                "start": f"{date}T00:00:00",
                "end": f"{date}T23:59:59",
                "backgroundColor": "#1f77b4",
                "borderColor": "#1f77b4", 
                "textColor": "white",
                "allDay": True,
                "extendedProps": {
                    "eventCount": count,
                    "isIndicator": True
                }
            })
    
    return indicators

# ==================== CSS OTIMIZADO ====================
def get_custom_css():
    return """
    <style>
    /* Estilos gerais do calendário */
    .fc {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Cabeçalho principal do calendário */
    .fc-toolbar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px 24px !important;
        border-radius: 20px 20px 0 0;
        margin-bottom: 0 !important;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        position: relative;
    }
    
    .fc-toolbar::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        border-radius: 20px 20px 0 0;
        pointer-events: none;
    }
    
    .fc-toolbar-title {
        font-size: 1.8rem;
        color: #ffffff !important;
        font-weight: 800;
        text-transform: capitalize;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        position: relative;
        z-index: 1;
    }
    
    .fc-button-primary {
        background: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 10px 18px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
    .fc-button-primary:hover {
        background: rgba(255, 255, 255, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
    }
    
    .fc-button-primary:active {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    }
    
    .fc-button-primary:focus {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3) !important;
    }
    
    .fc-event-title {
        font-weight: 600;
        font-size: 13px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .fc-daygrid-event {
        margin: 3px;
        border-radius: 12px;
        border: none;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
        transition: all 0.3s ease;
        overflow: hidden;
        position: relative;
    }
    
    .fc-daygrid-event::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        pointer-events: none;
    }
    
    .fc-daygrid-event:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }
    
    /* Fins de semana */
    .fc-day-sun, .fc-day-sat {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        position: relative;
    }
    
    .fc-day-sun::before, .fc-day-sat::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(148, 163, 184, 0.05);
        pointer-events: none;
    }
    
    .fc-day-sun .fc-daygrid-day-number, 
    .fc-day-sat .fc-daygrid-day-number {
        color: #64748b !important;
        font-weight: 500 !important;
    }
    
    /* Células dos dias - efeitos hover */
    .fc-daygrid-day {
        transition: all 0.3s ease;
        position: relative;
        border-radius: 8px;
        margin: 1px;
        border: 1px solid rgba(226, 232, 240, 0.5);
    }
    
    .fc-daygrid-day:hover {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        transform: scale(1.02);
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    
    .fc-daygrid-day-number {
        transition: all 0.3s ease;
        font-weight: 600;
        color: #374151;
        padding: 6px;
        border-radius: 6px;
        display: inline-block;
        min-width: 28px;
        text-align: center;
    }
    
    .fc-daygrid-day:hover .fc-daygrid-day-number {
        color: #1f2937;
        font-weight: 700;
        background: rgba(59, 130, 246, 0.1);
        transform: scale(1.1);
    }
    
    /* Melhorias no corpo do calendário */
    .fc-daygrid-body {
        border-radius: 0 0 20px 20px;
        overflow: hidden;
    }
    
    /* Cabeçalhos personalizados para visualização de mês */
    .fc-dayGridMonth-view .fc-col-header-cell {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-bottom: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .fc-dayGridMonth-view .fc-col-header-cell:hover {
        background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
        transform: translateY(-1px);
    }
    
    .fc-dayGridMonth-view .fc-col-header-cell .fc-col-header-cell-cushion {
        font-size: 0;
        position: relative;
        padding: 12px 8px;
    }
    
    .fc-dayGridMonth-view .fc-col-header-cell .fc-col-header-cell-cushion::after {
        font-size: 16px;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        transition: all 0.3s ease;
    }
    
    .fc-dayGridMonth-view .fc-col-header-cell:nth-child(1) .fc-col-header-cell-cushion::after { content: "Dom"; }
    .fc-dayGridMonth-view .fc-col-header-cell:nth-child(2) .fc-col-header-cell-cushion::after { content: "Seg"; }
    .fc-dayGridMonth-view .fc-col-header-cell:nth-child(3) .fc-col-header-cell-cushion::after { content: "Ter"; }
    .fc-dayGridMonth-view .fc-col-header-cell:nth-child(4) .fc-col-header-cell-cushion::after { content: "Qua"; }
    .fc-dayGridMonth-view .fc-col-header-cell:nth-child(5) .fc-col-header-cell-cushion::after { content: "Qui"; }
    .fc-dayGridMonth-view .fc-col-header-cell:nth-child(6) .fc-col-header-cell-cushion::after { content: "Sex"; }
    .fc-dayGridMonth-view .fc-col-header-cell:nth-child(7) .fc-col-header-cell-cushion::after { content: "Sáb"; }
    
    /* Cabeçalhos para visualização de ano */
    .fc-multiMonthYear-view .fc-col-header-cell {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border-bottom: 1px solid #e2e8f0 !important;
        transition: all 0.2s ease !important;
    }
    
    .fc-multiMonthYear-view .fc-col-header-cell:hover {
        background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%) !important;
    }
    
    .fc-multiMonthYear-view .fc-col-header-cell .fc-col-header-cell-cushion {
        font-size: 0 !important;
        position: relative !important;
        padding: 6px 4px !important;
    }
    
    .fc-multiMonthYear-view .fc-col-header-cell .fc-col-header-cell-cushion::after {
        font-size: 11px !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    /* Melhorias gerais de tipografia */
    .fc-daygrid-day-number {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.4;
    }
    
    .fc-event {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.3;
    }
    
    .fc-toolbar {
        margin-bottom: 1.5rem !important;
        padding: 0 1rem;
    }
    
    .fc-multiMonthYear-view .fc-col-header-cell:nth-child(1) .fc-col-header-cell-cushion::after { content: "D" !important; }
    .fc-multiMonthYear-view .fc-col-header-cell:nth-child(2) .fc-col-header-cell-cushion::after { content: "S" !important; }
    .fc-multiMonthYear-view .fc-col-header-cell:nth-child(3) .fc-col-header-cell-cushion::after { content: "T" !important; }
    .fc-multiMonthYear-view .fc-col-header-cell:nth-child(4) .fc-col-header-cell-cushion::after { content: "Q" !important; }
    .fc-multiMonthYear-view .fc-col-header-cell:nth-child(5) .fc-col-header-cell-cushion::after { content: "Q" !important; }
    .fc-multiMonthYear-view .fc-col-header-cell:nth-child(6) .fc-col-header-cell-cushion::after { content: "S" !important; }
    .fc-multiMonthYear-view .fc-col-header-cell:nth-child(7) .fc-col-header-cell-cushion::after { content: "S" !important; }
    </style>
    """

# ==================== INTERFACE PRINCIPAL ====================

# Inicializar session state
if 'events' not in st.session_state:
    st.session_state.events = load_events()

if 'selected_filters' not in st.session_state:
    st.session_state.selected_filters = ["Todos"]

if 'show_event_details' not in st.session_state:
    st.session_state.show_event_details = False

if 'selected_event' not in st.session_state:
    st.session_state.selected_event = None

# Sidebar
with st.sidebar:
    st.image("image/rav.png", use_container_width=True)
    st.write("---")
    
    # Filtros
    st.subheader("🔍 Filtros de Visualização")
    
    filter_options = [
        "Todos",
        "Feriados Nacionais", 
        "Feriados Estaduais",
        "Feriados Municipais",
        "Ações da Agenda"
    ]
    
    selected_filters = st.multiselect(
        "Selecione o que deseja visualizar:",
        options=filter_options,
        default=st.session_state.selected_filters,
        help="Escolha quais tipos de eventos deseja ver no calendário"
    )
    
    # Lógica simplificada para "Todos"
    if not selected_filters:
        selected_filters = ["Todos"]
    elif "Todos" in selected_filters and len(selected_filters) > 1:
        selected_filters = ["Todos"]
    
    st.session_state.selected_filters = selected_filters
    
    st.write("---")
    
    # Botão para adicionar evento
    if st.button("➕ Adicionar Novo Evento", type="primary", use_container_width=True):
        st.session_state.show_dialog = True

# Dialog para adicionar evento
if st.session_state.get('show_dialog', False):
    @st.dialog("➕ Novo Evento RAV", width="large")
    def add_event_dialog():
        st.write("Preencha os dados do evento:")
        
        with st.form("event_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                data_evento = st.date_input(
                    "📅 Data do Evento",
                    value=None,
                    help="Selecione a data do evento",
                    format="DD/MM/YYYY"
                )
                
                hora_inicio = st.selectbox(
                    "🕐 Horário",
                    options=generate_time_options(),
                    index=0,
                    help="Selecione o horário do evento"
                )
            
            with col2:
                condutor = st.selectbox(
                    "🚗 Condutor/Motorista",
                    options=MOTORISTAS,
                    help="Selecione o motorista responsável"
                )
                
                equipe = st.text_input(
                    "👥 Equipe",
                    placeholder="Ex: Equipe CREAS, Equipe CAPS...",
                    help="Informe a equipe responsável"
                )
            
            local = st.text_input(
                "📍 Local",
                placeholder="Ex: CREAS Centro, Escola Municipal...",
                help="Informe o local do evento"
            )
            
            evento = st.text_area(
                "📝 Descrição do Evento",
                placeholder="Descreva o evento ou atividade...",
                help="Descreva detalhadamente o evento"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submitted = st.form_submit_button("✅ Salvar Evento", type="primary", use_container_width=True)
            
            with col_btn2:
                cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if submitted:
                if not all([data_evento, equipe, local, evento]):
                    st.error("⚠️ Por favor, preencha todos os campos obrigatórios!")
                else:
                    # Calcular horário de fim
                    hora_inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
                    hora_fim_obj = datetime.combine(datetime.today(), hora_inicio_obj)
                    hora_fim_obj = (hora_fim_obj + timedelta(hours=1)).time()
                    
                    # Criar evento
                    new_event = {
                        "id": f"event_{len(st.session_state.events) + 1}",
                        "title": f"🎯 {evento[:25]}..." if len(evento) > 25 else f"🎯 {evento}",
                        "start": f"{data_evento}T{hora_inicio}:00",
                        "end": f"{data_evento}T{hora_fim_obj.strftime('%H:%M')}:00",
                        "condutor": condutor,
                        "equipe": equipe,
                        "local": local,
                        "evento": evento,
                        "backgroundColor": "#1f77b4",
                        "borderColor": "#1f77b4",
                        "textColor": "white"
                    }
                    
                    st.session_state.events.append(new_event)
                    save_events(st.session_state.events)
                    
                    st.success("✅ Evento criado com sucesso!")
                    st.session_state.show_dialog = False
                    st.rerun()
            
            if cancelled:
                st.session_state.show_dialog = False
                st.rerun()
    
    add_event_dialog()

# Preparar eventos para o calendário
all_events = st.session_state.events.copy()

# Adicionar feriados baseado nos filtros
feriado_events = get_feriado_events()
filtered_feriados = filter_events(feriado_events, st.session_state.selected_filters)
all_events.extend(filtered_feriados)

# Filtrar eventos da agenda
filtered_events = filter_events(all_events, st.session_state.selected_filters)

# Configurações do calendário
calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,multiMonthYear"
    },
    "initialView": "dayGridMonth",
    "locale": "pt-br",
    "buttonText": {
        "today": "Hoje",
        "month": "Mês", 
        "week": "Semana",
        "day": "Dia",
        "year": "Ano"
    },
    "slotMinTime": "07:00:00",
    "slotMaxTime": "19:00:00",
    "height": 600,
    "eventDisplay": "block",
    "displayEventTime": True
}

# Aplicar CSS customizado
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Renderizar calendário
st.write("---")
calendar_result = calendar(
    events=filtered_events,
    options=calendar_options,
    custom_css="",
    key="calendar"
)

# Gerenciar cliques em eventos
handle_event_click(calendar_result, filtered_feriados, st.session_state.events)

# Exibir diálogo de detalhes do evento
if st.session_state.get('show_event_details', False) and st.session_state.get('selected_event'):
    show_event_details(st.session_state.selected_event)

# Rodapé
st.write("---")
st.markdown("""
    <div style='text-align: center; color: #666; font-size: 14px;'>
        📅 RAV (Rede de Atenção à Violência)<br>
        Desenvolvido para otimizar o agendamento e coordenação de atividades
    </div>
""", unsafe_allow_html=True)