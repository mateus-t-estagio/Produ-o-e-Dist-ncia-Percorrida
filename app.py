import dash
#import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
#from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
import numpy as np
import pathlib
import warnings
warnings.filterwarnings("ignore")
import io
from flask import send_file
import flask


#### TREM FORMADO
# Path
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("Data").resolve()

lista = ['EFC', 'EFVM', 'FTC', 'FTL', 'FCA', 'RMN', 'RMP', 'RMO', 'RMS', 'MRS', 'EFPO', 'FNSTN']

# Querys
TremKMCarga = pd.read_excel(DATA_PATH.joinpath('Carga.xlsx'))
TremKMServ = pd.read_excel(DATA_PATH.joinpath('Serv.xlsx'))
Siade = pd.read_excel(DATA_PATH.joinpath('Siade.xlsx'))
TremFormado = pd.read_excel('TremFormado.xlsx')

df_trem_formado = {}
df_tremkm = {}
df_siade = {}

for i in lista:
    ferrovia = i
    # Filtro pra ferrovia
    iTremKMCarga = TremKMCarga['Ferrovia'] == ferrovia
    iTremKMServ = TremKMServ['Ferrovia'] == ferrovia
    iSiade = Siade['Ferrovia'] == ferrovia
    iTremFormado = TremFormado['Ferrovia'] == ferrovia

    TremKMCargaFilt = TremKMCarga[iTremKMCarga]
    TremKMServFilt = TremKMServ[iTremKMServ]
    SiadeFilt = Siade[iSiade]
    TremFormadoFilt = TremFormado[iTremFormado]

    # Wrangling do Trem Formado
    TremFormadoFilt = TremFormadoFilt.fillna(0)
    TremFormadoFilt['Periodo'] = pd.to_datetime(TremFormadoFilt['Periodo'], format='%m/%Y')
    TremFormadoFilt['TremKm'] = TremFormadoFilt['N Trens'] * TremFormadoFilt['Distancia (km)']
    TremFormadoFilt['TKU'] = TremFormadoFilt['TU'] * TremFormadoFilt['N Trens'] * TremFormadoFilt['Distancia (km)']
    TremFormadoFilt['TUa'] = TremFormadoFilt['TU'] * TremFormadoFilt['N Trens']

    # Adequação do resto pra abarcar o mesmo Periodo de tempo
    SiadeFilt = SiadeFilt[58:]
    TremKMCargaFilt = TremKMCargaFilt[58:]
    TremKMServFilt = TremKMServFilt[58:]

    # União das planilhas de trem km de carga e Servico
    frames = [TremKMCargaFilt['Mes/Ano'],
                TremKMCargaFilt['N de Trens Formados'],
                TremKMCargaFilt['Distancia Percorrida'],
                TremKMServFilt['Distancia Percorrida Servico']]
    TremKMFilt = pd.concat(frames, axis=1, sort=False)
    TremKMFilt['TremKm'] = float(0)
    TremKMFilt['Distancia Percorrida'] = TremKMFilt['Distancia Percorrida'].astype(int)
    TremKMFilt['TremKm'] = TremKMFilt['Distancia Percorrida'] + TremKMFilt['Distancia Percorrida Servico']

    # Adequação dos dados do dataframe tremkm
    lista2 = ['N Trens', 'Tempo de Viagem', 'Distancia (km)', 'TremKm', 'TKU', 'TUa']

    for x in lista2:
        TremFormadoFilt[x] = TremFormadoFilt[x].astype(float)

    df = TremFormadoFilt.pivot_table(['N Trens', 'Tempo de Viagem', 'Distancia (km)', 'TremKm', 'TKU', 'TUa'],
                                        ['Periodo'], aggfunc='sum')
    

    # Rename TremKm
    df = df.rename(columns={'TremKm': 'TremKm - Trem Formado'})
    TremKMFilt = TremKMFilt.rename(columns={'TremKm': 'Trem Km - Siade'})
    df_tremkm[i] = TremKMFilt

    # Rename TKU
    SiadeFilt = SiadeFilt.rename(columns={'TKU': 'TKU - Siade'})
    df = df.rename(columns={'TKU': 'TKU - Trem Formado'})

    # Rename TU
    SiadeFilt = SiadeFilt.rename(columns={'TU': 'TU - Siade'})
    df = df.rename(columns={'TUa': 'TU - Trem Formado'})
    df_siade[i] = SiadeFilt

    # Periodo de referência
    lst = pd.date_range('2010-11', '2019-7', freq='m')
    df.index = df.index.strftime('%m-%Y')
    df_trem_formado[i] = df


### INICIO DASHBOARD
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

#Texto do Relatório
intro = '''
## Produção e Distancia Percorrida
'''

parte2 = '''
## Material Rodante
'''

parte3 = '''
## Consumo de Combustível
'''

parte4 = '''
## Velocidade
'''
lista1 = ['EFC', 'EFVM', 'FTC', 'FTL', 'FCA', 'RMN', 'RMP', 'RMO', 'RMS', 'MRS', 'EFPO', 'FNSTN']
lista3 = ['TU', 'TKU']
# Definição do Layout do APP
app.layout = html.Div([
        html.Div([

            html.Div([
                dcc.Dropdown(
                    id='yaxis-column',
                    options=[{'label': i, 'value': i} for i in lista1],
                    value='EFC'
                ),

            ],style={'width': '20%', 'float': 'right', 'display': 'inline-block'}),
            html.Div([
                dcc.Markdown(children=intro)],
                style={'marginLeft': '5%', 'float': 'center', 'width': '80%', 'textAlign': 'justify', 'display': 'inline-block'}),
            html.Div([
            dcc.RadioItems(
                id='yxaxis-type',
                options=[{'label': i, 'value': i} for i in ['TU', 'TKU']],
                value='TU',
                labelStyle={'marginLeft': '5%', 'display': 'inline-block'}
            )
            ]),
        ]),



    html.Div([
    dcc.Graph(id='1'),
    dcc.Graph(id='2'),
                html.Div([
                    dcc.Graph(id='3')],
                    style={'width': '48%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='4')],
                        style={'width': '48%', 'display': 'inline-block'}
                        ),

    
    ]),

])
@app.callback(
    Output('1', 'figure'),
    [Input('yaxis-column', 'value'),
    Input('yxaxis-type', 'value')])
def update_graph1(x_ferr, y_tu):
    FerrSelect=x_ferr
    iProducao=Siade['Ferrovia']==FerrSelect
    Ferrovia_Escolhida=Siade[iProducao]
    Ferrovia_Escolhida['Mes/Ano']=pd.to_datetime(Ferrovia_Escolhida['Mes/Ano'])
    x=Ferrovia_Escolhida['Mes/Ano']
    y=Ferrovia_Escolhida[y_tu]

    trace = go.Scatter(x=x,
                        y=y,
                        mode='lines+markers',
                        name='Produção de Transporte',                            
                        #text="R² = "+str(rsq)
                        )
    
    data = [trace]

    return {
            'data': data,
            'layout': {
            'title':'Produção de Transporte - ' + str(x_ferr),
            'xaxis':{'title': 'Ano'},
            'yaxis':{'title':str(y_tu)},
        }

    }
@app.callback(
    Output('2', 'figure'),
    [Input('yaxis-column', 'value')])
def update_graph2(yaxis_column_name):
    x=pd.date_range('2010-11', '2019-7', freq='m')    
    y1 = df_trem_formado[yaxis_column_name]['TremKm - Trem Formado']
    y2 = df_tremkm[yaxis_column_name]['Trem Km - Siade']

    trace1 = go.Scatter(x=x,
                        y=y1,
                        mode='lines+markers',
                        name='TremKm - Trem Formado',                            
                        #text="R² = "+str(rsq)
                        )
    
    trace2 = go.Scatter(x=x,
                        y=y2,
                        mode='lines+markers',
                        name='Trem Km - Siade',
                        #text="R² = "+str(rsq)
                        )
    data = [trace1, trace2]

    return {
            'data': data,
            'layout': {
            'title':'Trem km - ' + str(yaxis_column_name),
            'xaxis':{'title': 'Ano'},
            'yaxis':{'title': 'Trem km'},
            
            'legend': {
                'orientation':'h'
            }
            }


    }

@app.callback(
    Output('3', 'figure'),
    [Input('yaxis-column', 'value')])
def update_graph3(yaxis_column_name):

    x = df_tremkm[yaxis_column_name]['Trem Km - Siade'].astype(float),
    y = df_siade[yaxis_column_name]['TKU - Siade'].astype(float),    
    correlation = np.corrcoef(x, y)[0,1]
    print(x)
    print('ok')
    print(y)
    rsq = correlation**2
    rsq = round(rsq, 4)
    #print(rsq)

    trace1 = go.Scatter(x=df_tremkm[yaxis_column_name]['Trem Km - Siade'],
                        y=df_siade[yaxis_column_name]['TKU - Siade'],
                        mode='markers',                          
                        #text="R² = "+str(rsq)
                        )

    data = [trace1]

    return {
            'data': data,
            'layout': {
            'title':str(yaxis_column_name) + ' - Trem Km vs. TKU: R² = ' + str(rsq),
            'xaxis':{'title': 'Trem KM'},
            'yaxis':{'title': 'TKU'},
            
            'legend': {
                'orientation':'h'
            }
            }


    }

@app.callback(
    Output('4', 'figure'),
    [Input('yaxis-column', 'value')])
def update_graph4(yaxis_column_name):
    x=pd.date_range('2010-11', '2019-7', freq='m')    
    y1 = df_siade[yaxis_column_name]['TKU - Siade']
    y2 = df_tremkm[yaxis_column_name]['Trem Km - Siade']

    trace1 = go.Scatter(x=x,
                        y=y1,
                        mode='lines',
                        name='TKU',
                        yaxis='y2'                            
                        #text="R² = "+str(rsq)
                        )
    
    trace2 = go.Scatter(x=x,
                        y=y2,
                        mode='lines',
                        name='Trem km',
                        #text="R² = "+str(rsq)
                        )
    data = [trace1, trace2]

    return {
            'data': data,
            'layout': go.Layout(
                title='Produção de Transporte vs. Trem Km',
                yaxis=dict(
                    title='yaxis title'
                ),
                yaxis2=dict(
                    title='yaxis2 title',
                    titlefont=dict(
                        color='rgb(148, 103, 189)'
                    ),
                    tickfont=dict(
                        color='rgb(148, 103, 189)'
                    ),
                    overlaying='y',
                    side='right'
                )
            )
    }

if __name__ == '__main__':
    app.run_server()
