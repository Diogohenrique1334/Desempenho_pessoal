import pandas as pd
import numpy as np
import datetime as dt

def options_lista_categorica_simples(
    df_filtrado: pd.DataFrame,
    categoria: str = 'categoria', 
    somatorio: str = 'amount', 
    controle:str = "name", 
    _agg:str = 'sum') -> list: 

    """Agrupa dataframe e retorna uma lista com valores e categoria"""

    dados = df_filtrado.groupby(categoria)[somatorio].agg(_agg).sort_values(ascending = False).reset_index()

    return [{"value": y, controle: x} for x,y in dados.values]

def options_lista_categorica_sum_count(
    df_filtrado: pd.DataFrame, 
    categoria:str = 'categoria', 
    somatorio:int = 'amount', 
    _agg: list = ['sum','count']) -> list:

    """Agrupa os dados com categoria, retornando a soma dos valores e a quantidade da categoria. Retornando uma lista com os valores"""

    dados = df_filtrado.groupby(categoria)[somatorio].agg(_agg).reset_index().rename(columns = {categoria:'product','sum':'amount','count':'score'})[['score','amount','product']]

    mylist = dados.values.tolist()

    mylist.sort(key=lambda x: x[1])

    mylist.reverse()

    mylist.append(list(dados))

    mylist.reverse()

    return mylist

def serie_temporal_data(
    df_filtrado: pd.DataFrame,
    col_data: str, 
    col_values: str,
    _agg: str = 'sum') -> list:

    """Agrupa os valores de um Data Frame a partir da data selecionada pelo usuário"""

    serie_gastos = df_filtrado.pivot_table(index=col_data,
                        values = col_values,
                        aggfunc = _agg)
    
    return serie_gastos.reset_index().rename(columns = {col_data:'Data', col_values:'value'})

def serie_temporal_dia_semana(
    df: pd.DataFrame,
    col_data: str,
    valores: str,
    colunas: str,
    agg: str) -> list:

    """Agrupa os valores pelo dia da semana e retorna uma lista compactadas com os parâmentros, use * para descompactar os parâmetros."""

    serie_gastos = df.pivot_table(index=colunas,
                        values = valores,
                        columns = df[col_data].dt.dayofweek,
                        aggfunc = agg)
    
    eixo = [ x for x in serie_gastos.columns.map({0:'Domingo',1:'Segunda',2:'Terça',3:'Quarta',4:'Quinta',5:'Sexta',6:'Sábado',7:'Domingo'})]

    categorias = [ x for x in serie_gastos.index]

    valores_series = serie_gastos.values.tolist()
    
    return valores_series, categorias, eixo

def serie_temporal_dia_semana_complexo(
    df: pd.DataFrame,
    col_data: str,
    valores: str,
    colunas: str,
    agg: str) -> list:

    """Agrupa os valores pelo dia da semana e retorna uma lista compactada com os parâmentros.
    Options ja está umbutido e é 1° valor retornado na lista desta função.
    Use essa função com os gráficos do echart: barras_empilhadas_horizontais,barras_empilhadas_laterais 
     use * para descompactar os parâmetros."""


    def config_data(lista_valores,categorias):

        add_dic = list()
        for x in range(len(lista_valores)):
            
            add_dic.append( {
            "name": categorias[x],
            "type": "bar",
            "stack": "total",
            "label": {"show": False},
            "emphasis": {"focus": "series"},
            "data": [round(float(l),2) for l in lista_valores[x] ],
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

def serei_semana_mes_complexo(
    df: pd.DataFrame,
    col_data: str,
    valores: str,
    colunas: str,
    agg: str) -> list:

    """Agrupa os valores pela semana do mês e retorna uma lista compactada com os parâmentros.
    Options ja está umbutido e é 1° valor retornado na lista desta função.
    Use essa função com os gráficos do echart: barras_empilhadas_horizontais,barras_empilhadas_laterais 
    use * para descompactar os parâmetros."""

    def config_data(lista_valores, categorias):
        add_dic = []
        for x in range(len(lista_valores)):
            add_dic.append({
                "name": categorias[x],
                "type": "bar",
                "stack": "total",
                "label": {"show": False},
                "emphasis": {"focus": "series"},
                "data": [round(float(l),2) for l in lista_valores[x]],
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

def lista_categorica_complexa(
    df: pd.DataFrame,
    col_categori: str,
    valores: str,
    colunas: str,
    _agg: str) -> list:

    """Agrupa os valores por categoria e retorna uma lista compactada com os parâmentros.
    Options ja está umbutido e é 1° valor retornado na lista desta função.
    Use essa função com os gráficos do echart: barras_empilhadas_horizontais,barras_empilhadas_laterais 
    use * para descompactar os parâmetros."""

    def config_data(lista_valores, categorias):
        add_dic = []
        for x in range(len(lista_valores)):
            add_dic.append({
                "name": categorias[x],
                "type": "bar",
                "stack": "total",
                "label": {"show": False},
                "emphasis": {"focus": "series"},
                "data": [int(l) for l in lista_valores[x]],
            })
        return add_dic

    serie_gastos = df.pivot_table(
        index=colunas,
        values=valores,
        columns=col_categori,
        aggfunc=_agg
    ).fillna(0)

    serie_gastos = serie_gastos[serie_gastos.sum().sort_values(ascending = False).index]

    eixo = [x for x in serie_gastos.columns]

    categorias = [x for x in serie_gastos.index]
    valores_series = serie_gastos.values.tolist()

    return config_data(valores_series, categorias), categorias, eixo

def dias_mes_sem_evento(
        df_filtrado: pd.DataFrame,
        col_data: str) -> pd.DataFrame:

    dias_mês =  pd.DataFrame({"mês":df_filtrado[col_data].dt.strftime('%Y%m'),"Dias do mês":df_filtrado[col_data].dt.daysinmonth}).drop_duplicates().set_index('mês').to_dict()['Dias do mês']

    dias_com_gastos = df_filtrado.pivot_table(index = df_filtrado[col_data].dt.strftime('%Y%m'),
                        values = col_data,
                        aggfunc = lambda x: len(x.unique())).rename(columns = {col_data:"dias com evento"}).reset_index()
    
    dias_com_gastos['Dias do mês'] = dias_com_gastos[col_data].map(dias_mês)

    dias_com_gastos['dias_sem_gastar'] = dias_com_gastos['Dias do mês'] - dias_com_gastos['dias com evento']

    #gastos_utilizacoes = df_filtrado.groupby(df_filtrado[col_data].dt.strftime('%Y%m'))['amount'].agg(['sum','count'])

    #dias_com_gastos.merge(gastos_utilizacoes, left_on = 'date', right_index = True, how = 'left')

    return dias_com_gastos

def top_10_categorias(
        df_filtrado: pd.DataFrame,
        categoria: str,
        sub_categoria:str,
        valores: str,
        _agg: str
        ) -> list:
    
    """Retorna uma lista com agregações de uma categoria e agregações da sub categoria atrelada a essa categoria.
    use esta função com o gráfico de barras e driw_drow"""

    categorias = [ x for x in (df_filtrado.groupby([categoria])[valores].agg(_agg).sort_values(ascending=False).index)]

    op = dict()

    for a in categorias:


        t = df_filtrado[df_filtrado[categoria] == a].pivot_table(index = sub_categoria,
                                                                values = valores,
                                                                aggfunc = _agg).sort_values(by = valores, ascending = False).head(15).reset_index()
        
        t = t.values.tolist()
         
        op.update({a:t})

        print(op)
        print("-----")

    return op,categorias,options_lista_categorica_simples(df_filtrado,categoria,valores,controle='groupId')

def get_delta(curr, prev, is_pct=False):

    """Calcula o percentual de variação entre dois valores.
    use com st.matric"""

    if prev is None or prev == 0:
        return None
    if is_pct:
        return f"{curr - prev:+.1f}%"
    return f"{(curr - prev) / prev * 100:+.1f}%"

def dados_grafico_cachoeira(
        df_filtrado: pd.DataFrame,
        col_data:str,
        col_valores: str,
        _agg: str = 'sum') -> list:
    
    """Retorna uma lista de variação temporal aculmulada"""



    gastos_mes = df_filtrado.groupby(df_filtrado[col_data].dt.strftime('%Y%m'))[col_valores].agg(_agg)

    aumento = [ '-' if x < 0 else int(x) for x in gastos_mes.diff().fillna(gastos_mes[0]) ]

    queda = [ '-' if x < 0 else int(x) for x in (gastos_mes.diff() * -1).fillna(-1) ]

    valores = [int(x) for x in gastos_mes.values ]

    categorias = [ x for x in gastos_mes.index ]

    return categorias, valores, aumento, queda

def Serie_tempo_relativo(df: pd.DataFrame,
                        coluna_data: str,
                        valores:str, 
                        epocas: int = 6, 
                        _agg: str = "sum", 
                        forma_data: str = '%Y%m'):
    
    """Retorna uma série com os valores dos ultimos x meses"""

    df_f = df.pivot_table(index = df[coluna_data].dt.strftime(forma_data),
                   values = valores,
                   aggfunc = _agg)
    
    date_completo = pd.DataFrame({'Date':pd.date_range(start = df[coluna_data].min(),end=dt.datetime.now()).strftime(forma_data).unique()})

    return df_f.merge(date_completo,
                   left_index=True,
                   right_on="Date",
                   how='right').set_index('Date').fillna(0).tail(epocas)

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

def dados_grafico_barras(df, agregardor,valores, _agg = 'sum', ordenacao = True):


    t = df.pivot_table(index = agregardor,
                        values = valores,
                         aggfunc = _agg )
    
    if ordenacao:
    
        t = t.sort_values(by = valores, ascending = False)
    
    categorias = [ x for x in t.index ]

    _valores = [ x for x in t[valores] ]

    return categorias,_valores