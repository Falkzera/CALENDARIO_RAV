import streamlit as st
import base64
from datetime import datetime
import calendar as pycalendar
from typing import List, Dict, Optional

from src.google_agenda import get_calendar_events
from src.google_sheets import get_dados_usuarios
from utils.utils import titulos_pagina

# Mapeamento de colorId do Google para HEX (mesma paleta do seu app)
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
DEFAULT_COLOR_HEX = "#3064ad"

# ==================== UTILITÁRIOS ====================

def _load_logo_base64() -> Optional[str]:
    """Carrega a logo em base64 para embutir no HTML/PDF (evita problemas de caminho)."""
    possible_paths = [
        "static/rav.png",
        "assets/image/rav.png",
    ]
    for p in possible_paths:
        try:
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            continue
    return None

def _filter_events_by_month(events: List[Dict], month: int, year: int) -> List[Dict]:
    """Filtra eventos pelo mês/ano do início com tratamento seguro para valores None e strings inválidas."""
    filtered = []
    for e in events:
        start_val = e.get("start")
        if not isinstance(start_val, str):
            continue
        start_str = start_val.strip()
        if not start_str or start_str.lower() == "none":
            continue
        dt = None
        # Tenta formatos comuns
        try:
            dt = datetime.strptime(start_str, "%Y-%m-%d")
        except Exception:
            try:
                dt = datetime.fromisoformat(start_str)
            except Exception:
                dt = None
        if dt and dt.month == month and dt.year == year:
            filtered.append(e)
    return filtered

def _get_event_color(event: Dict) -> str:
    """Determina a cor do evento pela colorId do Google (mesma lógica do calendário principal)."""
    # 1) Tenta pegar colorId do evento (top-level ou extendedProps)
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

def _format_event_details(e: Dict) -> Dict[str, str]:
    """Formata detalhes do evento para exibição."""
    ext = e.get("extendedProps", {}) or {}
    start_val = e.get("start")
    end_val = e.get("end")
    start_time = ext.get("start_time")
    end_time = ext.get("end_time")
    is_all_day = not bool(start_time)
    period = "Dia inteiro" if is_all_day else f"{start_time or '--'} - {end_time or '--'}"

    def fmt_date_safe(s: Optional[str]) -> Optional[str]:
        if not s or (isinstance(s, str) and s.strip().lower() == "none"):
            return None
        s = s.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
            except Exception:
                continue
        try:
            return datetime.fromisoformat(s).strftime("%d/%m/%Y")
        except Exception:
            return None

    date_fmt = fmt_date_safe(start_val if isinstance(start_val, str) else None) or "—"
    date_end_fmt = fmt_date_safe(end_val if isinstance(end_val, str) else None) or ""

    # Usa a mesma função de cor do calendário principal
    color = _get_event_color(e)

    return {
        "title": e.get("title", "—"),
        "date": date_fmt,
        "date_end": date_end_fmt,
        "period": period,
        "description": (e.get("description", "") or "—").replace("\n", "<br>"),
        "location": ext.get("location", "—") or "—",
        "attendees": ", ".join([a for a in ext.get("attendees", []) if a]) or "—",
        "link": ext.get("html_link", ""),
        "color": color,
    }

def _build_legend_html() -> str:
    """Constrói HTML da legenda de cores baseado nas cores do Google Calendar."""
    legend_items = []
    for color_id, info in GOOGLE_EVENT_COLORS.items():
        legend_items.append(
            f'<div style="display:flex; align-items:center; margin-bottom:6px;">'
            f'<span style="width:14px; height:14px; background:{info["hex"]}; display:inline-block; border-radius:3px; margin-right:8px;"></span>'
            f'<span style="font-size:12px; color:#555;">{info["name"]}</span>'
            f'</div>'
        )
    return ''.join(legend_items)

def _build_month_html(events: List[Dict], month: int, year: int, df_usuarios) -> str:
    """Cria HTML estilizado (similar ao e-mail) da agenda mensal, em formato horizontal."""
    logo_b64 = _load_logo_base64()
    month_name = pycalendar.month_name[month].capitalize()

    # Legenda de cores
    legend_html = _build_legend_html()

    # Construção dos cards de eventos
    eventos_html = []
    for e in events:
        d = _format_event_details(e)
        data_range = d["date"] + (f" a {d['date_end']}" if d["date_end"] and d["date_end"] != d["date"] else "")
        link_html = f'<a href="{d["link"]}" style="color:#3064ad; text-decoration:none;" target="_blank">Abrir no Google Calendar</a>' if d["link"] else ""
        eventos_html.append(f"""
        <div style="border-left:6px solid {d['color']}; background:#ffffff; border:1px solid #e5ecf6; border-radius:10px; padding:14px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; font-size:16px; color:#222;">{d['title']}</h4>
                <span style="font-size:12px; color:#666;">{data_range}</span>
            </div>
            <p style="margin:6px 0 0; font-size:12px; color:#444;"><strong>Horário:</strong> {d['period']}</p>
            <p style="margin:6px 0 0; font-size:12px; color:#444;"><strong>Local:</strong> {d['location']}</p>
            <div style="margin:8px 0 0;">
                <p style="margin:0 0 6px; font-size:12px; color:#444;"><strong>Descrição:</strong></p>
                <div style="background:#f9fbff; border:1px solid #e5ecf6; border-radius:8px; padding:10px; font-size:12px; color:#333;">{d['description']}</div>
            </div>
            <div style="margin-top:8px;">{link_html}</div>
        </div>
        """)

    eventos_html_str = "\n".join(eventos_html) or '<p style="margin:0; font-size:14px; color:#666;">Nenhum evento para este mês.</p>'

    # Cabeçalho com logo
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Logo" style="height:42px;"/>' if logo_b64 else ""

    # CSS para A4 landscape e estilos
    css = """
    <style>
    @page { size: A4 landscape; margin: 12mm; }
    body { margin:0; padding:0; background:#f6f8fb; font-family: Arial, Helvetica, sans-serif; color:#333; }
    .wrapper { width: 1120px; margin: 0 auto; }
    .card { background:#ffffff; border-radius:12px; box-shadow:0 4px 18px rgba(0,0,0,0.08); overflow:hidden; }
    .header { background: linear-gradient(135deg, #3064ad 0%, #4a7bc8 100%); color:#fff; padding:16px 20px; display:flex; align-items:center; justify-content:space-between; }
    .header .title { margin:0; font-size:20px; font-weight:700; }
    .header .date { margin:0; font-size:12px; opacity:0.9; }
    .content { display:grid; grid-template-columns: 3fr 1fr; gap:18px; padding:18px 20px; }
    .events { padding-right:8px; }
    .sidebar { background:#f9fbff; border:1px solid #e5ecf6; border-radius:10px; padding:14px; }
    .sidebar h4 { margin:0 0 10px; font-size:14px; color:#222; }
    .legend { margin-top:10px; }
    .users { margin-top:16px; }
    .footer { background:#f1f5fb; color:#667; padding:12px 20px; font-size:12px; }
    /* Calendário mensal estilizado */
    .month-calendar { margin: 18px 20px; border:1px solid #e5ecf6; border-radius:12px; background:#fff; padding:12px; }
    .calendar-row { display:grid; grid-template-columns: repeat(7, 1fr); gap:8px; margin-bottom:8px; }
    .calendar-row.header { margin-bottom:12px; }
    .day-header { text-align:center; font-weight:600; font-size:12px; color:#3064ad; padding:6px 0; background:#f1f5fb; border-radius:8px; border:1px solid #e5ecf6; }
    .day-cell { min-height:120px; background:#f9fbff; border:1px solid #d5e2f3; border-radius:12px; padding:28px 10px 10px 10px; position:relative; transition:box-shadow .15s ease, transform .15s ease; }
    .day-cell.has-events { background:#ffffff; box-shadow:0 2px 10px rgba(48,100,173,0.08); border-color:#c8d8ee; }
    .day-cell.empty { background:transparent; border-color:transparent; }
    .day-number { position:absolute; top:6px; right:8px; font-size:12px; color:#667; }
    .event-pill { display:flex; align-items:center; gap:6px; border-left:6px solid var(--event-color, #3064ad); background:#f1f6ff; border:1px solid #dbe7ff; border-radius:8px; padding:6px 8px; margin:6px 0; font-size:12px; color:#222; box-shadow:0 1px 2px rgba(0,0,0,0.04); }
    .event-pill:hover { transform: translateY(-1px); box-shadow:0 2px 6px rgba(0,0,0,0.08); }
    .event-dot { width:8px; height:8px; border-radius:50%; background: var(--event-color, #3064ad); flex-shrink:0; }
    .event-title { font-weight:600; }
    .event-time { background:#e9effd; color:#1f3b7d; border:1px solid #d5e2f3; border-radius:6px; padding:2px 6px; font-size:11px; }
    </style>
    """

    # Construção do calendário mensal (grid)
    def _parse_date_to_date(s: Optional[str]) -> Optional[datetime]:
        if not s or not isinstance(s, str):
            return None
        ss = s.strip()
        if not ss or ss.lower() == "none":
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(ss, fmt)
            except Exception:
                continue
        try:
            return datetime.fromisoformat(ss)
        except Exception:
            return None

    events_by_day = {}
    for e in events:
        dt = _parse_date_to_date(e.get("start"))
        if dt and dt.month == month and dt.year == year:
            day = dt.day
            d = _format_event_details(e)
            pill = f'<div class="event-pill" style="--event-color: {d["color"]}; border-left:6px solid {d["color"]};"><span class="event-dot"></span><span class="event-title">{d["title"]}</span>{("<span class=\"event-time\">" + d["period"] + "</span>") if d["period"] and d["period"] != "Dia inteiro" else ""}</div>'
            events_by_day.setdefault(day, []).append(pill)

    pycalendar.setfirstweekday(pycalendar.SUNDAY)
    weeks = pycalendar.monthcalendar(year, month)
    weekdays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    header_html = "".join([f'<div class="day-header">{w}</div>' for w in weekdays])
    calendar_rows = [f'<div class="calendar-row header">{header_html}</div>']
    for wk in weeks:
        cells = []
        for d in wk:
            if d == 0:
                cells.append('<div class="day-cell empty"></div>')
            else:
                day_list = events_by_day.get(d, [])
                day_events = "".join(day_list)
                cell_class = "day-cell has-events" if len(day_list) > 0 else "day-cell"
                cells.append(f'<div class="{cell_class}"><div class="day-number">{d}</div>{day_events}</div>')
        calendar_rows.append(f'<div class="calendar-row">{"".join(cells)}</div>')
    calendar_html = f'<div class="month-calendar">{"".join(calendar_rows)}</div>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Agenda do mês - {month_name} {year}</title>
      {css}
    </head>
    <body>
      <div class="wrapper">
        <div class="card">
          <div class="header">
            <div style="display:flex; align-items:center; gap:12px;">{logo_html}<h2 class="title">Agenda do mês — {month_name} / {year}</h2></div>
            <p class="date">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
          </div>
          <div class="content">
            <div class="events">
              {eventos_html_str}
            </div>
            <div class="sidebar">
              <h4>Legenda de Cores</h4>
              <div class="legend">{legend_html}</div>
              <div class="users">
              </div>
            </div>
          </div>
          <div style="padding: 0 20px 20px;">
            <h3 style="margin:12px 0 8px; font-size:16px; color:#222; text-align:center;">Calendário Mensal</h3>
            {calendar_html}
          </div>
          <div class="footer">
            <p style="margin:0;">Documento gerado automaticamente a partir da distribuição da Agenda.</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return html

def render_export_view():
    """Renderiza UI para exportar a agenda do mês em PDF (horizontal)."""
    titulos_pagina("Resumo Mensal de Eventos", font_size="2.0em")

    # Seleção do mês/ano
    col1, col2 = st.columns([2, 1])
    with col1:
        month = st.selectbox("Mês", options=list(range(1, 13)), format_func=lambda m: [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ][m - 1], index=datetime.now().month - 1)
    with col2:
        year = st.number_input("Ano", min_value=2020, max_value=2100, value=datetime.now().year, step=1)

    # Carregar dados
    with st.spinner("Carregando eventos do Google Calendar..."):
        events = get_calendar_events(months_back=12)  # coletar período amplo
        eventos_mes = _filter_events_by_month(events, month, year)
    df_usuarios = get_dados_usuarios()

    # Construir HTML
    html = _build_month_html(eventos_mes, month, year, df_usuarios)

    # Pré-visualização (HTML)
    with st.expander("Pré-visualização", expanded=True):
        st.components.v1.html(html, height=900, scrolling=True)
        
    st.write("---")
    st.download_button(
            label="📥 Baixar como HTML",
            data=html,
            use_container_width=True,
            file_name=f"agenda_{year}_{month:02d}.html",
            mime="text/html",
            type="primary")