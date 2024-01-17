#-------------------------------- CABEÇALHO --------------------------#
# Descrição: Aplicação de dashboard para área do sistema de           #
#            Armazenamento COIDS/SESUP.                               #
# Autores:                                                            # 
# Sugestão de usar plotly: Ivan                                       #
# Equipe: Jurandir Ventura Rodrigues - Análise/Desenvolvimento - COIDS#
#         João Pedro Guimarães - COIDS,                               #
#         Marcelo Prado - COIDS                                       #
#         Caio Lemes - COIDS                                          #
# Data Criação: 12/mai/2023                                           #
# Data de atualização: 16/jan/2024 - 17:00H                           #
# Requisitos: python3                                                 #
#             Instalar requiremensts (ferramentas/bibliotecas python) #
#             Google, Mozilla...                                      #
# Parâmetros: -                                                       #
# Exemplo de execução:                                                #
#     Seta ambiente 'env' .                                           #
#     python3 app_...py                                               #
#     Executa no browser: Porta 5007                                  #
#---------------------------------------------------------------------#

from dash import dash, dcc, html, Input, Output, dash_table, State
from dash.dash_table.Format import Group, Format, Symbol, Scheme
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from flask import Flask
from decimal import *
import locale
from gevent.pywsgi import WSGIServer
from datetime import datetime
from funcoes import *
from connection import *

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

server = Flask(__name__)

app_ambiente_coids = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.FLATLY, dbc.themes.GRID, dbc.icons.FONT_AWESOME, dbc.icons.FONT_AWESOME], url_base_pathname='/dashboard/') # Criando a instancia da aplicação
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
api = connect_zabbix()

hostgroup_name = "MS3"
hostgroup_info = get_hostgroup(hostgroup_name,api)
hostgroup_id = hostgroup_info[0]['groupid']

hostgroups,hosts,items=get_HostsItems(api,hostgroup_id)

# Define dropdown dos hosts
host_dropdown = []

for host in (hosts):
    host_dropdown.append(host['host'])

host_dropdown = sorted(host_dropdown)
numero_dias_zabbix = [5,10,15,20,30,60,90,120,180]   
numero_dias_super = [5,10,15,20,30,60,90,120,180]

# Encerra a etapa de dados da integração com zabbix

# Ambiente Virtual e Sistema de Armazenamento #
### CONEXÃO BANCO DE DADOS ###
cursor,conn=conecta_BD()

rows_ambiente=busca_Servidores(cursor)

### AMBIENTE VIRTUAL ###
df_ambiente = monta_DataframeVM(rows_ambiente)
df_vm = df_ambiente

# FINAL DA LEITURA DA TABELA 'SERVIDORES' DO AMBIENTE VIRTUAL 

# LEITURA DA TABELA 'VOLUMES' COM FILTRO 
rows=busca_Volumes(cursor,'Olinda')

df_volume = monta_DataframeOlinda(rows)
### FINAL DA LEITURA DA TABELA 'VOLUMES' : 'controller_volumes = Olinda' 

# LEITURA DA TABELA 'VOLUMES' COM FILTRO 'controller_volumes = Landsat'
rows=busca_Volumes(cursor,'Landsat')

df_volume_landsat = monta_DataframeLandsat(rows)
# FINAL DA LEITURA DA TABELA 'VOLUMES' COM FILTRO 'controller_volumes = Landsat'

# LEITURA DA TABELA 'VOLUMES' COM FILTRO POR GRUPOS 
rows=busca_VolumesPorGrupo(cursor,'Olinda')
df_grupo = rows

### CONVERSAO DE VALORES VOLUMES LANDSAT- Início ### 
#fator_convert = (1024*1024)       # KB para Gigabyte
fator_convert  = (1024*1024*1024)  # KB para Terabyte

# V O L U M E -> Converte de KB para TB LANDSAT (Início)
# Volume Total

soma_volume_total_landsat,soma_volume_usado_landsat,soma_volume_disponivel_landsat,soma_snap_total_landsat,soma_snap_usado_landsat,soma_snap_disponivel_landsat=define_ValoresVolumesLandsat(df_volume_landsat, fator_convert)

# Início leitura/conversão de planilha estatística de CSV para EXCEL
df1 = pd.read_csv("./planilha_estatistica_pool_host_vms.csv", sep = ";",
    encoding='utf-8', names=['LABEL_POOL','DESCR_POOL','HOST','nCPU_HOST',
    'MEMORIA_TOTAL_HOST','MEMORIA_LIVRE_HOST','MEMORIA_USADA_HOST','nCPU_VM',
    'MEMORIA_VM', 'STATUS_RUNNING','STATUS_HALTED'],header=0)

# Indexação para geração de tabela -------------------------------------
df_vm['id'] = df_vm['LABEL_POOL']
df_vm.set_index('id', inplace=True, drop=False)

# Início da conversão de valores ---------------------------------------
fator_convert = 1073741824  #(1024*1024*1024  Amb. Virt., Bytes -> GB)

mem_tot_host_GB,mem_livre_host_GB,mem_vm_GB,mem_usada_host_GB=define_ValoresMemoria(df_vm,fator_convert)

# Fim da conversão de valores  -----------------------------------------

# Filtro de dados para a tabela ----------------------------------------
df_filtro = df_ambiente.iloc[: , [1, 5, 11, 15, 16,2, 13, 14]].copy()

# Seta opção para Dropdown usando o nome do ambiente (LABEL_POOL) ------
opcoes_ambiente = list(df_vm['LABEL_POOL'].unique())

opcoes_hosts = list(df_vm['HOST'].unique())

#opcoes_ambiente.append("Ambientes Virtuais")
opcoes_ambiente.insert(0,'Ambientes Virtuais')

FA_icon = html.I(className="bi bi-arrows-angle-expand me-2"),
FA_button =  dbc.Button([FA_icon, ""], className="me-2"),

########################################################################

# LEITURA DA TABELA 'AGGREGATE', FILTRO 'nomeStorage_aggregate = OLINDA'
rows_aggr = busca_Aggregates(cursor,'OLINDA')

df_aggr = monta_DataframeAggregateOlinda(rows_aggr)
# FINAL DA LEITURA DA TABELA 'AGGREGATE', FILTRO 'nomeStorage_aggregate = OLINDA'


# LEITURA DA TABELA 'AGGREGATE', FILTRO 'nomeStorage_aggregate = LANDSAT'
rows_aggr_landsat = busca_Aggregates(cursor,'LANDSAT')

df_aggr_landsat = monta_DataframeAggregateLandsat(rows_aggr)
# FINAL DA LEITURA DA TABELA 'AGGREGATE', FILTRO 'nomeStorage_aggregate = LANDSAT'

#######################################################################

# LEITURA DA TABELA 'CONTRATO' - VALORES CONTRATUAIS EX.: CETEST, HELPDESK/NOC...
rows_contrato = busca_Contratos(cursor)

df_contrato = monta_DataframeContratos(rows_contrato)
# FINAL DA LEITURA DA TABELA 'CONTRATO' - VALORES CONTRATUAIS EX.: CETEST, # HELPDESK/NOC... #

#######################################################################

# LEITURA DA TABELA 'MÁQUINAS FÍSICAS' - Consumo #
rows_maqfisica = busca_MaquinasFisicas(cursor)

df_maqfisica = monta_DataframeMaqFisicas(rows_maqfisica)
# FINAL DA LEITURA DA TABELA 'MÁQUINAS FÍSICAS' - Consumo #

#######################################################################

# LEITURA DA TABELA 'DISCOS' - disk
rows_disk = busca_Discos(cursor)

df_disk = monta_DataframeDiscos(rows_disk)

# Desmonta o valor em bytes
fator_TB2B = (1024*1024*1024*1024*1024)  # Terabyte para byte
fator_GB2B = (1024*1024*1024*1024)       # Gigabyte para byte

fator_1000_B2TB = (1000*1000*1000*1000*1000)  # Byte -> TB (base 1000)

# Gerar processamento com o SSD
new_col = {"factory_disk": df_disk['SIZE']}
df_disk.insert(2, "FACTORY_DISK", new_col['factory_disk'], True)

df_disk= round(df_disk.assign(FACTORY_DISK = lambda x: (x.SIZE.astype(float) * fator_TB2B) / fator_1000_B2TB),1)

# ***Substituir valores que foram arredondados mas não condiz com a 
# realidade da especificação de disco (HD). Não foi possível usar 
# função porque teoricamente deveria funcionar mas ao testar cada uma 
# delas, não foi obtido o valor esperado. Por isso os valores foram
# identificados e inseridos no 'replace' manualmente (16.1,....)
for column in ['FACTORY_DISK']:
    df_disk[column] = list(df_disk[column].replace(16.1,16.0, regex=True))
    df_disk[column] = list(df_disk[column].replace(4.1,4.0, regex=True))
    df_disk[column] = list(df_disk[column].replace(0.9,1.0, regex=True))
    df_disk[column] = list(df_disk[column].replace(2.7,3.0, regex=True))

# Separa dataframe para Armazenamento OLINDA e LANDSAT 
df_disk_olinda = df_disk[df_disk["NODE_DISK"].str.contains("olinda") | df_disk["NODE_DISK"].str.contains("aggr")]
df_disk_landsat = df_disk[df_disk["NODE_DISK"].str.contains("landsat")]
# FINAL DA LEITURA DA TABELA 'DISCOS' - disk

###############################################################################

### CONVERSAO DE VALORES VOLUMES - Início ### 
#fator_convert = (1024*1024)      # KB para GB
fator_convert = (1024*1024*1024) # KB para TB

# V O L U M E -> Converte de KB para TB  (Início)
# Volume Total

soma_volume_total,soma_volume_usado,soma_volume_disponivel,soma_snap_total,soma_snap_usado,soma_snap_disponivel=define_ValoresVolumesOlinda(df_volume, fator_convert)

# (Início) AGGREGATE -> Converte de KB para TB
# OLINDA
soma_aggr_total,soma_aggr_usado,soma_aggr_disponivel=define_ValoresAggregatesOlinda(df_aggr, fator_convert)
# LANDSAT
soma_aggr_total_landsat,soma_aggr_usado_landsat,soma_aggr_disponivel_landsat=define_ValoresAggregatesLandsat(df_aggr_landsat,fator_convert)

# Fecha conexão
conn.close()

lista_dpto = list(df_volume['DEPARTAMENTO'].unique()),

lista_aggr = list(df_volume['VOLUME_AGGREGATE'].unique()),

### FILTRO DE TABELA e RENOMEAÇÃO ### 
# Volume
df_filtro_volume = df_volume.iloc[: , [13, 8, 1, 7, 2, 3, 5, 4, 6, 9, 10, 11, 12]].copy()

df_filtro_volume.columns = ['AGGREGATE','GRUPO','VOLUME','UNIDADE', \
'VOL.TOTAL','VOL.USADO','% USO','VOL.DISPONÍVEL','SVM','SNAP TOTAL', \
'SNAP USADO','SNAP DISPONÍVEL','% SNAP']

df_filtro_volume_landsat = df_volume_landsat.iloc[: , [13, 8, 1, 7, 2, 3, 5, 4, 6, 9, 10, 11, 12]].copy()

df_filtro_volume_landsat.columns = ['AGGREGATE','GRUPO','VOLUME','UNIDADE', \
'VOL.TOTAL','VOL.USADO','% USO','VOL.DISPONÍVEL','SVM','SNAP TOTAL', \
'SNAP USADO','SNAP DISPONÍVEL','% SNAP']

### OPÇÃO DE DROPDOWN ###
# Volume 
opcoes = [x for x in df_volume['DEPARTAMENTO'].unique()]
opcoes.insert(0,'Todas Unidades')
opcoes_aggr = [x for x in df_disk_olinda['NOME_AGGR'].unique()]
opcoes_aggr.insert(0,'Todos Aggregates')
opcoes_aggr_landsat = [x for x in df_disk_landsat['NOME_AGGR'].unique()]
opcoes_aggr_landsat.insert(0,'Todos Aggregates')
opcoes_aggr_geral = [x for x in df_disk['NOME_AGGR'].unique()]
opcoes_aggr_geral.insert(0,'Todos Aggregates')

# Discos 
opcoes_disco = [x for x in df_disk['NODE_DISK'].unique()]
opcoes_disco.insert(0,'Todos Nodes de Disco')

# Grupos 
opcoes_grupo = []
opcoes_grupo.insert(0,'Todos Grupos')
for x in df_grupo:
    departamento = x[0]
    grupo = x[1]
    grupo_concat = departamento+'_'+grupo
    opcoes_grupo.append(grupo_concat)

### INICIA SERVIDOR FLASK E DASH ###
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

FA_icon = html.I(className="bi bi-arrows-angle-expand me-2"),
FA_button =  dbc.Button([FA_icon, ""], className="me-2"),

# Início do Container geral #
# Monta as abas de Menu Geral
app_ambiente_coids.layout=get_Menu

# CHAMADAS DAS TABs #
@app_ambiente_coids.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'),
    Input('subtabs', 'value'),
    Input('subtabs1', 'value'),
)

def render_content(tab, subtab, subtab1):

    if tab == 'tab-sp':
        if subtab == 'tab-1':
                return html.Div([
            dbc.Col(
                dbc.Card([
                    html.Br(),
                    dcc.Dropdown(opcoes_ambiente, value='Selecione o Ambiente', id='ambiente_virtual',style = {'width':'100%'}, placeholder="Selecione o Ambiente", searchable=True),     
                ],style={'margin': '20px', 'width': '300px', 'border':'black'})
            ),

            dbc.Row(
                dbc.Col([
                    dbc.Button("+Info", id="open6", n_clicks=0,
                    style={'position':'right','width': '70%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'14px'}),
                ])            
            ),
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Resumo dos Recursos Computacionais COIDS e SESUP")),
                dbc.ModalBody([
                    html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
                    dash_table.DataTable(
                        id='datatable-row-ids',
                        columns=[
                            {'name': i, 'id': i, 'deletable': False} for i in df1.columns
                            # omit the id column
                            if i != 'id'
                        ],
                        data=df1.to_dict('records'),
                        editable=False,
                        sort_mode='multi',
                        selected_rows=[],
                        page_action='native',
                        page_current= 0,
                        page_size= 25,
                        style_table={'overflowY':'auto', "responsive":True},          
                        style_cell={'fontSize': '12px','text-align': 'justify', 'fontFamily': 'Courier'},
                        style_header={
                            'backgroundColor': 'lavender',
                            'fontWeight': 'bold',
                            'text-align': 'center',
                            'fontSize': '12px', 
                        },
                    )           
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close6", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal6",
            size="xl",
            is_open=False,
            ),

            # Início do gráfico de barras/pizza de memória-------------------------
            dbc.Row([  
                dbc.Card([
                    dbc.Button(FA_icon, id="open7", n_clicks=0, className="me-2", style={'width': '100.7%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                    dbc.Col([dcc.Graph(id = 'grafico_memoria', style={'width':'100%'}, responsive='auto')]),
                ],style={'margin': '2px', 'width': '70%','border':''},className="shadow"),
                
                dbc.Card([
                    dbc.Col([dcc.Graph(id = 'grafico_filtro_memoria', style={'width':'100%'}, responsive='auto')]),
                ],style={'margin':'5px','width': '28%', 'border':' '},className="shadow"),
            ]),    
        # Fim do gráfico de barras/pizza de memória----------------------------
        
            # Início Botões de ZOOM - Gráfico Memória --------------------------------------------
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle(" ")),
                dbc.ModalBody([
                    dbc.Col([
                        dcc.Graph(id='grafico_memoria1', style={'width':'100%'}),
                    ])
                ]),

                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close7", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal7",
            fullscreen=True,
            is_open=False,
            ),
    # Fim Botões de ZOOM - Gráfico Memória --------------------------------------------

        # Início do gráfico de CPU e os 2 cards--------------------------------
        html.Br(),
        dbc.Row([
                dbc.Card([
                    dbc.Button(FA_icon, id="open8", n_clicks=0, className="me-2", style={'width': '100%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                    dbc.Col([dcc.Graph(id = 'grafico_cpu', style={'width':'100%'}, responsive='auto')]),
                ],style={'margin': '2px', 'width': '80%', 'border':' ', "text-align":"center"},className="shadow"),
            

                #-------------------------------------> quantidade
                dbc.Card(id='card1_descritivo', style={'margin-left':'5px' ,'width': '18%', 'height':'100%', 'top':'5px', 'text-align':'center','paddingTop': '16px'}, className="shadow"),
        ]),    

        # Início Botões de ZOOM - Gráfico CPU -----------------------------
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle(" ")),
                dbc.ModalBody([
                    dbc.Col([
                        dcc.Graph(id='grafico_cpu1', style={'width':'100%'}),
                    ])
                ]),

                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close8", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal8",
            fullscreen=True,
            is_open=False,
            ),
            # Fim Botões de ZOOM - Gráfico Memória ------------------------
            
            # Ícone de zoom Tabela Ambiente Virtual - Início --------------
            html.Br(),
                dbc.Row([    
                    dbc.Card([
                        dbc.Col([
                            dbc.Button(FA_icon, id="open9", n_clicks=0, className="me-2", style={'width': '100.5%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}), 
                            html.Div(id='tabela_consumo_vm'), # id da tabela de consumo
                        ],style={'width': '100%', 'border':' '})
                    ],style={'width': '100%', 'border':' '},className="shadow"),
                ]),

                    dbc.Modal([
                        dbc.ModalHeader(dbc.ModalTitle(" ")),
                        dbc.ModalBody([
                            html.Div(id='tabela-dados-ambientevirtual1'), # id da tabela do ambiente
                        ]),

                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="close9", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="modal9",
                    fullscreen=True,
                    is_open=False,
                    ),            

                ]), 
                # Ícone de zoom Tabela Ambiente Virtual - Final -----------
        #FIM TAB-1-------------> Chamada de gráfico/tabela Ambiente Virtual            

        #TAB-2 -------------> Chamada de gráfico USO HOST - ZABBIX
        elif subtab == 'tab-2':
                return html.Div([

                # Dropdown do host
                    dbc.Row([
                        html.Br(),
                        dbc.Col(dcc.Dropdown(host_dropdown, value='Selecione o host', id='uso_host',style = {'width':'250px', 'margin-top':'10px'}, placeholder="Selecione o host", searchable=True)),     
                        dbc.Col(dcc.Dropdown(numero_dias_zabbix, value='15', id='periodo',style = {'width':'100px', 'margin-top':'10px'}, placeholder="N.dias", searchable=True)),
                    ],style={'width':'600px', 'margin-top':'30px', 'margin-bottom':'30px'}),

                    dbc.Row([ 
                        dbc.Card([
                            dbc.Col(id='descricao_vms'),
                            dbc.Col([dcc.Graph(id = 'usohost_cpu', style={'width':'100%'}, responsive='auto')]),
                            dbc.Col([dcc.Graph(id = 'usohost_memoria', style={'width':'100%'}, responsive='auto')]),
                        ],style={'margin': '5px','width': '100%', 'border':' '},className="shadow"),
                    ]),    
                ])     

        #FIM tab-2 -  Final Chamada USO HOST - ZABBIX

        elif subtab == 'tab-3':
                return html.Div([
                # Dropdown do host
                    dbc.Row([
                        html.Br(),
                        dbc.Col(dcc.Dropdown(numero_dias_super, value='30', id='periodo_super',style = {'width':'100px', 'margin-top':'10px'}, placeholder="N.dias", searchable=True)),
                    ],style={'width':'600px', 'margin-top':'30px', 'margin-bottom':'30px'}),

                    dbc.Row([ 
                        dbc.Card([
                            dbc.Col([dcc.Graph(id = 'egeon', style={'width':'100%'}, responsive='auto')]),
                            dbc.Col([dcc.Graph(id = 'xc50', style={'width':'100%'}, responsive='auto')]),
                        ],style={'margin': '5px','width': '100%', 'border':' '},className="shadow"),
                    ]),    
                ])     


    if tab == 'tab-sa':
        if subtab1 == 'tab-4':
                return html.Div([
                    dbc.Row([                                   
                        dbc.Col(dcc.Dropdown(opcoes_aggr_geral, value='Selecione o Aggregate', id='volume_aggr',style = {'width':'300px', 'margin-top':'10px'}, placeholder="Selecione o Aggregate", searchable=True),     ),
                        dbc.Col(dcc.Dropdown(opcoes, value='Selecione a Unidade', id='volume_unidade',style = {'width':'300px', 'margin-top':'10px'}, placeholder="Selecione a Unidade", searchable=True),     ),
                    ],style={'width':'660px', 'margin-top':'30px', 'margin-bottom':'30px'}),

                dbc.Card([  
                    dbc.Button(FA_icon, id="open13", n_clicks=0, className="me-2", style={'width': '100%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                    dbc.Row([ 
                        dbc.Row([                            
                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco_quantidade', style={'height':'36vh', 'width':'98%'})]),
                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco', style={'height':'36vh', 'width':'98%'})]),
                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco_olinda', style={'height':'36vh', 'width':'98%'})]),
                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco_landsat', style={'height':'36vh', 'width':'98%'})]),
                        ],style={'paddingTop': '1px', 'paddingBottom': '1px','color': 'white', 'background':'PowderBlue'}),    
                        
                        dbc.Row([
                                dbc.Col([dcc.Graph(id = 'grafico_pie_aggr', style={'height':'36vh', 'width':'98%'})]),
                                dbc.Col([dcc.Graph(id = 'grafico_pie_aggr_landsat', style={'height':'36vh', 'width':'98%'})]),
                                dbc.Col([dcc.Graph(id = 'grafico_volume', style={'height':'36vh', 'width':'98%'})]),
                                dbc.Col([dcc.Graph(id = 'grafico_volume_landsat', style={'height':'36vh', 'width':'98%'})]),
                        ],style={'paddingTop': '1px', 'paddingBottom': '1px','color': 'white', 'background':'PowderBlue'}),
                        dbc.Row([
                                dbc.Col(),
                                dbc.Col(),
                                dbc.Col([dcc.Graph(id = 'grafico_snap', style={'height':'36vh', 'width':'98%'})]),
                                dbc.Col([dcc.Graph(id = 'grafico_snap_landsat', style={'height':'36vh', 'width':'98%'})]),
                        ],style={'paddingTop': '1px', 'paddingBottom': '1px','color': 'white', 'background':'PowderBlue'}),
                    ]),
                ],style={'display': 'flex', 'border':' '},className="shadow"),   
                    
                        # Ícone de zoom Gráficos Pie Aggregate - Início ---------------------------------------------------------------------
                            dbc.Modal([
                                dbc.ModalHeader(dbc.ModalTitle(" ")),
                                dbc.ModalBody([                               
                                    dbc.Row([ 
                                        dbc.Row([                            
                                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco_quantidade1', style={'width':'100%'})]),
                                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco1', style={'width':'100%'})]),
                                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco_olinda1', style={'width':'100%'})]),
                                                dbc.Col([dcc.Graph(id = 'grafico_pie_disco_landsat1', style={'width':'100%'})]),
                                        ]),    
                                        dbc.Row([
                                            dbc.Col(children='AGGREGATES', style={'width':'400px', 'margin-bottom':'10px','margin-top':'10px', 'textAlign': 'center'}),
                                            dbc.Col(children='VOLUMES', style={'width':'400px', 'margin-bottom':'10px','margin-top':'10px', 'textAlign': 'center'}),
                                    ]),    
                                        dbc.Row([
                                                dbc.Col([dcc.Graph(id = 'grafico_pie_aggr1', style={'width':'100%'})]),
                                                dbc.Col([dcc.Graph(id = 'grafico_pie_aggr_landsat1', style={'width':'100%'})]),
                                                dbc.Col([dcc.Graph(id = 'grafico_volume1', style={'width':'100%'})]),
                                                dbc.Col([dcc.Graph(id = 'grafico_volume_landsat1', style={'width':'100%'})]),
                                        ]),
                                    ]),
                                ]),
                                dbc.ModalFooter(
                                    dbc.Button(
                                        "Close", id="close13", className="ms-auto", n_clicks=0
                                    )
                                ),
                            ],
                        id="modal13",
                        fullscreen=True,
                        is_open=False,
                        ),

                    # Gráfico de barras para demonstrar os discos juntos de aggregates e volumes
                    dbc.Row([
                        dbc.Card([
                            dbc.Col([
                                dbc.Button(FA_icon, id="open18", n_clicks=0, className="me-2", style={'width': '100.5%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                                dbc.Col([dcc.Graph(id = 'grafico_barras_disco_aggr', style={'width':'100%', 'height':'100%'}, responsive='auto')]),
                            ]),
                        ],style={'width': '98.5%', 'border':' '},className="shadow"),
                        
                        # Ícone de zoom Tabela Volume - Início ----------------------------------------------------------------

                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                #html.Div(id='grafico_barras_disco_aggr1'), # id da tabela do ambiente
                                dbc.Col([
                                    dcc.Graph(id = 'grafico_barras_disco_aggr1', style={'width':'100%','height':'82vh'}),
                                ], style={'width':'800%', 'overflowX':'scroll','height': 1150})
                            ]),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close18", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal18",
                        fullscreen=True,
                        is_open=False,
                        ),            
                    ]),

                    dbc.Row([
                        dbc.Card([
                            dbc.Col([
                                dbc.Button(FA_icon, id="open19", n_clicks=0, className="me-2", style={'width': '100.5%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                                html.Div(id='tabela-dados-discos'), # id da tabela do ambiente
                            ],style={'width': '100%', 'border':' '})
                        ],style={'width': '98.5%', 'border':' '},className="shadow"),
                        
                        # Ícone de zoom Tabela Volume - Início ----------------------------------------------------------------

                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                html.Div(id='tabela-dados-discos1'), # id da tabela do ambiente
                            ]),

                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close19", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal19",
                        fullscreen=True,
                        is_open=False,
                        ),            
                    ]),
                ]),

        elif subtab1 == 'tab-5':
                return html.Div([
                    dbc.Row([                                   
                        dbc.Col(dcc.Dropdown(opcoes_aggr, value='Selecione o Aggregate Olinda', id='volume_aggr',style = {'width':'300px', 'margin-top':'10px'}, placeholder="Selecione o Aggregate Olinda", searchable=True),     ),
                        dbc.Col(dcc.Dropdown(opcoes_aggr_landsat, value='Selecione o Aggregate Landsat', id='volume_aggr_landsat',style = {'width':'300px', 'margin-top':'10px'}, placeholder="Selecione o Aggregate Landsat", searchable=True),     ),
                    ],style={'width':'660px', 'margin-top':'30px', 'margin-bottom':'30px'}),

                    #-------------> Chamada de gráfico/tabela Aggregate Olinda
                    dbc.Row([  
                        dbc.Card([
                            dbc.Button(FA_icon, id="open14", n_clicks=0, className="me-2", style={'width': '100%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                            dbc.Col([dcc.Graph(id = 'grafico_aggr_volume', style={'width':'100%', 'height':'100%'}, responsive='auto')]),
                        ],style={'width': '70%','border':' '},className="shadow"),
                        
                        # Ícone de zoom Aggregate - Início ---------------------------------------------------------------------
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                dbc.Col([
                                    dcc.Graph(id='grafico_aggr_volume1', style={'width':'100%','height':'85vh'}),
                                ],style={'width':'800%', 'overflowX':'scroll','height': 1150})
                            ]),

                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close14", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal14",
                        fullscreen=True,
                        is_open=False,
                        ),
                        
                        # Ícone de zoom Aggregate - final ---------------------------------------------------------------------
                        
                            dbc.Card([
                                dbc.Button(FA_icon, id="open15", n_clicks=0, className="me-2", style={'width': '100%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                                dbc.Col([dcc.Graph(id = 'grafico_pie_aggr', style={'width':'100%'})]),
                                ],style={'margin': '5px','width': '28%', 'border':''},className="shadow"),
                            ]),

                        # Ícone de zoom Gráficos Pie Aggregate - Início ---------------------------------------------------------------------
                            dbc.Modal([
                                dbc.ModalHeader(dbc.ModalTitle(" ")),
                                dbc.ModalBody([
                                    dbc.Col([
                                        dcc.Graph(id='grafico_pie_aggr1', style={'width':'100%'}),
                                    ]),
                                    dbc.Col([
                                        dcc.Graph(id='grafico_pie_aggr1', style={'width':'100%'}),
                                    ])
                            ]),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close15", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal15",
                        fullscreen=True,
                        is_open=False,
                        ),
                        
                        # Ícone de zoom Gráficos Pie Aggregate - final ---------------------------------------------------------------------
                    html.Br(),
                    dbc.Row([
                        dbc.Card([
                            dbc.Col([
                                dbc.Button(FA_icon, id="open16", n_clicks=0, className="me-2", style={'width': '100.5%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}), 
                                html.Div(id='tabela-dados-aggregates'), # id da tabela do ambiente
                            ],style={'width': '100%', 'border':' '})
                        ],style={'width': '98.5%', 'border':' '},className="shadow"),

                        # Ícone de zoom Tabela Aggregate - Início ----------------------------------------------
                
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                html.Div(id='tabela-dados-aggregates1'), # id da tabela do ambiente
                            ]),

                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close16", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal16",
                        fullscreen=True,
                        is_open=False,
                        ),            
                    ]),

                    dbc.Row([  
                        dbc.Card([
                            dbc.Button(FA_icon, id="open3", n_clicks=0, className="me-2", style={'width': '100%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                            dbc.Col([dcc.Graph(id = 'grafico_aggr_volume_landsat', style={'width':'100%', 'height':'100%'}, responsive='auto')]),
                        ],style={'width': '70%','border':' '},className="shadow"),
                        
                        # Ícone de zoom Aggregate - Início ----------------
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                dbc.Col([
                                    dcc.Graph(id='grafico_aggr_volume_landsat1', style={'width':'100%','height':'85vh'}),
                                ],style={'width':'800%', 'overflowX':'scroll','height': 1150})
                            ]),

                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close3", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal3",
                        fullscreen=True,
                        is_open=False,
                        ),
                        
                        # Ícone de zoom Aggregate - final ---------------------------------------------------------------------
                            dbc.Card([
                                dbc.Button(FA_icon, id="open4", n_clicks=0, className="me-2", style={'width': '100%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                                dbc.Col([dcc.Graph(id = 'grafico_pie_aggr_landsat', style={'width':'100%'})]),
                                ],style={'margin': '5px','width': '28%', 'border':''},className="shadow"),
                            ]),

                            # Ícone de zoom Gráficos Pie Aggregate - Início ---------------------------------------------------------------------
                            dbc.Modal([
                                dbc.ModalHeader(dbc.ModalTitle(" ")),
                                dbc.ModalBody([
                                    dbc.Col([
                                        dcc.Graph(id='grafico_pie_aggr_landsat1', style={'width':'100%'}),
                                    ]),
                                    dbc.Col([
                                        dcc.Graph(id='grafico_pie_aggr_landsat1', style={'width':'100%'}),
                                    ])
                            ]),

                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close4", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal4",
                        fullscreen=True,
                        is_open=False,
                        ),
                        
                        # Ícone de zoom Gráficos Pie Aggregate - final ---------------------------------------------------------------------
                    html.Br(),
                    dbc.Row([
                        dbc.Card([
                            dbc.Col([
                                dbc.Button(FA_icon, id="open17", n_clicks=0, className="me-2", style={'width': '100.5%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}), 
                                html.Div(id='tabela-dados-aggregates-landsat'), # id da tabela do ambiente
                            ],style={'width': '100%', 'border':' '})
                        ],style={'width': '98.5%', 'border':' '},className="shadow"),

                        # Ícone de zoom Tabela Aggregate - Início ----------------------------------------------
                
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                html.Div(id='tabela-dados-aggregates-landsat1'), # id da tabela do ambiente
                            ]),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close17", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal17",
                        fullscreen=True,
                        is_open=False,
                        ),            
                    ]),
                ]),
                # Ícone de zoom Tabela Aggregate - final --------------------------------------------

        elif subtab1 == 'tab-6':
                return html.Div([
                    dbc.Row([
                        dbc.Col(
                            dbc.Card([
                                dcc.Dropdown(opcoes, value='Selecione a Unidade', id='volume_unidade',style = {'width':'100%', 'margin-top':'10px'}, placeholder="Selecione a Unidade", searchable=True),     
                            ],style={'margin': '20px', 'width': '300px', 'border':'black'})
                        ),
                    ]),

                    #TAB-3 -> Chamada de gráfico/tabela Volume
                    dbc.Row([  
                        dbc.Card([
                            dbc.Button(FA_icon, id="open1", n_clicks=0, className="me-2", style={'width': '100.7%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                            dbc.Col([dcc.Graph(id = 'grafico_volume_unidade', style={'width':'100%', 'height':'100%'}, responsive='auto')]),
                        ],style={'margin': '2px', 'width': '70%','border':' '},className="shadow"),
                        dbc.Card([
                            dbc.Col([dcc.Graph(id = 'grafico_volume', style={'width':'100%'}, responsive='auto')]),
                            dbc.Col([dcc.Graph(id = 'grafico_snap', style={'width':'100%'}, responsive='auto')]),
                        ],style={'margin': '5px','width': '28%', 'border':' '},className="shadow"),
                    ]),    

                        # Ícone de zoom Volume - Início -----------------------------------------------------------------------
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                dbc.Col([
                                    dcc.Graph(id='grafico_volume_unidade1', style={'width':'100%','height':'85vh'}),
                                ],style={'width':'800%', 'overflowX':'scroll', 'overflowY':'scroll','height': 1150})                            
                            ]),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close1", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal1",
                        fullscreen=True,
                        is_open=False,
                        ),
                        
                    # Ícone de zoom Volume - final ------------------------------------------------------------------------
                    dbc.Row([
                        dbc.Card([
                            dbc.Col([
                                dbc.Button(FA_icon, id="open2", n_clicks=0, className="me-2", style={'width': '100.5%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                                html.Div(id='tabela-dados-volumes'), # id da tabela do ambiente
                            ],style={'width': '100%', 'border':' '})
                        ],style={'width': '98.5%', 'border':' '},className="shadow"),
                        
                        # Ícone de zoom Tabela Volume - Início ----------------------------------------------------------------

                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                html.Div(id='tabela-dados-volumes1'), # id da tabela do ambiente
                            ]),

                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close2", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal2",
                        fullscreen=True,
                        is_open=False,
                        ),            
                    ]),
                ]),
                    # Ícone de zoom Tabela Volume - final ---------------------------------------------------------------------

        elif subtab1 == 'tab-7':
                return html.Div([
                    dbc.Row([
                        dbc.Col(
                            dbc.Card([
                                dcc.Dropdown(opcoes, value='Selecione a Unidade', id='volume_unidade',style = {'width':'100%', 'margin-top':'10px'}, placeholder="Selecione a Unidade", searchable=True),     
                            ],style={'margin': '20px', 'width': '300px', 'border':'black'})
                        ),
                    ]),
                html.Br(),
                dbc.Row([
                        # 1 card para cada host
                        html.Br(),
                        dbc.Row([  
                            dbc.Row(id = 'card_monitor_gt')
                        ]),  
                    ]),
                ]),

        elif subtab1 == 'tab-8':
                return html.Div([
                    dbc.Row([
                        dbc.Col(
                            dbc.Card([
                                dcc.Dropdown(opcoes, value='Selecione a Unidade', id='volume_unidade',style = {'width':'100%', 'margin-top':'10px'}, placeholder="Selecione a unidade", searchable=True),     
                            ],style={'margin': '20px', 'width': '300px', 'border':'black'})
                        ),
                    ]),
                    dbc.Row([  
                        dbc.Card([
                            dbc.Button(FA_icon, id="open20", n_clicks=0, className="me-2", style={'width': '100.7%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                            dbc.Col([dcc.Graph(id = 'grafico_volume_grupo', style={'width':'100%', 'height':'100%'}, responsive='auto')]),
                        ],style={'margin': '2px', 'width': '70%','border':' '},className="shadow"),
                        dbc.Card([
                            dbc.Col([dcc.Graph(id = 'grafico_grupo', style={'width':'100%'}, responsive='auto')]),
                        ],style={'margin': '5px','width': '28%', 'border':' '},className="shadow"),
                    ]),    
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                dbc.Col([
                                    dcc.Graph(id='grafico_volume_grupo1', style={'width':'100%','height':'85vh'}),
                                ],style={'width':'800%', 'overflowX':'scroll', 'overflowY':'scroll','height': 1150})                            
                            ]),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close20", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal20",
                        fullscreen=True,
                        is_open=False,
                        ),
                    dbc.Row([
                        dbc.Card([
                            dbc.Col([
                                dbc.Button(FA_icon, id="open21", n_clicks=0, className="me-2", style={'width': '100.5%','border':'white','text-align':'right', 'color': 'black', 'background-color':'white','font-size':'18px'}),
                                html.Div(id='tabela-dados-grupo'), 
                            ],style={'width': '100%', 'border':' '})
                        ],style={'width': '98.5%', 'border':' '},className="shadow"),
                        
                        # Ícone de zoom Tabela Volume - Início ----------------------------------------------------------------

                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(" ")),
                            dbc.ModalBody([
                                html.Div(id='tabela-dados-grupo1'), 
                            ]),

                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close", id="close21", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="modal21",
                        fullscreen=True,
                        is_open=False,
                        ),            
                    ]),
                ]),

    elif tab == 'tab-9':
        return html.Div([
            dbc.Col(
                dbc.Card([
                    html.Br(),
                    dcc.Dropdown(opcoes_ambiente, value='Selecione o Ambiente', id='ambiente_virtual',style = {'width':'100%'}, placeholder="Selecione o Ambiente", searchable=True),     
                ],style={'margin': '20px', 'width': '300px', 'border':'black'})
            ),
            html.Br(),
            dbc.Row([
                dbc.Card([
                    dbc.Col([dcc.Graph(id = 'card3_consumo_vm', style={'width':'100%'}, responsive='auto')]),
                        ],style={'margin': '2px', 'width': '80%', 'border':' ', "text-align":"center"},className="shadow"),
                    
                    # Descritivo do consumo OPEX
                    dbc.Card(id = 'consumo_card_opex', style={'margin-left':'5px' ,'width': '18%', 'height':'100%', 'top':'5px', 'text-align':'center','paddingTop': '16px'}, className="shadow")
                    ]),    

                    html.Br(),
                    dbc.Row([  
                        dbc.Row(id = 'card_info_por_host')
                    ]),  
            ]),

    elif tab == 'tab-10':
        return html.Div([
            dbc.Col(
                dbc.Card([
                    html.Br(),
                    dcc.Dropdown(opcoes_ambiente, value='Selecione o Ambiente', id='ambiente_virtual',style = {'width':'100%'}, placeholder="Selecione o Ambiente", searchable=True),     
                ],style={'margin': '20px', 'width': '300px', 'border':'black'})
            ),

             html.Br(),
            dbc.Row([
                    # 1 card para cada host
                    html.Br(),
                    dbc.Row([  
                        dbc.Row(id = 'card_resumo_financeiro')
                    ]),  
                ]),
            ]),

#######################################################################
### FUNÇÕES E CALL BACK ###

@app_ambiente_coids.callback(
    Output('card1_descritivo', 'children',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)
def update_card1_descritivo(value):
    if value == "Ambientes Virtuais":
        ########################################################## nCPU
        # Processa quantidade de Ambientes Virtuais, Hosts Físicos e VMs
        tot_geral_ambiente = len(list(df_vm['LABEL_POOL'].unique()))
        tot_geral_hostfisico = len(list(df_vm['HOST'].unique()))
        tot_geral_vm = len(list(df_vm['NOME_VM'].unique()))               

        # Converte nCPU string para Número
        tot_geral_cpu_host = (df_vm['nCPU_HOST'].astype(int)).sum()
        tot_geral_cpu_vm = (df_vm['nCPU_VM'].astype(int)).sum()
        tot_geral_cpu_livre = tot_geral_cpu_host - tot_geral_cpu_vm

        color = "Black",
        if tot_geral_cpu_livre < 0:
            color = "Red",
        
        card =  dbc.Col([
                html.Div("Descritivo " + value, style={"font-weight":"bold","text-transform":"uppercase","font-size":"16px","color":"darkblue", "text-align":"center", "background":"white"}),
                html.Br(),
            dbc.ListGroup(
                [
                    dbc.ListGroupItem("Ambiente Virtual: " + str(tot_geral_ambiente),color="#E5ECF6"),
                    dbc.ListGroupItem("Servidor físico: " + str(tot_geral_hostfisico),color="#F0FFFF"),
                    dbc.ListGroupItem("Quantidade (VM): " + str(tot_geral_vm),color="#E5ECF6"),
                    html.Br(),
                    html.Div("Nº de CPUs", style={"font-size":"16px","color":"darkblue","font-weight": "bold", "text-align":"center", "background":"white"}),
                    html.Br(),
                    dbc.ListGroupItem("Total: " + str(tot_geral_cpu_host),color="#E5ECF6"),
                    dbc.ListGroupItem("Provisionado: " + str(tot_geral_cpu_vm),color="#F0FFFF"),
                    dbc.ListGroupItem("Disponível: " + str(tot_geral_cpu_livre),color="#E5ECF6", 
                                    style = 
                                        { 
                                            'color': color,
                                            'font-weight':'bold',
                                        })   
                                    
                ],
                flush=True,
            ),
            ],style={'width': '100%', 'text-align':'justify','paddingTop': '10px', 'paddingBottom': '10px',"font-size":"14px"}, className="text-justify shadow"),


    else: 
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :]      

        ########################################################### nCPU
        # Processa quantidade de Ambientes Virtuais, Hosts Físicos e VMs
        tot_geral_ambiente = len(list(tabela_filtrada['LABEL_POOL'].unique()))
        tot_geral_hostfisico = len(list(tabela_filtrada['HOST'].unique()))
        tot_geral_vm = len(list(tabela_filtrada['NOME_VM'].unique()))               

        # Converte nCPU string para Número
        tot_geral_cpu_host = (tabela_filtrada['nCPU_HOST'].astype(int)).sum()
        tot_geral_cpu_vm = (tabela_filtrada['nCPU_VM'].astype(int)).sum()
        tot_geral_cpu_livre = tot_geral_cpu_host - tot_geral_cpu_vm
        
        color = "Black",
        if tot_geral_cpu_livre < 0:
            color = "Red",

        card =  dbc.Col([
                html.Div("Descritivo " + value, style={"font-weight":"bold","text-transform":"uppercase","font-size":"16px","color":"darkblue", "text-align":"center", "background":"white"}),
                html.Br(),
            dbc.ListGroup(
                [
                    dbc.ListGroupItem("Ambiente Virtual: " + str(tot_geral_ambiente),color="#E5ECF6"),
                    dbc.ListGroupItem("Servidor físico: " + str(tot_geral_hostfisico),color="#F0FFFF"),
                    dbc.ListGroupItem("Quantidade (VM): " + str(tot_geral_vm),color="#E5ECF6"),
                    html.Br(),
                    html.Div("Nº de CPUs", style={"font-size":"16px","color":"darkblue","font-weight": "bold", "text-align":"center", "background":"white"}),
                    html.Br(),
                    dbc.ListGroupItem("Total: " + str(tot_geral_cpu_host),color="#E5ECF6"),
                    dbc.ListGroupItem("Provisionado: " + str(tot_geral_cpu_vm),color="#F0FFFF"),
                    dbc.ListGroupItem("Disponível: " + str(tot_geral_cpu_livre),color="#E5ECF6", 
                                    style = 
                                        { 
                                            'color': color,
                                            'font-weight':'bold',
                                        })   
                ],
                flush=True,
            ),
            ],style={'width': '100%', 'text-align':'justify','paddingTop': '10px', 'paddingBottom': '10px',"font-size":"14px"}, className="text-justify shadow"),
    return card

## GRÁFICO - CONSUMO OPEX ### 
@app_ambiente_coids.callback(
        Output('card3_consumo_vm', 'figure',allow_duplicate=True),
        Input('ambiente_virtual','value'),
        prevent_initial_call = True,
)

def update_card3_consumo_vm(value):
    if value == "Ambientes Virtuais":
        ################################################# CONSUMO GERAL
        # Filtra todos hosts sem repetir, ref. a todos os ambientes
        filtro_host_fisico = df_vm['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', \
                'DT_ATUAL', 'TEMPO_DEPRECIADO', 'VL_ATUAL_DEPRECIADO', \
                'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            df_vm_hostselecionado =  df_vm.loc[df_vm['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'], \
                                    infer_datetime_format=True, \
                                    dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # CUSTO OPERACIONAL - Seta valores da tabela contrato
            # Dinâmico - Conforme inclusão na tabela 
            # Valores fixos 
            # Retira R$, ponto e substitui vírgula por ponto na casa decimal
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str.replace\
                                        ('\D','', regex=True))
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str[0:-2] \
                                        + '.' + df_contrato[column].str[-2:])

            df_contrato_ativo = df_contrato.loc[df_contrato['status_contrato'] == 'ATIVO']
            contrato_operacional_mensal = round(df_contrato_ativo['value_contrato'].astype(float).sum()/12,2)

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            # Nova fórmula - Inclui contratos operacionais
            # =SE(K2>0;((B$2+ (  ($B$7/12)+($B$8/12)+($B$9/12) )/G$2  +(B$4/B$5)/12)/G$2)*K2;0)

            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia \
                                            + (contrato_operacional_mensal \
                                            / tot_geral_cpu_host) \
                                            + (vl_atual_depreciado \
                                            / tempo_depreciado)/12) \
                                            / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0


            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core \
                                            * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core \
                                                    * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            #df_opex.append([df_vm_hostselecionado['LABEL_POOL'].unique(), df_consumo_host['NOME'],\
            df_opex.append([ambiente_selecionado, host_ambiente, \
                            valor_compra, dt_compra_str, dt_atual_str,\
                            tempo_depreciado, vl_atual_depreciado, \
                            custo_mensal_energia, tot_geral_cpu_host, \
                            vl_mensal_do_core, custo_geral_mensal_host,\
                            tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        ################# Área de geração do gráfico ###################
        df1_opex = pd.DataFrame(df_opex,columns=cols)        
        fig_custo_card3 = go.Figure(data = [
            go.Bar(x = [df1_opex['AMBIENTE'],df1_opex['HOST']], y = df1_opex['CUSTO_MENSAL_HOST'],
                name = 'Hosts Físicos', marker_color = '#ED9121', 
                text = df1_opex['CUSTO_MENSAL_HOST'].apply(locale.currency,grouping=True, symbol=False),
                textposition='inside',textfont_size=18),
            go.Bar(x = [df1_opex['AMBIENTE'],df1_opex['HOST']], y = df1_opex['VL_MENSAL_PROVISIONADO'],
            name = 'Hosts Virtuais', marker_color = '#3D59AB', 
            text = df1_opex['VL_MENSAL_PROVISIONADO'].apply(locale.currency,grouping=True, symbol=False),
            textposition = 'inside',textfont_size=18),
            ] 
        )                                   
        fig_custo_card3.update_layout(title = '<b>OPEX - COIDS/SESUP     Data Atual: ' + dt_atual_str, barmode = 'group',
        legend = dict(traceorder = 'normal', x=1, y=1.02,
            yanchor="bottom", xanchor="right", orientation="h"),
            font = dict(family = "Courier", size = 16, color = "black"),
        ),
        font = dict(family="Courier New, monospace",size=16),
        fig_custo_card3.update_yaxes(title_text='Valor Mensal R$'),
    
    else: 
        # Filtra os hosts referentes apenas ao ambiente selecionado
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :] 
        ########################################################### CONSUMO POR AMBIENTE
        # Filtra todos os hosts sem repetir, referente a todos os ambientes
        filtro_host_fisico = tabela_filtrada['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', \
                'DT_ATUAL', 'TEMPO_DEPRECIADO', 'VL_ATUAL_DEPRECIADO', \
                'CUSTO_MENSAL_ENERGIA','NCPU_HOST','VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_host selecionado
        # LAÇO FOR PARA CARDS - GERAR GRUPOS

        for host_ambiente in filtro_host_fisico:
            df_vm_hostselecionado =  tabela_filtrada.loc[tabela_filtrada['HOST'] == host_ambiente.lower(), :] 
            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # CUSTO OPERACIONAL - Seta valores da tabela contrato
            # Dinâmico - Conforme inclusão na tabela 
            # Valores fixos 
            # Retira R$, ponto e substitui vírgula por ponto na casa decimal
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str.replace('\D','', regex=True))
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str[0:-2] + '.' + df_contrato[column].str[-2:])

            df_contrato_ativo = df_contrato.loc[df_contrato['status_contrato'] == 'ATIVO']

            contrato_operacional_mensal = round(df_contrato_ativo['value_contrato'].astype(float).sum()/12,2)

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            # Nova fórmula - Inclui contratos operacionais
            # =SE(K2>0;((B$2+ (  ($B$7/12)+($B$8/12)+($B$9/12) )/G$2  +(B$4/B$5)/12)/G$2)*K2;0)

            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (contrato_operacional_mensal / tot_geral_cpu_host) \
                                            + (vl_atual_depreciado/tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0


            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  

        ################# Área de geração do gráfico ###################        
        fig_custo_card3 = go.Figure(data = [
            go.Bar(x = [df1_opex['AMBIENTE'],df1_opex['HOST']], y = df1_opex['CUSTO_MENSAL_HOST'],
                name = 'Hosts Físicos', marker_color = '#ED9121', 
                text = df1_opex['CUSTO_MENSAL_HOST'].apply(locale.currency,grouping=True, symbol=False),
                textposition='inside',textfont_size=18),
            go.Bar(x = [df1_opex['AMBIENTE'],df1_opex['HOST']], y = df1_opex['VL_MENSAL_PROVISIONADO'],
            name = 'Hosts Virtuais', marker_color = '#3D59AB', 
            text = df1_opex['VL_MENSAL_PROVISIONADO'].apply(locale.currency,grouping=True, symbol=False),
            textposition = 'inside',textfont_size=18),
            ] 
        )                                   
        fig_custo_card3.update_layout(title = '<b>OPEX - COIDS/SESUP     Data Atual: ' + dt_atual_str, barmode = 'group',
        legend = dict(traceorder = 'normal', x=1, y=1.02,
            yanchor="bottom", xanchor="right", orientation="h"),
            font = dict(family = "Courier", size = 16, color = "black"),
        ),
        font = dict(family="Courier New, monospace",size=16),
        fig_custo_card3.update_yaxes(title_text='Valor Mensal R$'),

    return fig_custo_card3 

@app_ambiente_coids.callback(
    Output('consumo_card_opex', 'children',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)

def update_card_opex(value):
    if value == "Ambientes Virtuais":
        ########################################################### CONSUMO GERAL
        # Filtra todos os hosts sem repetir, referente a todos os ambientes
        filtro_host_fisico = df_vm['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            df_vm_hostselecionado =  df_vm.loc[df_vm['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # CUSTO OPERACIONAL - Seta valores da tabela contrato
            # Dinâmico - Conforme inclusão na tabela 
            # Valores fixos 
            # Retira R$, ponto e substitui vírgula por ponto na casa decimal
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str.replace('\D','', regex=True))
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str[0:-2] + '.' + df_contrato[column].str[-2:])

            df_contrato_ativo = df_contrato.loc[df_contrato['status_contrato'] == 'ATIVO']

            lista_contrato_ativo = pd.concat([df_contrato_ativo.name_contrato,\
                                            (df_contrato_ativo.value_contrato.astype(float)).apply(locale.currency,grouping=True)], axis=1).to_string\
                                            (index=False,header=False)

            contrato_operacional_mensal = round(df_contrato_ativo['value_contrato'].astype(float).sum()/12,2)

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            # Nova fórmula - Inclui contratos operacionais
            # =SE(K2>0;((B$2+ (  ($B$7/12)+($B$8/12)+($B$9/12) )/G$2  +(B$4/B$5)/12)/G$2)*K2;0)

            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (contrato_operacional_mensal / tot_geral_cpu_host) \
                                            + (vl_atual_depreciado/tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0

            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica, custo do equipamento depreciado
            # e custos operacionais (Ex.: CETEST, HelpDesk/NOC, Sysadmin)
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)

        card = dbc.Col([
            html.Div(value, style={"font-weight": "bold","text-transform":"uppercase","font-size":"20px", "color":"darkblue", "text-align":"center", "background":"white"}),
            html.Br(),
            dbc.ListGroup(
                [
                    dbc.ListGroupItem("Aquisição   : " + locale.currency(total_custo_compra, grouping=True, symbol=True),color="#E5ECF6"),
                    dbc.ListGroupItem("Depreciação : " + locale.currency(total_custo_compra_depreciado, grouping=True, symbol=True),color="#F0FFFF"),
                    dbc.ListGroupItem("Energia     : " + locale.currency(total_gasto_energetico, grouping=True, symbol=True),color="#E5ECF6"),
                    html.Br(),
                    html.Div("CONTRATOS", style={"font-size":"20px","color":"darkblue","font-weight": "bold", "text-align":"center", "background":"white"}),
                    html.Br(),                    
                    dbc.ListGroupItem(lista_contrato_ativo, style = {'text-align':'right',"font-size":"14px"},color="#F0FFFF"),

                    html.Br(),
                    html.Div("CUSTOS MENSAIS", style={"font-size":"20px","color":"darkblue","font-weight": "bold", "text-align":"center", "background":"white"}),
                    html.Br(),                    
                    dbc.ListGroupItem("Core: " + locale.currency(total_custo_por_core, grouping=True, symbol=True),color="#E5ECF6"),
                    dbc.ListGroupItem("Hosts Físicos: " + locale.currency(total_mensal_custo_host, grouping=True, symbol=True),color="#F0FFFF"),
                    dbc.ListGroupItem("Hosts Virtuais: " + locale.currency(total_custo_provisionado, grouping=True, symbol=True),color="#E5ECF6"),
                ],
                flush=True,
            ), 
            ],style={'width': '100%', 'text-align':'justify','paddingTop': '10px', "font-size":"14px"}),

    else: 
        # Filtra os hosts referentes apenas ao ambiente selecionado
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :] 
        filtro_host_fisico = tabela_filtrada['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            df_vm_hostselecionado =  tabela_filtrada.loc[tabela_filtrada['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (vl_atual_depreciado / tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0

            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)
  
        card = dbc.Col([
                html.Div(value, style={"font-weight":"bold","text-transform":"uppercase","font-size":"20px","color":"darkblue","text-align":"center","background":"white"}),
                html.Br(),
            dbc.ListGroup(
                [
                    dbc.ListGroupItem("Aquisição   : " + locale.currency(total_custo_compra, grouping=True, symbol=True),color="#E5ECF6"),
                    dbc.ListGroupItem("Depreciação : " + locale.currency(total_custo_compra_depreciado, grouping=True, symbol=True),color="#F0FFFF"),
                    dbc.ListGroupItem("Energia     : " + locale.currency(total_gasto_energetico, grouping=True, symbol=True),color="#E5ECF6"),
                    html.Br(),
                    html.Div("CUSTOS MENSAIS", style={"font-size":"20px","color":"darkblue","font-weight": "bold", "text-align":"center", "background":"white"}),
                    html.Br(),
                    dbc.ListGroupItem("Core        : " + locale.currency(total_custo_por_core, grouping=True, symbol=True),color="#E5ECF6"),
                    dbc.ListGroupItem("Hosts Físicos: " + locale.currency(total_mensal_custo_host, grouping=True, symbol=True),color="#F0FFFF"),
                    dbc.ListGroupItem("Hosts Virtuais: " + locale.currency(total_custo_provisionado, grouping=True, symbol=True),color="#E5ECF6"),

                ],
                flush=True,
            ), 
            ],style={'width': '100%', 'text-align':'justify','paddingTop': '10px', "font-size":"14px"}),

    return card

@app_ambiente_coids.callback(
    Output('card_info_por_host', 'children',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)

def update_card_opex(value):
    if value == "Ambientes Virtuais":
        ########################################################### CONSUMO GERAL
        # Filtra todos os hosts sem repetir, referente a todos os ambientes
        filtro_host_fisico = df_vm['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            #host_ambiente = 'TURBILHAO3'
            df_vm_hostselecionado =  df_vm.loc[df_vm['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # CUSTO OPERACIONAL - Seta valores da tabela contrato
            # Dinâmico - Conforme inclusão na tabela 
            # Valores fixos 
            # Retira R$, ponto e substitui vírgula por ponto na casa decimal
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str.replace('\D','', regex=True))
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str[0:-2] + '.' + df_contrato[column].str[-2:])

            df_contrato_ativo = df_contrato.loc[df_contrato['status_contrato'] == 'ATIVO']

            contrato_operacional_mensal = round(df_contrato_ativo['value_contrato'].astype(float).sum()/12,2)

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            # Nova fórmula - Inclui contratos operacionais
            # =SE(K2>0;((B$2+ (  ($B$7/12)+($B$8/12)+($B$9/12) )/G$2  +(B$4/B$5)/12)/G$2)*K2;0)

            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (contrato_operacional_mensal / tot_geral_cpu_host) \
                                            + (vl_atual_depreciado/tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0


            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)
      
        card = *[dbc.Col([   
            html.Br(),
            html.Br(),
            html.Div(field, style={"width":"16Rem","font-weight": "bold", "color":"black", "text-align":"center", "background":"lightblue"}),
                dbc.ListGroup(
                    [  
                        dbc.ListGroupItem("Data Aquisição: " + str(df1_opex.loc[(df1_opex['HOST'] == field),['DT_COMPRA']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                         
                        dbc.ListGroupItem("Valor Aquisição: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VALOR_COMPRA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),      
                        dbc.ListGroupItem("Valor Depreciado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_ATUAL_DEPRECIADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Energia: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_ENERGIA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),
                        html.Div("CUSTOS MENSAIS", style={"width":"16Rem","font-size":"16px","color":"black","font-weight": "bold", "text-align":"center", "background":"lightblue"}),
                        dbc.ListGroupItem("Core: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),  ['VL_MENSAL_DO_CORE']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Host Físico: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_HOST']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Hosts Virtuais: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_MENSAL_PROVISIONADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ) 
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in filtro_host_fisico],

    else: 
        # Filtra os hosts referentes apenas ao ambiente selecionado
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :] 
        filtro_host_fisico = tabela_filtrada['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            df_vm_hostselecionado =  tabela_filtrada.loc[tabela_filtrada['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # CUSTO OPERACIONAL - Seta valores da tabela contrato
            # Dinâmico - Conforme inclusão na tabela 
            # Valores fixos 
            # Retira R$, ponto e substitui vírgula por ponto na casa decimal
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str.replace('\D','', regex=True))
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str[0:-2] + '.' + df_contrato[column].str[-2:])

            df_contrato_ativo = df_contrato.loc[df_contrato['status_contrato'] == 'ATIVO']

            contrato_operacional_mensal = round(df_contrato_ativo['value_contrato'].astype(float).sum()/12,2)

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            # Nova fórmula - Inclui contratos operacionais
            # =SE(K2>0;((B$2+ (  ($B$7/12)+($B$8/12)+($B$9/12) )/G$2  +(B$4/B$5)/12)/G$2)*K2;0)

            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (contrato_operacional_mensal / tot_geral_cpu_host) \
                                            + (vl_atual_depreciado/tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0


            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            #df_opex.append([df_vm_hostselecionado['LABEL_POOL'].unique(), df_consumo_host['NOME'],\
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)

        card = *[dbc.Col([  
            html.Br(),
            html.Br(),
            html.Div(field, style={"width":"16Rem","font-weight": "bold", "text-align":"center", "background":"lightblue"}),                        
                dbc.ListGroup(
                    [   
                        dbc.ListGroupItem("Data Aquisição: " + str(df1_opex.loc[(df1_opex['HOST'] == field),['DT_COMPRA']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                         
                        dbc.ListGroupItem("Valor Aquisição: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VALOR_COMPRA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Valor Depreciado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_ATUAL_DEPRECIADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Energia: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_ENERGIA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),
                        html.Div("CUSTOS MENSAIS", style={"width":"16Rem","font-size":"16px","color":"black","font-weight": "bold", "text-align":"center", "background":"lightblue"}),
                        dbc.ListGroupItem("Core: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),  ['VL_MENSAL_DO_CORE']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Host Físico: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_HOST']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Hosts Virtuais: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_MENSAL_PROVISIONADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ) 
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in filtro_host_fisico],
    return card

@app_ambiente_coids.callback(
    Output('card_resumo_financeiro', 'children',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)

def update_card_opex(value):
    if value == "Ambientes Virtuais":
        ########################################################### CONSUMO GERAL
        # Filtra todos os hosts sem repetir, referente a todos os ambientes
        filtro_host_fisico = df_vm['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            df_vm_hostselecionado =  df_vm.loc[df_vm['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # CUSTO OPERACIONAL - Seta valores da tabela contrato
            # Dinâmico - Conforme inclusão na tabela 
            # Valores fixos 
            # Retira R$, ponto e substitui vírgula por ponto na casa decimal
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str.replace('\D','', regex=True))
            for column in ['value_contrato']:
                df_contrato[column] = list(df_contrato[column].str[0:-2] + '.' + df_contrato[column].str[-2:])

            df_contrato_ativo = df_contrato.loc[df_contrato['status_contrato'] == 'ATIVO']

            contrato_operacional_mensal = round(df_contrato_ativo['value_contrato'].astype(float).sum()/12,2)

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            # Nova fórmula - Inclui contratos operacionais
            # =SE(K2>0;((B$2+ (  ($B$7/12)+($B$8/12)+($B$9/12) )/G$2  +(B$4/B$5)/12)/G$2)*K2;0)

            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (contrato_operacional_mensal / tot_geral_cpu_host) \
                                            + (vl_atual_depreciado/tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0

            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            #df_opex.append([df_vm_hostselecionado['LABEL_POOL'].unique(), df_consumo_host['NOME'],\
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)


        colors = ['#0099C6', '#00CC96'],
        labels = ['Custo', 'Provisionado']

        card = *[dbc.Col([            
            html.Br(),
            html.Br(),
            html.Div(field, style={"width":"16Rem","font-weight": "bold", "text-align":"center", "background":"lightblue"}),
            dbc.ListGroup(
                [   
                dbc.ListGroupItem("Core: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),  ['VL_MENSAL_DO_CORE']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                dbc.ListGroupItem("Mensal: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_HOST']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),                        
                dbc.ListGroupItem("Provisionado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_MENSAL_PROVISIONADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        

                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ), 
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in filtro_host_fisico],
    ####################################################### FUNCIONAL     

    else: 
        # Filtra os hosts referentes apenas ao ambiente selecionado
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :] 
        filtro_host_fisico = tabela_filtrada['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            df_vm_hostselecionado =  tabela_filtrada.loc[tabela_filtrada['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (vl_atual_depreciado / tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0

            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            #df_opex.append([df_vm_hostselecionado['LABEL_POOL'].unique(), df_consumo_host['NOME'],\
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)

        card = *[dbc.Col([  
            html.Br(),
            html.Br(),
            html.Div(field, style={"width":"16Rem","font-weight": "bold", "text-align":"center", "background":"lightblue"}),                        
                dbc.ListGroup(
                    [   
                        dbc.ListGroupItem("Core: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),  ['VL_MENSAL_DO_CORE']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Mensal: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_HOST']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Provisionado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_MENSAL_PROVISIONADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ) 
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in filtro_host_fisico],

    return card

@app_ambiente_coids.callback(
    Output('ambiente_maquinas_fisicas', 'children',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)

def update_card_opex(value):
    if value == "Ambientes Virtuais":
        ########################################################### CONSUMO GERAL
        # Filtra todos os hosts sem repetir, referente a todos os ambientes
        filtro_host_fisico = df_vm['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            #host_ambiente = 'TURBILHAO3'
            df_vm_hostselecionado =  df_vm.loc[df_vm['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())

            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (vl_atual_depreciado / tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0

            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)
 
        card = *[dbc.Col([            
            html.Br(),
            html.Br(),
            html.Div(field, style={"width":"16Rem","font-weight": "bold", "text-align":"center", "background":"lightblue"}),
                dbc.ListGroup(
                    [   
                        dbc.ListGroupItem("Data Aquisição: " + str(df1_opex.loc[(df1_opex['HOST'] == field),['DT_COMPRA']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                         
                        dbc.ListGroupItem("Valor Aquisição: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VALOR_COMPRA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Valor Depreciado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_ATUAL_DEPRECIADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Energia: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_ENERGIA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Valor Host/Core: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),  ['VL_MENSAL_DO_CORE']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Custo Host/Mensal: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_HOST']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Custo Provisionado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_MENSAL_PROVISIONADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ) 
            #),
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in filtro_host_fisico],

    else: 
        # Filtra os hosts referentes apenas ao ambiente selecionado
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :] 
        filtro_host_fisico = tabela_filtrada['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))

        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        # Retira R$, ponto e substitui vírgula por ponto na casa decimal
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))
        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL', 'VALOR_COMPRA']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Dataframe com dados OPEX
        df_opex = []
        cols = ['AMBIENTE', 'HOST', 'VALOR_COMPRA', 'DT_COMPRA', 'DT_ATUAL', 'TEMPO_DEPRECIADO',\
                'VL_ATUAL_DEPRECIADO', 'CUSTO_MENSAL_ENERGIA', 'NCPU_HOST', 'VL_MENSAL_DO_CORE',\
                'CUSTO_MENSAL_HOST','NCPU_VM', 'VL_MENSAL_PROVISIONADO']

        # Laço para filtro dos hosts e cálculo individual.
        # A cada iteração, cria-se um df_vm_hostselecionado
        for host_ambiente in filtro_host_fisico:
            #host_ambiente = 'TURBILHAO3'
            df_vm_hostselecionado =  tabela_filtrada.loc[tabela_filtrada['HOST'] == host_ambiente.lower(), :] 

            df_consumo_host = df_hosts.loc[df_hosts['NOME'] == host_ambiente, :] 

            if df_consumo_host.empty:
                continue
            valor_compra = round(df_consumo_host['VALOR_COMPRA'].astype(float).sum(),2)
            dt_atual = datetime.today()  # Data atual do sistema
            dt_compra = pd.to_datetime(df_consumo_host['DATA_COMPRA'],infer_datetime_format=True, dayfirst=True).dt.strftime('%d/%m/%Y')
            dt_compra_str = dt_compra.to_string(index=False)  # Converte a variável dt_compra para string
            dt_compra_str_data = datetime.strptime(dt_compra_str, '%d/%m/%Y')  # Converte a variável string para data igual o dt_atual
            delta_dt = (dt_atual - dt_compra_str_data).days   # Com as 2 variáveis no mesmo formato, é possível a operação de cálculo
            dt_atual_str = dt_atual.strftime('%d/%m/%Y')

            # FÓRMULA DE CÁLCULO DA DEPRECIAÇÃO DO HOST #
            # Cálculo do valor atual depreciado 
            #=SE(B6>0;B3*(1-0,2)^((A1-B6)/365);"")
            if dt_compra_str == '': 
                vl_atual_depreciado = 0
            else:
                vl_atual_depreciado = round(valor_compra * (1 - 0.2) ** ((delta_dt) / 365),2)

            tempo_depreciado = 10  #10 anos

            # Converte nCPU string para Número
            tot_geral_cpu_host = round((df_vm_hostselecionado['nCPU_HOST'].astype(int)).sum())
        
            # Valor de gasto com energia elétrica
            custo_diario_energia = round(df_consumo_host['CUSTO_DIARIO'].astype(float).sum(),2)
            custo_mensal_energia = round(df_consumo_host['CUSTO_MENSAL'].astype(float).sum(),2)        
            custo_anual_energia = round(df_consumo_host['CUSTO_ANUAL'].astype(float).sum(),2)
            
            # Cálculo do valor do core (unidade)
            # SE(K3>0;((B$2+(B$4/B$5)/12)/G$2);0)
            if tot_geral_cpu_host > 0:
                vl_mensal_do_core = round(((custo_mensal_energia + (vl_atual_depreciado / tempo_depreciado)/12) / tot_geral_cpu_host),2)
            else:
                vl_mensal_do_core = 0

            # Cálculo do custo mensal do host baseado nos valores de 
            # gasto com energia elétrica e custo do equipamento depreciado
            custo_geral_mensal_host = round(vl_mensal_do_core * tot_geral_cpu_host,2)

            # Cálculo do valor do core provisionado
            # (total com base no número de core da VM)
            # =SE(K3>0;((B$2+(B$4/B$5)/12)/G$2)*K3;0)
            tot_geral_cpu_vm = (df_vm_hostselecionado['nCPU_VM'].astype(int)).sum()
            if tot_geral_cpu_vm > 0:
                Vl_mensal_provisionado_core = round(vl_mensal_do_core * tot_geral_cpu_vm,2)
            else:
                Vl_mensal_provisionado_core = 0

            ambiente_selecionado = df_vm_hostselecionado['LABEL_POOL'].unique()

            # Gera dataframe com dados OPEX (custo operacional)
            df_opex.append([ambiente_selecionado, host_ambiente, valor_compra, dt_compra_str, dt_atual_str,tempo_depreciado,\
                            vl_atual_depreciado, custo_mensal_energia, tot_geral_cpu_host, vl_mensal_do_core,\
                            custo_geral_mensal_host, tot_geral_cpu_vm,Vl_mensal_provisionado_core])

        # Transcreve o dataframe com colunas renomeadas
        df1_opex = pd.DataFrame(df_opex,columns=cols)  
            
        # Área do card para inserção dos dados
        total_mensal_custo_host = round(df1_opex['CUSTO_MENSAL_HOST'].astype(float).sum(),2)
        total_custo_compra =  round(df1_opex['VALOR_COMPRA'].astype(float).sum(),2)
        total_custo_compra_depreciado =  round(df1_opex['VL_ATUAL_DEPRECIADO'].astype(float).sum(),2)
        total_gasto_energetico =  round(df1_opex['CUSTO_MENSAL_ENERGIA'].astype(float).sum(),2)
        total_custo_por_core =  round(df1_opex['VL_MENSAL_DO_CORE'].astype(float).sum(),2)
        total_custo_provisionado =  round(df1_opex['VL_MENSAL_PROVISIONADO'].astype(float).sum(),2)
 
        card = *[dbc.Col([  
            html.Br(),
            html.Br(),
            html.Div(field, style={"width":"16Rem","font-weight": "bold", "text-align":"center", "background":"lightblue"}),                        
                dbc.ListGroup(
                    [   
                        dbc.ListGroupItem("Data Aquisição: " + str(df1_opex.loc[(df1_opex['HOST'] == field),['DT_COMPRA']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                         
                        dbc.ListGroupItem("Valor Aquisição: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VALOR_COMPRA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Valor Depreciado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_ATUAL_DEPRECIADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Energia: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_ENERGIA']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),
                        dbc.ListGroupItem("Valor Host/Core: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),  ['VL_MENSAL_DO_CORE']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Custo Host/Mensal: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['CUSTO_MENSAL_HOST']].to_string(index=False,header=0)), color="#F0FFFF",style={"width":"16Rem"}),                        
                        dbc.ListGroupItem("Custo Provisionado: R$ " + str(df1_opex.loc[(df1_opex['HOST'] == field),['VL_MENSAL_PROVISIONADO']].to_string(index=False,header=0)), color="#E0EEEE",style={"width":"16Rem"}),                         
                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ) 
            #),
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in filtro_host_fisico],

    return card

@app_ambiente_coids.callback(
    Output('tabela_consumo_vm', 'children',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)
@app_ambiente_coids.callback(Output('tabela_consumo_vm1', 'children'),
    [Input('ambiente_virtual', 'value')])


def update_tabela_consumo_vm(value):
    if value == "Ambientes Virtuais":
        ########################################################### CONSUMO
        # Filtra todos os hosts sem repetir, referente a todos os ambientes
        filtro_host_fisico = df_vm['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))
        
        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))

        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Somatóra dos valores de custos
        custo_diario_geral = round(df_hosts['CUSTO_DIARIO'].astype(float).sum(),2)
        custo_mensal_geral = round(df_hosts['CUSTO_MENSAL'].astype(float).sum(),2)        
        custo_anual_geral = round(df_hosts['CUSTO_ANUAL'].astype(float).sum(),2)
        
        # Cálculo por core
        # Converte nCPU string para Número
        tot_geral_cpu_host = (df_vm['nCPU_HOST'].astype(int)).sum()
        
        custo_mensal_geral = round(df_hosts['CUSTO_MENSAL'].astype(float).sum(),2)        

        custo_diario_geral_core = round((custo_diario_geral / tot_geral_cpu_host),2)
        custo_mensal_geral_core = round((custo_mensal_geral / tot_geral_cpu_host),2)
        custo_anual_geral_core = round((custo_anual_geral / tot_geral_cpu_host),2)

        df_consumo_vm1 = df_vm.assign(VL_CORE_VM_DIARIO = lambda x: x.nCPU_VM.astype(int) * custo_diario_geral_core)
        df_consumo_vm2= df_consumo_vm1.assign(VL_CORE_VM_MENSAL = lambda x: x.nCPU_VM.astype(int) * custo_mensal_geral_core)
        df_consumo_vm = df_consumo_vm2.assign(VL_CORE_VM_ANUAL = lambda x: x.nCPU_VM.astype(int) * custo_anual_geral_core)

        ### FILTRO DE TABELA DE CONSUMO e RENOMEAÇÃO ### 
        # Volume
        df_filtro_consumo = df_consumo_vm.iloc[: , [1, 5, 11, 15, 16, 20, 21, 22, 2, 13, 14]].copy()
        df_filtro_consumo.columns = ['AMBIENTE','HOST','MAQ.VIRTUAL','nCPU_VM', \
                                    'MEMORIA_VM','VM_DIARIO R$','VM_MENSAL R$','VM_ANUAL R$', \
                                    'DESCR.AMBIENTE','DESCRIÇÃO DA VM','S.OPERACIONAL VM']

        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Ambientes Virtuais/Consumo', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True} for i in df_filtro_consumo
                    if i != 'id'
                ],
                data=df_filtro_consumo.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                row_selectable='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 20,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]

    else: 
        # Filtra os hosts referentes apenas ao ambiente selecionado
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :] 

        ########################################################### CONSUMO
        # Filtra todos os hosts sem repetir, referente a todos os ambientes
        filtro_host_fisico = tabela_filtrada['HOST'].unique()
        filtro_host_fisico = list((map(lambda x: x.upper(), filtro_host_fisico)))
        
        # Procura os nomes das máquinas no dataframe do ambiente inteiro
        df_maqfisica['NOME'] = df_maqfisica['NOME'].str.strip()  
        df_hosts = df_maqfisica[df_maqfisica['NOME'].isin(filtro_host_fisico)]

        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL']:
            df_hosts[column] = list(df_hosts[column].str.replace('\D','', regex=True))

        for column in ['CUSTO_DIARIO','CUSTO_MENSAL', 'CUSTO_ANUAL']:
            df_hosts[column] = list(df_hosts[column].str[0:-2] + '.' + df_hosts[column].str[-2:])

        # Somatóra dos valores de custos
        custo_diario_geral = round(df_hosts['CUSTO_DIARIO'].astype(float).sum(),2)
        custo_mensal_geral = round(df_hosts['CUSTO_MENSAL'].astype(float).sum(),2)        
        custo_anual_geral = round(df_hosts['CUSTO_ANUAL'].astype(float).sum(),2)
        
        # Cálculo por core
        # Converte nCPU string para Número
        tot_geral_cpu_host = (tabela_filtrada['nCPU_HOST'].astype(int)).sum()
        
        custo_mensal_geral = round(df_hosts['CUSTO_MENSAL'].astype(float).sum(),2)        

        custo_diario_geral_core = round((custo_diario_geral / tot_geral_cpu_host),2)
        custo_mensal_geral_core = round((custo_mensal_geral / tot_geral_cpu_host),2)
        custo_anual_geral_core = round((custo_anual_geral / tot_geral_cpu_host),2)

        df_consumo_vm1 = tabela_filtrada.assign(VL_CORE_VM_DIARIO = lambda x: x.nCPU_VM.astype(int) * custo_diario_geral_core)
        df_consumo_vm2= df_consumo_vm1.assign(VL_CORE_VM_MENSAL = lambda x: x.nCPU_VM.astype(int) * custo_mensal_geral_core)
        df_consumo_vm = df_consumo_vm2.assign(VL_CORE_VM_ANUAL = lambda x: x.nCPU_VM.astype(int) * custo_anual_geral_core)

        ### FILTRO DE TABELA DE CONSUMO e RENOMEAÇÃO ### 
        # Volume
        df_filtro_consumo = df_consumo_vm.iloc[: , [1, 5, 11, 15, 16, 20, 21, 22, 2, 13, 14]].copy()
        df_filtro_consumo.columns = ['AMBIENTE','HOST','MAQ.VIRTUAL','nCPU_VM', \
                                    'MEMORIA_VM','VM_DIARIO R$','VM_MENSAL R$','VM_ANUAL R$', \
                                    'DESCR.AMBIENTE','DESCRIÇÃO DA VM','S.OPERACIONAL VM']

        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Ambientes Virtuais/Consumo', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True} for i in df_filtro_consumo
                    if i != 'id'
                ],
                data=df_filtro_consumo.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                row_selectable='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 20,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]

###############################################################################

### FUNÇÃO e CALLBACK ### 
########################################
# V O L U M E S - Início               #
########################################
# Início para chamada do Gráfico de Barras para memória (GB)-----------------------------------------------------------
@app_ambiente_coids.callback(
        Output('grafico_volume_unidade', 'figure',allow_duplicate=True),
        Input('volume_unidade','value'),
        prevent_initial_call = True,
)
@app_ambiente_coids.callback(
        Output('grafico_volume_unidade1', 'figure',allow_duplicate=True),
        Input('volume_unidade','value'),
        prevent_initial_call = True,
)
def update_output(value):
    #JOAO

    
    if value == "Todas Unidades":
        fig_unidade = go.Figure (data = [
            go.Bar(x = [df_volume['DEPARTAMENTO'],df_volume['VOLUME']], y = df_volume['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', text = df_volume['VOLUME_TOTAL'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [df_volume['DEPARTAMENTO'],df_volume['VOLUME']], y = df_volume['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', text = df_volume['VOLUME_USADO'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [df_volume['DEPARTAMENTO'],df_volume['VOLUME']], y = df_volume['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', text = df_volume['VOLUME_DISPONIVEL'],
                textposition='inside',textfont_size=18),
        ])                                   
        fig_unidade.update_layout(title = '<b>V O L U M E</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_unidade.update_yaxes(title_text='Terabyte (TB)'),  
        fig_unidade.update_traces(marker_line_color='gray', marker_line_width=0.1)
    else:
        tabela_filtrada = df_volume.loc[df_volume['DEPARTAMENTO'] == value, :]
        # Calcula volume por unidade --------------------------------------------------------------------------------
        fig_unidade = go.Figure (data = [
            go.Bar(x = [tabela_filtrada['DEPARTAMENTO'],tabela_filtrada['VOLUME']], y = tabela_filtrada['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', text = tabela_filtrada['VOLUME_TOTAL'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [tabela_filtrada['DEPARTAMENTO'],tabela_filtrada['VOLUME']], y = tabela_filtrada['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', text = tabela_filtrada['VOLUME_USADO'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [tabela_filtrada['DEPARTAMENTO'],tabela_filtrada['VOLUME']], y = tabela_filtrada['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', text = tabela_filtrada['VOLUME_DISPONIVEL'],
                textposition='inside',textfont_size=18),
        ])                                   
        fig_unidade.update_layout(title = '<b>V O L U M E</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_unidade.update_yaxes(title_text='Terabyte (TB)'),  
        fig_unidade.update_traces(marker_line_color='gray', marker_line_width=0.1)
    return fig_unidade
# Fim para chamada do Gráfico de Barras para memória (GB) ---------------------

#Início para chamada do Gráfico de <Volumes> (pie Gauge) OLINDA----------------
@app_ambiente_coids.callback(
    Output('grafico_volume', 'figure', allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_volume1', 'figure', allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)

def update_output_volume(value):
    if value == "Todas Unidades" or value == "Todos Aggregates": 
        labels = ['Usado', 'Disponível']
        if soma_volume_total >= 1 and soma_volume_total < 1024:
            soma_volume_total_pie = soma_volume_total
            soma_volume_disponivel_pie = soma_volume_disponivel
            soma_volume_usado_pie = soma_volume_usado
            und = 'TB'

        if soma_volume_total >= 1024:
            soma_volume_total_pie = soma_volume_total/1024
            soma_volume_disponivel_pie = soma_volume_disponivel/1024
            soma_volume_usado_pie = soma_volume_usado/1024
            und = 'PB'

        if soma_volume_total < 1:
            soma_volume_total_pie = soma_volume_total*1024
            soma_volume_disponivel_pie = soma_volume_disponivel*1024
            soma_volume_usado_pie = soma_volume_usado*1024
            und = 'GB'
            if soma_volume_total_pie < 1:
                soma_volume_total_pie *= 1024
                soma_volume_disponivel_pie *= 1024
                soma_volume_usado_pie *= 1024
                und = 'MB'

        values = [np.round(soma_volume_usado_pie,2), np.round(soma_volume_disponivel_pie,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7,showlegend=False,
                                    textfont_size=15,
                                    #pull = [0,0.25,0,0],
                                    marker_colors = colors))
        fig_volume.update_layout(
                    #title_text = value, title_x=0.5,title_y=0.90,
                    title_text = "OLINDA - VOLUMES", title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume.add_annotation(x= 0.5, y = 0.5,
                            #text = str(np.round(soma_volume_total_pie,2)) + und,
                            text = locale.currency(np.round(soma_volume_total_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    else:
        tabela_filtrada = df_volume.loc[df_volume['DEPARTAMENTO'] == value, :]      
        # Converte KB para GB -------------------------------------------------------------------------------------------------
        soma_volume_total_filtro = tabela_filtrada['VOLUME_TOTAL'].sum()
        soma_volume_usado_filtro = tabela_filtrada['VOLUME_USADO'].sum()
        soma_volume_disponivel_filtro = tabela_filtrada['VOLUME_DISPONIVEL'].sum()

        labels = ['Usado', 'Disponível']

        if soma_volume_total_filtro >= 1 and soma_volume_total_filtro < 1024:
            soma_volume_total_filtro_pie = soma_volume_total_filtro
            soma_volume_disponivel_filtro_pie = soma_volume_disponivel_filtro
            soma_volume_usado_filtro_pie = soma_volume_usado_filtro
            und = 'TB'

        if soma_volume_total_filtro >= 1024:
            soma_volume_total_filtro_pie = soma_volume_total_filtro/1024
            soma_volume_disponivel_filtro_pie = soma_volume_disponivel_filtro/1024
            soma_volume_usado_filtro_pie = soma_volume_usado_filtro/1024
            und = 'PB'

        if soma_volume_total_filtro < 1:
            soma_volume_total_filtro_pie = soma_volume_total_filtro*1024
            soma_volume_disponivel_filtro_pie = soma_volume_disponivel_filtro*1024
            soma_volume_usado_filtro_pie = soma_volume_usado_filtro*1024
            und = 'GB'
            if soma_volume_total_filtro_pie < 1:
                soma_volume_total_filtro_pie *= 1024
                soma_volume_disponivel_filtro_pie *= 1024
                soma_volume_usado_filtro_pie *= 1024
                und = 'MB'

        values = [np.round(soma_volume_usado_filtro_pie,2), np.round(soma_volume_disponivel_filtro_pie,2)]

        colors = ['#0099C6', '#00CC96']

        fig_volume = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    #pull = [0,0.25,0,0],
                                    marker_colors = colors))
        fig_volume.update_layout(
                    title_text = value.upper(), title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume.add_annotation(x= 0.5, y = 0.5, 
                            #Ok text = str(np.round(soma_volume_total_filtro_pie,2)) + und,
                            text = locale.currency(np.round(soma_volume_total_filtro_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=30,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_volume     
# Fim da chamada do Gráfico de Volumes (pie Gauge) OLINDA----------------------

# S N A P -> Início para chamada do Gráfico de SNAP (pie Gauge) OLINDA---------
@app_ambiente_coids.callback(
    Output('grafico_snap', 'figure', allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)
def update_output_volume(value):
    if value == "Todas Unidades": 
        labels = ['Usado', 'Disponível']

        if soma_snap_total >= 1 and soma_snap_total < 1024:
            soma_snap_total_pie = soma_snap_total
            soma_snap_disponivel_pie = soma_snap_disponivel
            soma_snap_usado_pie = soma_snap_usado
            und = 'TB'

        if soma_snap_total >= 1024:
            soma_snap_total_pie = soma_snap_total/1024
            soma_snap_disponivel_pie = soma_snap_disponivel/1024
            soma_snap_usado_pie = soma_snap_usado/1024
            und = 'PB'

        if soma_snap_total < 1:
            soma_snap_total_pie = soma_snap_total*1024
            soma_snap_disponivel_pie = soma_snap_disponivel*1024
            soma_snap_usado_pie = soma_snap_usado*1024
            und = 'GB'     
            if soma_snap_total_pie < 1:
                soma_snap_total_pie *= 1024
                soma_snap_disponivel_pie *= 1024
                soma_snap_usado_pie *= 1024
                und = 'MB'

        values = [np.round(soma_snap_usado_pie,2), np.round(soma_snap_disponivel_pie,2)]
        colors = ['#0099C6', '#00CC96']
        fig_snap = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7,showlegend=False,
                                    textfont_size=15,
                                    #pull = [0,0.25,0,0],
                                    marker_colors = colors))
        fig_snap.update_layout(
                    title_text = "SNAP -> " + value, title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_snap.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_snap_total_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    else:
        tabela_filtrada = df_volume.loc[df_volume['DEPARTAMENTO'] == value, :]      
        soma_snap_total_filtro = tabela_filtrada['VOLUME_SNAP_TOTAL'].sum()

        soma_snap_usado_filtro = tabela_filtrada['VOLUME_SNAP_USADO'].sum()

        soma_snap_disponivel_filtro = tabela_filtrada['VOLUME_SNAP_DISPONIVEL'].sum()

        labels = ['Usado', 'Disponível']

        if soma_snap_total_filtro >= 1 and soma_snap_total_filtro < 1024:
            soma_snap_total_filtro_pie = soma_snap_total_filtro
            soma_snap_disponivel_filtro_pie = soma_snap_disponivel_filtro
            soma_snap_usado_filtro_pie = soma_snap_usado_filtro
            und = 'TB'

        if soma_snap_total >= 1024:
            soma_snap_total_filtro_pie = soma_snap_total_filtro/1024
            soma_snap_disponivel_filtro_pie = soma_snap_disponivel_filtro/1024
            soma_snap_usado_filtro_pie = soma_snap_usado_filtro/1024
            und = 'PB'

        if soma_snap_total_filtro < 1:
            soma_snap_total_filtro_pie = soma_snap_total_filtro*1024
            soma_snap_disponivel_filtro_pie = soma_snap_disponivel_filtro*1024
            soma_snap_usado_filtro_pie = soma_snap_usado_filtro*1024
            und = 'GB'     
            if soma_snap_total_filtro_pie < 1:
                soma_snap_total_filtro_pie *= 1024
                soma_snap_disponivel_filtro_pie *= 1024
                soma_snap_usado_filtro_pie *= 1024
                und = 'MB'

        values = [np.round(soma_snap_usado_filtro_pie,2), np.round(soma_snap_disponivel_filtro_pie,2)]
        colors = ['#0099C6', '#00CC96']

        fig_snap = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_snap.update_layout(
                    title_text = "SNAP -> " + value.upper(), title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_snap.add_annotation(x= 0.5, y = 0.5, 
                            text = locale.currency(np.round(soma_snap_total_filtro_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_snap     
# S N A P -> Fim para chamada do Gráfico de SNAP (pie Gauge) OLINDA------------

# Início da Tabela de Dados Volumes--------------------------------------------
@app_ambiente_coids.callback(Output('tabela-dados-volumes', 'children'),
    [Input('volume_unidade', 'value')],prevent_initial_call = True,
)

@app_ambiente_coids.callback(Output('tabela-dados-volumes1', 'children'),
    [Input('volume_unidade', 'value')],prevent_initial_call = True,
)

def update_table_volume(value):
    if value == "Todas Unidades":        
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Volumes (TB)', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True} for i in df_filtro_volume.columns
                    if i != 'id'
                ],
                data=df_filtro_volume.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 15,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
    else:
        tabela_filtrada = df_filtro_volume.loc[df_filtro_volume['UNIDADE'] == value, :]      
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Volume (TB)', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': False} for i in tabela_filtrada.columns
                    if i != 'id'
                ],
                data=tabela_filtrada.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 15,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
# Fim da Tabela de Dados ----------------------------------------------------------------------------------------------

### L A N D S A T ###
#Início para chamada do Gráfico de <Volumes> (pie Gauge) LANDSAT----------------
@app_ambiente_coids.callback(
    Output('grafico_volume_landsat', 'figure', allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_volume_landsat1', 'figure', allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)

def update_output_volume(value):
    if value == "Todas Unidades" or value == "Todos Aggregates": 
        labels = ['Usado', 'Disponível']
        if soma_volume_total_landsat >= 1 and soma_volume_total_landsat < 1024:
            soma_volume_total_pie_landsat = soma_volume_total_landsat
            soma_volume_disponivel_pie_landsat = soma_volume_disponivel_landsat
            soma_volume_usado_pie_landsat = soma_volume_usado_landsat
            und = 'TB'

        if soma_volume_total_landsat >= 1024:
            soma_volume_total_pie_landsat = soma_volume_total_landsat/1024
            soma_volume_disponivel_pie_landsat = soma_volume_disponivel_landsat/1024
            soma_volume_usado_pie_landsat = soma_volume_usado_landsat/1024
            und = 'PB'

        if soma_volume_total_landsat < 1:
            soma_volume_total_pie_landsat = soma_volume_total_landsat*1024
            soma_volume_disponivel_pie_landsat = soma_volume_disponivel_landsat*1024
            soma_volume_usado_pie_landsat = soma_volume_usado_landsat*1024
            und = 'GB'
            if soma_volume_total_pie_landsat < 1:
                soma_volume_total_pie_landsat *= 1024
                soma_volume_disponivel_pie_landsat *= 1024
                soma_volume_usado_pie_landsat *= 1024
                und = 'MB'

        values = [np.round(soma_volume_usado_pie_landsat,2), np.round(soma_volume_disponivel_pie_landsat,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7,showlegend=False,
                                    textfont_size=15,
                                    #pull = [0,0.25,0,0],
                                    marker_colors = colors))
        fig_volume_landsat.update_layout(
                    title_text = "LANDSAT - VOLUMES", title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_volume_total_pie_landsat,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    else:
        tabela_filtrada = df_volume_landsat.loc[df_volume_landsat['DEPARTAMENTO'] == value, :]      
        soma_volume_total_filtro_landsat = tabela_filtrada['VOLUME_TOTAL'].sum()

        soma_volume_usado_filtro_landsat = tabela_filtrada['VOLUME_USADO'].sum()

        soma_volume_disponivel_filtro_landsat = tabela_filtrada['VOLUME_DISPONIVEL'].sum()

        labels = ['Usado', 'Disponível']

        if soma_volume_total_filtro_landsat >= 1 and soma_volume_total_filtro_landsat < 1024:
            soma_volume_total_filtro_pie_landsat = soma_volume_total_filtro_landsat
            soma_volume_disponivel_filtro_pie_landsat = soma_volume_disponivel_filtro_landsat
            soma_volume_usado_filtro_pie_landsat = soma_volume_usado_filtro_landsat
            und = 'TB'

        if soma_volume_total_filtro_landsat >= 1024:
            soma_volume_total_filtro_pie_landsat = soma_volume_total_filtro_landsat/1024
            soma_volume_disponivel_filtro_pie_landsat = soma_volume_disponivel_filtro_landsat/1024
            soma_volume_usado_filtro_pie_landsat = soma_volume_usado_filtro_landsat/1024
            und = 'PB'

        if soma_volume_total_filtro_landsat < 1:
            soma_volume_total_filtro_pie_landsat = soma_volume_total_filtro_landsat*1024
            soma_volume_disponivel_filtro_pie_landsat = soma_volume_disponivel_filtro_landsat*1024
            soma_volume_usado_filtro_pie_landsat = soma_volume_usado_filtro_landsat*1024
            und = 'GB'
            if soma_volume_total_filtro_pie_landsat < 1:
                soma_volume_total_filtro_pie_landsat *= 1024
                soma_volume_disponivel_filtro_pie_landsat *= 1024
                soma_volume_usado_filtro_pie_landsat *= 1024
                und = 'MB'

        values = [np.round(soma_volume_usado_filtro_pie_landsat,2), np.round(soma_volume_disponivel_filtro_pie_landsat,2)]

        colors = ['#0099C6', '#00CC96']

        fig_volume_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_landsat.update_layout(
                    title_text = value.upper(), title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_landsat.add_annotation(x= 0.5, y = 0.5, 
                            text = locale.currency(np.round(soma_volume_total_filtro_pie_landsat,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_volume_landsat     
# Fim da chamada do Gráfico de Volumes (pie Gauge) OLINDA----------------------

# S N A P -> Início para chamada do Gráfico de SNAP (pie Gauge) LANDSAT---------
@app_ambiente_coids.callback(
    Output('grafico_snap_landsat', 'figure', allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)
def update_output_volume(value):
    if value == "Todas Unidades": 
        labels = ['Usado', 'Disponível']

        if soma_snap_total_landsat >= 1 and soma_snap_total_landsat < 1024:
            soma_snap_total_pie_landsat = soma_snap_total_landsat
            soma_snap_disponivel_pie_landsat = soma_snap_disponivel_landsat
            soma_snap_usado_pie_landsat = soma_snap_usado_landsat
            und = 'TB'

        if soma_snap_total_landsat >= 1024:
            soma_snap_total_pie_landsat = soma_snap_total_landsat/1024
            soma_snap_disponivel_pie_landsat = soma_snap_disponivel_landsat/1024
            soma_snap_usado_pie_landsat = soma_snap_usado_landsat/1024
            und = 'PB'

        if soma_snap_total_landsat < 1:
            soma_snap_total_pie_landsat = soma_snap_total_landsat*1024
            soma_snap_disponivel_pie_landsat = soma_snap_disponivel_landsat*1024
            soma_snap_usado_pie_landsat = soma_snap_usado_landsat*1024
            und = 'GB'     
            if soma_snap_total_pie_landsat < 1:
                soma_snap_total_pie_landsat *= 1024
                soma_snap_disponivel_pie_landsat *= 1024
                soma_snap_usado_pie_landsat *= 1024
                und = 'MB'

        values = [np.round(soma_snap_usado_pie_landsat,2), np.round(soma_snap_disponivel_pie_landsat,2)]
        colors = ['#0099C6', '#00CC96']
        fig_snap_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7,showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_snap_landsat.update_layout(
                    title_text = "SNAP -> " + value, title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_snap_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_snap_total_pie_landsat,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    else:
        tabela_filtrada = df_volume_landsat.loc[df_volume_landsat['DEPARTAMENTO'] == value, :]      
        soma_snap_total_filtro_landsat = tabela_filtrada['VOLUME_SNAP_TOTAL'].sum()

        soma_snap_usado_filtro_landsat = tabela_filtrada['VOLUME_SNAP_USADO'].sum()

        soma_snap_disponivel_filtro_landsat = tabela_filtrada['VOLUME_SNAP_DISPONIVEL'].sum()

        labels = ['Usado', 'Disponível']

        if soma_snap_total_filtro_landsat >= 1 and soma_snap_total_filtro_landsat < 1024:
            soma_snap_total_filtro_pie_landsat = soma_snap_total_filtro_landsat
            soma_snap_disponivel_filtro_pie_landsat = soma_snap_disponivel_filtro_landsat
            soma_snap_usado_filtro_pie_landsat = soma_snap_usado_filtro_landsat
            und = 'TB'

        if soma_snap_total_landsat >= 1024:
            soma_snap_total_filtro_pie_landsat = soma_snap_total_filtro_landsat/1024
            soma_snap_disponivel_filtro_pie_landsat = soma_snap_disponivel_filtro_landsat/1024
            soma_snap_usado_filtro_pie_landsat = soma_snap_usado_filtro_landsat/1024
            und = 'PB'

        if soma_snap_total_filtro_landsat < 1:
            soma_snap_total_filtro_pie_landsat = soma_snap_total_filtro_landsat*1024
            soma_snap_disponivel_filtro_pie_landsat = soma_snap_disponivel_filtro_landsat*1024
            soma_snap_usado_filtro_pie_landsat = soma_snap_usado_filtro_landsat*1024
            und = 'GB'     
            if soma_snap_total_filtro_pie_landsat < 1:
                soma_snap_total_filtro_pie_landsat *= 1024
                soma_snap_disponivel_filtro_pie_landsat *= 1024
                soma_snap_usado_filtro_pie_landsat *= 1024
                und = 'MB'

        values = [np.round(soma_snap_usado_filtro_pie_landsat,2), np.round(soma_snap_disponivel_filtro_pie_landsat,2)]
        colors = ['#0099C6', '#00CC96']

        fig_snap_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_snap_landsat.update_layout(
                    title_text = "SNAP -> " + value.upper(), title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_snap_landsat.add_annotation(x= 0.5, y = 0.5, 
                            text = locale.currency(np.round(soma_snap_total_filtro_pie_landsat,2),grouping=True,symbol=False) + und,
                            font = dict(size=30,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_snap_landsat     
# S N A P -> Fim para chamada do Gráfico de SNAP (pie Gauge) LANDSAT------------
########################################
# V O L U M E S - Fim                  #
########################################

### FUNÇÃO e CALLBACK ### 
########################################
# G R U P O S  - Início               #
########################################
# Início para chamada do Gráfico de Barras para memória (GB)-----------------------------------------------------------
@app_ambiente_coids.callback(
        Output('grafico_volume_grupo', 'figure',allow_duplicate=True),
        Input('volume_unidade','value'),
        prevent_initial_call = True,
)
@app_ambiente_coids.callback(
        Output('grafico_volume_grupo1', 'figure',allow_duplicate=True),
        Input('volume_unidade','value'),
        prevent_initial_call = True,
)

def update_output_grupo(value):
    if value == "Todas Unidades":

        df_depto_grupo = []
        cols = ['DEPARTAMENTO', 'VOLUME_GRUPO', 'VOLUME_TOTAL', 'VOLUME_USADO',\
               'VOLUME_DISPONIVEL']
        
        # Filtra as unidades (cgct, diotg...)
        for depto in opcoes:
            if depto == 'Todas Unidades':
                continue
            
            depto_selecionado =  df_volume.loc[df_volume['DEPARTAMENTO'] == depto, :] 
            if depto_selecionado.empty:
                continue
            
            # Filtra os grupos dentro de cada unidade e adiciona em um dataframe: df1_grupo)
            for grupo in depto_selecionado['VOLUME_GRUPO'].unique():
                filtro_depto_grupo = depto_selecionado.loc[depto_selecionado['VOLUME_GRUPO'] == grupo, :]
                soma_grupo_vol_total = filtro_depto_grupo['VOLUME_TOTAL'].sum()
                soma_grupo_vol_usado = filtro_depto_grupo['VOLUME_USADO'].sum() 
                soma_grupo_vol_disponivel = filtro_depto_grupo['VOLUME_DISPONIVEL'].sum()

                df_depto_grupo.append([depto, grupo, soma_grupo_vol_total, soma_grupo_vol_usado, soma_grupo_vol_disponivel])

        df1_grupo = pd.DataFrame(df_depto_grupo,columns=cols) 

        fig_unidade = go.Figure (data = [
            go.Bar(x = [df1_grupo['DEPARTAMENTO'],df1_grupo['VOLUME_GRUPO']], y = df1_grupo['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', 
                text = df1_grupo['VOLUME_TOTAL'].apply(locale.currency,grouping=True,symbol=False),  # text = df1_grupo['VOLUME_TOTAL'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [df1_grupo['DEPARTAMENTO'],df1_grupo['VOLUME_GRUPO']], y = df1_grupo['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', 
                text = df1_grupo['VOLUME_USADO'].apply(locale.currency,grouping=True,symbol=False), #text = df1_grupo['VOLUME_USADO'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [df1_grupo['DEPARTAMENTO'],df1_grupo['VOLUME_GRUPO']], y = df1_grupo['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', 
                text = df1_grupo['VOLUME_DISPONIVEL'].apply(locale.currency,grouping=True,symbol=False), #text = df1_grupo['VOLUME_DISPONIVEL'],
                textposition='inside',textfont_size=18),
        ])                                   
        fig_unidade.update_layout(title = '<b>V O L U M E</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_unidade.update_yaxes(title_text='Terabyte (TB)'),  
        fig_unidade.update_traces(marker_line_color='gray', marker_line_width=0.1)
    else:
        df_depto_grupo = []
        cols = ['DEPARTAMENTO', 'VOLUME_GRUPO', 'VOLUME_TOTAL', 'VOLUME_USADO',\
               'VOLUME_DISPONIVEL']
        
        # Filtra as unidades (cgct, diotg...)
        for depto in opcoes:
            if depto == 'Todas Unidades':
                continue
            
            depto_selecionado =  df_volume.loc[df_volume['DEPARTAMENTO'] == depto, :] 
            if depto_selecionado.empty:
                continue
            
            # Filtra os grupos dentro de cada unidade e adiciona em um dataframe: df1_grupo)
            for grupo in depto_selecionado['VOLUME_GRUPO'].unique():
                filtro_depto_grupo = depto_selecionado.loc[depto_selecionado['VOLUME_GRUPO'] == grupo, :]
                soma_grupo_vol_total = filtro_depto_grupo['VOLUME_TOTAL'].sum()
                soma_grupo_vol_usado = filtro_depto_grupo['VOLUME_USADO'].sum() 
                soma_grupo_vol_disponivel = filtro_depto_grupo['VOLUME_DISPONIVEL'].sum()

                df_depto_grupo.append([depto, grupo, soma_grupo_vol_total, soma_grupo_vol_usado, soma_grupo_vol_disponivel])

        df1_grupo = pd.DataFrame(df_depto_grupo,columns=cols) 

        tabela_filtrada = df1_grupo.loc[(df1_grupo['DEPARTAMENTO'] == value), :]
        # Calcula volume por unidade --------------------------------------------------------------------------------
        fig_unidade = go.Figure (data = [
            go.Bar(x = [tabela_filtrada['DEPARTAMENTO'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', 
                text = tabela_filtrada['VOLUME_TOTAL'].apply(locale.currency,grouping=True,symbol=False), # text = tabela_filtrada['VOLUME_TOTAL'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [tabela_filtrada['DEPARTAMENTO'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', 
                text = tabela_filtrada['VOLUME_USADO'].apply(locale.currency,grouping=True,symbol=False),  #text = tabela_filtrada['VOLUME_USADO'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [tabela_filtrada['DEPARTAMENTO'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', 
                text = tabela_filtrada['VOLUME_DISPONIVEL'].apply(locale.currency,grouping=True,symbol=False),  # text = tabela_filtrada['VOLUME_DISPONIVEL'],
                textposition='inside',textfont_size=18),
        ])                                   
        fig_unidade.update_layout(title = '<b>V O L U M E</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_unidade.update_yaxes(title_text='Terabyte (TB)'),  
        fig_unidade.update_traces(marker_line_color='gray', marker_line_width=0.1)

    return fig_unidade
# Fim para chamada do Gráfico de Barras para Volume Grupo---------------------

#Início para chamada do Gráfico de <Volumes> (pie Gauge) OLINDA----------------
@app_ambiente_coids.callback(
    Output('grafico_grupo', 'figure', allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)

def update_output_grupo(value):
    if value == "Todas Unidades":


        df_depto_grupo = []
        cols = ['DEPARTAMENTO', 'VOLUME_GRUPO', 'VOLUME_TOTAL', 'VOLUME_USADO',\
               'VOLUME_DISPONIVEL']
 
        # Filtra as unidades (cgct, diotg...)
        for depto in opcoes:
            if depto == 'Todas Unidades':
                continue
            
            depto_selecionado =  df_volume.loc[df_volume['DEPARTAMENTO'] == depto, :] 
            if depto_selecionado.empty:
                continue
            
            # Filtra os grupos dentro de cada unidade e adiciona em um dataframe: df1_grupo)
            for grupo in depto_selecionado['VOLUME_GRUPO'].unique():
                filtro_depto_grupo = depto_selecionado.loc[depto_selecionado['VOLUME_GRUPO'] == grupo, :]
                soma_grupo_vol_total = filtro_depto_grupo['VOLUME_TOTAL'].sum()
                soma_grupo_vol_usado = filtro_depto_grupo['VOLUME_USADO'].sum() 
                soma_grupo_vol_disponivel = filtro_depto_grupo['VOLUME_DISPONIVEL'].sum()

                df_depto_grupo.append([depto, grupo, soma_grupo_vol_total, soma_grupo_vol_usado, soma_grupo_vol_disponivel])

        df1_grupo = pd.DataFrame(df_depto_grupo,columns=cols) 

        soma_volume_total = df1_grupo['VOLUME_TOTAL'].sum()
        soma_volume_usado = df1_grupo['VOLUME_USADO'].sum()
        soma_volume_disponivel = df1_grupo['VOLUME_DISPONIVEL'].sum()

        if soma_volume_total >= 1 and soma_volume_total < 1024:
            soma_volume_total_pie = soma_volume_total
            soma_volume_disponivel_pie = soma_volume_disponivel
            soma_volume_usado_pie = soma_volume_usado
            und = 'TB'

        if soma_volume_total >= 1024:
            soma_volume_total_pie = soma_volume_total/1024
            soma_volume_disponivel_pie = soma_volume_disponivel/1024
            soma_volume_usado_pie = soma_volume_usado/1024
            und = 'PB'

        if soma_volume_total < 1:
            soma_volume_total_pie = soma_volume_total*1024
            soma_volume_disponivel_pie = soma_volume_disponivel*1024
            soma_volume_usado_pie = soma_volume_usado*1024
            und = 'GB'
            if soma_volume_total_pie < 1:
                soma_volume_total_pie *= 1024
                soma_volume_disponivel_pie *= 1024
                soma_volume_usado_pie *= 1024
                und = 'MB'
     
        labels = ['Usado', 'Disponível']
        values = [np.round(soma_volume_usado_pie,2), np.round(soma_volume_disponivel_pie,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7,showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume.update_layout(
                    title_text = "OLINDA - VOLUMES", title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_volume_total_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    else:
        df_depto_grupo = []
        cols = ['DEPARTAMENTO', 'VOLUME_GRUPO', 'VOLUME_TOTAL', 'VOLUME_USADO',\
               'VOLUME_DISPONIVEL']
        
        # Filtra as unidades (cgct, diotg...)
        for depto in opcoes:
            if depto == 'Todas Unidades':
                continue
            
            depto_selecionado =  df_volume.loc[df_volume['DEPARTAMENTO'] == depto, :] 
            if depto_selecionado.empty:
                continue
            
            # Filtra os grupos dentro de cada unidade e adiciona em um dataframe: df1_grupo)
            for grupo in depto_selecionado['VOLUME_GRUPO'].unique():
                filtro_depto_grupo = depto_selecionado.loc[depto_selecionado['VOLUME_GRUPO'] == grupo, :]
                soma_grupo_vol_total = filtro_depto_grupo['VOLUME_TOTAL'].sum()
                soma_grupo_vol_usado = filtro_depto_grupo['VOLUME_USADO'].sum() 
                soma_grupo_vol_disponivel = filtro_depto_grupo['VOLUME_DISPONIVEL'].sum()

                df_depto_grupo.append([depto, grupo, soma_grupo_vol_total, soma_grupo_vol_usado, soma_grupo_vol_disponivel])

        df1_grupo = pd.DataFrame(df_depto_grupo,columns=cols) 

        tabela_filtrada = df1_grupo.loc[(df1_grupo['DEPARTAMENTO'] == value), :]

        soma_volume_total_filtro = tabela_filtrada['VOLUME_TOTAL'].sum()
        soma_volume_usado_filtro = tabela_filtrada['VOLUME_USADO'].sum()
        soma_volume_disponivel_filtro = tabela_filtrada['VOLUME_DISPONIVEL'].sum()

        if soma_volume_total_filtro >= 1 and soma_volume_total_filtro < 1024:
            soma_volume_total_filtro_pie = soma_volume_total_filtro
            soma_volume_disponivel_filtro_pie = soma_volume_disponivel_filtro
            soma_volume_usado_filtro_pie = soma_volume_usado_filtro
            und = 'TB'

        if soma_volume_total_filtro >= 1024:
            soma_volume_total_filtro_pie = soma_volume_total_filtro/1024
            soma_volume_disponivel_filtro_pie = soma_volume_disponivel_filtro/1024
            soma_volume_usado_filtro_pie = soma_volume_usado_filtro/1024
            und = 'PB'

        if soma_volume_total_filtro < 1:
            soma_volume_total_filtro_pie = soma_volume_total_filtro*1024
            soma_volume_disponivel_filtro_pie = soma_volume_disponivel_filtro*1024
            soma_volume_usado_filtro_pie = soma_volume_usado_filtro*1024
            und = 'GB'
            if soma_volume_total_filtro_pie < 1:
                soma_volume_total_filtro_pie *= 1024
                soma_volume_disponivel_filtro_pie *= 1024
                soma_volume_usado_filtro_pie *= 1024
                und = 'MB'

        labels = ['Usado', 'Disponível']
        values = [np.round(soma_volume_usado_filtro_pie,2), np.round(soma_volume_disponivel_filtro_pie,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume.update_layout(
                    title_text = value.upper(), title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume.add_annotation(x= 0.5, y = 0.5, 
                            text = locale.currency(np.round(soma_volume_total_filtro_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=30,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_volume     
# Fim da chamada do Gráfico de Volumes (pie Gauge) OLINDA----------------------

# Início da Tabela de Dados Volumes--------------------------------------------
@app_ambiente_coids.callback(Output('tabela-dados-grupo', 'children'),
    [Input('volume_grupo', 'value')],prevent_initial_call = True,
)

@app_ambiente_coids.callback(Output('tabela-dados-grupo1', 'children'),
    [Input('volume_grupo', 'value')],prevent_initial_call = True,
)

def update_table_volume(value):
    #html.Div([
    if value == "Todos Grupos":        
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Volumes (TB)', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True} for i in df_filtro_volume.columns
                    if i != 'id'
                ],
                data=df_filtro_volume.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 15,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
    else:
        partes = value.split('_')
        value_depto = partes[0]
        value_grupo = partes[1]
        tabela_filtrada = df_volume.loc[(df_volume['DEPARTAMENTO'] == value_depto) & \
                                         (df_volume['VOLUME_GRUPO'] == value_grupo), :]
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Volume (TB)', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': False} for i in tabela_filtrada.columns
                    if i != 'id'
                ],
                data=tabela_filtrada.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 15,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
# Fim da Tabela de Dados ----------------------------------------------------------------------------------------------

# MONITOR DE GRUPO DE TRABALHO - GT
@app_ambiente_coids.callback(
    Output('card_monitor_gt', 'children',allow_duplicate=True),
    Input('volume_unidade','value'),
    prevent_initial_call = True,
)

def update_card_monitor_gt(value):
    if value == "Todas Unidades":
        ########################################################### GERAL
        # Filtra todas unidades mostrando o valor para cada unidade

        df_depto_grupo = []
        cols = ['DEPARTAMENTO', 'VOLUME_GRUPO', 'VOLUME_TOTAL', 'VOLUME_USADO',\
               'VOLUME_DISPONIVEL']

        # Filtra as unidades (cgct, diotg...)
        for depto in opcoes:
            if depto == 'Todas Unidades':
                continue
            
            depto_selecionado =  df_volume.loc[df_volume['DEPARTAMENTO'] == depto, :] 
            if depto_selecionado.empty:
                continue
            
            # Filtra os grupos dentro de cada unidade e adiciona em um dataframe: df1_grupo)
            for grupo in depto_selecionado['VOLUME_GRUPO'].unique():
                filtro_depto_grupo = depto_selecionado.loc[depto_selecionado['VOLUME_GRUPO'] == grupo, :]
                soma_grupo_vol_total = filtro_depto_grupo['VOLUME_TOTAL'].sum()
                soma_grupo_vol_usado = filtro_depto_grupo['VOLUME_USADO'].sum() 
                soma_grupo_vol_disponivel = filtro_depto_grupo['VOLUME_DISPONIVEL'].sum()
                df_depto_grupo.append([depto, grupo, soma_grupo_vol_total, soma_grupo_vol_usado, soma_grupo_vol_disponivel])

        df1_grupo = pd.DataFrame(df_depto_grupo,columns=cols) 

        colors = ['#0099C6', '#00CC96'],
        labels = ['Disponível', 'Usado']

        filtro_depto_df1 = len(df1_grupo)
        card = *[dbc.Col([  
                 
            html.Br(),
            html.Br(),
            html.Div(df1_grupo.iloc[field,1].upper(), style={"width":"16Rem","font-weight": "bold", "text-align":"center", "background":"lightblue"}),
            dbc.ListGroup(
                [   
                dbc.ListGroupItem("Departamento: " + str(df1_grupo.iloc[field,0].upper()), color="#E0EEEE",style={"width":"16Rem"}),                        
                dbc.ListGroupItem("Total (TB): " + str(locale.currency(np.round(df1_grupo.iloc[field,2],2),grouping=True,symbol=False)), color="#E0EEEE",style={"width":"16Rem"}),
                dbc.ListGroupItem("Usado (TB): " + str(locale.currency(np.round(df1_grupo.iloc[field,3],2),grouping=True,symbol=False)), color="#E0EEEE",style={"width":"16Rem"}),
                dbc.ListGroupItem("Disponível (TB): " + str(locale.currency(np.round(df1_grupo.iloc[field,4],2),grouping=True,symbol=False)), color="#E0EEEE",style={"width":"16Rem"}),
                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ), 
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in range(0,filtro_depto_df1)],

    else: 

        df_depto_grupo = []
        cols = ['DEPARTAMENTO', 'VOLUME_GRUPO', 'VOLUME_TOTAL', 'VOLUME_USADO',\
               'VOLUME_DISPONIVEL']
        
        # Filtra as unidades (cgct, diotg...)
        for depto in opcoes:
            if depto == 'Todas Unidades':
                continue
            
            depto_selecionado =  df_volume.loc[df_volume['DEPARTAMENTO'] == depto, :] 
            if depto_selecionado.empty:
                continue
            
            # Filtra os grupos dentro de cada unidade e adiciona em um dataframe: df1_grupo)
            for grupo in depto_selecionado['VOLUME_GRUPO'].unique():
                filtro_depto_grupo = depto_selecionado.loc[depto_selecionado['VOLUME_GRUPO'] == grupo, :]
                soma_grupo_vol_total = filtro_depto_grupo['VOLUME_TOTAL'].sum()
                soma_grupo_vol_usado = filtro_depto_grupo['VOLUME_USADO'].sum() 
                soma_grupo_vol_disponivel = filtro_depto_grupo['VOLUME_DISPONIVEL'].sum()
                df_depto_grupo.append([depto, grupo, soma_grupo_vol_total, soma_grupo_vol_usado, soma_grupo_vol_disponivel])

        df1_grupo = pd.DataFrame(df_depto_grupo,columns=cols) 

        tabela_filtrada = df1_grupo.loc[(df1_grupo['DEPARTAMENTO'] == value), :]

        filtro_depto_df1 = len(tabela_filtrada)
        card = *[dbc.Col([  
            html.Br(),
            html.Br(),
            html.Div(tabela_filtrada.iloc[field,1].upper(), style={"width":"16Rem","font-weight": "bold", "text-align":"center", "background":"lightblue"}),
            dbc.ListGroup(
                [   
                dbc.ListGroupItem("Departamento: " + str(tabela_filtrada.iloc[field,0].upper()), color="#E0EEEE",style={"width":"16Rem"}),                        
                dbc.ListGroupItem("Total (TB): " + str(locale.currency(np.round(tabela_filtrada.iloc[field,2],2),grouping=True,symbol=False)), color="#E0EEEE",style={"width":"16Rem"}),
                dbc.ListGroupItem("Usado (TB): " + str(locale.currency(np.round(tabela_filtrada.iloc[field,3],2),grouping=True,symbol=False)), color="#E0EEEE",style={"width":"16Rem"}),
                dbc.ListGroupItem("Disponível (TB): " + str(locale.currency(np.round(tabela_filtrada.iloc[field,4],2),grouping=True,symbol=False)), color="#E0EEEE",style={"width":"16Rem"}),
                    ],
                    flush=True,
                    style={"color":"primary", "text-align":"left", "font-size":"14px","color":"blue","border":"darkblue"},
                    className="text-justify shadow",
                ), 
        ],
        style={"width":"17Rem","color":"black"},width=3,
        ) for field in range(0,filtro_depto_df1)],

    return card   #Comentado até resolver o problema do CARD

########################################
# G R U P O S - Fim                  #
########################################

########################################
# A G G R E G A T E - Início           #
########################################
# Início para chamada do Gráfico de Barras para Aggregate OLINDA --------------------------
@app_ambiente_coids.callback(
        Output('grafico_aggr_volume', 'figure',allow_duplicate=True),
        Input('volume_aggr','value'),
        prevent_initial_call = True,
)
@app_ambiente_coids.callback(
        Output('grafico_aggr_volume1', 'figure',allow_duplicate=True),
        Input('volume_aggr','value'),
        prevent_initial_call = True,
)
def update_output(value):
    if value == "Todos Aggregates":
        fig_aggr = go.Figure (data = [
            go.Bar(x = [df_volume['VOLUME_AGGREGATE'],df_volume['VOLUME_GRUPO']], y = df_volume['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', \
                text = df_volume['VOLUME_TOTAL'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18, 
                hovertemplate='Aggregate/Unidade: %{x}'+'<br> Volume Total: %{y:.2f}'
            ),
            go.Bar(x = [df_volume['VOLUME_AGGREGATE'],df_volume['VOLUME_GRUPO']], y = df_volume['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', \
                text = df_volume['VOLUME_USADO'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18), 
            go.Bar(x = [df_volume['VOLUME_AGGREGATE'],df_volume['VOLUME_GRUPO']], y = df_volume['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', \
                text = df_volume['VOLUME_DISPONIVEL'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18),
        ])                                   
        fig_aggr.update_layout(title = '<b>A G G R E G A T E S - O L I N D A</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_aggr.update_yaxes(title_text='Terabyte (TB)'),  
        fig_aggr.update_traces(marker_line_color='gray', marker_line_width=0.1)

    else:
        tabela_filtrada = df_volume.loc[df_volume['VOLUME_AGGREGATE'] == value, :]
        # Calcula volume por unidade --------------------------------------------------------------------------------
        fig_aggr = go.Figure (data = [
            go.Bar(x = [tabela_filtrada['VOLUME_AGGREGATE'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', \
                text = tabela_filtrada['VOLUME_TOTAL'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18,
                hovertemplate='Aggregate/Unidade: %{x}'+'<br> Volume Total: %{y:.2f}' 
            ),
            go.Bar(x = [tabela_filtrada['VOLUME_AGGREGATE'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', \
                text = tabela_filtrada['VOLUME_USADO'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18), 
            go.Bar(x = [tabela_filtrada['VOLUME_AGGREGATE'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', \
                text = tabela_filtrada['VOLUME_DISPONIVEL'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18),
        ])                                   
        fig_aggr.update_layout(title = '<b>A G G R E G A T E S - O L I N D A</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_aggr.update_yaxes(title_text='Terabyte (TB)'),  
        fig_aggr.update_traces(marker_line_color='gray', marker_line_width=0.1)
    return fig_aggr
# Fim  para chamada do Gráfico de Barras para Aggregate OLINDA --------------------------

# Início para chamada do Gráfico de Barras para Aggregate LANDSAT--------------------------------
@app_ambiente_coids.callback(
        Output('grafico_aggr_volume_landsat', 'figure',allow_duplicate=True),
        Input('volume_aggr_landsat','value'),
        prevent_initial_call = True,
)
@app_ambiente_coids.callback(
        Output('grafico_aggr_volume_landsat1', 'figure',allow_duplicate=True),
        Input('volume_aggr_landsat','value'),
        prevent_initial_call = True,
)
def update_output_grafico_landsat(value):
    if value == "Todos Aggregates":
        fig_aggr_landsat = go.Figure (data = [
            go.Bar(x = [df_volume_landsat['VOLUME_AGGREGATE'],df_volume_landsat['VOLUME_GRUPO']], y = df_volume_landsat['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', text = df_volume['VOLUME_TOTAL'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [df_volume_landsat['VOLUME_AGGREGATE'],df_volume_landsat['VOLUME_GRUPO']], y = df_volume_landsat['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', text = df_volume_landsat['VOLUME_USADO'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [df_volume_landsat['VOLUME_AGGREGATE'],df_volume_landsat['VOLUME_GRUPO']], y = df_volume_landsat['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', text = df_volume['VOLUME_DISPONIVEL'],
                textposition='inside',textfont_size=18),
        ])                                   
        fig_aggr_landsat.update_layout(title = '<b>A G G R E G A T E S - L A N D S A T</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_aggr_landsat.update_yaxes(title_text='Terabyte (TB)'),  
        fig_aggr_landsat.update_traces(marker_line_color='gray', marker_line_width=0.1)

    else:
        tabela_filtrada = df_volume_landsat.loc[df_volume_landsat['VOLUME_AGGREGATE'] == value, :]
        # Calcula volume por unidade --------------------------------------------------------------------------------
        fig_aggr_landsat = go.Figure (data = [
            go.Bar(x = [tabela_filtrada['VOLUME_AGGREGATE'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_TOTAL'],
                name = 'Total', marker_color = '#54A24B', text = tabela_filtrada['VOLUME_TOTAL'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [tabela_filtrada['VOLUME_AGGREGATE'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_USADO'],
                name = 'Usado', marker_color = '#0099C6', text = tabela_filtrada['VOLUME_USADO'],
                textposition='inside',textfont_size=18), 
            go.Bar(x = [tabela_filtrada['VOLUME_AGGREGATE'],tabela_filtrada['VOLUME_GRUPO']], y = tabela_filtrada['VOLUME_DISPONIVEL'],
                name = 'Disponível', marker_color = '#00CC96', text = tabela_filtrada['VOLUME_DISPONIVEL'],
                textposition='inside',textfont_size=18),
        ])                                   
        fig_aggr_landsat.update_layout(title = '<b>A G G R E G A T E S - L A N D S A T</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_aggr_landsat.update_yaxes(title_text='Terabyte (TB)'),  
        fig_aggr_landsat.update_traces(marker_line_color='gray', marker_line_width=0.1)
    return fig_aggr_landsat
# Fim para chamada do Gráfico de Barras para Aggregate LANDSAT--------------------------------

#Início para chamada do Gráfico de <Volumes-AGGR> (pie Gauge) Olinda -----------------
# Obs.: Neste gráfico, a unidade utilizada é em Terabyte para facilitar a leitura
@app_ambiente_coids.callback(
    Output('grafico_pie_aggr', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_pie_aggr1', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

def update_output_volume(value):
    if value == "Todos Aggregates": 
        labels = ['Usado (PB)', 'Disponível (PB)']

        if soma_aggr_total >= 1 and soma_aggr_total < 1024:
            soma_aggr_total_pie = soma_aggr_total
            soma_aggr_disponivel_pie = soma_aggr_disponivel
            soma_aggr_usado_pie = soma_aggr_usado
            und = 'TB'

        if soma_aggr_total >= 1024:
            soma_aggr_total_pie = soma_aggr_total/1024
            soma_aggr_disponivel_pie = soma_aggr_disponivel/1024
            soma_aggr_usado_pie = soma_aggr_usado/1024
            und = 'PB'

        if soma_aggr_total < 1:
            soma_aggr_total_pie = soma_aggr_total*1024
            soma_aggr_disponivel_pie = soma_aggr_disponivel*1024
            soma_aggr_usado_pie = soma_aggr_usado*1024
            und = 'GB'
            if soma_aggr_total_pie < 1:
                soma_aggr_total_pie *= 1024
                soma_aggr_disponivel_pie *= 1024
                soma_aggr_usado_pie *= 1024
                und = 'MB'

        values = [np.round(soma_aggr_usado_pie,2), np.round(soma_aggr_disponivel_pie,2)]

        colors = ['#0099C6', '#00CC96']
        fig_volume_aggr = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_aggr.update_layout(
                    title_text = 'OLINDA - AGGREGATES', title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_aggr.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_aggr_total_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    else:
        tabela_filtrada = df_aggr.loc[df_aggr['AGGR'] == value, :]      
        soma_aggr_total_filtro = tabela_filtrada['AGGR_TOTAL'].sum()

        soma_aggr_usado_filtro = tabela_filtrada['AGGR_USADO'].sum()

        soma_aggr_disponivel_filtro = tabela_filtrada['AGGR_DISPONIVEL'].sum()

        labels = ['Usado', 'Disponível']

        if soma_aggr_total_filtro >= 1 and soma_aggr_total_filtro < 1024:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro
            und = 'TB'

        if soma_aggr_total_filtro >= 1024:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro/1024
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro/1024
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro/1024
            und = 'PB'

        if soma_aggr_total_filtro < 1:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro*1024
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro*1024
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro*1024
            und = 'GB'
            if soma_aggr_total_filtro_pie < 1:
                soma_aggr_total_filtro_pie *= 1024
                soma_aggr_disponivel_filtro_pie *= 1024
                soma_aggr_usado_filtro_pie *= 1024
                und = 'MB'

        values = [np.round(soma_aggr_usado_filtro_pie,2), np.round(soma_aggr_disponivel_filtro_pie,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume_aggr = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_aggr.update_layout(
                    title_text = value.upper(), title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_aggr.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_aggr_total_filtro_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_volume_aggr     

# L A N D S A T ## L A N D S A T ## L A N D S A T #
#Início para chamada do Gráfico de Volumes (pie Gauge) Landsat------------------------
# Obs.: Neste gráfico, a unidade utilizada é em Terabyte para facilitar a leitura
@app_ambiente_coids.callback(
    Output('grafico_pie_aggr_landsat', 'figure', allow_duplicate=True),
    Input('volume_aggr_landsat','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_pie_aggr_landsat1', 'figure', allow_duplicate=True),
    Input('volume_aggr_landsat','value'),
    prevent_initial_call = True,
)

def update_output_volume(value):
    if value == "Todos Aggregates": 
        labels = ['','']
        values = [np.round(soma_aggr_usado_landsat/1024,2), np.round(soma_aggr_disponivel_landsat/1024,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume_aggr_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_aggr_landsat.update_layout(
                        title_text = 'LANDSAT - AGGREGATES', title_x=0.5,title_y=0.96,
                        title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_aggr_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_aggr_total_landsat/1024,2),grouping=True,symbol=False) + ' PB',
                            font = dict(size=24,family='Courier-bold', 
                                            color='#54A24B'),
                            showarrow = False)
    else:
        tabela_filtrada = df_aggr_landsat.loc[df_aggr_landsat['AGGR'] == value, :]      
        soma_aggr_total_filtro = tabela_filtrada['AGGR_TOTAL'].sum()
        soma_aggr_usado_filtro = tabela_filtrada['AGGR_USADO'].sum()
        soma_aggr_disponivel_filtro = tabela_filtrada['AGGR_DISPONIVEL'].sum()
        labels = ['Usado', 'Disponível']

        if soma_aggr_total_filtro >= 1 and soma_aggr_total_filtro < 1024:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro
            und = 'TB'

        if soma_aggr_total_filtro >= 1024:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro/1024
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro/1024
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro/1024
            und = 'PB'

        if soma_aggr_total_filtro < 1:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro*1024
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro*1024
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro*1024
            und = 'GB'
            if soma_aggr_total_filtro_pie < 1:
                soma_aggr_total_filtro_pie *= 1024
                soma_aggr_disponivel_filtro_pie *= 1024
                soma_aggr_usado_filtro_pie *= 1024
                und = 'MB'

        values = [np.round(soma_aggr_usado_filtro_pie,2), np.round(soma_aggr_disponivel_filtro_pie,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume_aggr_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_aggr_landsat.update_layout(
                    title_text = value.upper(), title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_aggr_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_aggr_total_filtro_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_volume_aggr_landsat     
# Fim da chamada do Gráfico de Volumes (pie Gauge) Landsat ------------

# Início para chamada do Gráfico de Volumes (pie Gauge) Landsat: REPETIDO
# PARA SUPRIR ABA ARMAZENAMENTO 
# Obs.: Neste gráfico, a unidade utilizada é em Terabyte para facilitar 
# a leitura
@app_ambiente_coids.callback(
    Output('grafico_pie_aggr_landsat', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_pie_aggr_landsat1', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

def update_output_volume(value):
    if value == "Todos Aggregates": 
        labels = ['','']
        values = [np.round(soma_aggr_usado_landsat/1024,2), np.round(soma_aggr_disponivel_landsat/1024,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume_aggr_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_aggr_landsat.update_layout(
                        title_text = 'LANDSAT - AGGREGATES', title_x=0.5,title_y=0.86,
                        title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_aggr_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_aggr_total_landsat/1024,2),grouping=True,symbol=False) + ' PB',
                            font = dict(size=24,family='Courier-bold', 
                                            color='#54A24B'),
                            showarrow = False)
    else:
        tabela_filtrada = df_aggr_landsat.loc[df_aggr_landsat['AGGR'] == value, :]      
        soma_aggr_total_filtro = tabela_filtrada['AGGR_TOTAL'].sum()
        soma_aggr_usado_filtro = tabela_filtrada['AGGR_USADO'].sum()
        soma_aggr_disponivel_filtro = tabela_filtrada['AGGR_DISPONIVEL'].sum()
        labels = ['Usado', 'Disponível']

        if soma_aggr_total_filtro >= 1 and soma_aggr_total_filtro < 1024:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro
            und = 'TB'

        if soma_aggr_total_filtro >= 1024:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro/1024
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro/1024
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro/1024
            und = 'PB'

        if soma_aggr_total_filtro < 1:
            soma_aggr_total_filtro_pie = soma_aggr_total_filtro*1024
            soma_aggr_disponivel_filtro_pie = soma_aggr_disponivel_filtro*1024
            soma_aggr_usado_filtro_pie = soma_aggr_usado_filtro*1024
            und = 'GB'
            if soma_aggr_total_filtro_pie < 1:
                soma_aggr_total_filtro_pie *= 1024
                soma_aggr_disponivel_filtro_pie *= 1024
                soma_aggr_usado_filtro_pie *= 1024
                und = 'MB'

        values = [np.round(soma_aggr_usado_filtro_pie,2), np.round(soma_aggr_disponivel_filtro_pie,2)]
        colors = ['#0099C6', '#00CC96']
        fig_volume_aggr_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_aggr_landsat.update_layout(
                    title_text = value.upper(), title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_aggr_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(soma_aggr_total_filtro_pie,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#54A24B'),
                            showarrow = False)
    return fig_volume_aggr_landsat     
# Fim da chamada do Gráfico de Volumes (pie Gauge) Landsat ------------

# Início da Tabela de Dados Aggregates Olinda -------------------------
@app_ambiente_coids.callback(Output('tabela-dados-aggregates', 'children'),
    [Input('volume_aggr', 'value')],prevent_initial_call = True)
    
@app_ambiente_coids.callback(Output('tabela-dados-aggregates1', 'children'),
    [Input('volume_aggr', 'value')],prevent_initial_call = True,)

def update_table_volume(value):
    if value == "Todos Aggregates":        
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Olinda Aggregates (TB): ' + value, style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True} for i in df_filtro_volume.columns
                    if i != 'id'
                ],
                data=df_filtro_volume.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 10,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
    else:
        tabela_filtrada = df_filtro_volume.loc[df_filtro_volume['AGGREGATE'] == value, :]      
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Olinda Aggregate (TB): ' + value, style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': False} for i in tabela_filtrada.columns
                    if i != 'id'
                ],
                data=tabela_filtrada.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 10,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
# Fim da Tabela de Aggregates Olinda ----------------------------------

# Início da Tabela de Dados Aggregates LANDSAT ------------------------
@app_ambiente_coids.callback(Output('tabela-dados-aggregates-landsat', 'children'),
    [Input('volume_aggr_landsat', 'value')],prevent_initial_call = True)
    
@app_ambiente_coids.callback(Output('tabela-dados-aggregates-landsat1', 'children'),
    [Input('volume_aggr_landsat', 'value')],prevent_initial_call = True,)

def update_table_volume_aggr_landsat(value):
    #html.Div([
    if value == "Todos Aggregates":        
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Landsat Aggregates (TB): ' + value, style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True} for i in df_filtro_volume_landsat.columns
                    if i != 'id'
                ],
                data=df_filtro_volume_landsat.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 10,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
    else:
        tabela_filtrada = df_filtro_volume_landsat.loc[df_filtro_volume_landsat['AGGREGATE'] == value, :]      
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas -  Landsat Aggregate (TB): ' + value, style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': False} for i in tabela_filtrada.columns
                    if i != 'id'
                ],
                data=tabela_filtrada.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 10,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
# Fim da Tabela de Aggregates lANDSAT ---------------------------------
########################################
# A G G R E G A T E - Fim              #
########################################

########################################
# D I S C O S  -  Início               #
########################################
#Início para chamada do Gráfico - *** Discos GERAL *** (pie Gauge) ----
@app_ambiente_coids.callback(
    Output('grafico_pie_disco', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_pie_disco1', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

def update_output_disco(value):
    if value == "Todos Aggregates": 
        total_fabrica = (df_disk['FACTORY_DISK'].sum())/1024
        total_disco = (df_disk['SIZE'].astype(float).sum())/1024
        dif_fabrica = total_fabrica - total_disco
        filtro_spare = df_disk.loc[df_disk['TIPO_AGGR'] == 'spare', :]
        total_spare = (filtro_spare['SIZE'].astype(float).sum())/1024
        filtro_shared = df_disk.loc[df_disk['TIPO_AGGR'] == 'shared', :]
        total_shared = (filtro_shared['SIZE'].astype(float).sum())/1024
        filtro_ssd = df_disk.loc[df_disk['FORMATO'] == 'SSD', :]
        total_ssd = (filtro_ssd['SIZE'].astype(float).sum())/1024
        disco_menos_spare_shared = total_disco - total_spare - total_shared - total_ssd
        und ="PB"

        values = [np.round(disco_menos_spare_shared,2), np.round(dif_fabrica,2),np.round(total_spare,2),\
                np.round(total_shared,2),np.round(total_ssd,2)]

        colors = ['006600', '663300','FFCC00','660099','66FF66']

        labels = ['Volume Líquido (PB)', 'Alocação de Fábrica (PB)', 'Spare (PB)', 'Shared (PB)','SSD (PB)']

        fig_volume_disco = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_disco.update_layout(
                    title_text = '[OLINDA + LANDSAT]', title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(total_fabrica,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    else:
        tabela_filtrada = df_disk.loc[df_disk['NOME_AGGR'] == value, :]    
        total_fabrica = (tabela_filtrada['FACTORY_DISK'].sum())
        total_disco = (tabela_filtrada['SIZE'].astype(float).sum())
        dif_fabrica = total_fabrica - total_disco
        filtro_spare = tabela_filtrada.loc[tabela_filtrada['TIPO_AGGR'] == 'spare', :]
        total_spare = (filtro_spare['SIZE'].astype(float).sum())
        filtro_shared = tabela_filtrada.loc[tabela_filtrada['TIPO_AGGR'] == 'shared', :]
        total_shared = (filtro_shared['SIZE'].astype(float).sum())
        filtro_ssd = tabela_filtrada.loc[tabela_filtrada['FORMATO'] == 'SSD', :]
        total_ssd = (filtro_ssd['SIZE'].astype(float).sum())
        disco_menos_spare_shared = total_disco - total_spare - total_shared - total_ssd
        und = "TB"
        values = [np.round(disco_menos_spare_shared,2), np.round(dif_fabrica,2),np.round(total_spare,2),\
                np.round(total_shared,2),np.round(total_ssd,2)]
        colors = ['006600', '663300','FFCC00','660099','66FF66']
        labels = ['Volume Líquido (TB)', 'Alocação de Fábrica (TB)', 'Spare (TB)', 'Shared (TB)','SSD (TB)']
        fig_volume_disco = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_disco.update_layout(
                    title_text = 'DISCOS: ' + value, title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(total_fabrica,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    return fig_volume_disco 

#Início para chamada do Gráfico - *** Discos GERAL *** (pie Gauge) ----
@app_ambiente_coids.callback(
    Output('grafico_pie_disco_quantidade', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_pie_disco_quantidade1', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

def update_output_disco_quantidade(value):
    if value == "Todos Aggregates": 
        qtd_total_node_disco = df_disk['NODE_DISK'].count()
        total_fabrica = (df_disk['FACTORY_DISK'].sum())/1024
        total_disco = (df_disk['SIZE'].astype(float).sum())/1024
        df_disk_agrupado_qtd = df_disk.groupby(['NODE_DISK', 'FORMATO','NOME_AGGR'], as_index=False).size()  
        df_disk_formato_soma_volume = df_disk.groupby(['FORMATO',], as_index=False).sum(numeric_only=True)
        df_disk_formato_conta_discos = df_disk.groupby(['FORMATO'], as_index=False).count()
        formato_grupo_volume_pb = round(df_disk_formato_soma_volume['FACTORY_DISK']/1024,2)
        formato_grupo_tipo = df_disk_formato_soma_volume['FORMATO']
        qtd_por_formato = df_disk_formato_conta_discos['NODE_DISK']
        names_nodes = list(df_disk_agrupado_qtd['NODE_DISK'])
        values_nodes = list(df_disk_agrupado_qtd['size'])
        formato_disco = list(df_disk_agrupado_qtd['FORMATO'])  
        colors = ['#0099C6'],
        fig_volume_disco_qtd = go.Figure(data = [go.Pie(values = values_nodes, 
                                    labels = names_nodes, hole = 0.5, showlegend=False,
                                    textfont_size=15,
                                    textposition='inside',
                                    customdata = np.stack([formato_disco], axis=-1),
                                    direction='clockwise',
                                    sort=False,
                                    marker_colors = colors,
                                    hovertemplate="<br>".join([
                                        "Node de Disco: %{label} <br>Quantidade de Discos: %{value}"
                                        "<br>Formato: %{customdata}"
                                    ]),
                                ),

                                go.Pie(values = formato_grupo_volume_pb, 
                                    labels = formato_grupo_tipo, hole = 0.77, showlegend=False,
                                    textfont_size=15,
                                    textposition='inside',
                                    customdata = np.stack([qtd_por_formato], axis=-1),
                                    direction='clockwise',
                                    sort=False,
                                    marker_colors = colors,
                                    hovertemplate="<br>".join([
                                        "Tipo de Disco Geral: %{label} <br>Volume (PB): %{value}"
                                        "<br>Quantidade: %{customdata}"
                                    ]),
                                )
                            ],
                        )

        fig_volume_disco_qtd.update_layout(
                    title_text = 'TOTAL DE DISCOS', title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco_qtd.add_annotation(x= 0.5, y = 0.5,
                            text = str(np.round(qtd_total_node_disco,2)),
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    else:

        tabela_filtrada = df_disk.loc[df_disk['NOME_AGGR'] == value, :]  
        qtd_total_node_disco = tabela_filtrada['NODE_DISK'].count()
        total_fabrica = (tabela_filtrada['FACTORY_DISK'].sum())/1024
        total_disco = (tabela_filtrada['SIZE'].astype(float).sum())/1024
        df_disk_agrupado_qtd = tabela_filtrada.groupby(['NODE_DISK', 'FORMATO','NOME_AGGR'], as_index=False).size()  
        df_disk_formato_soma_volume = tabela_filtrada.groupby(['FORMATO'], as_index=False).sum()
        df_disk_formato_conta_discos = tabela_filtrada.groupby(['FORMATO'], as_index=False).count()
        formato_grupo_volume_pb = round(df_disk_formato_soma_volume['FACTORY_DISK']/1024,2)
        formato_grupo_tipo = df_disk_formato_soma_volume['FORMATO']
        qtd_por_formato = df_disk_formato_conta_discos['NODE_DISK']
        names_nodes = list(df_disk_agrupado_qtd['NODE_DISK'])
        values_nodes = list(df_disk_agrupado_qtd['size'])
        formato_disco = list(df_disk_agrupado_qtd['FORMATO'])   
        colors = ['#0099C6'],
        fig_volume_disco_qtd = go.Figure(data = [go.Pie(values = values_nodes, 
                                    labels = names_nodes, hole = 0.5, showlegend=False,
                                    textfont_size=15,
                                    textposition='inside',
                                    customdata = np.stack([formato_disco], axis=-1),
                                    direction='clockwise',
                                    sort=False,
                                    marker_colors = colors,
                                    hovertemplate="<br>".join([
                                        "Node de Disco: %{label} <br>Quantidade de Discos: %{value}"
                                        "<br>Formato: %{customdata}"
                                    ]),
                                ),
                                go.Pie(values = formato_grupo_volume_pb, 
                                    labels = formato_grupo_tipo, hole = 0.77, showlegend=False,
                                    textfont_size=15,
                                    textposition='inside',
                                    customdata = np.stack([qtd_por_formato], axis=-1),
                                    direction='clockwise',
                                    sort=False,
                                    marker_colors = colors,
                                    hovertemplate="<br>".join([
                                        "Tipo de Disco Geral: %{label} <br>Volume (PB): %{value}"
                                        "<br>Quantidade: %{customdata}"
                                    ]),
                                )
                            ],
                        )

        fig_volume_disco_qtd.update_layout(
                    title_text = 'NÚMERO TOTAL DE DISCOS', title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco_qtd.add_annotation(x= 0.5, y = 0.5,
                            text = str(np.round(qtd_total_node_disco,2)),
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    return fig_volume_disco_qtd

#Início para chamada do Gráfico - Discos *** OLINDA ***  (pie Gauge) --
@app_ambiente_coids.callback(
    Output('grafico_pie_disco_olinda', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_pie_disco_olinda1', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

def update_output_disco(value):
    if value == "Todos Aggregates": 
        labels = ['Volume Líquido (PB)', 'Alocação de Fábrica (PB)', 'Spare (PB)', 'Shared (PB)','SSD (PB)']
        total_fabrica = (df_disk_olinda['FACTORY_DISK'].sum())/1024
        total_disco = (df_disk_olinda['SIZE'].astype(float).sum())/1024
        dif_fabrica = total_fabrica - total_disco
        filtro_spare = df_disk_olinda.loc[df_disk_olinda['TIPO_AGGR'] == 'spare', :]
        total_spare = (filtro_spare['SIZE'].astype(float).sum())/1024
        filtro_shared = df_disk_olinda.loc[df_disk_olinda['TIPO_AGGR'] == 'shared', :]
        total_shared = (filtro_shared['SIZE'].astype(float).sum())/1024
        filtro_ssd = df_disk.loc[df_disk['FORMATO'] == 'SSD', :]
        total_ssd = (filtro_ssd['SIZE'].astype(float).sum())/1024
        disco_menos_spare_shared = total_disco - total_spare - total_shared - total_ssd
        und ="PB"
        values = [np.round(disco_menos_spare_shared,2), np.round(dif_fabrica,2),np.round(total_spare,2),\
                np.round(total_shared,2),np.round(total_ssd,2)]
        colors = ['006600', '663300','FFCC00','660099','66FF66']
        fig_volume_disco_olinda = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_disco_olinda.update_layout(
                    title_text = 'OLINDA', title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco_olinda.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(total_fabrica,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    else:
        tabela_filtrada = df_disk.loc[df_disk['NOME_AGGR'] == value, :]    
        total_fabrica = (tabela_filtrada['FACTORY_DISK'].sum())
        total_disco = (tabela_filtrada['SIZE'].astype(float).sum())
        dif_fabrica = total_fabrica - total_disco
        filtro_spare = tabela_filtrada.loc[tabela_filtrada['TIPO_AGGR'] == 'spare', :]
        total_spare = (filtro_spare['SIZE'].astype(float).sum())
        filtro_shared = tabela_filtrada.loc[tabela_filtrada['TIPO_AGGR'] == 'shared', :]
        total_shared = (filtro_shared['SIZE'].astype(float).sum())
        filtro_ssd = tabela_filtrada.loc[tabela_filtrada['FORMATO'] == 'SSD', :]
        total_ssd = (filtro_ssd['SIZE'].astype(float).sum())
        disco_menos_spare_shared = total_disco - total_spare - total_shared - total_ssd
        und = "TB"
        values = [np.round(disco_menos_spare_shared,2), np.round(dif_fabrica,2),np.round(total_spare,2),\
                np.round(total_shared,2),np.round(total_ssd,2)]
        colors = ['006600', '663300','FFCC00','660099','66FF66']
        labels = ['Volume Líquido (TB)', 'Alocação de Fábrica (TB)', 'Spare (TB)', 'Shared (TB)','SSD (TB)']
        fig_volume_disco_olinda = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_disco_olinda.update_layout(
                    title_text = 'DISCOS: ' + value, title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco_olinda.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(total_fabrica,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
        if "landsat" in value:
            fig_volume_disco_olinda = ""
    return fig_volume_disco_olinda 

#Início para chamada do Gráfico - Discos *** LANDSAT ***  (pie Gauge) 
@app_ambiente_coids.callback(
    Output('grafico_pie_disco_landsat', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_pie_disco_landsat1', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

def update_output_disco(value):
    if value == "Todos Aggregates": 
        labels = ['Volume Líquido (PB)', 'Alocação de Fábrica (PB)', 'Spare (PB)', 'Shared (PB)','SSD (PB)']
        total_fabrica = (df_disk_landsat['FACTORY_DISK'].sum())/1024
        total_disco = (df_disk_landsat['SIZE'].astype(float).sum())/1024
        dif_fabrica = total_fabrica - total_disco
        filtro_spare = df_disk_landsat.loc[df_disk_landsat['TIPO_AGGR'] == 'spare', :]
        total_spare = (filtro_spare['SIZE'].astype(float).sum())/1024
        filtro_shared = df_disk_landsat.loc[df_disk_landsat['TIPO_AGGR'] == 'shared', :]
        total_shared = (filtro_shared['SIZE'].astype(float).sum())/1024
        filtro_ssd = df_disk_landsat.loc[df_disk_landsat['FORMATO'] == 'SSD', :]
        total_ssd = (filtro_ssd['SIZE'].astype(float).sum())/1024
        disco_menos_spare_shared = total_disco - total_spare - total_shared - total_ssd
        und ="PB"
        values = [np.round(disco_menos_spare_shared,2), np.round(dif_fabrica,2),np.round(total_spare,2),\
                np.round(total_shared,2),np.round(total_ssd,2)]
        colors = ['006600', '663300','FFCC00','660099','66FF66']
        fig_volume_disco_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_disco_landsat.update_layout(
                    title_text = 'LANDSAT', title_x=0.5,title_y=0.96,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(total_fabrica,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    else:
        tabela_filtrada = df_disk_landsat.loc[df_disk_landsat['NOME_AGGR'] == value, :]    
        total_fabrica = (tabela_filtrada['FACTORY_DISK'].sum())
        total_disco = (tabela_filtrada['SIZE'].astype(float).sum())
        dif_fabrica = total_fabrica - total_disco
        filtro_spare = tabela_filtrada.loc[tabela_filtrada['TIPO_AGGR'] == 'spare', :]
        total_spare = (filtro_spare['SIZE'].astype(float).sum())
        filtro_shared = tabela_filtrada.loc[tabela_filtrada['TIPO_AGGR'] == 'shared', :]
        total_shared = (filtro_shared['SIZE'].astype(float).sum())
        filtro_ssd = tabela_filtrada.loc[tabela_filtrada['FORMATO'] == 'SSD', :]
        total_ssd = (filtro_ssd['SIZE'].astype(float).sum())
        disco_menos_spare_shared = total_disco - total_spare - total_shared - total_ssd
        und = "TB"
        values = [np.round(disco_menos_spare_shared,2), np.round(dif_fabrica,2),np.round(total_spare,2),\
                np.round(total_shared,2),np.round(total_ssd,2)]
        colors = ['006600', '663300','FFCC00','660099','66FF66']
        labels = ['Volume Líquido (TB)', 'Alocação de Fábrica (TB)', 'Spare (TB)', 'Shared (TB)','SSD (TB)']
        fig_volume_disco_landsat = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=False,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_volume_disco_landsat.update_layout(
                    title_text = 'LANDSAT - DISCOS: ' + value, title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_volume_disco_landsat.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(total_fabrica,2),grouping=True,symbol=False) + und,
                            font = dict(size=24,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    return fig_volume_disco_landsat
# Fim da chamada do Gráfico de Volumes (pie Gauge) --------------------

@app_ambiente_coids.callback(
    Output('grafico_barras_disco_aggr', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_barras_disco_aggr1', 'figure', allow_duplicate=True),
    Input('volume_aggr','value'),
    prevent_initial_call = True,
)

def update_output_grafico_barras_disco_aggr(value):
    if value == "Todos Aggregates": 
        qtd_total_node_disco = df_disk['NODE_DISK'].count()
        total_fabrica = (df_disk['FACTORY_DISK'].sum())/1024
        total_disco = (df_disk['SIZE'].astype(float).sum())/1024
        dif_fabrica = total_fabrica - total_disco
        filtro_spare = df_disk.loc[df_disk['TIPO_AGGR'] == 'spare', :]
        total_spare = (filtro_spare['SIZE'].astype(float).sum())/1024
        filtro_shared = df_disk.loc[df_disk['TIPO_AGGR'] == 'shared', :]
        total_shared = (filtro_shared['SIZE'].astype(float).sum())/1024
        filtro_ssd = df_disk.loc[df_disk['FORMATO'] == 'SSD', :]
        total_ssd = (filtro_ssd['SIZE'].astype(float).sum())/1024
        disco_menos_spare_shared = total_disco - total_spare - total_shared - total_ssd
        und = ""
        node_aggr_disco = df_disk[['NODE_DISK','NOME_AGGR']]   #Ok
        filtro_node_aggr = node_aggr_disco[['NODE_DISK', 'NOME_AGGR']].drop_duplicates() 
        aggr_unico = list(filtro_node_aggr['NOME_AGGR'])
        df_volume_aggr = []
        cols = ['ID_AGGR', 'AGGR', 'AGGR_TOTAL', 'AGGR_USADO', 'AGGR_DISPONIVEL', \
                'CAPACIDADE_AGGR', 'NOME_AGGR', 'NODE_DISK','AGGR_DISK']
        for aggr in aggr_unico: 
            node_aggr = filtro_node_aggr.loc[filtro_node_aggr['NOME_AGGR'] == aggr]
            linha  = df_aggr[df_aggr["AGGR"].str.contains(aggr)]
            if linha.empty:
                df_volume_aggr.append([0,aggr,0.0,0.0,\
                                    0.0,0,'',node_aggr.iloc[0,0],node_aggr.iloc[0,1]]) 
            else:    
                df_volume_aggr.append([linha.iloc[0,0],linha.iloc[0,1],linha.iloc[0,2],linha.iloc[0,3],\
                                    linha.iloc[0,4],linha.iloc[0,5],linha.iloc[0,6],\
                                    node_aggr.iloc[0,0],node_aggr.iloc[0,1]]) 
        df_volume_aggr = pd.DataFrame(df_volume_aggr,columns=cols)
        df_color = []
        cols = ['color']
        df_descr_color = []
        cols = ['descr_color']
        for n in range(len(df_disk)):
            if df_disk['TIPO_AGGR'][n] == 'spare':
                df_color.append('#FFCC00')  # yellow
                df_descr_color.append('Spare')
            elif df_disk['TIPO_AGGR'][n] == 'shared':   # purple
                df_color.append('#A020F0')  
                df_descr_color.append('Shared')
            elif df_disk['FORMATO'][n] == 'SSD':   # light0-green
                df_color.append('#66FF66')
                df_descr_color.append('SSD')
            elif df_disk['TIPO_AGGR'][n] == 'broken':   # black
                df_color.append('#000000')
                df_descr_color.append('Broken')
            else:
                df_color.append('#006600')   # green
                df_descr_color.append('Discos em uso')
        df_color_data = dict(zip(df_descr_color, df_color))
        df_color_data2 = [df_descr_color, df_color]
        df_color_data3 = pd.DataFrame([df_descr_color, df_color])
        a = df_color_data3.iloc[0]

        ##########################

        # Montagem do dicionário na barra do gráfico - disco
        df_disk['SIZE'] = df_disk['SIZE'].astype(float)
        df_discos_somavolume = list(df_disk.groupby(['NODE_DISK','NOME_AGGR'])['SIZE'].transform('sum'))
        df_discos_contaqtd = list(df_disk.groupby(['NODE_DISK', 'NOME_AGGR'])['NODE_DISK'].transform('count'))
        diff_aggr_disco = 0.00

        # Montagem do dicionário na barra do gráfico - disco Alocação Fábrica
        df_discos_somavolume_fabrica = list(df_disk.groupby(['NODE_DISK', 'NOME_AGGR'])['FACTORY_DISK'].transform('sum'))
        df_discos_contaqtd_fabrica = list(df_disk.groupby(['NODE_DISK', 'NOME_AGGR'])['NODE_DISK'].transform('count'))
        diff_aggr_disco = 0.00

        ############# Incluir volume no gráfico de barras  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        df_volume_no_aggregate = []
        cols = ['VOLUME_AGGREGATE','VOLUME_TOTAL', \
                    'VOLUME_SNAP', 'VOLUME_GERAL_NO_AGGR', \
                    'NODE_DISK','AGGR_DISK']

        # Separar dados de volume em relação ao aggregate
        for aggr in aggr_unico: 
            node_aggr = filtro_node_aggr.loc[filtro_node_aggr['NOME_AGGR'] == aggr]
            linha_filtro = df_volume.loc[df_volume['VOLUME_AGGREGATE'] == aggr, :]
            vol_total = linha_filtro['VOLUME_TOTAL'].sum()
            vol_snap = linha_filtro['VOLUME_SNAP_TOTAL'].sum()
            volume_geral_dentro_aggr = vol_total + vol_snap

            if linha_filtro.empty:
                df_volume_no_aggregate.append([aggr,0.0, 0.0, 0.0,node_aggr.iloc[0,0],node_aggr.iloc[0,1]]) 
            else:    
                df_volume_no_aggregate.append([aggr,vol_total, vol_snap,volume_geral_dentro_aggr,node_aggr.iloc[0,0],node_aggr.iloc[0,1]]) 
        df_volume_no_aggregate = pd.DataFrame(df_volume_no_aggregate,columns=cols)   
        df_volume_no_aggregate.loc[df_volume_no_aggregate['VOLUME_AGGREGATE']=='-', \
                                    ['VOLUME_GERAL_NO_AGGR']] = 0 

        fig_bar_disk = go.Figure(data = [
            # VOLUMES
            go.Bar(x = [df_volume_no_aggregate['NODE_DISK'],df_volume_no_aggregate['AGGR_DISK']], y = df_volume_no_aggregate['VOLUME_GERAL_NO_AGGR'],
                name = 'Volume dentro Aggregate: ', marker_color = '#00FF00', \
                text = df_volume_no_aggregate['VOLUME_GERAL_NO_AGGR'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=15,
                hovertemplate='Controladora/Aggregate: %{x}'+'<br> Volume dentro do Aggregate: %{y:.2f}'
                ), 

            # AGGREGATES
            go.Bar(x = [df_volume_aggr['NODE_DISK'],df_volume_aggr['AGGR_DISK']], y = df_volume_aggr['AGGR_TOTAL'],
                name = 'Aggregate: ', marker_color = '#0099C6', \
                text = df_volume_aggr['AGGR_TOTAL'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=15,
                hovertemplate='Controladora/Aggregate: %{x}'+'<br> Volume: %{y:.2f}'
                ), 

            # DISCOS
            go.Bar(x = [df_disk['NODE_DISK'],df_disk['NOME_AGGR']], y = df_disk['SIZE'],
                name = 'Discos', marker_color = df_color, \
                textposition='inside',textfont_size=15, 
                customdata = np.stack([df_discos_contaqtd, df_discos_somavolume], axis=-1),
                hovertemplate="<br>".join([
                    "Controladora/Aggregate: %{x} <br> Volume do disco(TB): %{y:.2f}", \
                    "Quantidade de Discos: %{customdata[0]}", \
                    "Volume Total dos discos(TB): %{customdata[1]:.2f}"
                ]),
            ), 
            
            go.Bar(x = [df_disk['NODE_DISK'],df_disk['NOME_AGGR']], y = df_disk['FACTORY_DISK'], 
                name = 'Aloc.Fábrica', marker_color = '#8B4726', \
                text = df_disk['FORMATO'] + "  " +  df_disk['FACTORY_DISK'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=15,
                customdata = np.stack([df_discos_contaqtd_fabrica, df_discos_somavolume_fabrica], axis=-1),
                hovertemplate="<br>".join([
                    "Controladora/Aggregate: %{x} <br> Volume do disco - Alocação de Fábrica(TB): %{y:.2f}", \
                    "Quantidade de Discos - Alocação de Fábrica: %{customdata[0]}", \
                    "Volume Total dos discos(TB) - Alocação de Fábrica : %{customdata[1]:.2f}"
                ]),
            ), 
        ])       

        fig_bar_disk.update_layout(title = '<b>SISTEMA DE ARMAZENAMENTO [Amarelo = Spare; Violeta = Shared; Verde Claro = SSD, Preto = Broken]</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 15, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 15, color = "black"),
        ),
        fig_bar_disk.update_yaxes(title_text='Volume (TB)'),  
        fig_bar_disk.update_traces(marker_line_color='gray', marker_line_width=0.1)

    return fig_bar_disk
    
# Início da Tabela de Dados dos discos de armazenamento ----------------
@app_ambiente_coids.callback(Output('tabela-dados-discos', 'children'),
    [Input('volume_aggr', 'value')],prevent_initial_call = True)
    
@app_ambiente_coids.callback(Output('tabela-dados-discos1', 'children'),
    [Input('volume_aggr', 'value')],prevent_initial_call = True,)

def update_table_discos(value):
    df_disk_tabela = df_disk.iloc[: , [0, 1, 2, 3, 4, 5, 6, 7]].copy()
    df_disk_tabela.columns = ['ID_DISCO','VOLUME(TB)','VOL.FABRICA(TB)','UND', \
                            'FORMATO','TIPO','AGGREGATE','NODE-DISCO']
    if value == "Todos Aggregates":        
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas de Discos e Aggregates: ' + value, style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True } for i in df_disk_tabela.columns
                    if i != 'id'
                ],
                data=df_disk_tabela.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 10,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
    else:
        tabela_filtrada = df_disk_tabela.loc[df_disk_tabela['NOME_AGGR'] == value, :]      
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas de Discos e Aggregates: ' + value, style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': False} for i in tabela_filtrada.columns
                    if i != 'id'
                ],
                data=tabela_filtrada.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 10,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
########################################
# D I S C O S   -    Fim               #
########################################

#######################################################################
  
# Início para chamada do Gráfico de Barras para memória (GB)-----------
@app_ambiente_coids.callback(
        Output('grafico_memoria', 'figure',allow_duplicate=True),
        Input('ambiente_virtual','value'),
        prevent_initial_call = True,
)

@app_ambiente_coids.callback(
        Output('grafico_memoria1', 'figure',allow_duplicate=True),
        Input('ambiente_virtual','value'),
        prevent_initial_call = True,
)

def update_output(value):

    if value == "Ambientes Virtuais":
        # Agrupa os valores de memória de cada VM ancoradas no HOST
        df_vm_soma = list(df_vm.groupby(['HOST'])['MEMORIA_VM'].transform('sum'))
        df_vm_conta = list(df_vm.groupby(['HOST'])['NOME_VM'].transform('count')-1)
        df_vm_soma_convertido = pd.DataFrame(df_vm_soma,columns=['dif_mem'])
       
        # Cria array com valor disponível de memória
        # (diferença entre: HOST - SOMATÓRIA DAS VMS) = disponível
        vl_disponivel = []
        for i in range(len(df_vm['MEMORIA_TOTAL_HOST'])):
            if df_vm['MEMORIA_TOTAL_HOST'][i] > 0:
                vl_disponivel.append(df_vm['MEMORIA_TOTAL_HOST'][i] - df_vm_soma_convertido['dif_mem'][i])
            else:
                vl_disponivel.append(0.0)
        vl_disponivel = pd.DataFrame(vl_disponivel,columns=['vl_livre'])
       
        fig_mem = go.Figure(data = [
            go.Bar(x = [df_vm['LABEL_POOL'],df_vm['HOST']], y = df_vm['MEMORIA_TOTAL_HOST'],
                name = 'Total', marker_color = '#54A24B', \
                text = df_vm['MEMORIA_TOTAL_HOST'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18,
                hovertemplate='Ambiente/Host Físico: %{x}'+'<br> Memória Total: %{y:.2f}'
                ), 

            go.Bar(x = [df_vm['LABEL_POOL'],df_vm['HOST']], y = vl_disponivel['vl_livre'],
                name = 'Disponível', marker_color = '#00CC96', \
                # ok text = df_vm['MEMORIA_LIVRE_HOST'].apply(locale.currency,grouping=True,symbol=False),
                text = vl_disponivel['vl_livre'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18,
                hovertemplate='Ambiente/Host Fisico: %{x}'+'<br> Memória Livre do Host: %{y:.2f}'
                ),
        
            go.Bar(x = [df_vm['LABEL_POOL'],df_vm['HOST']], y = mem_vm_GB,
                name = 'Provisionado', marker_color = '#0099C6', \
                text = df_vm['NOME_VM'],
                textposition = 'inside',textfont_size=18,
                customdata = np.stack([df_vm_conta, df_vm_soma], axis=-1),
                hovertemplate="<br>".join([
                    "Ambiente/Host Físico: %{x} <br> Memória da VM (GB): %{y:.2f}", \
                    "Nome da VM: %{text}", \
                    "Quantidade Total de VMs: %{customdata[0]}", \
                    "Memória geral das VMs (GB): %{customdata[1]:.2f}"
                ]),
            ), 
        ])                                   
        fig_mem.update_layout(title = '<b>MEMÓRIA</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
            ),
            font = dict(family = "Courier", size = 16, color = "black"),
        ),
        fig_mem.update_yaxes(title_text='Memória (GB)'),  
    else:
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :]
        mem_vm_GB_pool = tabela_filtrada['MEMORIA_VM']
        df_vm_soma = list(tabela_filtrada.groupby(['HOST'])['MEMORIA_VM'].transform('sum'))
        df_vm_conta = list(tabela_filtrada.groupby(['HOST'])['NOME_VM'].transform('count')-1)
        df_vm_soma_convertido = pd.DataFrame(df_vm_soma,columns=['dif_mem'])
       
        # Cria array com valor disponível de memória
        # (diferença entre: HOST - SOMATÓRIA DAS VMS) = disponível
        vl_disponivel = []
        for i in range(len(tabela_filtrada['MEMORIA_TOTAL_HOST'])):
            if tabela_filtrada['MEMORIA_TOTAL_HOST'][i] > 0:
                vl_disponivel.append(tabela_filtrada['MEMORIA_TOTAL_HOST'][i] - df_vm_soma_convertido['dif_mem'][i])
            else:
                vl_disponivel.append(0.0)
        vl_disponivel = pd.DataFrame(vl_disponivel,columns=['vl_livre'])

        # Calcula memória usada (host - livre) ------------------------
        fig_mem = go.Figure (data = [
            go.Bar(x = [tabela_filtrada['LABEL_POOL'],tabela_filtrada['HOST']], y = tabela_filtrada['MEMORIA_TOTAL_HOST'],
                name = 'Total', marker_color = '#54A24B',
                text = tabela_filtrada['MEMORIA_TOTAL_HOST'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18,
                hovertemplate='Ambiente/Host Físico: %{x}'+'<br> Memória Total: %{y:.2f}'
            ), 

            go.Bar(x = [tabela_filtrada['LABEL_POOL'],tabela_filtrada['HOST']], y = vl_disponivel['vl_livre'],
                name = 'Disponível', marker_color = '#00CC96', \
                text = vl_disponivel['vl_livre'].apply(locale.currency,grouping=True,symbol=False),
                textposition='inside',textfont_size=18,
                hovertemplate='Ambiente/Host Físico: %{x}'+'<br> Memória Livre do Host: %{y:.2f}'
            ),
                
            go.Bar(x = [tabela_filtrada['LABEL_POOL'],tabela_filtrada['HOST']], y = mem_vm_GB_pool, 
                name = 'Provisionado', marker_color = '#0099C6', text = tabela_filtrada['NOME_VM'],
                textposition = 'inside',textfont_size=18,
                customdata = np.stack([df_vm_conta, df_vm_soma], axis=-1),
                hovertemplate="<br>".join([
                    "Ambiente/Host Físico: %{x} <br> Memória da VM (GB): %{y:.2f}", \
                    "Nome da VM: %{text}", \
                    "Quantidade Total de VMs: %{customdata[0]}", \
                    "Memória geral das VMs (GB): %{customdata[1]:.2f}"
                ]),                
                ), 
            ]
        )                   
        fig_mem.update_layout(title = '<b>MEMÓRIA</b>', barmode = 'group',
            legend = dict(traceorder = 'normal', x=1, y=1.02,
                yanchor="bottom", xanchor="right", orientation="h",
                font = dict(family = "Courier", size = 16, color = "black"),
            ),
            font = dict(family = "Courier", size = 16, color = "black"),
        ),
        fig_mem.update_yaxes(title_text='Memória (GB)'),

    return fig_mem
# Fim para chamada do Gráfico de Barras para memória (GB) -------------

# Início para chamada do Gráfico de Barras para CPU -------------------
@app_ambiente_coids.callback(
    Output('grafico_cpu', 'figure',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)

@app_ambiente_coids.callback(
    Output('grafico_cpu1', 'figure',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)

def update_output_cpu(value):

    if value == "Ambientes Virtuais":
        a = list(df_vm['nCPU_HOST']),
        b = list(a[0])
        b_list = b[0:]
        integer_map = map(int, b_list)
        ncpu_tot_host = list(integer_map)

        # Gera a soma dos campos numéricos e também conta os campos
        # agrupados por 'HOST' SEM ALTERAR o indice, permitindo 
        # manter a ordem dos hosts
        # Ex.: df_vm_conta['NOME_VM'] mostra o número de VMs de cada
        #      HOST
        # funciona df_vm_soma = df_vm.groupby(by=['HOST'], sort=False).sum()
        # funciona df_vm_conta = df_vm.groupby(by=['HOST'], sort=False).count()
        tot_ncpu_vms = df_vm
        tot_ncpu_vms['nCPU_VM'] = tot_ncpu_vms['nCPU_VM'].astype(int)
        df_vm_soma = list(tot_ncpu_vms.groupby(['HOST'])['nCPU_VM'].transform('sum'))
        df_vm_conta = list(df_vm.groupby(['HOST'])['NOME_VM'].transform('count')-1)

        fig_cpu = go.Figure(data = [
            go.Bar(x = [df_vm['LABEL_POOL'],df_vm['HOST']], y = ncpu_tot_host,
                name = 'Total', marker_color = '#54A24B', 
                text = ncpu_tot_host,
                textposition='inside',textfont_size=18,
                hovertemplate='Ambiente/Host Físico: %{x}'+'<br> Quantidade de CPUs: %{y:.0f}'
            ),
            go.Bar(x = [df_vm['LABEL_POOL'],df_vm['HOST']], y = df_vm['nCPU_VM'],
                name = 'Provisionado', marker_color = '#0099C6', text = df_vm['NOME_VM'],
                textposition = 'inside',textfont_size=18,
                customdata = np.stack([df_vm_conta, df_vm_soma], axis=-1),
                hovertemplate="<br>".join([
                    "Ambiente/Host Físico: %{x} <br> Nº de CPUs da VM: %{y:.0f}", \
                    "Nome da VM: %{text}", \
                    "Quantidade Total de VMs: %{customdata[0]}", \
                    "Quantidade Total de CPUs das VMs: %{customdata[1]:.0f}"
                ]),  
            ),
            ] 
        )                                   
        fig_cpu.update_layout(title = '<b>CPU</b>', barmode = 'group',
        legend = dict(traceorder = 'normal', x=1, y=1.02,
            yanchor="bottom", xanchor="right", orientation="h"),
            font = dict(family = "Courier", size = 16, color = "black"),
        ),
        font = dict(family="Courier New, monospace",size=16),
        fig_cpu.update_yaxes(title_text='Nº CPUs'),
    else:
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :]
        a = list(tabela_filtrada['nCPU_HOST']),
        b = list(a[0])
        b_list = b[0:]
        integer_map = map(int, b_list)
        ncpu_tot_host = list(integer_map)
        tot_ncpu_vms = tabela_filtrada
        tot_ncpu_vms['nCPU_VM'] = tot_ncpu_vms['nCPU_VM'].astype(int)
        df_vm_soma = list(tot_ncpu_vms.groupby(['HOST'])['nCPU_VM'].transform('sum'))
        df_vm_conta = list(tabela_filtrada.groupby(['HOST'])['NOME_VM'].transform('count')-1)
        fig_cpu = go.Figure(data = [
            go.Bar(x = [tabela_filtrada['LABEL_POOL'],tabela_filtrada['HOST']], y = ncpu_tot_host,
                name = 'Total', marker_color = '#54A24B', text = ncpu_tot_host,
                textposition='inside',textfont_size=18,
                hovertemplate='Ambiente/Host Físico: %{x}'+'<br> Quantidade de CPUs: %{y:.0f}'
            ), 
            go.Bar(x = [tabela_filtrada['LABEL_POOL'],tabela_filtrada['HOST']], y = tabela_filtrada['nCPU_VM'],
                name = 'Provisionado', marker_color = '#0099C6', text = tabela_filtrada['NOME_VM'],
                textposition = 'inside',textfont_size=18,
                # customdata = Dados adicionais conforme filtro agrupado anteiormente
                customdata = np.stack([df_vm_conta, df_vm_soma], axis=-1),
                hovertemplate="<br>".join([
                    "Ambiente/Host Físico: %{x} <br> Nº de CPUs da VM: %{y:.0f}", \
                    "Nome da VM: %{text}", \
                    "Quantidade Total de VMs: %{customdata[0]}", \
                    "Quantidade Total de CPUs das VMs: %{customdata[1]:.0f}"
                ]),                
            ),
            ] 
        )      
        fig_cpu.update_layout(title = '<b>CPU</b>', barmode = 'group',
        legend = dict(traceorder = 'normal', x=1, y=1.02,
            yanchor="bottom", xanchor="right", orientation="h"),
            font = dict(family = "Courier", size = 16, color = "black"),
        ),
        font = dict(family="Courier New, monospace",size=16),
        fig_cpu.update_yaxes(title_text='Nº CPUs'),
    return fig_cpu
    # Fim para chamada do Gráfico de Barras para CPU ------------------

# Início para chamada do Gráfico de Pizza para Total Geral de Memória -
@app_ambiente_coids.callback(
    Output('grafico_filtro_memoria', 'figure',allow_duplicate=True),
    Input('ambiente_virtual','value'),
    prevent_initial_call = True,
)

def update_output_filtro_memoria(value):
    if value == "Ambientes Virtuais":
        tot_geral_mem_host = df_vm['MEMORIA_TOTAL_HOST'].sum()
        tot_geral_mem_livre_host = df_vm['MEMORIA_LIVRE_HOST'].sum()
        tot_geral_mem_usada = mem_usada_host_GB.sum()
        tot_geral_mem_vm = df_vm['MEMORIA_VM'].sum()
        dif_geral_host_vm = (tot_geral_mem_host - tot_geral_mem_livre_host) - tot_geral_mem_vm 
        und = 'GB'
        if tot_geral_mem_host < 1000:
            und = 'GB'
        if tot_geral_mem_host >= 1000:
            tot_geral_mem_host /= 1024
            tot_geral_mem_livre_host /= 1024
            tot_geral_mem_vm /= 1024
            dif_geral_host_vm /= 1024
            und = 'TB'

        values = [np.round(tot_geral_mem_livre_host,2), np.round(tot_geral_mem_vm,2),np.round(dif_geral_host_vm,2)]
        labels = ['Disponível', 'Provisionado','Gerenciamento']
        l_pool = df_vm["LABEL_POOL"],
        colors = ['#00CC96', '#0099C6','gray']
        fig_mem_geral = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=True,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_mem_geral.update_layout(
                    title_text = 'MEMÓRIA - ' + value, title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_mem_geral.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(tot_geral_mem_host,2),grouping=True,symbol=False) + und,
                            font = dict(size=30,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    else:
        tabela_filtrada = df_vm.loc[df_vm['LABEL_POOL'] == value, :]
        tot_geral_mem_host = tabela_filtrada['MEMORIA_TOTAL_HOST'].sum()
        tot_geral_mem_livre_host = tabela_filtrada['MEMORIA_LIVRE_HOST'].sum()
        tot_geral_mem_usada = mem_usada_host_GB.sum()
        tot_geral_mem_vm = tabela_filtrada['MEMORIA_VM'].sum()
        dif_geral_host_vm = (tot_geral_mem_host - tot_geral_mem_livre_host) - tot_geral_mem_vm 
        und = 'GB'
        if tot_geral_mem_host < 1000:
            und = 'GB'
        if tot_geral_mem_host >= 1000:
            tot_geral_mem_host /= 1024
            tot_geral_mem_livre_host /= 1024
            tot_geral_mem_vm /= 1024
            dif_geral_host_vm /= 1024
            und = 'TB'
        values = [np.round(tot_geral_mem_livre_host,2), np.round(tot_geral_mem_vm,2),np.round(dif_geral_host_vm,2)]
        labels = ['Disponível', 'Provisionado','Gerenciamento']
        l_pool = df_vm["LABEL_POOL"],
        colors = ['#00CC96', '#0099C6','gray']
        fig_mem_geral = go.Figure(data = go.Pie(values = values, 
                                    labels = labels, hole = 0.7, showlegend=True,
                                    textfont_size=15,
                                    marker_colors = colors))
        fig_mem_geral.update_layout(
                    title_text = 'MEMÓRIA - ' + value, title_x=0.5,title_y=0.90,
                    title_font = dict(size=15,family='Courier', 
                                        color='darkred'))
        fig_mem_geral.add_annotation(x= 0.5, y = 0.5,
                            text = locale.currency(np.round(tot_geral_mem_host,2),grouping=True,symbol=False) + und,
                            font = dict(size=30,family='Courier-bold', 
                                        color='#333333'),
                            showarrow = False)
    return fig_mem_geral
# Fim para chamada do Gráfico de Pizza para Total Geral de Memória ----

# Início da Tabela de Dados -------------------------------------------
@app_ambiente_coids.callback(Output('tabela-dados-ambientevirtual', 'children'),
    [Input('ambiente_virtual', 'value')])

@app_ambiente_coids.callback(Output('tabela-dados-ambientevirtual1', 'children'),
    [Input('ambiente_virtual', 'value')])

def update_table_ambientevirtual(value):
    if value == "Ambientes Virtuais":        
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Ambientes Virtuais', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': True} for i in df_filtro.columns
                    if i != 'id'
                ],
                data=df_filtro.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 20,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
    else:
        tabela_filtrada = df_filtro.loc[df_filtro['LABEL_POOL'] == value, :]      
        html.H2(children='', style={'textAlign': 'center', 'color': '#071d41'}),
        return [
            html.Br(),
            html.H4(children='Informações Detalhadas - Ambiente Virtual', style={'textAlign': 'center', 'color': '#071d41'}),
            html.Br(),
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': i, 'id': i,
                    'type':'numeric',
                    'format': Format(
                        scheme=Scheme.fixed, 
                        precision=2,
                        group=Group.yes,
                        groups=3,
                        group_delimiter='.',
                        decimal_delimiter=',',
                        symbol=Symbol.no), 
                    'deletable': False} for i in tabela_filtrada.columns
                    if i != 'id'
                ],
                data=tabela_filtrada.to_dict('records'),
                sort_action="native",
                sort_mode='multi',
                selected_rows=[],
                page_action='native',
                page_current= 0,
                page_size= 20,
                style_table={'overflowY':'auto', "responsive":True},          
                style_cell={'fontSize': '14px','text-align': 'justify', 'fontFamily': 'Courier'},
                style_header={
                    'backgroundColor': 'lavender',
                    'fontWeight': 'bold',
                    'text-align': 'center',
                    'fontSize': '14px', 
                },
            )
        ]
# Fim da Tabela de Dados ----------------------------------------------

###########################################
# Zabbix Inicio                           #
###########################################
    
@app_ambiente_coids.callback(
        Output('descricao_vms', 'children'),
        Input('uso_host','value'),
        prevent_initial_call = True,
)

def update_output_descricao(value):
        nome_host = value
        memoria,cpu,descricao=buscaInfoHostZabbix(nome_host,df_vm)
        return html.Span([html.B("Descrição: "), descricao.upper()])

# Início para chamada do Gráfico de CPU - uso do host--------------------------
@app_ambiente_coids.callback(
        Output('usohost_cpu', 'figure',allow_duplicate=True),
        Input('uso_host','value'),
        Input('periodo','value'),
        prevent_initial_call = True,
)

def update_output_usohost_cpu(value,value_1):
        recebe_frame = get_df_dados(value_1,api,hosts)
        df1_valores = recebe_frame['df1_valores']
        tabela_filtrada = df1_valores.loc[df1_valores['NOME_HOST'] == value, :]    
        nome_host = value
        ndias = value_1
        data_hora = tabela_filtrada['DATA_HORA']
        v_min = np.round(tabela_filtrada['VALOR_MINIMO'].astype(float),2)
        v_med = np.round(tabela_filtrada['VALOR_MEDIO'].astype(float),2)
        v_max = np.round(tabela_filtrada['VALOR_MAXIMO'].astype(float),2)
        fig_usocpu = go.Figure (data = [
            go.Scatter(x = data_hora, y = v_min,
                name = 'Mínimo', marker_color = '#54A24B', #verde 
                text = v_min, 
                hovertemplate='Data e hora: %{x}'+'<br> Utilização mínima %: %{y:.2f}'),
            go.Scatter(x = data_hora, y = v_med,
                name = 'Médio', marker_color = '#FFCC00', # '#0099C6', azul
                text = v_med, 
                hovertemplate='Data e hora: %{x}'+'<br> Utilização média %: %{y:.2f}'),
            go.Scatter(x = data_hora, y = v_max,
                name = 'Máximo', marker_color = '#FF6600' ,  # '#CC3333' vermelho; #FF6600 laranja
                text = v_max, 
                hovertemplate='Data e hora: %{x}'+'<br> Utilização máxima %: %{y:.2f}'),
        ])                       

        memoria,cpu,descricao=buscaInfoHostZabbix(nome_host,df_vm)
        fig_usocpu.update_layout(title = '<b>Processadores: </b>{}'.format(cpu),
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
                title_text = 'Host: ' + value,
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_usocpu.update_yaxes(title_text='%'),  
        fig_usocpu.update_traces(marker_line_color='gray', marker_line_width=0.1)
        return fig_usocpu

# Início para chamada do Gráfico de MEMÓRIA - uso do host--------------------------
@app_ambiente_coids.callback(
        Output('usohost_memoria', 'figure',allow_duplicate=True),
        Input('uso_host','value'),
        Input('periodo','value'),
        prevent_initial_call = True,
)

def update_output_usohost_memoria(value, value_1):
        recebe_frame = get_df_dados(value_1,api,hosts)
        df1_valores_memoria = recebe_frame['df1_valores_memoria']        
        tabela_filtrada = df1_valores_memoria.loc[df1_valores_memoria['NOME_HOST'] == value, :]    
        nome_host = value
        ndias = value_1
        data_hora = tabela_filtrada['DATA_HORA']
        v_min = np.round(tabela_filtrada['VALOR_MINIMO'].astype(float),2)
        v_med = np.round(tabela_filtrada['VALOR_MEDIO'].astype(float),2)
        v_max = np.round(tabela_filtrada['VALOR_MAXIMO'].astype(float),2)
        fig_usomemoria = go.Figure (data = [
            go.Scatter(x = data_hora, y = v_min,
                name = 'Mínimo', marker_color = '#54A24B', 
                text = v_min,
                hovertemplate='Data e hora: %{x}'+'<br> Utilização mínima %: %{y:.2f}'),
            go.Scatter(x = data_hora, y = v_med,
                name = 'Médio', marker_color = '#FFCC00', 
                text = v_med,
                hovertemplate='Data e hora: %{x}'+'<br> Utilização média %: %{y:.2f}'),                 
            go.Scatter(x = data_hora, y = v_max,
                name = 'Máximo', marker_color = '#CC3333', 
                text = v_max,
                hovertemplate='Data e hora: %{x}'+'<br> Utilização máxima %: %{y:.2f}'), 
        ])                                   

        memoria,cpu,descricao=buscaInfoHostZabbix(nome_host,df_vm)
        fig_usomemoria.update_layout(title = '<b>Memória: </b>{} GB'.format(memoria), 
            legend = dict(traceorder = 'normal', x=1, y=1.02, 
                font = dict(family = "Courier", size = 16, color = "black"),
                yanchor="bottom", xanchor="right", orientation="h",
                title_text = 'Host: ' + value, 
            ),
            font = dict(family = "Courier", size = 13, color = "black"),
        ),
        fig_usomemoria.update_yaxes(title_text='%'),  
        fig_usomemoria.update_traces(marker_line_color='gray', marker_line_width=0.1)
        return fig_usomemoria
###########################################
# Zabbix FIM                              #
###########################################

# Supercomputacao -- Inicio

@app_ambiente_coids.callback(
        Output('egeon', 'figure',allow_duplicate=True),
        Input('periodo_super','value'),
        prevent_initial_call = True,
)

def update_output_uso_egeon(value):
    cursor,conn = conecta_BD_Super()
    egeon = buscaDadosEgeon(cursor)
    conn.close()
    graficoEgeon = geraGrafico(egeon, 'Egeon', value)

    return graficoEgeon

@app_ambiente_coids.callback(
        Output('xc50', 'figure',allow_duplicate=True),
        Input('periodo_super','value'),
        prevent_initial_call = True,
)

def update_output_uso_xc50(value):
    cursor,conn = conecta_BD_Super()
    xc50 = buscaDadosXC50(cursor)
    conn.close()
    graficoXC50 = geraGrafico(xc50, 'XC50', value)

    return graficoXC50

# Supercomputacao -- Fim


# Início  da Chamada dos gráficos e Tabelas fullsize ------------------
# CHAMADAS MODAL MODAIS #
@app_ambiente_coids.callback(
    Output("modal1", "is_open"),
    [Input("open1", "n_clicks"), Input("close1", "n_clicks")],
    [State("modal1", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal2", "is_open"),
    [Input("open2", "n_clicks"), Input("close2", "n_clicks")],
    [State("modal2", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal3", "is_open"),
    [Input("open3", "n_clicks"), Input("close3", "n_clicks")],
    [State("modal3", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal4", "is_open"),
    [Input("open4", "n_clicks"), Input("close4", "n_clicks")],
    [State("modal4", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal5", "is_open"),
    [Input("open5", "n_clicks"), Input("close5", "n_clicks")],
    [State("modal5", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal6", "is_open"),
    [Input("open6", "n_clicks"), Input("close6", "n_clicks")],
    [State("modal6", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal7", "is_open"),
    [Input("open7", "n_clicks"), Input("close7", "n_clicks")],
    [State("modal7", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal8", "is_open"),
    [Input("open8", "n_clicks"), Input("close8", "n_clicks")],
    [State("modal8", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal9", "is_open"),
    [Input("open9", "n_clicks"), Input("close9", "n_clicks")],
    [State("modal9", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal10", "is_open"),
    [Input("open10", "n_clicks"), Input("close10", "n_clicks")],
    [State("modal10", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal11", "is_open"),
    [Input("open11", "n_clicks"), Input("close11", "n_clicks")],
    [State("modal11", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal12", "is_open"),
    [Input("open12", "n_clicks"), Input("close12", "n_clicks")],
    [State("modal12", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal13", "is_open"),
    [Input("open13", "n_clicks"), Input("close13", "n_clicks")],
    [State("modal13", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal14", "is_open"),
    [Input("open14", "n_clicks"), Input("close14", "n_clicks")],
    [State("modal14", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal15", "is_open"),
    [Input("open15", "n_clicks"), Input("close15", "n_clicks")],
    [State("modal15", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal16", "is_open"),
    [Input("open16", "n_clicks"), Input("close16", "n_clicks")],
    [State("modal16", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal17", "is_open"),
    [Input("open17", "n_clicks"), Input("close17", "n_clicks")],
    [State("modal17", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal18", "is_open"),
    [Input("open18", "n_clicks"), Input("close18", "n_clicks")],
    [State("modal18", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal19", "is_open"),
    [Input("open19", "n_clicks"), Input("close19", "n_clicks")],
    [State("modal19", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal20", "is_open"),
    [Input("open20", "n_clicks"), Input("close20", "n_clicks")],
    [State("modal20", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app_ambiente_coids.callback(
    Output("modal21", "is_open"),
    [Input("open21", "n_clicks"), Input("close21", "n_clicks")],
    [State("modal21", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open
# Fim da Chamada dos gráficos e Tabelas fullsize ----------------------

# Configuração final - servidor Web -----------------------------------
@server.route("/dashboard")
def my_dash_app():
    conecta_BD()
    # rows_ambiente=busca_Servidores(cursor)

    return app_ambiente_coids.index()

if __name__ == '__main__':
    # Production
    http_server = WSGIServer(('',5007),server)
    http_server.serve_forever()
