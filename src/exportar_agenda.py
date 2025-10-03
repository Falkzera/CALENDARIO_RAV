import streamlit as st
import base64
from datetime import datetime
import calendar as pycalendar
from typing import List, Dict, Optional

from src.google_agenda import get_calendar_events
from src.google_sheets import get_dados_usuarios
from src.agenda import COLOR_MAPPING

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

def _format_event_details(e: Dict) -> Dict[str, str]:
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

    return {
        "title": e.get("title", "—"),
        "date": date_fmt,
        "date_end": date_end_fmt,
        "period": period,
        "description": (e.get("description", "") or "—").replace("\n", "<br>"),
        "location": ext.get("location", "—") or "—",
        "attendees": ", ".join([a for a in ext.get("attendees", []) if a]) or "—",
        "link": ext.get("html_link", ""),
        "color": COLOR_MAPPING.get(e.get("title", "").lower(), "#3064ad"),
    }


def _build_month_html(events: List[Dict], month: int, year: int, df_usuarios) -> str:
    """Cria HTML estilizado (similar ao e-mail) da agenda mensal, em formato horizontal."""
    logo_b64 = _load_logo_base64()
    month_name = pycalendar.month_name[month].capitalize()

    # Resumo de usuários
    resumo_usuarios = []
    try:
        if df_usuarios is not None and hasattr(df_usuarios, "iterrows"):
            total_users = len(df_usuarios)
            resumo_usuarios.append(f"Total de usuários: {total_users}")
            # Mostrar até 12 usuários (nome e e-mail quando disponível)
            nomes_col = "NOME"
            possiveis_cols_email = ["E-MAIL", "EMAIL", "E_mail", "E-mail", "E Mail", "email"]
            count = 0
            for _, row in df_usuarios.iterrows():
                nome = row.get(nomes_col, "—")
                email = next((str(row[c]).strip() for c in possiveis_cols_email if c in row and str(row[c]).strip()), "—")
                resumo_usuarios.append(f"• {nome} — {email}")
                count += 1
                if count >= 12:
                    break
        else:
            resumo_usuarios.append("Dados de usuários indisponíveis.")
    except Exception:
        resumo_usuarios.append("Falha ao carregar resumo de usuários.")

    # Resumo da Equipe: apenas usuários que estão em algum evento
    resumo_equipe = []
    try:
        # Extrai participantes exclusivamente do bloco "👥 Equipe:" na descrição dos eventos
        participantes_set = set()
        for e in events:
            ext = e.get("extendedProps", {})
            desc = e.get("description") or ext.get("description") or ""
            for nome in _extract_participants_from_description(desc):
                nome_norm = _normalize_name(nome)
                if nome_norm:
                    participantes_set.add(nome_norm)

        # Cruzar com df_usuarios para exibir nomes oficiais; priorizar correspondência por nome
        if df_usuarios is not None and hasattr(df_usuarios, "iterrows"):
            nomes_col = "NOME"
            equipe_list = []
            for _, row in df_usuarios.iterrows():
                nome = str(row.get(nomes_col, "")).strip()
                nome_norm = _normalize_name(nome) if nome else ""
                if nome_norm and nome_norm in participantes_set:
                    equipe_list.append(f"• {nome or '—'}")
            if equipe_list:
                resumo_equipe.append(f"Membros com eventos: {len(equipe_list)}")
                resumo_equipe.extend(equipe_list)
            else:
                resumo_equipe.append("Nenhum membro com eventos neste mês.")
        else:
            # Sem df_usuarios, mostrar nomes detectados diretamente da descrição
            if participantes_set:
                resumo_equipe.append(f"Participantes em eventos: {len(participantes_set)}")
                for p in sorted(participantes_set):
                    resumo_equipe.append(f"• {p}")
            else:
                resumo_equipe.append("Dados de equipe indisponíveis.")
    except Exception:
        resumo_equipe.append("Falha ao carregar resumo da equipe.")

    legend_items = []
    for nome, cor in COLOR_MAPPING.items():
        legend_items.append(f"<div style=\"display:flex; align-items:center; margin-bottom:6px;\"><span style=\"width:14px; height:14px; background:{cor}; display:inline-block; border-radius:3px; margin-right:8px;\"></span><span style=\"font-size:12px; color:#555; text-transform:capitalize;\">{nome}</span></div>")

    # Construção dos cards de eventos
    eventos_html = []
    for e in events:
        d = _format_event_details(e)
        data_range = d["date"] + (f" a {d['date_end']}" if d["date_end"] and d["date_end"] != d["date"] else "")
        link_html = f"<a href=\"{d['link']}\" style=\"color:#3064ad; text-decoration:none;\" target=\"_blank\">Abrir no Google Calendar</a>" if d["link"] else ""
        eventos_html.append(f"""
        <div style=\"border-left:6px solid {d['color']}; background:#ffffff; border:1px solid #e5ecf6; border-radius:10px; padding:14px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.04);\">
            <div style=\"display:flex; justify-content:space-between; align-items:center;\">
                <h4 style=\"margin:0; font-size:16px; color:#222;\">{d['title']}</h4>
                <span style=\"font-size:12px; color:#666;\">{data_range}</span>
            </div>
            <p style=\"margin:6px 0 0; font-size:12px; color:#444;\"><strong>Horário:</strong> {d['period']}</p>
            <p style=\"margin:6px 0 0; font-size:12px; color:#444;\"><strong>Local:</strong> {d['location']}</p>
            <div style=\"margin:8px 0 0;\">
                <p style=\"margin:0 0 6px; font-size:12px; color:#444;\"><strong>Descrição:</strong></p>
                <div style=\"background:#f9fbff; border:1px solid #e5ecf6; border-radius:8px; padding:10px; font-size:12px; color:#333;\">{d['description']}</div>
            </div>
            <p style=\"margin:8px 0 0; font-size:12px; color:#444;\"><strong>Participantes:</strong> {d['attendees']}</p>
            <div style=\"margin-top:8px;\">{link_html}</div>
        </div>
        """)

    eventos_html_str = "\n".join(eventos_html) or "<p style=\"margin:0; font-size:14px; color:#666;\">Nenhum evento para este mês.</p>"

    # Cabeçalho com logo
    logo_html = f"<img src=\"data:image/png;base64,{logo_b64}\" alt=\"Logo\" style=\"height:42px;\"/>" if logo_b64 else ""

    # CSS para A4 landscape e estilos
    css = f"""
    <style>
    @page {{ size: A4 landscape; margin: 12mm; }}
    body {{ margin:0; padding:0; background:#f6f8fb; font-family: Arial, Helvetica, sans-serif; color:#333; }}
    .wrapper {{ width: 1120px; margin: 0 auto; }}
    .card {{ background:#ffffff; border-radius:12px; box-shadow:0 4px 18px rgba(0,0,0,0.08); overflow:hidden; }}
    .header {{ background: linear-gradient(135deg, #3064ad 0%, #4a7bc8 100%); color:#fff; padding:16px 20px; display:flex; align-items:center; justify-content:space-between; }}
    .header .title {{ margin:0; font-size:20px; font-weight:700; }}
    .header .date {{ margin:0; font-size:12px; opacity:0.9; }}
    .content {{ display:grid; grid-template-columns: 3fr 1fr; gap:18px; padding:18px 20px; }}
    .events {{ padding-right:8px; }}
    .sidebar {{ background:#f9fbff; border:1px solid #e5ecf6; border-radius:10px; padding:14px; }}
    .sidebar h4 {{ margin:0 0 10px; font-size:14px; color:#222; }}
    .legend {{ margin-top:10px; }}
    .users {{ margin-top:16px; }}
    .footer {{ background:#f1f5fb; color:#667; padding:12px 20px; font-size:12px; }}
    /* Calendário mensal estilizado */
    .month-calendar {{ margin: 18px 20px; border:1px solid #e5ecf6; border-radius:12px; background:#fff; padding:12px; }}
    .calendar-row {{ display:grid; grid-template-columns: repeat(7, 1fr); gap:8px; margin-bottom:8px; }}
    .calendar-row.header {{ margin-bottom:12px; }}
    .day-header {{ text-align:center; font-weight:600; font-size:12px; color:#3064ad; padding:6px 0; background:#f1f5fb; border-radius:8px; border:1px solid #e5ecf6; }}
    .day-cell {{ min-height:90px; background:#f9fbff; border:1px solid #e5ecf6; border-radius:10px; padding:8px; position:relative; }}
    .day-cell.empty {{ background:transparent; border-color:transparent; }}
    .day-number {{ position:absolute; top:6px; right:8px; font-size:12px; color:#667; }}
    .event-pill {{ }}
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
            pill = f"<div class=\"event-pill\" style=\"border-left:4px solid {d['color']}; background:#f9fbff; border:1px solid #e5ecf6; border-radius:6px; padding:4px 6px; margin:4px 0; font-size:11px; color:#333;\">{d['title']}{' — ' + d['period'] if d['period'] and d['period'] != 'Dia inteiro' else ''}</div>"
            events_by_day.setdefault(day, []).append(pill)

    pycalendar.setfirstweekday(pycalendar.SUNDAY)
    weeks = pycalendar.monthcalendar(year, month)
    weekdays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    header_html = "".join([f"<div class=\"day-header\">{w}</div>" for w in weekdays])
    calendar_rows = [f"<div class=\"calendar-row header\">{header_html}</div>"]
    for wk in weeks:
        cells = []
        for d in wk:
            if d == 0:
                cells.append("<div class=\"day-cell empty\"></div>")
            else:
                day_events = "".join(events_by_day.get(d, []))
                cells.append(f"<div class=\"day-cell\"><div class=\"day-number\">{d}</div>{day_events}</div>")
        calendar_rows.append(f"<div class=\"calendar-row\">{''.join(cells)}</div>")
    calendar_html = f"<div class=\"month-calendar\">{''.join(calendar_rows)}</div>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset=\"utf-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
      <title>Agenda do mês - {month_name}/{year}</title>
      {css}
    </head>
    <body>
      <div class=\"wrapper\">
        <div class=\"card\">
          <div class=\"header\">
            <div style=\"display:flex; align-items:center; gap:12px;\">{logo_html}<h2 class=\"title\">Agenda do mês — {month_name} / {year}</h2></div>
            <p class=\"date\">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
          </div>
          <div class=\"content\">
            <div class=\"events\">
              {eventos_html_str}
            </div>
            <div class=\"sidebar\">
              <h4>Legenda</h4>
              <div class=\"legend\">{''.join(legend_items)}</div>
              <div class=\"users\">
                <h4>Resumo da Equipe</h4>
                <div style=\"font-size:12px; color:#555; line-height:1.5;\">{('<br>'.join(resumo_equipe))}</div>
              </div>
            </div>
          </div>
          <div style=\"padding: 0 20px 20px;\">
            <h3 style=\"margin:12px 0 8px; font-size:16px; color:#222; text-align:center;\">Calendário mensal</h3>
            {calendar_html}
          </div>
          <div class=\"footer\">
            <p style=\"margin:0;\">Documento gerado automaticamente a partir do Google Calendar.</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return html


def _convert_html_to_pdf_bytes(html: str) -> Optional[bytes]:
    """Tenta converter HTML em PDF usando bibliotecas disponíveis (WeasyPrint ou pdfkit)."""
    # Primeiro: WeasyPrint (preferível, sem binários externos)
    try:
        from weasyprint import HTML, CSS  # type: ignore
        pdf_bytes = HTML(string=html, base_url=".").write_pdf(stylesheets=[])
        return pdf_bytes
    except Exception:
        pass

    # Segundo: pdfkit (requer wkhtmltopdf instalado no sistema)
    try:
        import pdfkit  # type: ignore
        pdf_bytes = pdfkit.from_string(html, False)
        return pdf_bytes
    except Exception:
        pass

    return None

def render_export_view():
    """Renderiza UI para exportar a agenda do mês em PDF (horizontal)."""
    st.subheader("Exportar agenda do mês (PDF)")

    # Seleção do mês/ano
    col1, col2 = st.columns([2, 1])
    with col1:
        month = st.selectbox("Mês", options=list(range(1, 13)), format_func=lambda m: pycalendar.month_name[m].capitalize(), index=datetime.now().month - 1)
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
    with st.expander("Pré-visualização", expanded=False):
        st.components.v1.html(html, height=600, scrolling=True)

    # Gerar PDF
    if st.button("Gerar PDF", type="primary"):
        pdf_bytes = _convert_html_to_pdf_bytes(html)
        if pdf_bytes:
            st.success("PDF gerado com sucesso!")
            st.download_button(
                label="Baixar PDF",
                data=pdf_bytes,
                file_name=f"agenda_{year}_{month:02d}.pdf",
                mime="application/pdf",
            )
        else:
            st.warning("Não foi possível converter automaticamente para PDF neste ambiente.")
            st.download_button(
                label="Baixar como HTML (imprima em PDF pelo navegador)",
                data=html,
                file_name=f"agenda_{year}_{month:02d}.html",
                mime="text/html",
            )
            st.info("Dica: Abra o HTML baixado no navegador e use Imprimir > Salvar como PDF (paisagem).")