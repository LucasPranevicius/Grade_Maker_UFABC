import re
import pandas as pd
import fitz

def extrair_grade_ideal(pdf_path):
    grade_ideal = {}
    print(f"📖 Lendo o projeto pedagógico e extraindo créditos: {pdf_path}...")
    
    try:
        doc = fitz.open(pdf_path)
        texto_corrido = ""
        for pagina in doc:
            texto_corrido += pagina.get_text("text").replace('\n', ' ') + " "
        doc.close()
        
        codigos = re.finditer(r"\b([A-Z]{3,4}\d{3,4}-\d{2})\b", texto_corrido)
        
        for match in codigos:
            codigo = match.group(1)
            pos_start = match.end()
            
            janela = texto_corrido[pos_start:pos_start+150].strip()
            
            match_nome_cred = re.search(r"^([A-Za-zÀ-ÖØ-öø-ÿ\s\-\,\.]+?)\s+(\d+)\s+(\d+)\s+(\d+)", janela)
            
            if match_nome_cred:
                nome = match_nome_cred.group(1).strip()
                creditos = int(match_nome_cred.group(2)) + int(match_nome_cred.group(3))
            else:
                match_nome = re.search(r"^([A-Za-zÀ-ÖØ-öø-ÿ\s\-]+)", janela)
                nome = match_nome.group(1).strip() if match_nome else "Disciplina Desconhecida"
                creditos = 4
                
            nome = re.split(r"(\sEixo\s|\s-\sdisciplina|\sOBR|\sOL|\sLIV|\sCH|\sCred|\sT\s*P\s*I)", nome, flags=re.IGNORECASE)[0].strip()
            
            if len(nome) > 3:
                if codigo not in grade_ideal:
                    grade_ideal[codigo] = {"Nome": nome, "Creditos": creditos}
                    
        df_todas = pd.DataFrame([{"Codigo": k, "Materia_Ideal": v["Nome"], "Creditos": v["Creditos"]} for k, v in grade_ideal.items()])
        
        prefixos_ignorados = ('ESTM', 'ESAM', 'ESBM', 'ESEN', 'ESGE', 'ESIN', 'ESIR', 'NH', 'DA', 'QA')
        df_filtrado = df_todas[~df_todas['Codigo'].str.startswith(prefixos_ignorados)].copy()
        
        return df_filtrado
        
    except Exception as e:
        print(f"❌ Erro fatal ao ler o PDF: {e}")
        return pd.DataFrame()

def identificar_pendencias(csv_feitas, df_grade_ideal):
    print("⚙️ Cruzando seu histórico com a grade (por Código E por Nome)...")
    
    try:
        df_feitas = pd.read_csv(csv_feitas)
        codigos_concluidos = set(df_feitas["Codigo"].dropna().tolist())
        nomes_concluidos = set(df_feitas["Materia"].dropna().str.lower().str.strip().tolist())
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo '{csv_feitas}' não foi encontrado.")
        return pd.DataFrame()

    pendentes = []
    for _, row in df_grade_ideal.iterrows():
        cod = row['Codigo']
        nome = row['Materia_Ideal'].lower().strip()
        
        # 1. Se o código exato está no histórico -> Feita
        if cod in codigos_concluidos:
            continue
            
        # 2. Se o nome exato está no histórico (resolve matérias que mudaram de código) -> Feita
        if nome in nomes_concluidos:
            continue
            
        # 3. Tratamento especial para Projetos Dirigidos (Busca por palavra-chave)
        if "projeto dirigido" in nome and any("projeto dirigido" in n for n in nomes_concluidos):
            continue
            
        pendentes.append(row)
        
    return pd.DataFrame(pendentes)