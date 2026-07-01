import pandas as pd

def extrair_recomendacoes_catalogo(pdf_path):
    return {}

def classificar_pendencias(csv_pendentes, csv_feitas, mapa_recs):
    print("⚖️  Calculando prioridade (Modo Raiz: APENAS Hierarquia por Código)...")
    
    try:
        df_pendentes = pd.read_csv(csv_pendentes)
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo '{csv_pendentes}' não foi encontrado.")
        return pd.DataFrame()

    pesos = []
    for _, row in df_pendentes.iterrows():
        codigo = str(row['Codigo']).upper()
        
        if codigo.startswith(('BC', 'BI', 'BM')):
            peso_final = 10000  # 1. BCT no topo do Olimpo
            
        elif codigo.startswith(('ESTO', 'ESMA', 'ESTI')):
            peso_final = 5000   # 2. Comuns das Engenharias
            
        elif codigo.startswith(('ESAE', 'ESTS', 'ESTA', 'ESTG')):
            peso_final = 1000   # 3. Específicas da Aeroespacial
            
        else:
            peso_final = 1      # 4. Qualquer outra coisa (Limitadas/Livres como ESTB) vai pro esgoto
            
        pesos.append(peso_final)

    df_pendentes['Peso'] = pesos
    
    df_pendentes = df_pendentes.sort_values(by=['Peso', 'Codigo'], ascending=[False, True])

    return df_pendentes