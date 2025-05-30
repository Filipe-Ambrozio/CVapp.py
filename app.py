import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import plotly.express as px

# Configure suas credenciais do Supabase
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "your-anon-key"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Funções de banco de dados
def salvar_produto(nome, categoria, preco):
    data = {"nome": nome, "categoria": categoria, "preco": preco, "data_cadastro": datetime.now().isoformat()}
    supabase.table("produtos").insert(data).execute()

def carregar_produtos():
    res = supabase.table("produtos").select("*").execute()
    return res.data if res.data else []

def salvar_usuario(nome, email, permissao):
    data = {"nome": nome, "email": email, "permissao": permissao, "data_criacao": datetime.now().isoformat()}
    supabase.table("usuarios").insert(data).execute()

def carregar_usuarios():
    res = supabase.table("usuarios").select("*").execute()
    return res.data if res.data else []

def salvar_status(status_texto):
    data = {"status": status_texto, "data": datetime.now().isoformat()}
    supabase.table("status_sistema").insert(data).execute()

def carregar_status():
    res = supabase.table("status_sistema").select("*").order("data", desc=True).limit(10).execute()
    return res.data if res.data else []

# Interface Streamlit
st.set_page_config(page_title="Sistema de Gestão", layout="wide")

menu = st.sidebar.selectbox("Menu", ["Cadastrar Produto", "Cadastrar Usuário", "Relatórios", "Status do Sistema", "Sobre"])

if menu == "Cadastrar Produto":
    st.title("Cadastro de Produto")
    nome = st.text_input("Nome do Produto")
    categoria = st.selectbox("Categoria", ["Eletrônico", "Alimento", "Vestuário", "Outros"])
    preco = st.number_input("Preço", min_value=0.0, format="%.2f")
    if st.button("Salvar"):
        if nome and preco > 0:
            salvar_produto(nome, categoria, preco)
            st.success("Produto salvo com sucesso!")
        else:
            st.error("Preencha todos os campos corretamente.")

elif menu == "Cadastrar Usuário":
    st.title("Cadastro de Usuário")
    nome = st.text_input("Nome")
    email = st.text_input("Email")
    permissao = st.selectbox("Permissão", ["Administrador", "Usuário"])
    if st.button("Salvar"):
        if nome and email:
            salvar_usuario(nome, email, permissao)
            st.success("Usuário salvo com sucesso!")
        else:
            st.error("Preencha todos os campos.")

elif menu == "Relatórios":
    st.title("Relatórios")
    produtos = carregar_produtos()
    if produtos:
        df = pd.DataFrame(produtos)
        st.subheader("Tabela de Produtos")
        st.dataframe(df)

        st.subheader("Distribuição por Categoria")
        fig = px.histogram(df, x="categoria", color="categoria")
        st.plotly_chart(fig)
    else:
        st.warning("Nenhum produto cadastrado.")

elif menu == "Status do Sistema":
    st.title("Status do Sistema")
    novo_status = st.text_input("Atualizar status")
    if st.button("Salvar Status"):
        if novo_status:
            salvar_status(novo_status)
            st.success("Status atualizado!")
    st.subheader("Histórico de Status")
    status = carregar_status()
    for s in status:
        st.write(f"{s['data'][:19]} - {s['status']}")

elif menu == "Sobre":
    st.title("Sobre Nós")
    st.markdown("""
    Este sistema foi desenvolvido para controle interno de produtos e usuários.
    
    **Tecnologias usadas**:
    - [Streamlit](https://streamlit.io)
    - [Supabase](https://supabase.com)
    - Python
    
    Desenvolvido com ❤️ em 2025.
    """)