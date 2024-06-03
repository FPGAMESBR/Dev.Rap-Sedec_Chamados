import streamlit as st
import folium
from folium.features import GeoJsonTooltip
import plotly.graph_objects as go
import json
import pandas as pd
from streamlit_folium import st_folium

# Carregar o arquivo GeoJSON
with open('rpa.geojson') as f:
    rpa_geojson = json.load(f)

# Carregar os dados dos chamados
sedec_chamados = pd.read_csv('sedec_chamados-2.csv')

# Converter a coluna de datas para datetime
sedec_chamados['solicitacao_data'] = pd.to_datetime(sedec_chamados['solicitacao_data'], errors='coerce')

# Criar uma coluna para o ano
sedec_chamados['ano'] = sedec_chamados['solicitacao_data'].dt.year

# Obter a lista de anos disponíveis nos dados
anos_disponiveis = ['All'] + sorted(sedec_chamados['ano'].dropna().unique().tolist())

# Título do app
st.title("Análise de Chamados por Ano e Mapa Interativo")

# Seleção de ano
ano_selecionado = st.selectbox("Selecione o ano:", anos_disponiveis)

# Filtrar os dados conforme o ano selecionado
if ano_selecionado == 'All':
    chamados_filtrados = sedec_chamados
else:
    chamados_filtrados = sedec_chamados[sedec_chamados['ano'] == int(ano_selecionado)]

# Agrupar os chamados por RPA e contar a quantidade em cada região
chamados_grouped = chamados_filtrados.groupby('rpa_codigo').size().reset_index(name='chamados_count')

# Criar um dicionário de RPA para contagem de chamados
rpa_counts = dict(zip(chamados_grouped['rpa_codigo'].astype(str), chamados_grouped['chamados_count']))

# Adicionar a contagem de casos às propriedades do GeoJSON
for feature in rpa_geojson['features']:
    rpa_codigo = str(feature['properties']['RPA'])
    chamados_count = rpa_counts.get(rpa_codigo, 0)
    feature['properties']['chamados_count'] = chamados_count

# Inicializar o mapa
m = folium.Map(location=[-8.047562, -34.876964], zoom_start=12, tiles='cartodbpositron')

# Função para definir o estilo das regiões
def style_function(feature):
    chamados_count = feature['properties']['chamados_count']
    return {
        'fillOpacity': 0.5,
        'weight': 1,
        'fillColor': '#ff0000' if chamados_count > 100 else '#ffff00' if chamados_count > 50 else '#00ff00',
        'color': 'black'
    }

# Adicionar as regiões ao mapa com estilo e tooltip
folium.GeoJson(
    rpa_geojson,
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=['RPA', 'chamados_count'],
        aliases=['RPA:', 'Número de casos:'],
        labels=True,
        sticky=True,
        localize=True
    ),
    highlight_function=lambda x: {'weight': 3, 'color': 'blue', 'fillOpacity': 0.7}
).add_to(m)

# Mostrar o mapa no Streamlit
st_folium(m, width=700, height=500)

# Função para filtrar e agrupar os dados por ano
def filter_and_group_data_by_year(year):
    filtered_data = sedec_chamados[sedec_chamados['ano'] == year]
    chamados_por_rpa = filtered_data['rpa_codigo'].value_counts().sort_index()
    chamados_por_data = filtered_data.groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_bairro = filtered_data['solicitacao_bairro'].value_counts().head(10)
    chamados_por_situacao = filtered_data['processo_situacao'].value_counts()
    return chamados_por_rpa, chamados_por_data, chamados_por_bairro, chamados_por_situacao

# Inicializar dados para o primeiro ano presente nos dados
ano_inicial = anos_disponiveis[1] if anos_disponiveis[0] == 'All' else anos_disponiveis[0]
dados_iniciais = filter_and_group_data_by_year(ano_inicial) if ano_inicial != 'All' else filter_and_group_data_by_year(anos_disponiveis[1])

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
