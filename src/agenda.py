import time
import streamlit as st
from datetime import datetime, timedelta
from src.google_agenda import get_calendar_events, create_calendar_event, update_calendar_event, delete_calendar_event, normalize_html_description, get_holidays_from_google
from utils.utils import titulos_pagina
from streamlit_calendar import calendar
from src.google_sheets import get_dados_usuarios, get_dados_motorista
from src.email import send_event_email_for_event

df_usuarios = get_dados_usuarios()
st.session_state.df_usuarios = df_usuarios
df_motorista = get_dados_motorista()
st.session_state.df_motoristas = df_motorista

# Paleta de cores disponíveis para eventos
# Paleta de seleção (nome -> colorId do Google)
COLOR_SELECT_TO_ID = {
    'Lavanda': '1',
    'Sálvia (Verde Claro)': '2',
    'Roxo (Grape)': '3',
    'Coral (Flamingo)': '4',
    'Amarelo (Banana)': '5',
    'Laranja (Tangerine)': '6',
    'Azul (Peacock)': '7',
    'Cinza (Graphite)': '8',
    'Azul (Blueberry)': '9',
    'Verde (Basil)': '10',
    'Vermelho (Tomato)': '11',
}

# Para preview visual no formulário (colorId -> hex aproximado oficial)
GOOGLE_EVENT_COLORS = {
    "1":  {"name": "Lavender",      "hex": "#7986CB"},
    "2":  {"name": "Sage",          "hex": "#33B679"},
    "3":  {"name": "Grape",         "hex": "#8E24AA"},
    "4":  {"name": "Flamingo",      "hex": "#E67C73"},
    "5":  {"name": "Banana",        "hex": "#F6BF26"},
    "6":  {"name": "Tangerine",     "hex": "#F4511E"},
    "7":  {"name": "Peacock",       "hex": "#039BE5"},
    "8":  {"name": "Graphite",      "hex": "#616161"},
    "9":  {"name": "Blueberry",     "hex": "#3F51B5"},
    "10": {"name": "Basil",         "hex": "#0B8043"},
    "11": {"name": "Tomato",        "hex": "#D50000"},
}
DEFAULT_COLOR_ID = None  # usa a cor padrão do calendário
DEFAULT_COLOR_HEX = "#3064ad"  # apenas para fallback visual

DEFAULT_COLOR = '#3064ad'
SALA_LOCATION = "Palácio República dos Palmares, R. Cincinato Pinto, s/n - Centro, Maceió - AL, 57020-050, Brasil"
TIME_SLOT_INTERVAL = 15  # minutos
START_HOUR = 7
END_HOUR = 20

# ==================== FUNÇÕES AUXILIARES ====================

def get_event_color(event):
    """Determina a cor do evento pela colorId do Google (se houver) ou fallback visual."""
    # 1) Se vier colorId do Google no evento (top-level ou em extendedProps), usa o hex correspondente para a UI
    color_id = event.get('colorId') or event.get('extendedProps', {}).get('colorId')
    if color_id and str(color_id) in GOOGLE_EVENT_COLORS:
        return GOOGLE_EVENT_COLORS[str(color_id)]['hex']
    
    # 2) Fallback: se ainda houver custom_color antigo em extendedProps (migração), use-o
    extended_props = event.get('extendedProps', {})
    custom_color = extended_props.get('custom_color')
    if custom_color:
        return custom_color
    
    # 3) Cor padrão visual
    return DEFAULT_COLOR_HEX

# Novo: obtém colorId para Google Calendar
def get_event_color_id(title):
    title_lower = title.lower()
    for keyword, color_id in COLOR_ID_MAPPING.items():
        if keyword in title_lower:
            return color_id
    return None

def generate_time_options():
    """Gera opções de horário com intervalos de 15 minutos entre 7h e 20h."""
    times = []
    for hour in range(START_HOUR, END_HOUR + 1):
        for minute in [0, 15, 30, 45]:
            if hour == END_HOUR and minute > 0:
                break
            times.append(f"{hour:02d}:{minute:02d}")
    return times

def get_available_times(selected_date):
    """Retorna horários disponíveis para a data selecionada (permite passado e horários já passados de hoje)."""
    all_times = generate_time_options()

    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()

    current_date = datetime.now().date()

    # Data passada → permitir todos os horários
    if selected_date < current_date:
        return all_times

    # Data futura → todos os horários
    if selected_date > current_date:
        return all_times

    # Hoje → todos os horários (inclusive os que já passaram)
    return all_times

def validate_time_selection(start_date, start_time_str, end_date, end_time_str):
    """Valida se os horários selecionados são válidos."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    start_datetime = datetime.combine(start_date, datetime.strptime(start_time_str, "%H:%M").time())
    end_datetime = datetime.combine(end_date, datetime.strptime(end_time_str, "%H:%M").time())
    
    if end_datetime <= start_datetime:
        return False, "❌ O horário de fim deve ser posterior ao horário de início!"

    warning = ""
    if start_datetime <= datetime.now():
        warning = "⚠️ ⏳ Viajante do tempo? Agendar no passado é um truque e tanto! 😉"
        
    return True, warning

def is_event_in_past(event):
    """Verifica se um evento já passou."""
    try:
        now = datetime.now()
        start_str = event.get('start', '')
        is_all_day = event.get('allDay', False)
        
        if is_all_day:
            event_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            return event_date < now.date()
        else:
            if 'T' in start_str:
                start_clean = start_str.replace('Z', '').split('+')[0]
                event_datetime = datetime.fromisoformat(start_clean)
                return event_datetime < now
            else:
                event_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                return event_date < now.date()
    except:
        return False

def format_event_for_calendar(event):
    """Formata um evento para exibição no calendário."""
    title = event.get('title', 'Evento sem título')
    extended_props = event.get('extendedProps', {})
    start_time = extended_props.get('start_time')
    end_time = extended_props.get('end_time')
    
    start_date = event.get('start', '')
    end_date = event.get('end', '')
    
    formatted_event = {
        'title': title,
        'description': event.get('description', ''),
        'location': event.get('location', ''),
        'start': start_date,
        'end': end_date,
        'backgroundColor': get_event_color(event), # <--- AQUI: Usa a nova função get_event_color
        'textColor': '#ffffff',
        'allDay': event.get('allDay', start_time is None),
        'extendedProps': extended_props
    }
    
    # Adicionar horários se não for evento de dia inteiro
    if start_time and not event.get('allDay', False):
        if 'T' not in start_date:
            formatted_event['start'] = f"{start_date}T{start_time}:00"
        if end_time and end_date:
            if 'T' not in end_date:
                formatted_event['end'] = f"{end_date}T{end_time}:00"
    
    return formatted_event

def parse_event_datetime(event):
    """Extrai e formata datas e horários de um evento."""
    start_str = str(event.get('start', ''))
    end_str = str(event.get('end', ''))
    extended_props = event.get('extendedProps', {})
    
    result = {
        'start_date': None,
        'end_date': None,
        'start_time': None,
        'end_time': None,
        'is_all_day': event.get('allDay', False)
    }
    
    # Parse start
    if 'T' in start_str:
        date_part, time_part = start_str.split('T')
        result['start_date'] = datetime.fromisoformat(date_part).strftime('%d/%m/%Y')
        result['start_time'] = time_part.split('+')[0].split('-')[0].split('Z')[0][:5]
    elif start_str:
        result['start_date'] = datetime.fromisoformat(start_str).strftime('%d/%m/%Y')
    
    # Parse end
    if 'T' in end_str:
        date_part, time_part = end_str.split('T')
        result['end_date'] = datetime.fromisoformat(date_part).strftime('%d/%m/%Y')
        result['end_time'] = time_part.split('+')[0].split('-')[0].split('Z')[0][:5]
    elif end_str:
        result['end_date'] = datetime.fromisoformat(end_str).strftime('%d/%m/%Y')
    
    # Override com extendedProps se disponível
    if extended_props.get('start_time'):
        result['start_time'] = extended_props['start_time']
    if extended_props.get('end_time'):
        result['end_time'] = extended_props['end_time']
    
    return result

# ==================== CSS E OPÇÕES DO CALENDÁRIO ====================

def get_custom_css():
    """Retorna o CSS customizado do calendário."""
    return """
        .fc {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(48, 100, 173, 0.1);
            overflow: hidden;
        }
        .fc-header-toolbar {
            background: linear-gradient(135deg, #3064ad 0%, #4a7bc8 100%);
            padding: 1rem 1.5rem;
            margin-bottom: 0 !important;
            border-radius: 12px 12px 0 0;
        }
        .fc-toolbar-title {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: #ffffff !important;
            text-transform: capitalize;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .fc-button {
            background: rgba(255, 255, 255, 0.2) !important;
            border: 2px solid rgba(255, 255, 255, 0.3) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            text-transform: capitalize !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease !important;
            backdrop-filter: blur(10px);
        }
        .fc-button:hover {
            background: rgba(255, 255, 255, 0.3) !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .fc-button-active {
            background: #ffffff !important;
            color: #3064ad !important;
            border-color: #ffffff !important;
            font-weight: 700 !important;
        }
        .fc-col-header {
            background: #f8f9fa;
            border-bottom: 2px solid #3064ad;
        }
        .fc-col-header-cell {
            padding: 1rem 0.5rem;
            font-weight: 700;
            color: #3064ad;
            text-transform: uppercase;
            font-size: 0.9rem;
            letter-spacing: 0.5px;
        }
        .fc-daygrid-day:hover {
            background-color: rgba(48, 100, 173, 0.05);
        }
        .fc-day-today {
            background-color: rgba(48, 100, 173, 0.1) !important;
            border: 2px solid #3064ad !important;
        }
        .fc-day-today .fc-daygrid-day-number {
            background: #3064ad;
            color: #ffffff;
            border-radius: 50%;
            width: 2rem;
            height: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0.25rem;
        }
        .fc-event {
            border: none !important;
            border-radius: 6px !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            padding: 2px 6px !important;
            margin: 1px 2px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .fc-event:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .fc-event-past {
            opacity: 0.7;
            filter: grayscale(20%);
        }
        @media (max-width: 768px) {
            .fc-toolbar-title { font-size: 1.4rem !important; }
            .fc-button { padding: 0.4rem 0.8rem !important; font-size: 0.85rem !important; }
        }
    """

def get_calendar_options():
    """Retorna as opções de configuração do calendário."""
    return {
        "editable": False,
        "selectable": True,
        "selectMirror": True,
        "dayMaxEvents": True,
        "weekends": True,
        "locale": "pt-br",
        "timeZone": "America/Sao_Paulo",
        "droppable": False,
        "dragScroll": False,
        "eventStartEditable": True,
        "eventDurationEditable": True,
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "multiMonthYear,dayGridMonth,timeGridWeek,timeGridDay",
        },
        "slotMinTime": "06:00:00",
        "slotMaxTime": "22:00:00",
        "slotDuration": "00:30:00",
        "initialView": "dayGridMonth",
        "height": 750,
        "nowIndicator": True,
        "businessHours": {
            "daysOfWeek": [1, 2, 3, 4, 5],
            "startTime": "08:00",
            "endTime": "18:00"
        },
        "buttonText": {
            "today": "Hoje",
            "month": "Mês",
            "week": "Semana",
            "day": "Dia",
            "year": "Ano",
        },
        "eventTimeFormat": {
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        },
    }

# ==================== DIÁLOGOS ====================

@st.dialog("📅", width="large")
def show_event_details(event):
    """Exibe os detalhes do evento em um diálogo."""
    
    st.markdown("""
    <style>
    .event-description {
        background: #EAEDF1;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        border-left: 3px solid #3064ad;
        font-style: italic;
        color: #000000;
    }
    .event-info-item {
        background: #EAEDF1;
        border-radius: 8px;
        padding: 10px 15px;
        margin: 5px 0;
        border-left: 3px solid #3064ad;
    }
    .time-highlight {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 2px 8px;
        font-weight: bold;
        color: #856404;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título
    if 'title' in event:
        titulos_pagina(event['title'], font_size="1.5em")
    
    # Descrição
    if 'extendedProps' in event and 'description' in event['extendedProps']:
        normalized_description = normalize_html_description(
            event['extendedProps']['description'], 
            for_html_display=True
        )
        st.markdown(
            f'<div class="event-description">📝 <strong>Descrição:</strong><br>{normalized_description}</div>',
            unsafe_allow_html=True
        )
    
    # Data e horário
    dt_info = parse_event_datetime(event)
    
    if dt_info['is_all_day']:
        # Evento de dia inteiro
        if dt_info['end_date'] and dt_info['end_date'] != dt_info['start_date']:
            st.markdown(
                f'<div class="event-info-item"><strong>📅 Período:</strong> {dt_info["start_date"]} até {dt_info["end_date"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="event-info-item"><strong>📅 Data:</strong> {dt_info["start_date"]}</div>',
                unsafe_allow_html=True
            )
    else:
        # Evento com horário
        col_start, col_end = st.columns(2)
        with col_start:
            time_display = f'<span class="time-highlight">{dt_info["start_time"]}</span>' if dt_info['start_time'] else 'Não informado'
            st.markdown(
                f'<div><strong>🕐 Início:</strong><br>📅 {dt_info["start_date"]}<br>⏰ {time_display}</div>',
                unsafe_allow_html=True
            )
        with col_end:
            if dt_info['end_date'] or dt_info['end_time']:
                end_date_display = dt_info['end_date'] or dt_info['start_date']
                time_display = f'<span class="time-highlight">{dt_info["end_time"]}</span>' if dt_info['end_time'] else 'Não informado'
                st.markdown(
                    f'<div><strong>🕑 Fim:</strong><br>📅 {end_date_display}<br>⏰ {time_display}</div>',
                    unsafe_allow_html=True
                )
    
    # Localização
    if 'extendedProps' in event and event['extendedProps'].get('location'):
        st.markdown(
            f'<div class="event-info-item">📍 <strong>Localização:</strong><br>{event["extendedProps"]["location"]}</div>',
            unsafe_allow_html=True
        )
    
    # Participantes
    participants_list = event.get('attendees') or event.get('extendedProps', {}).get('attendees', [])
    if participants_list:
        processed = []
        for p in participants_list:
            if isinstance(p, dict):
                processed.append(p.get('displayName') or p.get('email', str(p)))
            else:
                processed.append(str(p))
        participants_text = '<br>'.join([f"• {p}" for p in processed])
        st.markdown(
            f'<div class="event-info-item">👥 <strong>Participantes:</strong><br>{participants_text}</div>',
            unsafe_allow_html=True
        )
    
    # Link do Google Agenda
    meet_link = event.get('extendedProps', {}).get('html_link')
    if meet_link:
        st.markdown("📅 **Link do Google Agenda**")
        st.markdown(
            f'<a href="{meet_link}" target="_blank" style="color: #2196f3; text-decoration: none; font-weight: bold;">🔗 Abrir no Google Agenda</a>',
            unsafe_allow_html=True
        )
    
    st.write("---")
    
    # Botões de ação (apenas para eventos futuros)
    # if not is_event_in_past(event):

    col_edit, col_delete = st.columns(2)
    with col_edit:
        if st.button("✏️ Editar Evento", key=f"edit_{event.get('id', 'unknown')}", type='primary', use_container_width=True):
            st.session_state.show_edit_event = True
            st.session_state.selected_event = event
            st.rerun()
    
    with col_delete:
        with st.popover("🗑️ Deletar Evento", use_container_width=True):
            st.write("⚠️ Tem certeza de que deseja DELETAR este evento?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sim", key=f"confirm_delete_{event.get('id', 'unknown')}", type='secondary', use_container_width=True):
                    google_event_id = event.get('extendedProps', {}).get('google_event_id')
                    if google_event_id and delete_calendar_event(google_event_id):
                        st.success("✅ Evento deletado com sucesso!")
                        st.session_state.calendar_events = [
                            e for e in st.session_state.calendar_events
                            if e.get('extendedProps', {}).get('google_event_id') != google_event_id
                        ]
                        st.rerun()
                    else:
                        st.error("❌ Erro ao deletar evento")
            with col2:
                if st.button("Não", key=f"cancel_delete_{event.get('id', 'unknown')}", type='secondary', use_container_width=True):
                    pass

@st.dialog("➕", width="large", dismissible=False)
def show_create_event_form():
    """Interface para criação de novos eventos."""
    
    with st.container(border=True):
        opcoes_evento = st.selectbox("📝 Tipo de Evento*", ["PERSONALIZADO"])
        
        if opcoes_evento == "PERSONALIZADO":

            # Datas selecionadas no calendário (necessário para lógica de horários)
            start_date_str = st.session_state.get("selected_date", datetime.now().strftime("%Y-%m-%d"))
            end_date_str = st.session_state.get("selected_end_date", start_date_str)
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            # 1) Checkbox: Evento de dia inteiro (acima do Nome do Evento)
            all_day = st.checkbox("🌅 Evento de dia inteiro", value=True)

            # 2) Nome do Evento e Descrição
            title = st.text_input("🏷️ Nome do Evento*", key="custom_title", placeholder="Ex: Reunião de Planejamento")
            description_base = st.text_area("📄 Descrição", placeholder="Descreva os detalhes do evento")

            # 2.5) Seletor de Cor
            # 2.5) Seletor de Cor (via colorId do Google)
            col_color, col_preview = st.columns([1, 1])
            with col_color:
                color_names = list(COLOR_SELECT_TO_ID.keys())
                selected_color_name = st.selectbox(
                    "🎨 Cor do Evento",
                    options=color_names,
                    index=0,
                    key="event_color_selector"
                )
                selected_color_id = COLOR_SELECT_TO_ID[selected_color_name]
                selected_hex = GOOGLE_EVENT_COLORS.get(selected_color_id, {}).get("hex", DEFAULT_COLOR_HEX)

            with col_preview:
                st.markdown(
                    f"""
                    <div style="margin-top: 28px;">
                        <div style="
                            background-color: {selected_hex};
                            width: 100%;
                            height: 40px;
                            border-radius: 8px;
                            border: 2px solid #ddd;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        "></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # 3) Widgets de horários (caso não seja dia inteiro)
            if not all_day:
                available_times = get_available_times(start_date)
                if not available_times:
                    st.error("❌ Não é possível selecionar horário para datas passadas!")
                    return

                # Inicializar horários padrão em session_state
                if "custom_start_time_str" not in st.session_state:
                    st.session_state.custom_start_time_str = available_times[0]
                if "custom_end_time_str" not in st.session_state:
                    start_idx = available_times.index(st.session_state.custom_start_time_str)
                    end_idx = min(start_idx + 4, len(available_times) - 1)  # 1 hora padrão
                    st.session_state.custom_end_time_str = available_times[end_idx]

                # Selectboxes de horários
                col1, col2 = st.columns(2)
                with col1:
                    start_time_str = st.selectbox(
                        "🕐 Hora de Início",
                        options=available_times,
                        index=available_times.index(st.session_state.custom_start_time_str),
                        key="custom_start_time_select"
                    )
                    if start_time_str != st.session_state.custom_start_time_str:
                        st.session_state.custom_start_time_str = start_time_str
                        start_idx = available_times.index(start_time_str)
                        end_idx = min(start_idx + 4, len(available_times) - 1)
                        st.session_state.custom_end_time_str = available_times[end_idx]
                        st.rerun()

                with col2:
                    start_idx = available_times.index(st.session_state.custom_start_time_str)
                    end_time_options = available_times[start_idx + 1:]

                    if not end_time_options:
                        st.error("❌ Não há horários de fim disponíveis!")
                        return

                    if st.session_state.custom_end_time_str not in end_time_options:
                        st.session_state.custom_end_time_str = end_time_options[0]

                    end_time_str = st.selectbox(
                        "🕐 Hora de Fim",
                        options=end_time_options,
                        index=end_time_options.index(st.session_state.custom_end_time_str),
                        key="custom_end_time_select"
                    )
                    if end_time_str != st.session_state.custom_end_time_str:
                        st.session_state.custom_end_time_str = end_time_str
            else:
                start_time_str = None
                end_time_str = None

            # 4) Em colunas: Equipe (coluna 1) e Motorista (coluna 2)
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                equipe_opcoes = sorted(list(st.session_state.df_usuarios["NOME"])) if "df_usuarios" in st.session_state else []
                equipe_selecionada = st.multiselect("👥 Equipe (participantes)", options=equipe_opcoes, key="custom_equipe", placeholder="Selecione os participantes")

            with col_e2:
                motorista = st.text_input("🚗 Motorista", key="custom_motorista", placeholder="Digite o nome do motorista")

            # 5) Localização
            location = st.text_input("📍 Localização", value="", placeholder="Endereço ou local do evento")

            # Montar descrição incluindo Equipe e Motorista
            equipe_str = "\n".join([f"• {n}" for n in equipe_selecionada]) if equipe_selecionada else "—"
            motorista_str = motorista if motorista else "—"
            description = (description_base or "").strip()
            description += "\n\n👥 Equipe:\n" + (equipe_str if equipe_selecionada else "—")
            description += f"\n\n🚗 Motorista:\n" + (motorista_str if motorista_str else "—")
        
        
        # Botões de ação
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submitted = st.button("✅ Criar Evento", use_container_width=True, type='primary')
        
        with col_cancel:
            cancelled = st.button("❌ Cancelar", use_container_width=True, type='primary')
        
        if submitted:
            mensagem = st.toast("Validando evento...", duration="short")
            time.sleep(0.5)
            if not title:
                st.error("❌ O título do evento é obrigatório!")
                return
            
            # Validar horários
            if not all_day:
                is_valid, message = validate_time_selection(start_date, start_time_str, end_date, end_time_str)
                
                if not is_valid:
                    st.error(message)
                    return
                
                if message:
                    st.toast(message, duration="short")
            
            # Dados base do evento
            event_data = {
                'title': title,
                'description': description,
                'location': location,
                'start_date': start_date,
                'end_date': end_date,
                'start_time': start_time_str if not all_day else None,
                'end_time': end_time_str if not all_day else None,
                'all_day': all_day,
                'colorId': selected_color_id,  # Adicionar cor customizada
            }
            
            # Criar evento(s)
            if not all_day and end_date > start_date:
                total_days = (end_date - start_date).days + 1
                with st.spinner(f"Criando {total_days} eventos diários de {start_time_str} às {end_time_str}..."):
                    created_all = True
                    current_date = start_date
                    while current_date <= end_date:
                        single_event_data = dict(event_data)
                        single_event_data['start_date'] = current_date
                        single_event_data['end_date'] = current_date
                        single_event_data['start_time'] = start_time_str
                        single_event_data['end_time'] = end_time_str
                        ev = create_calendar_event(single_event_data)
                        if not ev:
                            created_all = False
                        current_date += timedelta(days=1)
                if created_all:
                    st.toast("✅ Eventos criados com sucesso!")
                    time.sleep(0.5)

                    # Limpar cache e estado
                    st.session_state.google_calendar_loaded = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state.calendar_events
                    # Limpar estados temporários
                    for key in ['show_create_event', 'selected_date', 'selected_end_date',
                                'agenda_start_time_str', 'agenda_end_time_str',
                                'custom_start_time_str', 'custom_end_time_str',
                                'participantes_emails', 'participantes_nomes', 'event_color_selector']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("❌ Erro ao criar um ou mais eventos")
            else:
                created_event = create_calendar_event(event_data)   
                
                if created_event:
                    
                    mensagem.toast("Criando evento...", duration="short")
                    time.sleep(1)
                    
                    st.session_state.google_calendar_loaded = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state.calendar_events
                    
                    mensagem.toast("Criando evento....", duration="short")

                    for key in ['show_create_event', 'selected_date', 'selected_end_date',
                                'agenda_start_time_str', 'agenda_end_time_str',
                                'custom_start_time_str', 'custom_end_time_str',
                                'absence_start_time_str', 'absence_end_time_str',
                                'participantes_emails', 'participantes_nomes', 'event_color_selector']:
                        if key in st.session_state:
                            del st.session_state[key]

                    mensagem.toast("✅ Evento Criado com Sucesso!", duration="short")

                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Erro ao criar evento")
        
        if cancelled:
            mensagem = st.toast("Cancelando...", duration="short")
            time.sleep(1)
            
            st.session_state.show_create_event = False
            for key in ['selected_date', 'selected_end_date',
                        'agenda_start_time_str', 'agenda_end_time_str',
                        'custom_start_time_str', 'custom_end_time_str',
                        'participantes_emails', 'participantes_nomes', 'event_color_selector']:
                if key in st.session_state:
                    del st.session_state[key]

            time.sleep(1)
            mensagem.toast("❌ Operação cancelada!", duration="short")
            time.sleep(0.5)
            st.rerun()

# ==================== FUNÇÃO PRINCIPAL ====================

def func_agenda_rav():
    """Sistema completo de Agenda de Governança."""
    
    # Inicializar eventos
    if 'calendar_events' not in st.session_state:
        st.session_state.calendar_events = []
    
    if 'google_calendar_loaded' not in st.session_state:
        st.session_state.google_calendar_loaded = False
    
    # Carregar eventos do Google Calendar (apenas uma vez)

    if not st.session_state.google_calendar_loaded:
        try:
            with st.status("Carregando eventos do Google Calendar...", expanded=False):
                # Eventos normais
                api_events = get_calendar_events(months_back=12)
                if api_events:
                    st.session_state.calendar_events.extend(api_events)
                
                # Feriados
                holidays = get_holidays_from_google(months_back=12)
                if holidays:
                    st.session_state.calendar_events.extend(holidays)
                    st.toast(f"✅ {len(holidays)} feriados carregados!", duration="short")
            
            st.session_state.google_calendar_loaded = True
        except Exception as e:
            st.error(f"Erro ao carregar eventos: {e}")
    
    # Formatar eventos
    formatted_events = [format_event_for_calendar(event) for event in st.session_state.calendar_events]
    
    # Renderizar calendário
    calendar_component = calendar(
        events=formatted_events,
        options=get_calendar_options(),
        custom_css=get_custom_css(),
        key='agenda_governanca_calendar'
    )
    
    # Processar interações
    if calendar_component:
        callback = calendar_component.get("callback")
        
        if callback == "dateClick":
            date_clicked = calendar_component["dateClick"]["date"]
            clicked_date = datetime.fromisoformat(date_clicked.replace('Z', '+00:00')).date()
            current_datetime = datetime.now()
            
            st.write("---")
            
            # Aviso se for data passada
            if clicked_date < current_datetime.date():
                st.toast(f"Data passada selecionada: {clicked_date.strftime('%d/%m/%Y')}", duration="short")
            
            if clicked_date > current_datetime.date():
                st.toast(f"Data futura selecionada: {clicked_date.strftime('%d/%m/%Y')}", duration="short")
            
            if clicked_date == current_datetime.date():
                st.toast(f"Data atual selecionada: {clicked_date.strftime('%d/%m/%Y')}", duration="short")
            
            data_formatada = clicked_date.strftime('%d/%m/%Y')
            if st.button(f"➕ Criar Evento para: {data_formatada}", key=f"create_event_{date_clicked}", type="primary", use_container_width=True):
                st.session_state.selected_date = date_clicked.split('T')[0]
                st.session_state.show_create_event = True
                st.rerun()
        
        elif callback == "eventClick":
            event = calendar_component["eventClick"]["event"]
            show_event_details(event)
        
        elif callback == "select":
            selection = calendar_component["select"]
            start_dt = datetime.fromisoformat(selection['start'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(selection['end'].replace('Z', '+00:00')) - timedelta(days=1)
            st.info(f"📅 Período selecionado: {start_dt.strftime('%d/%m/%Y')} até {end_dt.strftime('%d/%m/%Y')}")
            
            if st.button("➕ Criar Evento no Período Selecionado", key=f"create_period_{selection['start']}"):
                st.session_state.show_create_event = True
                st.session_state.selected_date = selection['start'].split('T')[0]
                end_date = datetime.strptime(selection['end'].split('T')[0], "%Y-%m-%d").date() - timedelta(days=1)
                st.session_state.selected_end_date = end_date.strftime("%Y-%m-%d")
                st.rerun()
    
    # Mostrar formulário de criação se necessário
    if st.session_state.get('show_create_event', False):
        show_create_event_form()
    
    return calendar_component   