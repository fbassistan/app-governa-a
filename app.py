import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time
import os

st.set_page_config(page_title="Ciclo de Limpeza - Hotel", page_icon="🧹", layout="centered")

# ➔ SUA URL DO APP DA WEB DO GOOGLE SCRIPTS (Terminada em /exec)
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzcNped3ftP-9FkLcWC-u65kl0RlX-rW2Z_8AHLGKgrw2ETjkoKJI2CHqisiSQnoUUb/exec"

# Configurações fixas do Hotel
SUITES = [f"B{i}" for i in range(11, 28)]  # Gera a lista de B11 até B27
SITUACOES = ["Vaga", "Ocupada", "IN", "Out", "Abert"]

# Inicialização do estado da aplicação
if 'limpezas_df' not in st.session_state:
    st.session_state.limpezas_df = pd.DataFrame(columns=[
        "Data", "Suite", "Hora_Entrada", "Hora_Saida", "Situacao", "Colaborador", "Observacao"
    ])

if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

st.title("🧹 Monitoramento do Ciclo de Limpeza")
st.write("Utilize este aplicativo para registrar o progresso e status de limpeza das suítes.")

# Identificação do Colaborador
nome_colaborador = st.text_input("Nome do Colaborador / Camareira:", placeholder="Ex: Maria Silva")

st.write("---")
st.write("### 🛏️ Registrar Limpeza")

# Organização dos campos em colunas para facilitar o preenchimento no celular/tablet
col1, col2 = st.columns(2)

with col1:
    suite_selecionada = st.selectbox("Selecione a Suíte:", SUITES, key=f"suite_{st.session_state.reset_counter}")
    situacao_selecionada = st.selectbox("Situação da Suíte:", SITUACOES, key=f"situacao_{st.session_state.reset_counter}")
    data_selecionada = st.date_input("Data da Limpeza:", datetime.now(), key=f"data_{st.session_state.reset_counter}")

with col2:
    # Captura o horário atual por padrão para facilitar o preenchimento
    hora_entrada = st.time_input("Hora de Entrada:", value=datetime.now().time(), key=f"entrada_{st.session_state.reset_counter}")
    hora_saida = st.time_input("Hora de Saída:", value=datetime.now().time(), key=f"saida_{st.session_state.reset_counter}")

observacao = st.text_input("Observações (Opcional):", placeholder="Ex: Troca de enxoval completa, frigobar abastecido...", key=f"obs_{st.session_state.reset_counter}")

# Botão para adicionar à lista local
if st.button("➕ Adicionar Registro à Lista", use_container_width=True):
    if nome_colaborador.strip() == "":
        st.error("Por favor, preencha o **Nome do Colaborador** antes de adicionar.")
    else:
        texto_obs = observacao.strip() if observacao.strip() != "" else "-"
        
        # Cria a linha com os dados formatados
        novo_registro = pd.DataFrame([{
            "Data": data_selecionada.strftime("%d/%m/%Y"),
            "Suite": suite_selecionada,
            "Hora_Entrada": hora_entrada.strftime("%H:%M"),
            "Hora_Saida": hora_saida.strftime("%H:%M"),
            "Situacao": situacao_selecionada,
            "Colaborador": nome_colaborador.strip().upper(),
            "Observacao": texto_obs
        }])
        
        # Junta ao DataFrame existente
        st.session_state.limpezas_df = pd.concat([st.session_state.limpezas_df, novo_registro], ignore_index=True)
        st.success(f"Suíte {suite_selecionada} adicionada com sucesso à lista!")
        
        # Reseta os campos incrementando o contador
        st.session_state.reset_counter += 1
        time.sleep(0.5)
        st.rerun()

# Se existirem itens na lista, mostra a tabela de edição e o botão de envio definitivo
if not st.session_state.limpezas_df.empty:
    st.write("---")
    st.write("### 📋 Limpezas prontas para envio")
    st.caption("💡 Caso necessário, você pode dar dois cliques em qualquer célula abaixo para corrigir a informação antes de enviar.")
    
    # Editor de dados interativo do Streamlit
    st.session_state.limpezas_df = st.data_editor(
        st.session_state.limpezas_df,
        column_config={
            "Data": st.column_config.TextColumn("Data", disabled=True),
            "Suite": st.column_config.SelectboxColumn("Suíte", options=SUITES),
            "Hora_Entrada": st.column_config.TextColumn("H. Entrada"),
            "Hora_Saida": st.column_config.TextColumn("H. Saída"),
            "Situacao": st.column_config.SelectboxColumn("Situação", options=SITUACOES),
            "Colaborador": st.column_config.TextColumn("Colaborador"),
            "Observacao": st.column_config.TextColumn("Observações")
        },
        use_container_width=True, num_rows="dynamic"
    )
    
    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        if st.button("🗑️ Limpar Lista", type="secondary", use_container_width=True):
            st.session_state.limpezas_df = pd.DataFrame(columns=["Data", "Suite", "Hora_Entrada", "Hora_Saida", "Situacao", "Colaborador", "Observacao"])
            st.rerun()
            
    with col_btn2:
        if st.button("🚀 ENVIAR PARA A PLANILHA", type="primary", use_container_width=True):
            with st.spinner("Transmitindo dados para a central..."):
                try:
                    # Transforma a tabela em lista de dicionários (JSON)
                    lista_dados = st.session_state.limpezas_df.to_dict(orient='records')
                    
                    # Prepara a requisição HTTP POST
                    req = urllib.request.Request(URL_WEB_APP, method="POST")
                    req.add_header('Content-Type', 'application/json')
                    payload = json.dumps(lista_dados).encode('utf-8')
                    
                    # Envia os dados
                    with urllib.request.urlopen(req, data=payload) as response:
                        resultado = response.read().decode('utf-8')
                    
                    if "Error" in resultado:
                        st.error(f"Erro reportado pelo Google Sheets: {resultado}")
                    else:
                        st.balloons()
                        st.success("🎉 Dados de limpeza registrados com sucesso no banco de dados!")
                        # Limpa a tabela após o sucesso
                        st.session_state.limpezas_df = pd.DataFrame(columns=["Data", "Suite", "Hora_Entrada", "Hora_Saida", "Situacao", "Colaborador", "Observacao"])
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Falha na conexão com o servidor: {e}")
