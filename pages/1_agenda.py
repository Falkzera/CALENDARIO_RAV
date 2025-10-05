import streamlit as st
from src.agenda import func_agenda_rav
from utils.utils import padrao_importacao_page, rodape_desenvolvedor

padrao_importacao_page()

func_agenda_rav()


rodape_desenvolvedor()