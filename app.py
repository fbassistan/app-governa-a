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
st.write("Governança — Insira os dados para sincronização com a central.")

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

    with col2:
        data_selecionada = st.date_input("Data:", datetime.now(), key=f"data_{st.session_state.reset_counter}")
        observacao = st.text_input("Observações (Opcional):", placeholder="Ex: Troca de enxoval...", key=f"obs_{st.session_state.reset_counter}")

    with col3:
        hora_entrada = st.time_input("Hora de Início:", value=datetime.now().time(), key=f"entrada_{st.session_state.reset_counter}")
        hora_saida = st.time_input("Hora de Término:", value=datetime.now().time(), key=f"saida_{st.session_state.reset_counter}")

# Botão para adicionar à lista local
if st.button("➕ Adicionar à Lista de Envio", use_container_width=True):
    if nome_colaborador.strip() == "":
        st.error("Por favor, preencha o **Nome do Colaborador** antes de continuar.")
    else:
        try:
            fmt = '%H:%M'
            t_inicio = datetime.strptime(hora_entrada.strftime(fmt), fmt)
            t_termino = datetime.strptime(hora_saida.strftime(fmt), fmt)
            
            delta = t_termino - t_inicio
            segundos_totais = int(delta.total_seconds())
            
            if segundos_totais < 0:
                segundos_totais += 24 * 3600
                
            horas, resto = divmod(segundos_totais, 3600)
            minutos, _ = divmod(resto, 60)
            tempo_total_str = f"{horas:02d}:{minutos:02d}"
        except:
            tempo_total_str = "00:00"

        vaga, ocup, col_in, col_out, aber = "", "", "", "", ""
        if situacao_selecionada == "Vaga": vaga = "X"
        elif situacao_selecionada == "Ocupada": ocup = "X"
        elif situacao_selecionada == "IN": col_in = "X"
        elif situacao_selecionada == "Out": col_out = "X"
        elif situacao_selecionada == "Abert": aber = "X"
        
        texto_obs = observacao.strip() if observacao.strip() != "" else "-"
        
        novo_registro = pd.DataFrame([{
            "DATA": data_selecionada.strftime("%d/%m/%Y"),
            "SUITE": suite_selecionada,
            "VAGA": vaga,
            "OCUP": ocup,
            "IN": col_in,
            "OUT": col_out,
