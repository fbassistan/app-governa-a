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
# CONFIGURAÇÕES DE PERSONALIZAÇÃO (Altere aqui com os dados do seu Hotel)
# ==============================================================================
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxtiREdyIV5xQ0HY0AE34I_yOY6j08r5-opzawg11pUzLC_VNPXzaVTst55nCktJ1SF/exec"

# Cole aqui links de imagens hospedadas na internet (ex: do Imgur, do site do hotel, etc.)
URL_FUNDO = "https://www.thebarracuda.com.br/dados/galeria-bhv/full/8.jpg" # Foto padrão de hotel luxuoso
URL_LOGO = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCoWtXmWKvlUcgGnpVEm56JhjQWztWcdAR6Q&s" # Opcional: Cole o link da logo do seu hotel aqui (PNG transparente de preferência)
# ==============================================================================

# Injeção de CSS Customizado para o Fundo e Estilização Geral
css_customizado = f"""
<style>
    /* Configura a foto de fundo com uma película branca transparente (0.85) para dar leitura */
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), url("{URL_FUNDO}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}
    
    /* Deixa os blocos de entrada de dados mais modernos e destacados */
    div[data-testid="stBlock"] {{
        background-color: rgba(255, 255, 255, 0.9);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
    }}
    
    /* Estilização do título principal */
    h1 {{
        color: #1E3A8A !important; /* Azul escuro corporativo */
        font-weight: 700;
    }}
</style>
"""
st.markdown(css_customizado, unsafe_allow_html=True)

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

# Topo do App: Exibe a Logo da Empresa se o link for preenchido
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

# Seção de Cadastro envelopada visualmente
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
            "INICIO": hora_entrada.strftime("%H:%M"),
            "TERMINO": hora_saida.strftime("%H:%M"),
            "TOTAL": tempo_total_str,
            "COLABORADOR": nome_colaborador.strip().upper(),
            "OBSERVAÇÕES": texto_obs
        }])
        
        st.session_state.limpezas_df = pd.concat([st.session_state.limpezas_df, novo_registro], ignore_index=True)
        
        if arquivo_rascunho:
            with open(arquivo_rascunho, "w", encoding="utf-8") as f:
                json.dump(st.session_state.limpezas_df.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
        
        st.success(f"Suíte {suite_selecionada} adicionada e salva no rascunho!")
        st.session_state.reset_counter += 1
        time.sleep(0.4)
        st.rerun()

# Se houver dados na lista, mostra o gerenciador
if not st.session_state.limpezas_df.empty:
    st.write("---")
    st.write("### 📋 Registros salvos no celular (Prontos para envio)")
    
    st.session_state.limpezas_df = st.data_editor(
        st.session_state.limpezas_df,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if arquivo_rascunho and not st.session_state.limpezas_df.empty:
        with open(arquivo_rascunho, "w", encoding="utf-8") as f:
            json.dump(st.session_state.limpezas_df.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

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
                    lista_dados = st.session_state.limpezas_df.to_dict(orient='records')
                    
                    req = urllib.request.Request(URL_WEB_APP, method="POST")
                    req.add_header('Content-Type', 'application/json')
                    payload = json.dumps(lista_dados).encode('utf-8')
                    
                    with urllib.request.urlopen(req, data=payload) as response:
                        resultado = response.read().decode('utf-8')
                    
                    if "Error" in resultado:
                        st.error(f"Erro na Planilha: {resultado}")
                    else:
                        st.balloons()
                        st.success("🎉 Ciclos salvos e sincronizados com a planilha do hotel!")
                        if arquivo_rascunho and os.path.exists(arquivo_rascunho):
                            os.remove(arquivo_rascunho)
                        st.session_state.limpezas_df = pd.DataFrame(columns=COLUNAS_MODELO)
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro de conexão: {e}. Fique tranquila, seus dados continuam guardados aqui.")
