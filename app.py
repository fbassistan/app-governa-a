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
# CSS ULTRA SEGURO (Altera cores sem quebrar os seletores do React)
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

    /* 3. CAIXAS DE INTERAÇÃO (Fundo Verde, Letra Branca e Negrito) */
    /* Target cirúrgico nas classes do Streamlit, sem quebrar os containers internos */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[role="button"], .stTimeInput input, .stDateInput input {
        background-color: #23493A !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: 1px solid #1A372B !important;
        border-radius: 4px !important;
        -webkit-text-fill-color: #FFFFFF !important; /* Estabilidade total em iPhones */
    }}
    
    /* Mantém os ícones internos (como o calendário e setas) visíveis em branco */
    svg, [data-testid="stWidgetLabel"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* 4. BOTÃO PRINCIPAL DE AÇÃO (Adicionar à Lista) - MÁXIMO DESTAQUE */
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

# CONGELAMENTO DOS HORÁRIOS: Evita que a hora fique mudando sozinha a cada renderização na tela do celular
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

    with col2:
        data_selecionada = st.date_input("Data:", datetime.now().date(), key=f"data_{st.session_state.reset_counter}")
        observacao = st.text_input("Observações (Opcional):", placeholder="Ex: Troca de enxoval...", key=f"obs_{st.session_state.reset_counter}")

    with col3:
        # Passa o valor congelado e estável para os inputs de horário
        hora_entrada = st.time_input("Hora de Início:", value=st.session_state.base_time_entrada, key=f"entrada_{st.session_state.reset_counter}")
        hora_saida = st.time_input("Hora de Término:", value=st.session_state.base_time_saida, key=f"saida_{st.session_state.reset_counter}")

# Botão para adicionar à lista local
if st.button("➕ Adicionar à Lista de Envio", use_container_width=True):
    if nome_colaborador.strip() == "":
        st.error("Por favor, preencha o **Nome do Colaborador** antes de continuar.")
    elif hora_entrada is None or hora_saida is None:
        st.error("Por favor, preencha os horários de Início e Término corretamente.")
    else:
        try:
            hoje = datetime.today()
            t_inicio = datetime.combine(hoje, hora_entrada)
            t_termino = datetime.combine(hoje, hora_saida)
            
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
            "ABER": aber,
            "INICIO": hora_entrada.strftime("%H:%M") if hora_entrada else "00:00",
            "TERMINO": hora_saida.strftime("%H:%M") if hora_saida else "00:00",
            "TOTAL": tempo_total_str,
            "COLABORADOR": nome_colaborador.strip().upper(),
            "OBSERVAÇÕES": texto_obs
        }])
        
        st.session_state.limpezas_df = pd.concat([st.session_state.limpezas_df, novo_registro], ignore_index=True)
        
        if arquivo_rascunho:
            with open(arquivo_rascunho, "w", encoding="utf-8") as f:
                json.dump(st.session_state.limpezas_df.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
        
        st.success(f"Suíte {suite_selecionada} adicionada e salva no rascunho!")
        
        # Renova o congelamento de horário para o próximo registro
        st.session_state.base_time_entrada = datetime.now().time()
        st.session_state.base_time_saida = datetime.now().time()
        
        st.session_state.reset_counter += 1
        time.sleep(0.4)
        st.rerun()

# Se houver dados na lista, mostra o gerenciador de forma isolada e segura
if not st.session_state.limpezas_df.empty:
    st.write("---")
    st.write("### 📋 Registros salvos no celular (Prontos para envio)")
    
    # Armazena as edições em uma variável temporária para evitar loops circulares no React
    dados_editados = st.data_editor(
        st.session_state.limpezas_df,
        use_container_width=True,
        num_rows="dynamic",
        key="visualizador_tabela_limpeza"
    )
    
    # Só processa a gravação se houver uma mudança real feita pelo usuário na tabela
    if not dados_editados.equals(st.session_state.limpezas_df):
        st.session_state.limpezas_df = dados_editados
        if arquivo_rascunho:
            with open(arquivo_rascunho, "w", encoding="utf-8") as f:
                json.dump(dados_editados.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("🗑️ Limpar Tudo", type="secondary", use_container_width=True):
            st.session_state.limpezas_df = pd.DataFrame(columns=COLUNAS_MODELO)
            if arquivo_rascunho and os.path.exists(arquivo_rascunho):
                os.remove(arquivo_rascunho)
            st.rerun()
            
    with col_btn2:
        if st.button("🚀 ENVIAR RELATÓRIO DO DIA", type="primary", use_container_width=True):
            with st.spinner("Conectando à planilha central..."):
                try:
                    lista_dados = st.session_state.limpezas_df
