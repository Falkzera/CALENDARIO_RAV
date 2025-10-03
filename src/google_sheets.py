import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
from datetime import datetime
import pytz

def ler_google_sheet(worksheet_name: str) -> pd.DataFrame:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=worksheet_name, ttl=300)
    return df

# realocar posteriormente ---
def data_hr_atual():
    # Define o fuso horário GMT-3
    fuso_horario = pytz.timezone("America/Sao_Paulo")
    # Obtém a data e hora atual no fuso horário especificado
    now = datetime.now(fuso_horario)
    # Formata no estilo dd-mm-yyyy hh:mm
    data_hora_atual = now.strftime("%d/%m/%Y %H:%M")
    return data_hora_atual


def connect_to_gsheet(creds_json, spreadsheet_name, sheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(spreadsheet_name)
    return spreadsheet.worksheet(sheet_name)

CREDENTIALS_FILE = st.secrets['google_credentials2']

# Função para ler os dados
def read_data(planilha, aba):
    sheet = connect_to_gsheet(CREDENTIALS_FILE, planilha, aba)
    data = sheet.get_all_values()
    data = pd.DataFrame(data)
    data.columns = data.iloc[0]
    data = data.drop(data.index[0]).reset_index(drop=True)
    return data

# Função para adicionar nova linh
def add_data(planilha, aba, linha):
    sheet = connect_to_gsheet(CREDENTIALS_FILE, planilha, aba)
    sheet.append_row(linha)

@st.cache_data(show_spinner=False)
def get_dados_usuarios():
    with st.spinner("Carregando dados..."):
        try:
            return read_data('calendario_rav', 'usuarios_rav')
        except Exception as e:
            return st.error(f"Erro ao carregar dados: {e}")
        

# @st.cache_data(show_spinner=False)
def get_historico_acessos():
    with st.spinner("Carregando dados..."):
        try:
            return read_data('calendario_rav', 'historico_acessos')
        except Exception as e:
            return st.error(f"Erro ao carregar dados: {e}")
        
def get_nome_usuario(df_usuarios, cpf):

    nome_completo_user = df_usuarios.loc[df_usuarios['CPF'] == cpf]['NOME'].values[0]
    nome = nome_completo_user.split()[0]

    return [nome_completo_user, nome]