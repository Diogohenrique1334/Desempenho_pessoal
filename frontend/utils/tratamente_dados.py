import pandas as pd
import datetime as dt

    
def preparar_df(df):

    def Humor(table):

        table['Humor'] = table.apply(lambda x: (x['Nota do humor'] + x['Nota do humor fim do dia']) / 2, axis = 1)

        return table

    usuario = {'5511959536031':"Diogo",'5511991422452':"Michele"}

    Colunas_tratadas = {'data':'Data',
                        'nota_humor':'Nota do humor',
                        'Exercício_aerobico':'Exercício aeróbico',
                        'Alimentação_saudavel':'Alimentação saudável',
                        'Consumo_de_agua':'Consumo de água',
                        'Atividade_sexual':'Atividade sexual',
                        'Nota_humor_fim_dia':'Nota do humor fim do dia',

                        'data_hora_acordei':'Hora que eu acordei',
                        'data_hora_dormi':'Horario que eu fui dormir'
                    }
    
    Hiper_categoria = {'secreto':'Lazer', 'Estudar':'Evolução pessoal', 'Leitura':'Evolução pessoal','Exercício aeróbico':'Saúde do corpo', 
    'Alimentação saudável':'Saúde do corpo', 'Consumo de água':'Saúde do corpo','Atenção plena':'Saúde da mente', 'Academia':'Saúde do corpo',
    'Atividade sexual':'Lazer'}

    # Garante que a coluna 'data' é do tipo datetime e ajusta para o fuso horário correto
    df['data'] = pd.to_datetime(df['data'].dt.date)

    # Criação das colunas de data/hora a partir da coluna 'data'
    df['Dia da semana'] = df['data'].dt.weekday.map({6:'Dom',0:'Seg',1:'Ter',2:'Qua',3:'Qui',4:'Sex',5:'Sab'})
    df['mes'] = df["data"].dt.strftime('%m - %Y')
    df['mes_ordenacao'] = pd.to_datetime(df['data']).dt.to_period('M')
    df['mes'] = pd.Categorical(df['mes'], categories=df.sort_values('mes_ordenacao')['mes'].unique(), ordered=True)
    df = df.drop(columns=['mes_ordenacao','Diario_e_fixacao','Atencao_plena','status_conversa']).rename(columns = Colunas_tratadas)
    df['Dia da semana'] = pd.Categorical(df['Dia da semana'], categories=['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'], ordered=True)
    df['user_phone_number'] = df['user_phone_number'].map(usuario).astype('category')

    df['Nota do humor'] = df['Nota do humor'].fillna(df['Nota do humor'].mean())
    df['Horario que eu fui dormir'] = df['Horario que eu fui dormir'].fillna(df['Horario que eu fui dormir'].mean())

    # Converte colunas booleanas para 0 e 1 para cálculos
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype('bool').astype(int)

    df.sort_values('Data', inplace=True)

    df = df[df['user_phone_number'] == 'Diogo']
    
    mask = ~df['Horario que eu fui dormir'].isnull()
    
    df['Tempo de sono'] = None
    
    df.loc[mask,'Tempo de sono'] = (df.loc[mask,'Hora que eu acordei'] - df.loc[mask,'Horario que eu fui dormir']).map(
    lambda x: ((x - dt.timedelta(days = int(str(x).split(" ")[0]))).total_seconds() / 60) / 60 if pd.notna(x) else x)
    
    #df['Tempo de sono'] = df['Tempo de sono'].fillna(df['Tempo de sono'].mean())

    return Humor(df)