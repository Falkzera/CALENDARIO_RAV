import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime
from typing import List, Optional

def _get_email_credentials() -> tuple[Optional[str], Optional[str]]:
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        return sender, str(password).replace(" ", "")
    except Exception:
        return None, None

def _format_event_datetime(event_data: dict) -> tuple[str, str, str]:
    """Retorna datas e período formatados para exibição."""
    start_date = event_data.get("start_date")
    end_date = event_data.get("end_date", start_date)
    all_day = bool(event_data.get("all_day", False))
    start_time = event_data.get("start_time")
    end_time = event_data.get("end_time")

    try:
        start_str = start_date.strftime("%d/%m/%Y") if hasattr(start_date, "strftime") else str(start_date)
        end_str = end_date.strftime("%d/%m/%Y") if hasattr(end_date, "strftime") else str(end_date)
    except Exception:
        start_str = str(start_date)
        end_str = str(end_date)

    if all_day or not start_time or not end_time:
        period_str = "Dia inteiro"
    else:
        period_str = f"{start_time} - {end_time}"

    return start_str, end_str, period_str


def _resolve_recipients(df_usuarios, equipe_nomes: List[str]) -> List[str]:
    """Obtém os e-mails dos usuários selecionados a partir de df_usuarios."""
    emails: List[str] = []
    if df_usuarios is None or not hasattr(df_usuarios, "columns"):
        return emails

    nome_col = "NOME"
    possiveis_cols_email = ["E-MAIL", "EMAIL", "E_mail", "E-mail", "E Mail", "email"]

    try:
        for nome in equipe_nomes or []:
            try:
                matches = df_usuarios[df_usuarios[nome_col] == nome]
            except Exception:
                matches = []
            for _, row in getattr(matches, "iterrows", lambda: [])():
                found = None
                for col in possiveis_cols_email:
                    if col in row and str(row[col]).strip():
                        found = str(row[col]).strip()
                        break
                if found:
                    emails.append(found)
    except Exception:
        pass

    # Remover duplicados preservando ordem
    deduped = list(dict.fromkeys([e for e in emails if e]))
    return deduped


def _build_email_subject(event_data: dict) -> str:
    titulo = event_data.get("title", "Evento")
    return f"Convite: {titulo}"


def _build_email_text(event_data: dict, equipe_nomes: List[str], motorista: Optional[str], event_link: Optional[str]) -> str:
    start_str, end_str, period_str = _format_event_datetime(event_data)
    titulo = event_data.get("title", "Evento")
    descricao = event_data.get("description", "")
    local = event_data.get("location", "")

    lines = [
        f"Convite: {titulo}",
        "",
        f"Data: {start_str}" + (f" a {end_str}" if end_str != start_str else ""),
        f"Horário: {period_str}",
        f"Local: {local}",
        "",
        "Descrição:",
        descricao,
        "",
        "Participantes:",
        *[f"- {n}" for n in (equipe_nomes or [])],
        f"Motorista: {motorista or '—'}",
    ]
    if event_link:
        lines += ["", f"Link do evento: {event_link}"]

    return "\n".join(lines)


def _build_email_html(event_data: dict, equipe_nomes: List[str], motorista: Optional[str], event_link: Optional[str]) -> str:
    start_str, end_str, period_str = _format_event_datetime(event_data)
    titulo = event_data.get("title", "Evento")
    descricao = (event_data.get("description", "") or "").replace("\n", "<br>")
    local = event_data.get("location", "")
    participantes_html = "".join([f"<li>{n}</li>" for n in (equipe_nomes or [])]) or "<li>—</li>"

    link_html = f"<a href=\"{event_link}\" style=\"color:#3064ad; text-decoration:none;\">Abrir no Google Calendar</a>" if event_link else ""

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Convite de Evento</title>
</head>
<body style=\"margin:0; padding:0; background:#f6f8fb; font-family:Arial, Helvetica, sans-serif; color:#333;\">
  <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"background:#f6f8fb; padding:24px 0;\">
    <tr>
      <td align=\"center\">
        <table role=\"presentation\" width=\"600\" cellspacing=\"0\" cellpadding=\"0\" style=\"background:#ffffff; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.08); overflow:hidden;\">
          <tr>
            <td style=\"background:#3064ad; color:#fff; padding:24px;\">
              <h2 style=\"margin:0; font-size:20px;\">Convite de Evento</h2>
              <p style=\"margin:8px 0 0; font-size:14px; opacity:0.9;\">{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </td>
          </tr>
          <tr>
            <td style=\"padding:24px;\">
              <h3 style=\"margin:0 0 16px; font-size:18px; color:#222;\">{titulo}</h3>
              <p style=\"margin:0 0 8px;\"><strong>Data:</strong> {start_str}{' a ' + end_str if end_str != start_str else ''}</p>
              <p style=\"margin:0 0 8px;\"><strong>Horário:</strong> {period_str}</p>
              <p style=\"margin:0 0 16px;\"><strong>Local:</strong> {local}</p>
              <div style=\"margin:0 0 16px;\">
                <p style=\"margin:0 0 8px;\"><strong>Descrição:</strong></p>
                <div style=\"background:#f9fbff; border:1px solid #e5ecf6; border-radius:8px; padding:12px;\">{descricao or '—'}</div>
              </div>
              <div style=\"margin:0 0 16px;\">
                <p style=\"margin:0 0 8px;\"><strong>Participantes:</strong></p>
                <ul style=\"margin:0; padding-left:18px;\">{participantes_html}</ul>
              </div>
              <p style=\"margin:0 0 8px;\"><strong>Motorista:</strong> {motorista or '—'}</p>
              {link_html}
            </td>
          </tr>
          <tr>
            <td style=\"background:#f1f5fb; color:#667; padding:16px 24px; font-size:12px;\">
              <p style=\"margin:0;\">Este é um e-mail automático. Por favor, não responda.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_event_email_for_event(event_data: dict, equipe_nomes: List[str], motorista: Optional[str], df_usuarios, created_event: Optional[dict] = None) -> bool:
    """Envia e-mail aos usuários selecionados com detalhes do evento.

    Args:
        event_data: Dados do evento conforme utilizados em create_calendar_event
        equipe_nomes: Lista de nomes dos participantes selecionados
        motorista: Nome do motorista selecionado
        df_usuarios: DataFrame com colunas NOME e E-MAIL
        created_event: Evento retornado pela API (para incluir link)
    Returns:
        bool: True se enviado com sucesso para ao menos um destinatário
    """
    try:
        sender, password = _get_email_credentials()
        if not sender or not password:
            print("[EMAIL] REMETENTE/SENHA não configurados em st.secrets.")
            return False

        recipients = _resolve_recipients(df_usuarios, equipe_nomes)
        if not recipients:
            print("[EMAIL] Nenhum destinatário encontrado para os participantes selecionados.")
            return False

        subject = _build_email_subject(event_data)
        event_link = created_event.get("htmlLink") if isinstance(created_event, dict) else None
        text_body = _build_email_text(event_data, equipe_nomes, motorista, event_link)
        html_body = _build_email_html(event_data, equipe_nomes, motorista, event_link)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

        print(f"[EMAIL] E-mail enviado com sucesso para: {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"[EMAIL] Falha ao enviar: {e}")
        return False