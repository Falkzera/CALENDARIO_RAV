import streamlit as st
from src.agenda import func_agenda_rav
from utils.utils import padrao_importacao_page, rodape_desenvolvedor
from src.exportar_agenda import render_export_view

padrao_importacao_page()

# Abas: Agenda e Exportação PDF
aba1, aba2 = st.tabs(["Agenda", "Exportar PDF"])
with aba1:
    func_agenda_rav()
with aba2:
    render_export_view()

rodape_desenvolvedor()