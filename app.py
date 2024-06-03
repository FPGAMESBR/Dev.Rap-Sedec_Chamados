import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Carregar os dados dos chamados
sedec_chamados = pd.read_csv('sedec_chamados-2.csv', low_memory=False)

# Converter a coluna de datas para datetime
sedec_chamados['solicitacao_data'] = pd.to_datetime(sedec_chamados['solicitacao_data'], errors='coerce')

# Criar uma coluna para o ano
sedec_chamados['ano'] = sedec_chamados['solicitacao_data'].dt.year

# Função para filtrar e agrupar os dados por ano
def filter_and_group_data_by_year(year):
    filtered_data = sedec_chamados[sedec_chamados['ano'] == year]
    chamados_por_rpa = filtered_data['rpa_codigo'].value_counts().sort_index()
    chamados_por_data = filtered_data.groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_bairro = filtered_data['solicitacao_bairro'].value_counts().head(10)
    chamados_por_situacao = filtered_data['processo_situacao'].value_counts()
    return chamados_por_rpa, chamados_por_data, chamados_por_bairro, chamados_por_situacao

# Obter a lista de anos disponíveis nos dados
anos_disponiveis = sorted(sedec_chamados['ano'].dropna().unique())

# Título do app
st.title("Análise de Chamados por Ano")

# Slider para selecionar o ano
ano_selecionado = st.slider("Selecione o ano:", min_value=int(min(anos_disponiveis)), max_value=int(max(anos_disponiveis)), step=1)

# Obter dados para o ano selecionado
dados_iniciais = filter_and_group_data_by_year(ano_selecionado)

# Gráfico 1: Contagem de Chamados por RPA
fig1 = go.Figure(data=[
    go.Bar(x=dados_iniciais[0].index, y=dados_iniciais[0].values, marker=dict(color=dados_iniciais[0].values, colorscale='Viridis'))
])
fig1.update_layout(
    title="Contagem de Chamados por RPA",
    xaxis_title="RPA",
    yaxis_title="Número de Chamados"
)

# Gráfico 2: Número de Chamados ao Longo do Tempo
fig2 = go.Figure(data=[
    go.Scatter(x=dados_iniciais[1]['solicitacao_data'], y=dados_iniciais[1]['count'], mode='lines')
])
fig2.update_layout(
    title="Número de Chamados ao Longo do Tempo",
    xaxis_title="Data",
    yaxis_title="Número de Chamados"
)

# Gráfico 3: Contagem de Chamados por Bairro
fig3 = go.Figure(data=[
    go.Bar(x=dados_iniciais[2].index, y=dados_iniciais[2].values, marker=dict(color=dados_iniciais[2].values, colorscale='Viridis'))
])
fig3.update_layout(
    title="Contagem de Chamados por Bairro",
    xaxis_title="Bairro",
    yaxis_title="Número de Chamados"
)

# Gráfico 4: Contagem de Chamados por Situação do Processo
fig4 = go.Figure(data=[
    go.Pie(labels=dados_iniciais[3].index, values=dados_iniciais[3].values)
])
fig4.update_layout(
    title="Contagem de Chamados por Situação do Processo"
)

# Mostrar os gráficos no Streamlit
st.plotly_chart(fig1)
st.plotly_chart(fig2)
st.plotly_chart(fig3)
st.plotly_chart(fig4)
