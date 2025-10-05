import streamlit as st
from src.agenda import func_agenda_rav
from utils.utils import padrao_importacao_page, rodape_desenvolvedor
from src.exportar_agenda import render_export_view

padrao_importacao_page()

render_export_view()

rodape_desenvolvedor()