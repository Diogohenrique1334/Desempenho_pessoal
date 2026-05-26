import pandas as pd


def df_para_lista_dict(df_filtrado,categoria = 'categoria', somatorio = 'amount', controle = "name",_agg = 'sum'):

    """Transforma de em um uma lista de categoria:valores para alimentar graficos do e_chart"""

    dados = df_filtrado.groupby(categoria)[somatorio].agg(_agg).sort_values(ascending = False).reset_index()

    return [{"value": y, controle: x} for x,y in dados.values]

def df_para_lista(df_filtrado, categoria = 'categoria', somatorio = 'amount'):

    """Transforma df em um uma lista de categoria:soma_valores,contagem_valores para alimentar graficos do e_chart"""

    dados = df_filtrado.groupby(categoria)[somatorio].agg(['sum','count']).reset_index().rename(columns = {categoria:'product','sum':'amount','count':'score'})[['score','amount','product']]

    mylist = dados.values.tolist()

    mylist.sort(key=lambda x: x[1])

    mylist.reverse()

    mylist.append(list(dados))

    mylist.reverse()

    return mylist

def Serie_simples(df_filtrado, col_data, col_values,_agg):

    """Transforma df em um uma série temporal simples alimentar graficos calendário do e_chart"""

    serie_gastos = df_filtrado.pivot_table(index=col_data,
                        values = col_values,
                        aggfunc = _agg)
    
    return serie_gastos.reset_index().rename(columns = {"date":'Data', 'amount':'value'})

def serei_dia_semana(df,col_data,valores,colunas,_agg):

    """Transforma df em 3 listas eixo com dia da semana, categorias, valores de série, para alimentar graficos do e_chart"""

    serie_gastos = df.pivot_table(index=colunas,
                        values = valores,
                        columns = df[col_data].dt.dayofweek,
                        aggfunc = _agg)
    
    eixo = [ x for x in serie_gastos.columns.map({0:'Domingo',1:'Segunda',2:'Terça',3:'Quarta',4:'Quinta',5:'Sexta',6:'Sábado',7:'Domingo'})]

    categorias = [ x for x in serie_gastos.index]

    valores_series = serie_gastos.values.tolist()
    
    return valores_series, categorias, eixo

def serei_dia_semana_options(df,col_data,valores,colunas,agg):

    """Transforma df em 3 listas eixo com dia da semana, categorias, valores de série, para alimentar graficos do e_chart"""

    def config_data(lista_valores,categorias):

        add_dic = list()
        for x in range(len(lista_valores)):
            
            add_dic.append( {
            "name": categorias[x],
            "type": "bar",
            "stack": "total",
            "label": {"show": False},
            "emphasis": {"focus": "series"},
            "data": [ round(float(l), 2) for l in lista_valores[x] ],
            })

        return add_dic

    serie_gastos = df.pivot_table(index=colunas,
                        values = valores,
                        columns = df[col_data].dt.dayofweek,
                        aggfunc = agg)
    
    eixo = [ x for x in serie_gastos.columns.map({6:'Domingo',0:'Segunda',1:'Terça',2:'Quarta',3:'Quinta',4:'Sexta',5:'Sábado'})]
    #eixo = [ x for x in serie_gastos.columns]

    categorias = [ x for x in serie_gastos.index]

    valores_series = serie_gastos.values.tolist()

    return config_data(valores_series,categorias), categorias, eixo

def serei_semana_mes_options(df, col_data, valores, colunas, agg):

    """Transforma df em 3 listas eixo com semana do mê, categorias, valores de série, para alimentar graficos do e_chart"""

    def config_data(lista_valores, categorias):
        add_dic = []
        for x in range(len(lista_valores)):
            add_dic.append({
                "name": categorias[x],
                "type": "bar",
                "stack": "total",
                "label": {"show": False},
                "emphasis": {"focus": "series"},
                "data": [round(float(l), 2) for l in lista_valores[x]],
            })
        return add_dic

    # Calcula a semana do mês (1ª semana, 2ª semana, etc.)
    semanas_mes = ((df[col_data].dt.day - 1) // 7) + 1

    serie_gastos = df.pivot_table(
        index=colunas,
        values=valores,
        columns=semanas_mes,
        aggfunc=agg
    )

    # Nomeando os eixos como "Semana 1", "Semana 2", etc.
    eixo = [f"Semana {x}" for x in serie_gastos.columns]

    categorias = [x for x in serie_gastos.index]
    valores_series = serie_gastos.values.tolist()

    return config_data(valores_series, categorias), categorias, eixo

def serei_mes_ano_options(df,col_data,valores,colunas,agg):

    """Transforma df em 3 listas eixo com dia da semana, categorias, valores de série, para alimentar graficos do e_chart"""

    def config_data(lista_valores,categorias):

        add_dic = list()
        for x in range(len(lista_valores)):
            
            add_dic.append( {
            "name": categorias[x],
            "type": "bar",
            "stack": "total",
            "label": {"show": False},
            "emphasis": {"focus": "series"},
            "data": [ round(float(l), 2) for l in lista_valores[x] ],
            })

        return add_dic

    serie_gastos = df.pivot_table(index=colunas,
                        values = valores,
                        columns = df[col_data].dt.strftime('%Y%m'),
                        aggfunc = agg)
    
    eixo = [ x for x in serie_gastos.columns ]

    categorias = [ x for x in serie_gastos.index]

    valores_series = serie_gastos.values.tolist()

    return config_data(valores_series,categorias), categorias, eixo

def dias_sem_gastos(df_filtrado):

    dias_mês =  pd.DataFrame({"mês":df_filtrado.date.dt.strftime('%Y%m'),"Dias do mês":df_filtrado.date.dt.daysinmonth}).drop_duplicates().set_index('mês').to_dict()['Dias do mês']

    dias_com_gastos = df_filtrado.pivot_table(index = df_filtrado.date.dt.strftime('%Y%m'),
                        values = 'date',
                        aggfunc = lambda x: len(x.unique())).rename(columns = {"date":"dias com gastos"}).reset_index()
    
    dias_com_gastos['Dias do mês'] = dias_com_gastos.date.map(dias_mês)

    dias_com_gastos['dias_sem_gastar'] = dias_com_gastos['Dias do mês'] - dias_com_gastos['dias com gastos']

    gastos_utilizacoes = df_filtrado.groupby(df_filtrado.date.dt.strftime('%Y%m'))['amount'].agg(['sum','count'])

    return dias_com_gastos.merge(gastos_utilizacoes, left_on = 'date', right_index = True, how = 'left')

def top_10_categorias(df_filtrado):

    categorias = [ x for x in df_filtrado.groupby('categoria')['amount'].sum().sort_values(ascending = False).reset_index().categoria ] 

    op = dict()

    for a in categorias:

        t = df_filtrado[df_filtrado.categoria == a].pivot_table(index = 'descricao',
                                                                values = 'amount',
                                                                aggfunc = 'sum').sort_values(by = 'amount', ascending = False).head(15).reset_index()
        
        t = t.values.tolist()

        op.update({a:t})

    return op,categorias,df_para_lista_dict(df_filtrado,controle='groupId')

def get_delta(curr, prev, is_pct=False):

    """Retorna o percentual de variação entre dois períodos"""

    if prev is None or prev == 0:
        return None
    if is_pct:
        return f"{curr - prev:+.1f}%"
    return f"{(curr - prev) / prev * 100:+.1f}%"

def dados_grafico_cachoeira(df_filtrado,col_data, valores):

    """Transforma df em 4 listas categoria, valores acumulados, aumento do acumulado, queda do acumulado para alimentar graficos do e_chart"""

    gastos_mes = df_filtrado.groupby(df_filtrado[col_data].dt.strftime('%Y%m'))[valores].sum()

    aumento = [ '-' if x < 0 else int(x) for x in gastos_mes.diff().fillna(gastos_mes[0]) ]

    queda = [ '-' if x < 0 else int(x) for x in (gastos_mes.diff() * -1).fillna(-1) ]

    valores = [int(x) for x in gastos_mes.values ]

    categorias = [ x for x in gastos_mes.index ]

    return categorias, valores, aumento, queda

def dados_grafico_barras(df, agregardor,valores, _agg = 'sum', ordenacao = True):


    t = df.pivot_table(index = agregardor,
                        values = valores,
                         aggfunc = _agg )
    
    if ordenacao:
    
        t = t.sort_values(by = valores, ascending = False)
    
    categorias = [ x for x in t.index ]

    _valores = [ x for x in t[valores] ]

    return categorias,_valores

def De_df_para_options(df, categoria, values, _agg = "sum"):

    dft = df.pivot_table(index = categoria,
                                    values = values,
                                    aggfunc = _agg).reset_index()
    series = []
    legend_data = []

    # percorre cada linha do DataFrame
    for i, row in dft.iterrows():
        nome = row[categoria]
        valor = row[values]
        legend_data.append(nome)

        series.append({
            "name": nome,
            "type": "liquidFill",
            "data": [valor],
            "center": [f"{25 + i*25}%", "50%"],  # distribui os círculos
            "radius": "30%",
            "label": {
                "normal": {
                    "formatter": f"{nome}\n{{c}}%",
                    "textStyle": {"fontSize": 16, "color": "#ffffff"}
                }
            },
            "color": ["#18990b", "#1e90ff", "#ff4500"][i % 3]  # alterna cores
        })

    return series
