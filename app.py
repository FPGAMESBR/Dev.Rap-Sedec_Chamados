import streamlit as st
import folium
from folium.features import GeoJsonTooltip
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import json
import pandas as pd
from streamlit_folium import st_folium


with open('rpa.geojson') as f:
    rpa_geojson = json.load(f)

with open('bairros.geojson', encoding='utf-8') as f:
    bairros_geojson = json.load(f)

sedec_chamados = pd.read_csv('sedec_chamados-2.csv')

sedec_chamados['solicitacao_data'] = pd.to_datetime(sedec_chamados['solicitacao_data'], errors='coerce')

sedec_chamados['ano'] = sedec_chamados['solicitacao_data'].dt.year

anos_disponiveis = ['All'] + sorted(sedec_chamados['ano'].dropna().unique().tolist())

st.title("Análise de Chamados por Ano e Mapa Interativo")

def filter_and_group_data_by_year(year):
    filtered_data = sedec_chamados if year == 'All' else sedec_chamados[sedec_chamados['ano'] == year]
    chamados_por_rpa = filtered_data['rpa_codigo'].value_counts().sort_index()
    chamados_por_data = filtered_data.groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_bairro = filtered_data['solicitacao_bairro'].value_counts().head(10)
    chamados_por_situacao = filtered_data['processo_situacao'].value_counts()
    chamados_por_vitimas = filtered_data[filtered_data['solicitacao_vitimas'] == 'Sim'].groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_vitimas_fatais = filtered_data[filtered_data['solicitacao_vitimas_fatais'] == 'Sim'].groupby(filtered_data['solicitacao_data'].dt.date).size().reset_index(name='count')
    chamados_por_origem = filtered_data['solicitacao_origem_chamado'].value_counts()
    return chamados_por_rpa, chamados_por_data, chamados_por_bairro, chamados_por_situacao, chamados_por_vitimas, chamados_por_vitimas_fatais, chamados_por_origem

st.write("""
Este projeto visa analisar os chamados da SEDEC ao longo dos anos, visualizando a distribuição espacial e temporal desses chamados. 
Utilizamos mapas interativos para mostrar a distribuição por RPA e bairros, e gráficos para detalhar o número de chamados, situação dos processos, origem, e outros aspectos relevantes.
Explore os dados para obter insights valiosos sobre os padrões e tendências dos chamados.
""")


ano_selecionado = st.selectbox("Selecione o ano:", anos_disponiveis)

dados_atualizados = filter_and_group_data_by_year(ano_selecionado)

chamados_filtrados = sedec_chamados if ano_selecionado == 'All' else sedec_chamados[sedec_chamados['ano'] == int(ano_selecionado)]

chamados_grouped = chamados_filtrados.groupby('rpa_codigo').size().reset_index(name='chamados_count')

rpa_counts = dict(zip(chamados_grouped['rpa_codigo'].astype(str), chamados_grouped['chamados_count']))

for feature in rpa_geojson['features']:
    rpa_codigo = str(feature['properties']['RPA'])
    chamados_count = rpa_counts.get(rpa_codigo, 0)
    feature['properties']['chamados_count'] = chamados_count

m = folium.Map(location=[-8.047562, -34.876964], zoom_start=12, tiles='OpenStreetMap')

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

folium.GeoJson(
    bairros_geojson,
    style_function=lambda feature: {'fillOpacity': 0.5, 'weight': 1, 'fillColor': '#00ff00'},  # Verde para todos os bairros
    tooltip=folium.GeoJsonTooltip(fields=['EBAIRRNOME'], aliases=['Bairro:']),
    name='Bairros'
).add_to(m)

folium.LayerControl(collapsed=False, overlay=True).add_to(m)

st_folium(m, width=700, height=500)

fig1 = go.Figure(data=[
    go.Bar(x=dados_atualizados[0].index, y=dados_atualizados[0].values, marker=dict(color=dados_atualizados[0].values, colorscale='Viridis'))
])
fig1.update_layout(
    title="Contagem de Chamados por RPA",
    xaxis_title="RPA",
    yaxis_title="Número de Chamados"
)

fig2 = go.Figure(data=[
    go.Scatter(x=dados_atualizados[1]['solicitacao_data'], y=dados_atualizados[1]['count'], mode='lines')
])
fig2.update_layout(
    title="Número de Chamados ao Longo do Tempo",
    xaxis_title="Data",
    yaxis_title="Número de Chamados"
)

fig3 = go.Figure(data=[
    go.Bar(x=dados_atualizados[2].index, y=dados_atualizados[2].values, marker=dict(color=dados_atualizados[2].values, colorscale='Viridis'))
])
fig3.update_layout(
    title="Contagem de Chamados por Bairro",
    xaxis_title="Bairro",
    yaxis_title="Número de Chamados"
)

fig4 = go.Figure(data=[
    go.Pie(labels=dados_atualizados[3].index, values=dados_atualizados[3].values)
])
fig4.update_layout(
    title="Contagem de Chamados por Situação do Processo"
)

st.plotly_chart(fig1)
st.plotly_chart(fig2)
st.plotly_chart(fig3)
st.plotly_chart(fig4)

if ano_selecionado == 'All':
    chamados_por_mes = sedec_chamados.groupby(sedec_chamados['solicitacao_data'].dt.month).size().reset_index(name='count')
else:
    chamados_por_mes = sedec_chamados[sedec_chamados['ano'] == int(ano_selecionado)].groupby(sedec_chamados['solicitacao_data'].dt.month).size().reset_index(name='count')

fig8 = go.Figure(data=[
    go.Bar(x=chamados_por_mes['solicitacao_data'], y=chamados_por_mes['count'], marker=dict(color=chamados_por_mes['count'], colorscale='Viridis'))
])
fig8.update_layout(
    title="Distribuição de Chamados por Mês",
    xaxis_title="Mês",
    yaxis_title="Número de Chamados"
)
st.plotly_chart(fig8)

if ano_selecionado == 'All':
    chamados_por_dia_semana = sedec_chamados.groupby(sedec_chamados['solicitacao_data'].dt.dayofweek).size().reset_index(name='count')
else:
    chamados_por_dia_semana = sedec_chamados[sedec_chamados['ano'] == int(ano_selecionado)].groupby(sedec_chamados['solicitacao_data'].dt.dayofweek).size().reset_index(name='count')

nome_dia_semana = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
chamados_por_dia_semana['dia_semana'] = chamados_por_dia_semana['solicitacao_data'].map(nome_dia_semana)

fig9 = go.Figure(data=[
    go.Bar(x=chamados_por_dia_semana['dia_semana'], y=chamados_por_dia_semana['count'], marker=dict(color=chamados_por_dia_semana['count'], colorscale='Viridis'))
])
fig9.update_layout(
    title="Distribuição de Chamados por Dia da Semana",
    xaxis_title="Dia da Semana",
    yaxis_title="Número de Chamados",
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 1, 2, 3, 4, 5, 6],
        ticktext=['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    )
)
st.plotly_chart(fig9)

def extrair_hora(valor):
    try:
        hora_limpa = valor.split(':')[0]  # Extrair apenas a hora
        return int(hora_limpa)  # Converter para inteiro
    except ValueError:
        return None  # Retornar None se não for possível converter

if ano_selecionado == 'All':
    sedec_chamados_ano = sedec_chamados
else:
    sedec_chamados_ano = sedec_chamados[sedec_chamados['ano'] == int(ano_selecionado)]

sedec_chamados_ano['hora'] = sedec_chamados_ano['solicitacao_hora'].apply(extrair_hora)

sedec_chamados_ano = sedec_chamados_ano.dropna(subset=['hora'])

todas_horas = pd.DataFrame({'hora': range(0, 24)})

chamados_por_hora = sedec_chamados_ano.groupby('hora').size().reset_index(name='count')

chamados_por_hora = todas_horas.merge(chamados_por_hora, on='hora', how='left')

chamados_por_hora['count'] = chamados_por_hora['count'].fillna(0)

chamados_por_hora = chamados_por_hora.sort_values(by='hora')

hora_minima = chamados_por_hora['hora'].min()
hora_maxima = chamados_por_hora['hora'].max()

hora_selecionada = st.slider('Selecione a Hora:', hora_minima, hora_maxima, (hora_minima, hora_maxima))

chamados_filtrados = chamados_por_hora[(chamados_por_hora['hora'] >= hora_selecionada[0]) & 
                                    (chamados_por_hora['hora'] <= hora_selecionada[1])]

fig10 = go.Figure(data=[
    go.Bar(x=chamados_filtrados['hora'], y=chamados_filtrados['count'], 
        marker=dict(color=chamados_filtrados['count'], colorscale='Viridis'))
])
fig10.update_layout(
    title="Distribuição de Chamados por Hora do Dia",
    xaxis_title="Hora do Dia",
    yaxis_title="Número de Chamados",
    xaxis=dict(tickmode='linear')  # Configuração para garantir que todas as horas sejam exibidas
)
st.plotly_chart(fig10)

media_total_chamados = sedec_chamados.groupby('ano').size().mean()

ultimo_ano = sedec_chamados['ano'].max()

anos_futuros = range(ultimo_ano + 1, ultimo_ano + 6)  # Próximos 5 anos
projecao_chamados = [media_total_chamados] * len(anos_futuros)

dados_hist = sedec_chamados.groupby('ano').size()
anos_hist = dados_hist.index
chamados_hist = dados_hist.values

anos_projecao = list(anos_futuros)
chamados_projecao = projecao_chamados

fig_proj = go.Figure()

fig_proj.add_trace(go.Scatter(x=anos_hist, y=chamados_hist, mode='lines+markers', name='Chamados por ano'))

fig_proj.add_trace(go.Scatter(x=anos_projecao, y=chamados_projecao, mode='lines', line=dict(dash='dash', color='rgba(255, 255, 0, 0.8)'), name='Projeção para os próximos anos'))

fig_proj.update_layout(
    title='Projeção de Chamados para os Próximos Anos',
    xaxis_title='Ano',
    yaxis_title='Número de Chamados',
    legend=dict(x=0, y=1, traceorder='normal')
)

st.plotly_chart(fig_proj, use_container_width=True)
