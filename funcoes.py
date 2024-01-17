from dash import dcc, html
from pyzabbix import ZabbixAPI
from datetime import datetime, timedelta
import plotly.graph_objs as go
import configparser
import time 
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

def connect_zabbix():
    config = configparser.ConfigParser()
    config.read("config.ini")
    user = config.get('zabbix', 'user')
    password = config.get('zabbix', 'password')
    server = config.get('zabbix', 'server')
    zapi = ZabbixAPI(server)
    zapi.session.verify = False
    zapi.login(user, password)
    
    return zapi

def get_hostgroup(hostgroup_name,api):
    hostgroup = api.hostgroup.get({"output": "extend", "filter": {"name": hostgroup_name}})
    return hostgroup

def get_HostsItems(api,hostgroup_id):
    hostgroups = api.hostgroup.get(output=['id'],filter={'name': 'MS3'},)
    hosts = api.host.get({"output": ['name', 'status'],"groupids": hostgroup_id,"filter": {"status": 0}})
    items = api.item.get(output=['name','lastvalue','hostid',], groupids=hostgroups[0]['groupid'],)
    return hostgroups, hosts, items

def get_df_dados(ndias,api,hosts):
    minutos_dia = 1440

    # Define valor default de busca de 15 dias caso nao seja definido outro valor
    if ndias is None or ndias == '15':
        numero_dias = 15
    else:
        numero_dias = ndias

    fromTimestamp = int(time.mktime(datetime.now().timetuple()))
    tillTimestamp = int(fromTimestamp - (minutos_dia * numero_dias) * 60 * 1)  # dias

    itemFilter = {'name': 'CPU utilization'}  
    itemFilter_2 = {'name': 'Memory utilization'} 

    df_valores = []
    cols = ['NOME_HOST', 'ITEM_ID', 'CLOCK', 'DATA_HORA', 'VALOR_MINIMO', 'VALOR_MEDIO',\
            'VALOR_MAXIMO']
    for host in (hosts):
        items = api.item.get(
            output=[
                'name',
                'lastvalue',
                'hostid',
            ],
            filter=itemFilter, host=host['host'], selectHosts=['host', 'name'],
        )

        for item in items:
            # Busca os valores dos itens. Poderia usar o comando 'history'
            # porém foi usado o trend para conseguir maior período de dados.
            values = api.trend.get(itemids=item['itemid'],time_from=tillTimestamp, time_till=fromTimestamp)   # funcionou

            for historyValue in values:
                # Formata a saída e armazena os valores em variável.
                host_hist = host['name']
                itemid_hist  = historyValue['itemid']
                clock_hist = historyValue['clock']
                data_hora = datetime.fromtimestamp(int(clock_hist)).strftime('%d-%m-%Y %H:%M:%S')
                value_min_hist = historyValue['value_min']
                value_avg_hist = historyValue['value_avg']
                value_max_hist = historyValue['value_max']
                df_valores.append([host_hist, itemid_hist, clock_hist, data_hora, value_min_hist, value_avg_hist, value_max_hist])

    # df1 contém os valores de dados de CPU
    df1_valores = pd.DataFrame(df_valores,columns=cols) 
    #------------------------------------------------- Final Items de CPU 

    #------------------------------------------------- Items de MEMÓRIA 
    # Utiliza o mesmo conceito usado na rotina de cpu 
    df_valores_memoria = []
    cols = ['NOME_HOST', 'ITEM_ID', 'CLOCK', 'DATA_HORA', 'VALOR_MINIMO', 'VALOR_MEDIO',\
            'VALOR_MAXIMO']
    for host in (hosts):
        items = api.item.get(
            output=[
                'name',
                'lastvalue',
                'hostid',
            ],
            filter=itemFilter_2, host=host['host'], selectHosts=['host', 'name'],
        )

        for item in items:
            # Busca os valores dos itens. Poderia usar o comando 'history'
            # porém foi usado o trend para conseguir maior período de dados.
            values = api.trend.get(itemids=item['itemid'],time_from=tillTimestamp, time_till=fromTimestamp)   # funcionou

            for historyValue in values:
                # Formata a saída e armazena os valores em variável.                
                host_hist = host['name']
                itemid_hist  = historyValue['itemid']
                clock_hist = historyValue['clock']
                data_hora = datetime.fromtimestamp(int(clock_hist)).strftime('%d-%m-%Y %H:%M:%S')
                value_min_hist = historyValue['value_min']
                value_avg_hist = historyValue['value_avg']
                value_max_hist = historyValue['value_max']
                df_valores_memoria.append([host_hist, itemid_hist, clock_hist, data_hora, value_min_hist, value_avg_hist, value_max_hist])

    df1_valores_memoria = pd.DataFrame(df_valores_memoria,columns=cols) 
    
    # Retorna um 'df' para cpu e outro para memória
    return {'df1_valores':df1_valores, 'df1_valores_memoria':df1_valores_memoria}

def buscaInfoHostZabbix(host,df_vm):
    host = host.split('.')
    basenamehost=host[0]
    #TEMPORARIO PARA TESTE#
    basenamehost='equinocio'
    # REMOVER LINHA ACIMA #
    selecao = df_vm['NOME_VM']==basenamehost
    memoria_total_vm = pd.to_numeric(df_vm[selecao]['MEMORIA_VM'], errors='coerce').tolist()
    cpu_total_vm = pd.to_numeric(df_vm[selecao]['nCPU_VM'], errors='coerce').tolist()    
    descricao_vm = df_vm.loc[selecao, 'DESCR_VM']

    return memoria_total_vm[0], cpu_total_vm[0], descricao_vm[0]

def get_Menu():
    layout=dbc.Container([
        dbc.Row([
            html.H4(children='RECURSOS COMPUTACIONAIS COIDS E SESUP', style={'margin-bottom':'10px','margin-top':'10px', 'textAlign': 'center', 'color': 'white', 'background':'darkblue'}),
            html.Div(children='Gráficos e Tabelas do Ambiente Virtual, de Volumes por Unidade Organizacional e Aggregates.', style={'textAlign': 'center', 'paddingTop': "1px", 'paddingBottom': "20px", 'color': 'white', 'background':'darkblue'}),
        ],style={'color': 'white', 'background':'darkblue'}),
        html.Br(),    
        # TABs #
        dbc.Row([        
            dcc.Tabs(id='tabs', value='', children=[
                dcc.Tab(label='Sistema de Processamento', value='tab-sp', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}, children=[
                    dcc.Tabs(id='subtabs', value='', children=[
                        dcc.Tab(label='Servidores', value='tab-1', className='card-text', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                        dcc.Tab(label='Uso do Host', value='tab-2', className='card-text', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                        dcc.Tab(label='Supercomputação', value='tab-3', className='card-text', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                    ], style={'width': '100%','fontWeight': '12px'})
                ]),

                dcc.Tab(label='Sistema de Armazenamento', value='tab-sa', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}, children=[
                    dcc.Tabs(id='subtabs1', value='', children=[
                        dcc.Tab(label='Geral', value='tab-4', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                        dcc.Tab(label='Aggregates', value='tab-5', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                        dcc.Tab(label='Volumes', value='tab-6', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                        dcc.Tab(label='Monitor-GT', value='tab-7', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                        dcc.Tab(label='Grupos', value='tab-8', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                    ], style={'width': '100%','fontWeight': '12px'})
                ]),

                dcc.Tab(label='OPEX', value='tab-9', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),
                dcc.Tab(label='Monitor de Custos', value='tab-10', className='custom-tab', selected_className='custom-tab--selected', style={'borderRadius': '10px'}),

            ], style={'width': '100%','fontWeight': 'bold'}),
            html.Div(id='tabs-content')
        ])
    ], fluid=True)  
    
    return layout

def define_ValoresVolumesLandsat(df_volume_landsat, fator_convert):
    df_volume_landsat['VOLUME_TOTAL'] = df_volume_landsat['VOLUME_TOTAL'].astype(float)
    df_volume_landsat['VOLUME_TOTAL'] = np.round(df_volume_landsat['VOLUME_TOTAL'] / fator_convert,3)
    soma_volume_total_landsat = df_volume_landsat['VOLUME_TOTAL'].sum()
    soma_volume_total_landsat = np.round(soma_volume_total_landsat,2)

    # Volume Usado LANDSAT
    df_volume_landsat['VOLUME_USADO'] = df_volume_landsat['VOLUME_USADO'].astype(float)
    df_volume_landsat['VOLUME_USADO'] = np.round(df_volume_landsat['VOLUME_USADO'] / fator_convert,3)
    soma_volume_usado_landsat = df_volume_landsat['VOLUME_USADO'].sum()
    soma_volume_usado_landsat = np.round(soma_volume_usado_landsat,2)

    # Volume Disponível LANDSAT
    df_volume_landsat['VOLUME_DISPONIVEL'] = df_volume_landsat['VOLUME_DISPONIVEL'].astype(float)
    df_volume_landsat['VOLUME_DISPONIVEL'] = np.round(df_volume_landsat['VOLUME_DISPONIVEL'] / fator_convert,3)
    soma_volume_disponivel_landsat = df_volume_landsat['VOLUME_DISPONIVEL'].sum()
    soma_volume_disponivel_landsat = np.round(soma_volume_disponivel_landsat,2)

    #-------------------------------------- Em GB
    # Volume Snap Total LANDSAT
    df_volume_landsat['VOLUME_SNAP_TOTAL'] = df_volume_landsat['VOLUME_SNAP_TOTAL'].astype(float)
    df_volume_landsat['VOLUME_SNAP_TOTAL'] = np.round(df_volume_landsat['VOLUME_SNAP_TOTAL'] / fator_convert,3)
    soma_snap_total_landsat = df_volume_landsat['VOLUME_SNAP_TOTAL'].sum()

    # Volume Snap Usado LANDSAT
    df_volume_landsat['VOLUME_SNAP_USADO'] = df_volume_landsat['VOLUME_SNAP_USADO'].astype(float)
    df_volume_landsat['VOLUME_SNAP_USADO'] = np.round(df_volume_landsat['VOLUME_SNAP_USADO'] / fator_convert,3)
    soma_snap_usado_landsat = df_volume_landsat['VOLUME_SNAP_USADO'].sum()

    # Volume Snap Disponível LANDSAT
    df_volume_landsat['VOLUME_SNAP_DISPONIVEL'] = df_volume_landsat['VOLUME_SNAP_DISPONIVEL'].astype(float)
    df_volume_landsat['VOLUME_SNAP_DISPONIVEL'] = np.round(df_volume_landsat['VOLUME_SNAP_DISPONIVEL'] / fator_convert,3)
    soma_snap_disponivel_landsat = df_volume_landsat['VOLUME_SNAP_DISPONIVEL'].sum()
    # V O L U M E -> Converte de KB para TB  (Fim)
    # FINAL DA LEITURA DA TABELA 'VOLUMES' COM FILTRO 'controller_volumes = Landsat'
    
    return soma_volume_total_landsat,soma_volume_usado_landsat,soma_volume_disponivel_landsat,soma_snap_total_landsat,soma_snap_usado_landsat,soma_snap_disponivel_landsat

def define_ValoresMemoria(df_vm,fator_convert):
    # Converte KB para GB --------------------------------------------------
    df_vm['MEMORIA_TOTAL_HOST'] = df_vm['MEMORIA_TOTAL_HOST'].astype(float)
    df_vm['MEMORIA_TOTAL_HOST'] = np.round(df_vm['MEMORIA_TOTAL_HOST'] / fator_convert,2)
    mem_tot_host_GB = df_vm['MEMORIA_TOTAL_HOST']

    df_vm['MEMORIA_LIVRE_HOST'] = df_vm['MEMORIA_LIVRE_HOST'].astype(float)
    df_vm['MEMORIA_LIVRE_HOST'] = np.round(df_vm['MEMORIA_LIVRE_HOST'] / fator_convert,2)
    mem_livre_host_GB = df_vm['MEMORIA_LIVRE_HOST']

    df_vm['MEMORIA_VM'] = df_vm['MEMORIA_VM'].astype(float)
    df_vm['MEMORIA_VM'] = np.round(df_vm['MEMORIA_VM'] / fator_convert,2)
    mem_vm_GB = df_vm['MEMORIA_VM']

    # Calcula memória usada (host - livre) com base apenas no host ---------
    mem_usada_host_GB = df_vm['MEMORIA_TOTAL_HOST'] - df_vm['MEMORIA_LIVRE_HOST']
    mem_usada_host_GB = np.round(mem_usada_host_GB)

    return mem_tot_host_GB,mem_livre_host_GB,mem_vm_GB,mem_usada_host_GB

def define_ValoresVolumesOlinda(df_volume, fator_convert):
    df_volume['VOLUME_TOTAL'] = df_volume['VOLUME_TOTAL'].astype(float)
    df_volume['VOLUME_TOTAL'] = np.round(df_volume['VOLUME_TOTAL'] / fator_convert,3)
    soma_volume_total = df_volume['VOLUME_TOTAL'].sum()
    #soma_volume_total /= 1024  #(Convertido para TB)
    soma_volume_total = np.round(soma_volume_total,2)

    # Volume Usado
    df_volume['VOLUME_USADO'] = df_volume['VOLUME_USADO'].astype(float)
    df_volume['VOLUME_USADO'] = np.round(df_volume['VOLUME_USADO'] / fator_convert,3)
    soma_volume_usado = df_volume['VOLUME_USADO'].sum()
    #soma_volume_usado /= 1024  #(Convertido para TB)
    soma_volume_usado = np.round(soma_volume_usado,2)

    # Volume Disponível
    df_volume['VOLUME_DISPONIVEL'] = df_volume['VOLUME_DISPONIVEL'].astype(float)
    df_volume['VOLUME_DISPONIVEL'] = np.round(df_volume['VOLUME_DISPONIVEL'] / fator_convert,3)
    soma_volume_disponivel = df_volume['VOLUME_DISPONIVEL'].sum()
    #soma_volume_disponivel /= 1024  #(Convertido para TB)
    soma_volume_disponivel = np.round(soma_volume_disponivel,2)

    # Em GB
    # Volume Snap Total
    df_volume['VOLUME_SNAP_TOTAL'] = df_volume['VOLUME_SNAP_TOTAL'].astype(float)
    df_volume['VOLUME_SNAP_TOTAL'] = np.round(df_volume['VOLUME_SNAP_TOTAL'] / fator_convert,3)
    soma_snap_total = df_volume['VOLUME_SNAP_TOTAL'].sum()

    # Volume Snap Usado
    df_volume['VOLUME_SNAP_USADO'] = df_volume['VOLUME_SNAP_USADO'].astype(float)
    df_volume['VOLUME_SNAP_USADO'] = np.round(df_volume['VOLUME_SNAP_USADO'] / fator_convert,3)
    soma_snap_usado = df_volume['VOLUME_SNAP_USADO'].sum()

    # Volume Snap Disponível
    df_volume['VOLUME_SNAP_DISPONIVEL'] = df_volume['VOLUME_SNAP_DISPONIVEL'].astype(float)
    df_volume['VOLUME_SNAP_DISPONIVEL'] = np.round(df_volume['VOLUME_SNAP_DISPONIVEL'] / fator_convert,3)
    soma_snap_disponivel = df_volume['VOLUME_SNAP_DISPONIVEL'].sum()
    # (Fim) V O L U M E -> Converte de KB para TB

    return soma_volume_total,soma_volume_usado,soma_volume_disponivel,soma_snap_total,soma_snap_usado,soma_snap_disponivel

def define_ValoresAggregatesOlinda(df_aggr,fator_convert):
    # (Início) A G G R E G A T E -> Converte de KB para TB
    # Aggregate Total
    df_aggr['AGGR_TOTAL'] = df_aggr['AGGR_TOTAL'].astype(float)
    df_aggr['AGGR_TOTAL'] = np.round(df_aggr['AGGR_TOTAL'] / fator_convert,3)
    soma_aggr_total = df_aggr['AGGR_TOTAL'].sum()
    soma_aggr_total = np.round(soma_aggr_total,2)
    #soma_aggr_total /= 1024  #(Convertido para TB)

    # Aggregate Usado
    df_aggr['AGGR_USADO'] = df_aggr['AGGR_USADO'].astype(float)
    df_aggr['AGGR_USADO'] = np.round(df_aggr['AGGR_USADO'] / fator_convert,3)
    soma_aggr_usado = df_aggr['AGGR_USADO'].sum()
    soma_aggr_usado = np.round(soma_aggr_usado,2)
    #soma_aggr_usado /= 1024   #(Convertido para TB)

    # Aggregate Disponível
    df_aggr['AGGR_DISPONIVEL'] = df_aggr['AGGR_DISPONIVEL'].astype(float)
    df_aggr['AGGR_DISPONIVEL'] = np.round(df_aggr['AGGR_DISPONIVEL'] / fator_convert,3)
    soma_aggr_disponivel = df_aggr['AGGR_DISPONIVEL'].sum()
    soma_aggr_disponivel = np.round(soma_aggr_disponivel,2)
    #soma_aggr_disponivel /= 1024   #(Convertido para TB)
    # (Fim) A G G R E G A T E -> Converte de KB para TB

    return soma_aggr_total,soma_aggr_usado,soma_aggr_disponivel

def define_ValoresAggregatesLandsat(df_aggr_landsat,fator_convert):
    df_aggr_landsat['AGGR_TOTAL'] = df_aggr_landsat['AGGR_TOTAL'].astype(float)
    df_aggr_landsat['AGGR_TOTAL'] = np.round(df_aggr_landsat['AGGR_TOTAL'] / fator_convert,3)
    soma_aggr_total_landsat = df_aggr_landsat['AGGR_TOTAL'].sum()
    soma_aggr_total_landsat = np.round(soma_aggr_total_landsat,2)
    #soma_aggr_total_landsat /= 1024  #(Convertido para TB)

    # Aggregate Usado
    df_aggr_landsat['AGGR_USADO'] = df_aggr_landsat['AGGR_USADO'].astype(float)
    df_aggr_landsat['AGGR_USADO'] = np.round(df_aggr_landsat['AGGR_USADO'] / fator_convert,3)
    soma_aggr_usado_landsat = df_aggr_landsat['AGGR_USADO'].sum()
    soma_aggr_usado_landsat = np.round(soma_aggr_usado_landsat,2)
    #soma_aggr_usado_landsat /= 1024   #(Convertido para TB)

    # Aggregate Disponível
    df_aggr_landsat['AGGR_DISPONIVEL'] = df_aggr_landsat['AGGR_DISPONIVEL'].astype(float)
    df_aggr_landsat['AGGR_DISPONIVEL'] = np.round(df_aggr_landsat['AGGR_DISPONIVEL'] / fator_convert,3)
    soma_aggr_disponivel_landsat = df_aggr_landsat['AGGR_DISPONIVEL'].sum()
    soma_aggr_disponivel_landsat = np.round(soma_aggr_disponivel_landsat,2)
    #soma_aggr_disponivel_landsat /= 1024   #(Convertido para TB)
    # (Início) AGGREGATE L A N D S A T    L A N D S A T -> Converte de KB para TB

    return soma_aggr_total_landsat,soma_aggr_usado_landsat,soma_aggr_disponivel_landsat

def monta_DataframeVM(rows_ambiente):
    df_ambiente = pd.DataFrame( [[ij for ij in i] for i in rows_ambiente] )
    df_ambiente.rename(columns={0: 'UUID_POOL', 1: 'LABEL_POOL', 2: 'DESCR_POOL',\
                                3: 'MASTER_POOL', 4: 'DEFAULT_SR', 5: 'HOST', \
                                6: 'UUID_HOST', 7: 'MODELO_HOST', 8: 'nCPU_HOST',\
                                9: 'MEMORIA_TOTAL_HOST', 10: 'MEMORIA_LIVRE_HOST',\
                                11: 'NOME_VM', 12: 'UUID_VM', 13: 'DESCR_VM', \
                                14: 'SISTEMA_OPERACIONAL_VM', 15: 'nCPU_VM', \
                                16: 'MEMORIA_VM', 17: 'HOST_RESIDENTE_ON', \
                                18: 'POWER_STATUS'}, inplace=True);
    return df_ambiente

def monta_DataframeLandsat(rows):
    df = pd.DataFrame( [[ij for ij in i] for i in rows] )
    df.rename(columns={0: 'ID_VOLUME', 1: 'VOLUME', 2: 'VOLUME_TOTAL', \
                    3: 'VOLUME_USADO', 4:'VOLUME_DISPONIVEL', 5:'PORCENTAGEM',\
                    6: 'VOLUME_SVM', 7: 'DEPARTAMENTO', 8: 'VOLUME_GRUPO', \
                    9: 'VOLUME_SNAP_TOTAL', 10: 'VOLUME_SNAP_USADO', \
                    11: 'VOLUME_SNAP_DISPONIVEL',12:'VOLUME_SNAP_PORCENTAGEM',\
                    13: 'VOLUME_AGGREGATE',14:'CONTROLLER_VOLUMES'}, \
                    inplace=True),
    df_volume_landsat = df
    return df_volume_landsat

def monta_DataframeOlinda(rows):
    df = pd.DataFrame( [[ij for ij in i] for i in rows] )
    df.rename(columns={0: 'ID_VOLUME', 1: 'VOLUME', 2: 'VOLUME_TOTAL', \
                    3: 'VOLUME_USADO', 4:'VOLUME_DISPONIVEL', 5:'PORCENTAGEM',\
                    6: 'VOLUME_SVM', 7: 'DEPARTAMENTO', 8: 'VOLUME_GRUPO',\
                    9: 'VOLUME_SNAP_TOTAL', 10: 'VOLUME_SNAP_USADO', \
                    11: 'VOLUME_SNAP_DISPONIVEL',12:'VOLUME_SNAP_PORCENTAGEM',\
                    13: 'VOLUME_AGGREGATE',14:'CONTROLLER_VOLUMES'},\
                    inplace=True),
    df_volume = df
    return df_volume

def monta_DataframeAggregateOlinda(rows_aggr):
    df_aggr = pd.DataFrame( [[ij for ij in i] for i in rows_aggr] )
    df_aggr.rename(columns={0: 'ID_AGGR', 1: 'AGGR', 2: 'AGGR_TOTAL', 3: 'AGGR_USADO', \
                        4: 'AGGR_DISPONIVEL', 5: 'CAPACIDADE_AGGR', 6: 'NOME_AGGR',\
                        }, inplace=True),
    return df_aggr

def monta_DataframeAggregateLandsat(rows_aggr_landsat):
    df_aggr_landsat = pd.DataFrame( [[ij for ij in i] for i in rows_aggr_landsat] )
    df_aggr_landsat.rename(columns={0: 'ID_AGGR', 1: 'AGGR', 2: 'AGGR_TOTAL', 3: 'AGGR_USADO', \
                    4: 'AGGR_DISPONIVEL', 5: 'CAPACIDADE_AGGR', 6: 'NOME_AGGR',\
                    }, inplace=True),
    return df_aggr_landsat

def monta_DataframeContratos(rows_contrato):
    df_contrato = pd.DataFrame( [[ij for ij in i] for i in rows_contrato] )
    df_contrato.rename(columns={0: 'name_contrato', 1: 'value_contrato', 2: 'currency_contrato',\
                    3: 'initData_contrato', 4: 'endDate_contrato', 5: 'status_contrato'}, inplace=True),
    return df_contrato

def monta_DataframeMaqFisicas(rows_maqfisica):
    df_maqfisica = pd.DataFrame( [[ij for ij in i] for i in rows_maqfisica])
    df_maqfisica.rename(columns={0: 'RACK', 1: 'NOME', 2: 'MARCA', 3: 'MODELO', \
                    4: 'DEPARTAMENTO', 5: 'SERVICO', 6: 'GARANTIA',\
                    7: 'DATA_GARANTIA', 8: 'PATRIMONIO', 9: 'HOLDER',\
                    10: 'PROCESSADOR', 11: 'POTENCIA', 12: 'CUSTO_DIARIO',\
                    13: 'CUSTO_MENSAL', 14: 'CUSTO_ANUAL',15: 'DATA_COMPRA',\
                    16: 'VALOR_COMPRA'}, inplace=True),
    return df_maqfisica

def monta_DataframeDiscos(rows_disk):
    df_disk = pd.DataFrame( [[ij for ij in i] for i in rows_disk] )
    df_disk.rename(columns={0: 'ID_DISK', 1: 'SIZE', 2: 'UNIDADE', 3: 'FORMATO', \
                        4: 'TIPO_AGGR', 5: 'NOME_AGGR', 6: 'NODE_DISK',\
                        }, inplace=True),

    # Converte o que está em GB para TB para padronizar o cálculo
    df_disk.loc[df_disk['UNIDADE'] == "GB", 'SIZE'] = df_disk['SIZE'].astype(float)/1024
    df_disk.loc[df_disk['UNIDADE'] == "GB", 'UNIDADE'] = "TB"
    return df_disk

def geraGrafico(dados, titulo, dias):
    
    # Converter os dados recebidos em timestamps
    timestamps = [datetime.fromtimestamp(int(data[0])) for data in dados]
    values = [int(data[1]) for data in dados]

    # Determinar a data inicial baseada no número de dias
    data_inicial = datetime.now() - timedelta(days=dias)

    # Filtrar os dados para manter apenas os últimos 'dias' dias
    timestamps_filtrados = []
    values_filtrados = []
    hover = [] 

    for i, timestamp in enumerate(timestamps):
        if timestamp >= data_inicial:
            timestamps_filtrados.append(timestamps[i])
            values_filtrados.append(values[i])
            hover.append(f'Data: {timestamps[i]}<br>Nodes: {values[i]}')

    trace = go.Scatter(
        x=timestamps_filtrados,
        y=values_filtrados,
        mode='lines',
        line=dict(color='green'),   
        hovertemplate='%{text}',     
        name=''
    )
    trace.text = hover
    
    data = [trace]

    layout = go.Layout(
        title=f'{titulo} - Gráfico Temporal dos últimos {dias} dias',
        xaxis=dict(title='Data / Hora'),
        yaxis=dict(title='Nodes'),        
        hovermode='closest',
    )

    fig = go.Figure(data=data, layout=layout)
    return fig
