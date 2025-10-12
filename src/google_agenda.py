import re
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta

secrets = st.secrets
CREDENTIALS_INFO = secrets['google_credentials2']

def create_calendar_event(event_data, calendar_id='ravsistema@gmail.com'):
    """
    Cria um novo evento no Google Calendar.
    """
    try:        
        service = get_calendar_service()
        
        event = {
            'summary': event_data.get('title', 'Novo Evento'),
            'description': event_data.get('description', ''),
            'location': event_data.get('location', ''),
        }
        
        # aplicar colorId se fornecido
# aplicar colorId se fornecido
        color_id = event_data.get('colorId') or event_data.get('color_id')  # aceita ambos, por segurança
        if color_id:
            event['colorId'] = str(color_id)  # garantir string
        
        start_date = event_data.get('start_date')
        end_date = event_data.get('end_date', start_date)
        start_time = event_data.get('start_time')
        end_time = event_data.get('end_time')
        all_day = event_data.get('all_day', False)
        
        if hasattr(start_date, 'strftime'):
            start_date = start_date.strftime('%Y-%m-%d')
        if hasattr(end_date, 'strftime'):
            end_date = end_date.strftime('%Y-%m-%d')
        
        if not all_day and start_time and end_time:
            event['start'] = {
                'dateTime': f"{start_date}T{start_time}:00",
                'timeZone': 'America/Sao_Paulo',
            }
            event['end'] = {
                'dateTime': f"{end_date}T{end_time}:00",
                'timeZone': 'America/Sao_Paulo',
            }
        else:
            event['start'] = {'date': start_date}
            event['end'] = {'date': end_date}
        
        attendees = event_data.get('attendees', [])
        
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        return created_event
        
    except Exception as e:
        print(f"[DEBUG] Erro ao criar evento: {str(e)}")
        return None

def update_calendar_event(event_id, event_data, calendar_id='ravsistema@gmail.com'):
    """
    Atualiza um evento existente no Google Calendar.
    """
    try:
        service = get_calendar_service()
        
        current_event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        if 'title' in event_data:
            current_event['summary'] = event_data['title']
        if 'description' in event_data:
            current_event['description'] = event_data['description']
        if 'location' in event_data:
            current_event['location'] = event_data['location']
        
        # aplicar colorId se fornecido
# aplicar colorId se fornecido
        color_id = event_data.get('colorId') or event_data.get('color_id')
        if color_id:
            current_event['colorId'] = str(color_id)
        
        if 'start_date' in event_data:
            start_date = event_data['start_date']
            end_date = event_data.get('end_date', start_date)
            start_time = event_data.get('start_time')
            end_time = event_data.get('end_time')
            
            if start_time and end_time:
                current_event['start'] = {
                    'dateTime': f"{start_date}T{start_time}:00",
                    'timeZone': 'America/Sao_Paulo',
                }
                current_event['end'] = {
                    'dateTime': f"{end_date}T{end_time}:00",
                    'timeZone': 'America/Sao_Paulo',
                }
            else:
                current_event['start'] = {'date': start_date}
                current_event['end'] = {'date': end_date}
        
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=current_event
        ).execute()
        
        return updated_event
        
    except Exception as e:
        print(f"[DEBUG] Erro ao atualizar evento: {str(e)}")
        return None

def delete_calendar_event(event_id, calendar_id='ravsistema@gmail.com'):
    """
    Deleta um evento do Google Calendar.
    
    Args:
        event_id (str): ID do evento a ser deletado
        calendar_id (str): ID do calendário
    
    Returns:
        bool: True se deletado com sucesso, False caso contrário
    """
    try:
        service = get_calendar_service()
        
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        return True
        
    except Exception as e:
        print(f"[DEBUG] Erro ao deletar evento: {str(e)}")
        return False

def get_calendar_service():
    """
    Autentica e retorna o serviço do Google Calendar API.
    
    Returns:
        service: Instância autenticada da API do Google Calendar
    """
    credentials = service_account.Credentials.from_service_account_info(
        CREDENTIALS_INFO,
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    return build('calendar', 'v3', credentials=credentials)


def get_calendar_events(calendar_id='ravsistema@gmail.com', max_results=2500, months_back=6):
    """
    Coleta eventos do Google Calendar (passados e futuros).
    
    Args:
        calendar_id (str): ID do calendário (padrão: 'ravsistema@gmail.com')
        max_results (int): Número máximo de eventos a serem retornados (padrão: 2500)
        months_back (int): Quantos meses no passado buscar eventos (padrão: 6)
    
    Returns:
        list: Lista de eventos formatados para uso no calendário
    """
    try:   
        service = get_calendar_service()
        
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=months_back * 30)
        time_min = start_date.replace(microsecond=0).isoformat()
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        
        for event in events:
            title = event.get('summary', 'Sem título')
            description = normalize_html_description(event.get('description', ''))
            
            start = event['start']
            if 'dateTime' in start:
                start_datetime = start['dateTime']
                start_date = start_datetime.split('T')[0]
                start_time = start_datetime.split('T')[1].split('+')[0].split('-')[0].split('Z')[0][:5]
            else:
                start_date = start['date']
                start_time = None
            
            end = event['end']
            if 'dateTime' in end:
                end_datetime = end['dateTime']
                end_date = end_datetime.split('T')[0]
                end_time = end_datetime.split('T')[1].split('+')[0].split('-')[0].split('Z')[0][:5]
            else:
                end_date = end['date']
                end_time = None
            
            formatted_event = {
                'title': title,
                'start': start_date,
                'end': end_date if end_date != start_date else None,
                'description': description,
                'allDay': start_time is None,
                'extendedProps': {
                    'google_event_id': event.get('id', ''),
                    'google_calendar_id': calendar_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'location': event.get('location', ''),
                    'attendees': [attendee.get('email', '') for attendee in event.get('attendees', [])],
                    'creator': event.get('creator', {}).get('email', ''),
                    'organizer': event.get('organizer', {}).get('email', ''),
                    'status': event.get('status', ''),
                    'html_link': event.get('htmlLink', ''),
                    'colorId': event.get('colorId', '')
                }
            }
            
            formatted_events.append(formatted_event)
        
        return formatted_events
        
    except Exception as e:
        print(f"[DEBUG] ERRO na função get_calendar_events: {str(e)}")
        return []

def normalize_html_description(description, for_html_display=True):
    """
    Normaliza descrições HTML removendo tags e preservando quebras de linha.
    Converte HTML para texto limpo mantendo a estrutura visual.
    
    Args:
        description (str): Texto HTML a ser normalizado
        for_html_display (bool): Se True, converte \n para <br> para exibição em HTML
    
    Returns:
        str: Descrição normalizada
    """
    if not description:
        return description
    
    description = description.replace('\\n', '\n')
    description = re.sub(r'<br\s*/?>', '\n', description, flags=re.IGNORECASE)
    description = re.sub(r'</p>', '\n', description, flags=re.IGNORECASE)
    description = re.sub(r'</div>', '\n', description, flags=re.IGNORECASE)
    description = re.sub(r'</h[1-6]>', '\n', description, flags=re.IGNORECASE)
    description = re.sub(r'<li>(.*?)</li>', r'• \1\n', description, flags=re.IGNORECASE | re.DOTALL)
    description = re.sub(r'</?[uo]l>', '', description, flags=re.IGNORECASE)
    description = re.sub(r'<p[^>]*>', '\n', description, flags=re.IGNORECASE)
    description = re.sub(r'<[^>]+>', '', description)
    
    html_entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&apos;': "'",
        '&hellip;': '...',
        '&mdash;': '—',
        '&ndash;': '–'
    }
    
    for entity, char in html_entities.items():
        description = description.replace(entity, char)
    
    description = re.sub(r'\n{3,}', '\n\n', description)
    
    lines = description.split('\n')
    lines = [line.strip() for line in lines]
    
    description = '\n'.join(lines)
    description = re.sub(r'[ \t]+', ' ', description)
    description = description.strip()
    
    if for_html_display:
        description = description.replace('\n', '<br>')
    
    return description