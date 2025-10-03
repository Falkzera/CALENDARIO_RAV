import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import calendar

from utils.utils import padrao_importacao_page



padrao_importacao_page()

# ==================== CSS CUSTOMIZADO ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .main {
        padding: 0rem 1rem;
    }
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 25%, #EC4899 50%, #F59E0B 75%, #EF4444 100%);
        padding: 3rem 2rem;
        border-radius: 25px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 40px rgba(139, 92, 246, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .header-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        display: block;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .header-title {
        color: white;
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.95);
        font-size: 1.4rem;
        font-weight: 400;
        margin: 1rem 0 0 0;
        position: relative;
        z-index: 1;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.85) 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #8B5CF6, #EC4899, #F59E0B);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #8B5CF6, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-label {
        font-size: 1.1rem;
        color: #6B7280;
        font-weight: 500;
        margin: 0.5rem 0 0 0;
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin: 2rem 0 1rem 0;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    .chart-container {
        background: rgba(255,255,255,0.95);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .tab-container {
        background: rgba(255,255,255,0.95);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .footer {
        background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.6) 100%);
        color: white;
        text-align: center;
        padding: 2rem;
        border-radius: 20px;
        margin-top: 3rem;
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: none !important;
        background: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #8B5CF6, #EC4899);
        color: white;
        border-radius: 15px;
        padding: 0.5rem 1.5rem;
        border: none !important;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #F59E0B, #EF4444) !important;
        border: none !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        border: none !important;
        background: transparent !important;
    }
    
    .stTabs > div > div {
        border: none !important;
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES DE ANÁLISE ====================

def load_events():
    """Carrega os eventos do arquivo JSON"""
    try:
        with open("data/events.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []



def analyze_events_data(events):
    """Analisa os dados dos eventos e retorna métricas"""
    if not events:
        return {
            'total_eventos': 0,
            'eventos_por_mes': {},
            'eventos_por_equipe': {},
            'mes_mais_eventos': 'N/A',
            'eventos_df': pd.DataFrame()
        }
    
    # Converter para DataFrame para análise
    df = pd.DataFrame(events)
    
    # Converter datas
    df['start_date'] = pd.to_datetime(df['start'])
    df['mes'] = df['start_date'].dt.month
    df['mes_nome'] = df['start_date'].dt.strftime('%B')
    df['ano'] = df['start_date'].dt.year
    df['dia_semana'] = df['start_date'].dt.day_name()
    
    # Métricas básicas
    total_eventos = len(df)
    
    # Eventos por mês
    eventos_por_mes = df['mes_nome'].value_counts().to_dict()
    mes_mais_eventos = df['mes_nome'].value_counts().index[0] if not df.empty else 'N/A'
    
    # Eventos por equipe - separando nomes múltiplos
    import unicodedata
    
    def remover_acentos(texto):
        """Remove acentos e normaliza o texto"""
        if pd.isna(texto):
            return ""
        texto = str(texto)
        # Normalizar unicode e remover acentos
        texto_normalizado = unicodedata.normalize('NFD', texto)
        texto_sem_acentos = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
        return texto_sem_acentos.strip().title()
    
    nomes_individuais = []
    if 'equipe' in df.columns:
        for equipe in df['equipe']:
            if pd.notna(equipe) and str(equipe).strip():
                # Separar nomes por vírgula e "e"
                nomes = []
                # Primeiro separar por vírgula
                partes = str(equipe).split(',')
                for parte in partes:
                    # Depois separar por "e" (com espaços)
                    sub_partes = parte.split(' e ')
                    for sub_parte in sub_partes:
                        nome = remover_acentos(sub_parte)
                        if nome:
                            nomes.append(nome)
                
                # Adicionar cada nome à lista
                nomes_individuais.extend(nomes)
    
    # Criar DataFrame e contar ocorrências
    if nomes_individuais:
        equipe_df = pd.DataFrame({'Nome': nomes_individuais})
        eventos_por_equipe_df = equipe_df['Nome'].value_counts().reset_index()
        eventos_por_equipe_df.columns = ['Nome', 'Quantidade_Eventos']
        eventos_por_equipe = eventos_por_equipe_df.set_index('Nome')['Quantidade_Eventos'].to_dict()
    else:
        eventos_por_equipe = {}
    
    return {
        'total_eventos': total_eventos,
        'eventos_por_mes': eventos_por_mes,
        'eventos_por_equipe': eventos_por_equipe,
        'mes_mais_eventos': mes_mais_eventos,
        'eventos_df': df
    }

def create_month_chart(eventos_por_mes):
    """Cria gráfico de eventos por mês"""
    if not eventos_por_mes:
        return None
    
    # Ordenar meses corretamente
    meses_ordem = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    # Converter nomes dos meses para português
    eventos_ordenados = {}
    for i, mes_en in enumerate(meses_ordem):
        if mes_en in eventos_por_mes:
            eventos_ordenados[meses_pt[i]] = eventos_por_mes[mes_en]
    
    if not eventos_ordenados:
        return None
    
    # Paleta de cores temática
    colors = ['#8B5CF6', '#A855F7', '#EC4899', '#F472B6', '#F59E0B', '#FBBF24', 
              '#EF4444', '#F87171', '#06B6D4', '#22D3EE', '#10B981', '#34D399']
    
    fig = px.bar(
        x=list(eventos_ordenados.keys()),
        y=list(eventos_ordenados.values()),
        labels={'x': 'Mês', 'y': 'Número de Eventos'},
        color=list(eventos_ordenados.values()),
        color_continuous_scale=[[0, '#8B5CF6'], [0.5, '#EC4899'], [1, '#F59E0B']]
    )
    
    fig.update_layout(
        showlegend=False,
        height=450,
        title={
            'text': "📅 Distribuição de Eventos por Mês",
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 24,
                'color': '#374151',
                'family': 'Inter, sans-serif'
            }
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(size=11, color="#6B7280")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(107, 114, 128, 0.1)',
            showline=False,
            tickfont=dict(size=11, color="#6B7280")
        )
    )
    
    fig.update_traces(
        marker_line_color='rgba(255,255,255,0.8)',
        marker_line_width=2,
        hovertemplate='<b>%{x}</b><br>Eventos: %{y}<extra></extra>',
        texttemplate='%{y}',
        textposition='outside',
        textfont=dict(size=14, color='#374151', family='Inter')
    )
    
    return fig

def create_timeline_chart(df):
    """Cria gráfico de linha temporal dos eventos"""
    if df.empty:
        return None
    
    # Agrupar por data
    eventos_por_data = df.groupby(df['start_date'].dt.date).size().reset_index()
    eventos_por_data.columns = ['Data', 'Eventos']
    
    fig = px.line(
        eventos_por_data,
        x='Data',
        y='Eventos',
        markers=True,
        line_shape='spline'  # Linha suavizada
    )
    
    # Personalizar a linha para ficar mais suave
    fig.update_traces(
        line=dict(width=4, smoothing=1.3, color='#EC4899'),
        marker=dict(size=10, color='#8B5CF6', line=dict(width=2, color='white')),
        hovertemplate='<b>Data:</b> %{x}<br><b>Eventos:</b> %{y}<extra></extra>'
    )
    
    fig.update_layout(
        height=450,
        title={
            'text': "📈 Evolução Temporal dos Eventos",
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 24,
                'color': '#374151',
                'family': 'Inter, sans-serif'
            }
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            title="Data",
            title_font=dict(size=14, color="#6B7280"),
            showgrid=True,
            gridcolor='rgba(107, 114, 128, 0.1)',
            showline=False,
            tickfont=dict(size=11, color="#6B7280")
        ),
        yaxis=dict(
            title="Número de Eventos",
            title_font=dict(size=14, color="#6B7280"),
            showgrid=True,
            gridcolor='rgba(107, 114, 128, 0.1)',
            showline=False,
            tickfont=dict(size=11, color="#6B7280")
        )
    )
    
    return fig

# ==================== INTERFACE PRINCIPAL ====================
# Carregar dados
events = load_events()
analysis = analyze_events_data(events)

# ==================== MÉTRICAS PRINCIPAIS ====================
st.markdown("<h2 class='section-title'>📊 Indicadores Principais</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(f"""
        <div class='metric-card'>
            <h2 class='metric-value'>{analysis['total_eventos']}</h2>
            <p class='metric-label'>🗓️ Total de Eventos Registrados</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    # Traduzir mês para português
    mes_traduzido = analysis['mes_mais_eventos']
    if mes_traduzido != 'N/A':
        meses_en_pt = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        mes_traduzido = meses_en_pt.get(mes_traduzido, mes_traduzido)
    
    st.markdown(f"""
        <div class='metric-card'>
            <h2 class='metric-value'>{mes_traduzido}</h2>
            <p class='metric-label'>📈 Período de Maior Atividade</p>
        </div>
    """, unsafe_allow_html=True)

# ==================== GRÁFICOS ====================
st.markdown("<h2 class='section-title'>📈 Análises Visuais Inteligentes</h2>", unsafe_allow_html=True)

if analysis['total_eventos'] > 0:
    # Gráfico de eventos por mês
    month_chart = create_month_chart(analysis['eventos_por_mes'])
    if month_chart:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.plotly_chart(month_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Gráfico de linha temporal
    timeline_chart = create_timeline_chart(analysis['eventos_df'])
    if timeline_chart:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.plotly_chart(timeline_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ==================== TABELAS DETALHADAS ====================
    st.markdown("<h2 class='section-title'>📋 Análise Detalhada por Segmento</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='tab-container'>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["👥 Análise por Equipe", "📅 Distribuição Mensal"])
    
    with tab1:
        if analysis['eventos_por_equipe']:
            equipe_df = pd.DataFrame(list(analysis['eventos_por_equipe'].items()), 
                                   columns=['👤 Profissional', '📊 Eventos Atendidos'])
            equipe_df = equipe_df.sort_values('📊 Eventos Atendidos', ascending=False)
            equipe_df.index = range(1, len(equipe_df) + 1)
            
            st.markdown("### 🏆 Ranking de Profissionais por Atendimentos")
            st.dataframe(
                equipe_df, 
                use_container_width=True,
                height=400
            )
            
            # Estatísticas adicionais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Total de Profissionais", len(equipe_df))
            with col2:
                st.metric("🥇 Maior Participação", equipe_df.iloc[0]['📊 Eventos Atendidos'] if len(equipe_df) > 0 else 0)
            with col3:
                media_eventos = equipe_df['📊 Eventos Atendidos'].mean() if len(equipe_df) > 0 else 0
                st.metric("📊 Média por Profissional", f"{media_eventos:.1f}")
        else:
            st.info("🔍 Nenhum dado de equipe disponível para análise")
    
    with tab2:
        if analysis['eventos_por_mes']:
            # Traduzir meses para português
            meses_en_pt = {
                'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
                'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
                'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
                'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
            }
            
            mes_data = []
            for mes_en, quantidade in analysis['eventos_por_mes'].items():
                mes_pt = meses_en_pt.get(mes_en, mes_en)
                mes_data.append([mes_pt, quantidade])
            
            mes_df = pd.DataFrame(mes_data, columns=['📅 Mês', '📊 Quantidade de Eventos'])
            mes_df = mes_df.sort_values('📊 Quantidade de Eventos', ascending=False)
            mes_df.index = range(1, len(mes_df) + 1)
            
            st.markdown("### 📈 Distribuição Temporal de Eventos")
            st.dataframe(
                mes_df, 
                use_container_width=True,
                height=400
            )
            
            # Estatísticas mensais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📅 Meses Ativos", len(mes_df))
            with col2:
                st.metric("🔥 Pico Mensal", mes_df.iloc[0]['📊 Quantidade de Eventos'] if len(mes_df) > 0 else 0)
            with col3:
                media_mensal = mes_df['📊 Quantidade de Eventos'].mean() if len(mes_df) > 0 else 0
                st.metric("📊 Média Mensal", f"{media_mensal:.1f}")
        else:
            st.info("🔍 Nenhum dado mensal disponível para análise")
    
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("""
        <div style='text-align: center; padding: 3rem; background: rgba(255,255,255,0.9); border-radius: 20px; margin: 2rem 0;'>
            <h3 style='color: #6B7280; margin-bottom: 1rem;'>📝 Aguardando Dados</h3>
            <p style='color: #9CA3AF; font-size: 1.1rem;'>
                Nenhum evento encontrado para análise.<br>
                Adicione eventos no calendário para visualizar as métricas e insights.
            </p>
        </div>
    """, unsafe_allow_html=True)

# ==================== RODAPÉ ====================
