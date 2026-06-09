import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time

st.set_page_config(page_title="Ciclo de Limpeza - Hotel", page_icon="🧹", layout="wide")

# ➔ SUA URL DO APP DA WEB DO GOOGLE SCRIPTS (Terminada em /exec)
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxtiREdyIV5xQ0HY0AE34I_yOY6j08r5-opzawg11pUzLC_VNPXzaVTst55nCktJ1SF/exec"

# Configurações fixas do Hotel
SUITES = [f"B{i}" for i in range(11, 28)]  # Gera de B11 até B27
SITUACOES = ["Vaga", "Ocupada", "IN", "Out", "Abert"]

# Inicialização do estado da aplicação com o NOVO MODELO de colunas
COLUNAS_MODELO = ["DATA", "SUITE", "VAGA", "OCUP", "IN", "OUT", "ABER", "INICIO", "TERMINO", "TOTAL", "COLABORADOR", "OBSERVAÇÕES"]

if 'limpezas_df' not in st.session_state:
    st.session_state.limpezas_df = pd.DataFrame(columns=COLUNAS_MODELO)

if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

st.title("🧹 Monitoramento do Ciclo de Limpeza")
st.write("Insira as informações abaixo. O sistema organizará os dados e calculará o tempo total automaticamente.")

# Identificação do Colaborador
nome_colaborador = st.text_input("Nome do Colaborador / Camareira:", placeholder="Ex: Maria Silva")

st.write("---")
st.write("### 🛏️ Registrar Nova Limpeza")

# Layout em colunas para preenchimento rápido
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
        # 1. Cálculo Automático do Tempo Total (Diferença entre Término e Início)
        fmt = '%H:%M'
        t_inicio = datetime.strptime(hora_entrada.strftime(fmt), fmt)
        t_termino = datetime.strptime(hora_saida.strftime(fmt), fmt)
        
        delta = t_termino - t_inicio
        segundos_totais = int(delta.total_seconds())
        
        # Caso a limpeza vire a meia-noite (ajuste de dia)
        if segundos_totais < 0:
            segundos_totais += 24 * 3600
            
        horas, resto = divmod(segundos_totais, 3600)
        minutos, _ = divmod(resto, 60)
        tempo_total_str = f"{horas:02d}:{minutos:02d}"
        
        # 2. Separação da Situação nas colunas específicas do seu modelo (X na coluna escolhida)
        vaga, ocup, col_in, col_out, aber = "", "", "", "", ""
        if situacao_selecionada == "Vaga": vaga = "X"
        elif situacao_selecionada == "Ocupada": ocup = "X"
        elif situacao_selecionada == "IN": col_in = "X"
        elif situacao_selecionada == "Out": col_out = "X"
        elif situacao_selecionada == "Abert": aber = "X"
        
        texto_obs = observacao.strip() if observacao.strip() != "" else "-"
        
        # Criando o novo registro estruturado exatamente como o modelo solicitado
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
        
        # Acumula no estado da sessão
        st.session_state.limpezas_df = pd.concat([st.session_state.limpezas_df, novo_registro], ignore_index=True)
        st.success(f"Suíte {suite_selecionada} adicionada temporariamente!")
        
        # Atualiza a tela limpando os campos
        st.session_state.reset_counter += 1
        time.sleep(0.4)
        st.rerun()

# Se houver dados na lista, mostra o gerenciador e botão de envio definitivo
if not st.session_state.limpezas_df.empty:
    st.write("---")
    st.write("### 📋 Registros prontos para serem salvos na Planilha")
    
    st.session_state.limpezas_df = st.data_editor(
        st.session_state.limpezas_df,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("🗑️ Limpar Tudo", type="secondary", use_container_width=True):
            st.session_state.limpezas_df = pd.DataFrame(columns=COLUNAS_MODELO)
            st.rerun()
            
    with col_btn2:
        if st.button("🚀 SALVAR DADOS NA PLANILHA GOOGLE", type="primary", use_container_width=True):
            with st.spinner("Enviando dados..."):
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
                        st.success("🎉 Ciclo de limpeza registrado com sucesso na planilha oficial!")
                        st.session_state.limpezas_df = pd.DataFrame(columns=COLUNAS_MODELO)
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")
