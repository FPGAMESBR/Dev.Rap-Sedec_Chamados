import streamlit as st
import folium
from folium.features import GeoJsonTooltip
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import json
import pandas as pd
from streamlit_folium import st_folium

# Carregar o arquivo GeoJSON
with open('rpa.geojson') as f:
    rpa_geojson = json.load(f)

# Carregar o arquivo GeoJSON dos bairros
with open('bairros.geojson', encoding='utf-8') as f:
    bairros_geojson = json.load(f)

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

# Função para filtrar e agrupar os dados por ano
def filter_and_group_data_by_year(year):
    filtered_data = sedec_chamados[sedec_chamados['ano'] == year]
    chamados_por_rpa = filtered_data['rpa_codigo'].value_counts().sort_index()
    chamados_por_data = filtered_data.groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_bairro = filtered_data['solicitacao_bairro'].value_counts().head(10)
    chamados_por_situacao = filtered_data['processo_situacao'].value_counts()
    chamados_por_vitimas = filtered_data[filtered_data['solicitacao_vitimas'] == 'Sim'].groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_vitimas_fatais = filtered_data[filtered_data['solicitacao_vitimas_fatais'] == 'Sim'].groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_origem = filtered_data['solicitacao_origem_chamado'].value_counts()
    return chamados_por_rpa, chamados_por_data, chamados_por_bairro, chamados_por_situacao, chamados_por_vitimas, chamados_por_vitimas_fatais, chamados_por_origem

# Seleção de ano
ano_selecionado = st.selectbox("Selecione o ano:", anos_disponiveis)

# Atualizar dados conforme o ano selecionado
dados_atualizados = filter_and_group_data_by_year(ano_selecionado)

# Filtrar os dados conforme o ano selecionado
if ano_selecionado == 'All':
    chamados_filtrados = sedec_chamados
else:
    chamados_filtrados = sedec_chamados[sedec_chamados['ano'] == int(ano_selecionado)]

# Agrupar os chamados por RPA e contar a quantidade em cada região
chamados_grouped = chamados_filtrados.groupby('rpa_codigo').size().reset_index(name='chamados_count')

# Criar um dicionário de RPA para contagem de chamados
rpa_counts = dict(zip(chamados_grouped['rpa_codigo'].astype(str), chamados_grouped['chamados_count']))

# Adicionar a contagem de chamados diretamente às propriedades do GeoJSON
for feature in rpa_geojson['features']:
    rpa_codigo = str(feature['properties']['RPA'])
    chamados_count = rpa_counts.get(rpa_codigo, 0)
    feature['properties']['chamados_count'] = chamados_count

# Inicializar o mapa
m = folium.Map(location=[-8.047562, -34.876964], zoom_start=12, tiles='OpenStreetMap')

# Função para definir o estilo das regiões
def style_function(feature):
    chamados_count = feature['properties']['chamados_count']
    if chamados_count > 1000:
        fillColor = '#ff0000'  # Vermelho para mais alta
    elif chamados_count > 500:
        fillColor = '#ffa500'  # Laranja para acima da média
    elif chamados_count >= 300:
        fillColor = '#ffff00'  # Amarelo para média
    else:
        fillColor = '#ff69b4'  # Rosa para moderado
    return {
        'fillOpacity': 0.5,
        'weight': 1,
        'fillColor': fillColor,
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
    highlight_function=lambda x: {'weight': 3, 'color': 'blue', 'fillOpacity': 0.7},
    name='RPAs'
).add_to(m)

# Adicionar os bairros ao mapa com estilo e tooltip
folium.GeoJson(
    bairros_geojson,
    style_function=lambda feature: {'fillOpacity': 0.5, 'weight': 1, 'fillColor': '#00ff00'},  # Verde para todos os bairros
    tooltip=folium.GeoJsonTooltip(fields=['EBAIRRNOME'], aliases=['Bairro:']),
    name='Bairros'
).add_to(m)

# Adicionar controle de camadas
folium.LayerControl(collapsed=False, overlay=True).add_to(m)

# Mostrar o mapa no Streamlit
st_folium(m, width=700, height=500)

# Gráfico 1: Contagem de Chamados por RPA
fig1 = go.Figure(data=[
    go.Bar(x=dados_atualizados[0].index, y=dados_atualizados[0].values, marker=dict(color=dados_atualizados[0].values, colorscale='Viridis'))
])
fig1.update_layout(
    title="Contagem de Chamados por RPA",
    xaxis_title="RPA",
    yaxis_title="Número de Chamados"
)

# Gráfico 2: Número de Chamados ao Longo do Tempo
fig2 = go.Figure(data=[
    go.Scatter(x=dados_atualizados[1]['solicitacao_data'], y=dados_atualizados[1]['count'], mode='lines')
])
fig2.update_layout(
    title="Número de Chamados ao Longo do Tempo",
    xaxis_title="Data",
    yaxis_title="Número de Chamados"
)

# Gráfico 3: Contagem de Chamados por Bairro
fig3 = go.Figure(data=[
    go.Bar(x=dados_atualizados[2].index, y=dados_atualizados[2].values, marker=dict(color=dados_atualizados[2].values, colorscale='Viridis'))
])
fig3.update_layout(
    title="Contagem de Chamados por Bairro",
    xaxis_title="Bairro",
    yaxis_title="Número de Chamados"
)

# Gráfico 4: Contagem de Chamados por Situação do Processo
fig4 = go.Figure(data=[
    go.Pie(labels=dados_atualizados[3].index, values=dados_atualizados[3].values)
])
fig4.update_layout(
    title="Contagem de Chamados por Situação do Processo"
)

# Gráfico 5: Número de Chamados com Vítimas ao Longo do Tempo
fig5 = go.Figure(data=[
    go.Scatter(x=dados_atualizados[4]['solicitacao_data'], y=dados_atualizados[4]['count'], mode='lines')
])
fig5.update_layout(
    title="Número de Chamados com Vítimas ao Longo do Tempo",
    xaxis_title="Data",
    yaxis_title="Número de Chamados com Vítimas"
)

# Gráfico 6: Número de Chamados com Vítimas Fatais ao Longo do Tempo
fig6 = go.Figure(data=[
    go.Scatter(x=dados_atualizados[5]['solicitacao_data'], y=dados_atualizados[5]['count'], mode='lines')
])
fig6.update_layout(
    title="Número de Chamados com Vítimas Fatais ao Longo do Tempo",
    xaxis_title="Data",
    yaxis_title="Número de Chamados com Vítimas Fatais"
)

# Gráfico 7: Contagem de Chamados por Origem do Chamado
fig7 = go.Figure(data=[
    go.Bar(x=dados_atualizados[6].index, y=dados_atualizados[6].values, marker=dict(color=dados_atualizados[6].values, colorscale='Viridis'))
])
fig7.update_layout(
    title="Contagem de Chamados por Origem do Chamado",
    xaxis_title="Origem do Chamado",
    yaxis_title="Número de Chamados"
)

# Mostrar os gráficos no Streamlit
if ano_selecionado != 'All':
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.plotly_chart(fig5, use_container_width=True)
        
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig4, use_container_width=True)
        st.plotly_chart(fig6, use_container_width=True)
    
    st.plotly_chart(fig7, use_container_width=True)

# Calcular a média de todos os chamados
media_total_chamados = sedec_chamados.groupby('ano').size().mean()

# Extrair o último ano disponível nos dados
ultimo_ano = sedec_chamados['ano'].max()

# Calcular a projeção para os próximos anos usando a média total
anos_futuros = range(ultimo_ano + 1, ultimo_ano + 6)  # Próximos 5 anos
projecao_chamados = [media_total_chamados] * len(anos_futuros)

# Criar os dados para o gráfico
dados_hist = sedec_chamados.groupby('ano').size()
anos_hist = dados_hist.index
chamados_hist = dados_hist.values

# Adicionar os dados da projeção
anos_projecao = list(anos_futuros)
chamados_projecao = projecao_chamados

# Criar o gráfico
fig_proj = go.Figure()

# Adicionar os dados do histórico
fig_proj.add_trace(go.Scatter(x=anos_hist, y=chamados_hist, mode='lines+markers', name='Chamados por ano'))

# Adicionar os dados da projeção como uma linha mais suave
fig_proj.add_trace(go.Scatter(x=anos_projecao, y=chamados_projecao, mode='lines', line=dict(dash='dash', color='rgba(255, 255, 0, 0.8)'), name='Projeção para os próximos anos'))

# Atualizar o layout
fig_proj.update_layout(
    title='Projeção de Chamados para os Próximos Anos',
    xaxis_title='Ano',
    yaxis_title='Número de Chamados',
    legend=dict(x=0, y=1, traceorder='normal')
)

# Exibir o gráfico no Streamlit
st.plotly_chart(fig_proj, use_container_width=True)

# Mostrar o mapa e gráficos juntos
st.header("Mapa Interativo e Análise de Chamados")
st.subheader("Mapa de Chamados por RPA e Bairros")

# Adicionar uma breve descrição ou instruções
st.write("""
Explore o mapa interativo para visualizar a distribuição dos chamados por RPA e bairros. Use os gráficos abaixo para obter insights detalhados sobre os chamados ao longo do tempo e outras características relevantes.
""")