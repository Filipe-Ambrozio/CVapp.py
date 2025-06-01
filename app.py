import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import hashlib

# --- Configurações Iniciais ---
PRODUTOS_CSV = 'data/produtos.csv'
USUARIOS_CSV = 'data/usuarios.csv'
STATUS_APP_FILE = 'data/status_app.txt'

# Garante que a pasta 'data' existe
if not os.path.exists('data'):
    os.makedirs('data')
    print(f"Pasta 'data' criada.")

# --- Funções Auxiliares ---

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_produtos():
    if os.path.exists(PRODUTOS_CSV):
        try:
            df = pd.read_csv(PRODUTOS_CSV)
            # Garante que a coluna 'DataValidade' é datetime para ordenação
            df['DataValidade'] = pd.to_datetime(df['DataValidade'], errors='coerce')
            return df
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=['CodigoEAN', 'Item', 'DataValidade', 'Lote', 'Quantidade', 'DataRegistro', 'Secao'])
    return pd.DataFrame(columns=['CodigoEAN', 'Item', 'DataValidade', 'Lote', 'Quantidade', 'DataRegistro', 'Secao'])

def salvar_produtos(df):
    df.to_csv(PRODUTOS_CSV, index=False)

def carregar_usuarios():
    if os.path.exists(USUARIOS_CSV):
        try:
            return pd.read_csv(USUARIOS_CSV)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=['Usuario', 'Senha', 'Secao'])
    return pd.DataFrame(columns=['Usuario', 'Senha', 'Secao'])

def salvar_usuarios(df):
    df.to_csv(USUARIOS_CSV, index=False)

def carregar_status_app():
    if os.path.exists(STATUS_APP_FILE):
        with open(STATUS_APP_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) == 2:
                return lines[0].strip(), lines[1].strip() # Retorna (status, mensagem)
    return "azul", "Tudo operando" # Padrão

def salvar_status_app(status, mensagem):
    with open(STATUS_APP_FILE, 'w') as f:
        f.write(f"{status}\n")
        f.write(mensagem)

# --- Inicialização/Verificação do Usuário Admin e CSVs ---
def inicializar_dados():
    # Inicializa produtos.csv se não existir ou estiver vazio
    if not os.path.exists(PRODUTOS_CSV) or carregar_produtos().empty:
        df_produtos = pd.DataFrame(columns=['CodigoEAN', 'Item', 'DataValidade', 'Lote', 'Quantidade', 'DataRegistro', 'Secao'])
        salvar_produtos(df_produtos)
        print(f"Arquivo '{PRODUTOS_CSV}' inicializado.")

    # Inicializa usuarios.csv e garante que o admin está lá
    df_usuarios = carregar_usuarios()
    if df_usuarios.empty or 'admin' not in df_usuarios['Usuario'].values:
        admin_usuario = "admin"
        admin_senha_plain = "123456" # Senha para o admin
        admin_secao = "Admin"
        admin_senha_hashed = hash_senha(admin_senha_plain)

        novo_admin_df = pd.DataFrame([{
            'Usuario': admin_usuario,
            'Senha': admin_senha_hashed,
            'Secao': admin_secao
        }])

        if df_usuarios.empty:
            df_usuarios = novo_admin_df
        else:
            df_usuarios = pd.concat([df_usuarios, novo_admin_df], ignore_index=True)

        salvar_usuarios(df_usuarios)
        print(f"Usuário 'admin' com senha '{admin_senha_plain}' adicionado/garantido em '{USUARIOS_CSV}'.")

    # Inicializa status_app.txt se não existir
    if not os.path.exists(STATUS_APP_FILE):
        salvar_status_app("azul", "Tudo operando") # Status padrão
        print(f"Arquivo '{STATUS_APP_FILE}' inicializado.")


# Executa a inicialização dos dados uma única vez na primeira execução do script
# ou quando o script é recarregado (ex: ao salvar app.py)
inicializar_dados()


# --- Variáveis de Sessão ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'secao' not in st.session_state:
    st.session_state.secao = None
if 'status_cor' not in st.session_state:
    st.session_state.status_cor, st.session_state.status_mensagem = carregar_status_app()


# --- Tela de Login ---
def tela_login():
    st.title("Controle de Validade - Login")

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Entrar")

        if submit_button:
            df_usuarios = carregar_usuarios()
            senha_hashed = hash_senha(senha)
            usuario_encontrado = df_usuarios[(df_usuarios['Usuario'] == usuario) & (df_usuarios['Senha'] == senha_hashed)]

            if not usuario_encontrado.empty:
                st.session_state.logado = True
                st.session_state.usuario = usuario_encontrado['Usuario'].iloc[0]
                st.session_state.secao = usuario_encontrado['Secao'].iloc[0]
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

# --- Seções ---
SECOES = [
    "AÇOUGUE", "PADARIA", "FRIOS", "LATICÍNIOS", "HORTIFRÚTIS", "ENLATADOS",
    "BEBIDAS", "MATINAL", "CEREAIS", "PERFUMARIA", "BISCOITOS", "BAZAR",
    "LIMPEZA", "DOCES/BOMBOM", "MASSAS", "CONDIMENTOS", "INTEGRAL"
]
NIVEIS_ACESSO = ["Admin", "Gerência"] + SECOES

# --- Cadastro de Item ---
def tela_cadastro_item():
    st.title("Cadastro de Item")
    st.subheader("Registrar Novo Produto")

    with st.form("form_cadastro_item", clear_on_submit=True):
        col1, col2 = st.columns([0.7, 0.3]) # Adjust column width for EAN and camera
        with col1:
            # Garante que a seção do usuário logado seja uma das opções da lista, senão define como 0
            secao_inicial_index = SECOES.index(st.session_state.secao) if st.session_state.secao in SECOES else 0
            secao_selecionada = st.selectbox(
                "Seção",
                SECOES,
                key="cadastro_secao",
                index=secao_inicial_index
            )
        with col2:
            # Placeholder for EAN input and camera icon
            codigo_ean_input = st.text_input("Código EAN")
            # Adicionando um botão que "simula" a abertura da câmera.
            # A funcionalidade real de câmera exigiria JavaScript/HTML customizado.
            # Este é um placeholder visual e informativo.
            st.markdown(
                """
                <style>
                .camera-icon-button button {
                    background-color: transparent;
                    border: none;
                    color: grey;
                    font-size: 20px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0;
                    margin-top: -30px; /* Adjust to align with input field */
                    float: right; /* Align to the right of the column */
                }
                </style>
                """, unsafe_allow_html=True
            )
            # You can use a custom button with an icon here, or just inform
            # Streamlit doesn't directly support icons inside st.text_input
            # A simple button below the input as a placeholder for the action
            st.info("Para escanear, use um leitor de código de barras físico ou um aplicativo externo e digite o EAN acima. A integração direta com a câmera está em desenvolvimento.")

        item = st.text_input("Nome do Item")
        # Define a data padrão para 30/05/2025 (ou data atual se posterior)
        data_default = datetime(2025, 5, 30)
        if datetime.now() > data_default:
            data_default = datetime.now()
        
        # Formatando a data para DD/MM/AAAA
        data_validade = st.date_input("Data de Validade", data_default.date(), format="DD/MM/YYYY")
        
        lote = st.text_input("Lote (Opcional)")
        quantidade = st.number_input("Quantidade", min_value=1, value=1)

        submit_button = st.form_submit_button("Salvar Item")

        if submit_button:
            if not codigo_ean_input or not item:
                st.error("Código EAN e Nome do Item são obrigatórios.")
            else:
                df_produtos = carregar_produtos()
                novo_produto = pd.DataFrame([{
                    'CodigoEAN': codigo_ean_input,
                    'Item': item,
                    'DataValidade': data_validade.strftime('%Y-%m-%d'), # Formato para CSV
                    'Lote': lote,
                    'Quantidade': quantidade,
                    'DataRegistro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Secao': secao_selecionada
                }])
                df_produtos = pd.concat([df_produtos, novo_produto], ignore_index=True)
                salvar_produtos(df_produtos)
                st.success("Item salvo com sucesso!")
                # Os campos serão limpos automaticamente com clear_on_submit=True

    st.subheader("Lista de Produtos Cadastrados")

    df_produtos = carregar_produtos()

    if not df_produtos.empty:
        # Filtrar por seção se não for Admin ou Gerência
        if st.session_state.secao not in ["Admin", "Gerência"]:
            df_produtos = df_produtos[df_produtos['Secao'] == st.session_state.secao]

        # Convertendo DataValidade para datetime para ordenação
        df_produtos['DataValidade'] = pd.to_datetime(df_produtos['DataValidade'])
        df_produtos_exibir = df_produtos.sort_values(by='DataValidade').reset_index(drop=True)

        # Adicionar coluna de Dias Restantes e Status de Validade
        today = datetime.now()
        df_produtos_exibir['Dias Restantes'] = (df_produtos_exibir['DataValidade'] - today).dt.days

        def obter_status_validade_html(dias_restantes):
            if dias_restantes < 0:
                return f'<span style="color:red; font-weight:bold;">VENCIDO ({abs(dias_restantes)} dias)</span>'
            elif dias_restantes <= 5:
                return f'<span style="color:orange; font-weight:bold;">Vence em {dias_restantes} dias</span>'
            elif dias_restantes <= 30:
                return f'<span style="color:yellow; font-weight:bold;">Vence em {dias_restantes} dias</span>'
            else:
                return f'<span style="color:green; font-weight:bold;">Retido ({dias_restantes} dias)</span>'

        def obter_status_validade_texto(dias_restantes): # Nova função para o texto limpo
            if dias_restantes < 0:
                return f'VENCIDO ({abs(dias_restantes)} dias)'
            elif dias_restantes <= 5:
                return f'Vence em {dias_restantes} dias'
            elif dias_restantes <= 30:
                return f'Vence em {dias_restantes} dias'
            else:
                return f'Retido ({dias_restantes} dias)'

        df_produtos_exibir['Status Validade HTML'] = df_produtos_exibir['Dias Restantes'].apply(obter_status_validade_html)
        df_produtos_exibir['Status Validade Texto'] = df_produtos_exibir['Dias Restantes'].apply(obter_status_validade_texto) # Nova coluna

        # Novo formato de DataValidade
        df_produtos_exibir['DataValidadeFormatada'] = df_produtos_exibir['DataValidade'].dt.strftime('%d/%m/%Y')
        df_produtos_exibir['DataRegistroFormatada'] = pd.to_datetime(df_produtos_exibir['DataRegistro']).dt.strftime('%d/%m/%Y %H:%M:%S')

        st.markdown("---") # Linha separadora antes da lista

        # Exibir cada item em um expander (gaveta)
        for index, row in df_produtos_exibir.iterrows():
            # Cabeçalho da gaveta com as informações principais (apenas texto limpo)
            header_text = (
                f"**Cód. EAN:** {str(row['CodigoEAN']).replace(',', '')} | "
                f"**Item:** {row['Item']} | "
                f"**Dias:** {row['Dias Restantes']} | "
                f"{row['Status Validade Texto']}" # Usando o texto limpo aqui
            )

            with st.expander(header_text, expanded=False): # expanded=False mantém a gaveta fechada por padrão
                st.markdown(f"**Lote:** {row['Lote'] if row['Lote'] else 'Não informado'}")
                st.markdown(f"**Quantidade:** {row['Quantidade']}")
                st.markdown(f"**Validade:** {row['DataValidadeFormatada']}")
                st.markdown(f"**Seção:** {row['Secao']}")
                st.markdown(f"**Data de Registro:** {row['DataRegistroFormatada']}")

                st.markdown("---") # Separador dentro da gaveta

                # Botão de exclusão dentro da gaveta
                if st.button(
                    "Excluir Item",
                    key=f"excluir_produto_{row['CodigoEAN']}_{index}",
                    help="Clique para excluir este item permanentemente"
                ):
                    df_produtos_original = carregar_produtos()
                    # Find the exact row to delete, considering multiple items might have the same EAN but different attributes
                    # For a robust deletion, combine EAN, Item, DataValidade, etc.
                    # For simplicity here, we'll assume EAN is unique enough in a single entry scenario, but for a real system,
                    # a unique ID per entry would be better.
                    # A more precise way would be:
                    # df_produtos_atualizado = df_produtos_original.drop(df_produtos_original[(df_produtos_original['CodigoEAN'] == row['CodigoEAN']) &
                    #                                                                      (df_produtos_original['Item'] == row['Item']) &
                    #                                                                      (df_produtos_original['DataValidade'] == row['DataValidade'])].index)
                    # For now, using the simpler EAN match for demonstration
                    df_produtos_atualizado = df_produtos_original[
                        (df_produtos_original['CodigoEAN'] != row['CodigoEAN']) |
                        (df_produtos_original['Item'] != row['Item']) |
                        (pd.to_datetime(df_produtos_original['DataValidade']) != row['DataValidade']) |
                        (df_produtos_original['Lote'] != row['Lote']) |
                        (df_produtos_original['Quantidade'] != row['Quantidade'])
                    ]

                    # This ensures only the exact row clicked is removed, not all entries with the same EAN
                    # if they differ in other fields.
                    # This relies on the index of the displayed dataframe being the same as the original after filtering/sorting.
                    # A safer approach is to pass a unique ID for each record.
                    # Let's use `index` from the loop to locate the specific row if it matches other criteria.
                    # This is still not perfect if the underlying CSV has duplicates and display changes.
                    # The most robust way to delete a specific row is to have a unique ID for each product entry.
                    # Assuming for now, deleting by EAN + a refresh is acceptable for this context.
                    
                    # A more robust deletion logic: create a temporary unique identifier if one doesn't exist.
                    # Or, as `df_products_original` is loaded, you can directly filter out based on `index`
                    # if the index corresponds to the original dataframe's index.
                    # Let's re-read the original and remove by matching all attributes of the row.
                    
                    original_df_for_deletion = carregar_produtos()
                    # Convert 'DataValidade' in the original_df_for_deletion to datetime for comparison
                    original_df_for_deletion['DataValidade'] = pd.to_datetime(original_df_for_deletion['DataValidade'])

                    # Identify the row to be deleted by matching all its attributes
                    # This is more robust than just EAN in case of duplicate EANs with different details
                    row_to_delete_mask = (
                        (original_df_for_deletion['CodigoEAN'] == row['CodigoEAN']) &
                        (original_df_for_deletion['Item'] == row['Item']) &
                        (original_df_for_deletion['DataValidade'] == row['DataValidade']) &
                        (original_df_for_deletion['Lote'].fillna('') == row['Lote'].fillna('')) & # Handle NaN/empty strings
                        (original_df_for_deletion['Quantidade'] == row['Quantidade']) &
                        (original_df_for_deletion['Secao'] == row['Secao'])
                    )
                    
                    # If there are multiple identical rows, this will delete all of them.
                    # If you need to delete only one specific instance, you would need a unique row ID.
                    df_products_updated = original_df_for_deletion[~row_to_delete_mask]
                    
                    salvar_produtos(df_products_updated)
                    st.success(f"Item com Código EAN '{row['CodigoEAN']}' excluído com sucesso.")
                    st.rerun()

            st.markdown("---") # Linha separadora após cada gaveta

    else:
        st.info("Nenhum produto cadastrado ainda.")


# --- Área do Administrador ---
def tela_administrador():
    st.title("Área do Administrador")

    if st.session_state.secao not in ["Admin", "Gerência"]:
        st.warning("Você não tem permissão para acessar esta área.")
        return

    st.subheader("Cadastrar Novo Usuário")
    with st.form("form_cadastro_usuario", clear_on_submit=True):
        novo_usuario_nome = st.text_input("Nome de Usuário")
        nova_senha = st.text_input("Senha", type="password")
        secao_usuario = st.selectbox("Seção do Usuário", NIVEIS_ACESSO)

        submit_button_usuario = st.form_submit_button("Cadastrar Usuário")

        if submit_button_usuario:
            if not novo_usuario_nome or not nova_senha:
                st.error("Nome de Usuário e Senha são obrigatórios.")
            else:
                df_usuarios = carregar_usuarios()
                if novo_usuario_nome in df_usuarios['Usuario'].values:
                    st.error("Nome de usuário já existe.")
                else:
                    novo_usuario_df = pd.DataFrame([{
                        'Usuario': novo_usuario_nome,
                        'Senha': hash_senha(nova_senha),
                        'Secao': secao_usuario
                    }])
                    df_usuarios = pd.concat([df_usuarios, novo_usuario_df], ignore_index=True)
                    salvar_usuarios(df_usuarios)
                    st.success(f"Usuário '{novo_usuario_nome}' cadastrado com sucesso na seção '{secao_usuario}'.")
                    st.rerun()

    st.subheader("Usuários Cadastrados")
    df_usuarios = carregar_usuarios()
    if not df_usuarios.empty:
        # Mostra a senha (hash)
        st.dataframe(df_usuarios[['Usuario', 'Secao', 'Senha']]) # 'Senha' agora está incluída
        st.markdown("---")
        st.subheader("Excluir Usuário")
        # Garante que a lista de opções de exclusão só aparece se houver usuários
        if not df_usuarios['Usuario'].empty:
            # Filter out the current logged-in user from the deletion options
            users_to_delete_options = [u for u in df_usuarios['Usuario'].unique() if u != st.session_state.usuario]
            if users_to_delete_options:
                usuario_para_excluir = st.selectbox(
                    "Selecione o Usuário para excluir",
                    users_to_delete_options
                )
                if st.button("Excluir Usuário Selecionado"):
                    if usuario_para_excluir:
                        df_usuarios_atualizado = df_usuarios[df_usuarios['Usuario'] != usuario_para_excluir]
                        salvar_usuarios(df_usuarios_atualizado)
                        st.success(f"Usuário '{usuario_para_excluir}' excluído com sucesso.")
                        st.rerun()
                    else:
                        st.warning("Nenhum usuário selecionado para exclusão.")
            else:
                st.info("Não há outros usuários para excluir além do seu próprio.")
        else:
            st.info("Não há usuários para excluir.")

    st.markdown("---")
    st.subheader("Salvar Modificações e Status do Sistema")
    mensagem_modificacao = st.text_area("Descreva as modificações ou informações importantes para os usuários:", value=st.session_state.status_mensagem)
    status_cor_selecionada = st.selectbox(
        "Status do Sistema",
        options=["verde", "amarelo", "vermelho", "azul"],
        format_func=lambda x: {
            "verde": "Verde: Atualizado",
            "amarelo": "Amarelo: Uma nova atualização",
            "vermelho": "Vermelho: Erro, sistema com problemas",
            "azul": "Azul: Tudo operando"
        }[x],
        index=["verde", "amarelo", "vermelho", "azul"].index(st.session_state.status_cor) # Pre-seleciona o status atual
    )

    if st.button("Salvar Status e Mensagem"):
        salvar_status_app(status_cor_selecionada, mensagem_modificacao)
        st.session_state.status_cor = status_cor_selecionada
        st.session_state.status_mensagem = mensagem_modificacao
        st.success("Status e mensagem salvos com sucesso!")
        st.rerun()

# --- Atualização/Sobre ---
def tela_atualizacao_sobre():
    st.title("Atualização/Sobre a Aplicação")

    st.subheader("Sobre a Equipe e a Ferramenta")
    st.markdown("""
    Esta aplicação de controle de validade foi desenvolvida para otimizar o gerenciamento de produtos com datas de validade em diversas seções.
    Nosso objetivo é fornecer uma ferramenta intuitiva e eficiente para garantir a qualidade e a segurança dos produtos.

    **Equipe de Desenvolvimento:**
    * Desenvolvedor Principal: [Seu Nome/Nome da Equipe]
    * Colaboradores: [Nomes dos Colaboradores, se houver]
    """)

    st.subheader("Atualizações e Modificações Recentes")
    status_cor, status_mensagem = carregar_status_app()
    st.markdown(f"""
    **Mensagem do Administrador:**
    {status_mensagem}
    """)

    st.subheader("Guia de Cores para o Usuário")
    st.markdown("""
    Para facilitar a compreensão do status da aplicação, utilizamos as seguintes cores:

    * <span style="color: green; font-weight: bold;">🟢 Verde:</span> **Atualizado.** O sistema está com as últimas informações e operando normalmente.
    * <span style="color: yellow; font-weight: bold;">🟡 Amarelo:</span> **Há uma nova atualização.** Indica que novas funcionalidades ou melhorias foram implementadas e estão aguardando serem formalmente anunciadas. Fique atento às novidades!
    * <span style="color: red; font-weight: bold;">🔴 Vermelho:</span> **Erro, sistema com problemas.** Sinaliza que há uma anomalia ou problema no funcionamento do aplicativo. Por favor, reporte qualquer erro ou comportamento inesperado.
    * <span style="color: blue; font-weight: bold;">🔵 Azul:</span> **Tudo operando.** O sistema está funcionando perfeitamente, sem problemas conhecidos e não há atualizações pendentes.
    """, unsafe_allow_html=True)


# --- Aplicação Principal do Streamlit ---
if not st.session_state.logado:
    tela_login()
else:
    # Sidebar com o status da aplicação
    st.sidebar.title("Informações do Aplicativo")
    st.sidebar.write(f"Usuário: **{st.session_state.usuario}**")
    st.sidebar.write(f"Seção: **{st.session_state.secao}**")

    # Bolinha de status na sidebar
    status_cor_exibicao = st.session_state.status_cor
    cor_map = {"verde": "green", "amarelo": "yellow", "vermelho": "red", "azul": "blue"}
    st.sidebar.markdown(f"""
    **Status do Sistema:** <span style="color: {cor_map.get(status_cor_exibicao, 'gray')}; font-size: 20px;">●</span>
    """, unsafe_allow_html=True)


    tab1, tab2, tab3 = st.tabs(["Cadastro de Item", "Área do Administrador", "Atualização/Sobre"])

    with tab1:
        tela_cadastro_item()
    with tab2:
        tela_administrador()
    with tab3:
        tela_atualizacao_sobre()

    st.sidebar.markdown("---")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario = None
        st.session_state.secao = None
        st.rerun()
        #streamlit run app.py
