import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time
import os
import re

st.set_page_config(page_title="Ciclo de Limpeza - Hotel", page_icon="🧹", layout="wide")

# ==============================================================================
# CONFIGURAÇÕES DE PERSONALIZAÇÃO (Preservadas do seu modelo)
# ==============================================================================
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxtiREdyIV5xQ0HY0AE34I_yOY6j08r5-opzawg11pUzLC_VNPXzaVTst55nCktJ1SF/exec"
URL_LOGO = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCoWtXmWKvlUcgGnpVEm56JhjQWztWcdAR6Q&s"
# ==============================================================================

# ==============================================================================
# CSS BLINDADO (Visual "The Barracuda" sem quebrar o motor do celular)
# ==============================================================================
css_barracuda = """
<style>
    /* 1. FUNDO GERAL (Linen/Sand) */
    .stApp {
        background-color: #FAF9F5 !important;
        background-image: none !important;
    }
    
    /* 2. CORES DOS TEXTOS FIXOS E TÍTULOS (Verde Barracuda) */
    h1, h2, h3, h4, label, p, [data-testid="stWidgetLabel"] p {
        color: #23493A !important;
        font-family: 'Merriweather', serif;
    }

    /* 3. BOTÃO PRINCIPAL DE AÇÃO (Adicionar à Lista) - MÁXIMO DESTAQUE */
    div.stButton > button {
        background-color: #23493A !important; 
        color: #FFFFFF !important; 
        border: 2px solid #1A372B !important; 
        border-radius: 6px !important;
        font-weight: 900 !important; 
        font-size: 18px !important; 
        text-transform: uppercase !important; 
        letter-spacing: 1.5px !important; 
        width: 100%;
        height: 55px; 
        box-shadow: 0px 4px 15px rgba(35, 73, 58, 0.2) !important; 
        transition: all 0.2s ease !important;
    }
    
    div.stButton > button:hover {
        background-color: #1A372B !important;
        box-shadow: 0px 6px 20px rgba(35, 73, 58, 0.35) !important;
    }
</style>
"""
st.markdown(css_barracuda, unsafe_allow_html=True)
# ==============================================================================

# Inicialização de variáveis estáveis na memória
if 'base_time_entrada' not in st.session_state:
    st.session_state.base_time_entrada = datetime.now().time()
if 'base_time_saida' not in st.session_state:
    st.session_state.base_time_saida = datetime.now().time()

# Configurações fixas do Hotel
SUITES = [f"B{i}" for i in range(11, 28)]
SITUACOES = ["Vaga", "Ocupada", "IN", "Out", "Abert"]
COLUNAS_MODELO = ["DATA", "SUITE", "VAGA", "OCUP", "IN", "OUT", "ABER", "INICIO", "TERMINO", "TOTAL", "COLABORADOR", "OBSERVAÇÕES"]

if 'limpezas_df' not in st.session_state:
    st.session_state.limpezas_df = pd.DataFrame(columns=COLUNAS_MODELO)

if 'usuario_anterior' not in st.session_state:
    st.session_state.usuario_anterior = ""

if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

def gerar_nome_arquivo(nome):
    nome_limpo = re.sub(r'[^a-zA-Z0-9]', '_', nome.strip().lower())
    return f"rascunho_{nome_limpo}.json"

# Topo do App: Exibe a Logo da Empresa
if URL_LOGO:
    st.image(URL_LOGO, width=160)

st.title("🧹 Monitoramento do Ciclo de Limpeza")
st.write("Governança Inteligente — Insira os dados para sincronização com a central.")

# IDENTIFICAÇÃO DO COLABORADOR
nome_colaborador = st.text_input("Nome do Colaborador / Camareira:", placeholder="Ex: Maria Silva")

arquivo_rascunho = None
if nome_colaborador.strip():
    arquivo_rascunho = gerar_nome_arquivo(nome_colaborador)
    if st.session_state.usuario_anterior != nome_colaborador.strip():
        if os.path.exists(arquivo_rascunho):
            try:
                with open(arquivo_rascunho, "r", encoding="utf-8") as f:
                    dados_salvos = json.load(f)
                st.session_state.limpezas_df = pd.DataFrame(dados_salvos)
                st.toast(f"🔄 Rascunho de {nome_colaborador} recuperado com sucesso!", icon="💾")
            except:
                pass
        st.session_state.usuario_anterior = nome_colaborador.strip()

st.write("---")

# Seção de Cadastro
with st.container():
    st.write("#### 🛏️ Registrar Nova Suíte")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        suite_selecionada = st.selectbox("Selecione a Suíte:", SUITES, key=f"suite_{st.session_state.reset_counter}")
        situacao_selecionada = st.selectbox("Situação atual:", SITUACOES, key=f"situacao_{st.session_state.reset_counter}")
