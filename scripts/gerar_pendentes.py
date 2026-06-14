# pip install PyMuPDF pandas
import re
import pandas as pd
import fitz

def extrair_grade_ideal(pdf_path):
    grade_ideal = {}
    print(f"📖 Lendo o projeto pedagógico completo: {pdf_path}...")
    
    try:
        doc = fitz.open(pdf_path)
        texto_corrido = ""
        for pagina in doc:
            # Amassa o texto inteiro do documento
            texto_corrido += pagina.get_text("text").replace('\n', ' ') + " "
        doc.close()
        
        # Encontra absolutamente TODOS os códigos da UFABC no documento
        codigos = re.finditer(r"\b([A-Z]{3,4}\d{3,4}-\d{2})\b", texto_corrido)
        
        for match in codigos:
            codigo = match.group(1)
            pos_start = match.end()
            
            # Captura o nome da matéria logo após o código
            janela = texto_corrido[pos_start:pos_start+150].strip()
            match_nome = re.search(r"^([A-Za-zÀ-ÖØ-öø-ÿ\s\-]+)", janela)
            
            if match_nome:
                nome = match_nome.group(1).strip()
                # Limpeza de resíduos de tabelas do PDF
                nome = re.sub(r"\s*(OBR|OL|LIV|CH|Cred|T\s*P\s*I|Teoria|Pr[áa]tica|Campus).*$", "", nome, flags=re.IGNORECASE).strip()
                
                if len(nome) > 3:
                    grade_ideal[codigo] = nome
                    
        df_todas = pd.DataFrame(list(grade_ideal.items()), columns=["Codigo", "Materia_Ideal"])
        df_todas = df_todas.drop_duplicates(subset=["Codigo"])
        
        # ---------------------------------------------------------
        # FILTRO CIRÚRGICO: BCT + NÚCLEO COMUM + AEROESPACIAL
        # ---------------------------------------------------------
        # Códigos específicos de OUTRAS engenharias que queremos ignorar
        # para que a sua lista não fique com 200 matérias falsas.
        prefixos_ignorados = (
            'ESTM', # Materiais
            'ESAM', # Ambiental
            'ESBM', # Biomédica
            'ESEN', # Energia
            'ESGE', # Gestão
            'ESIN', # Informação
            'ESIR', # Instrumentação e Robótica
            'NH', 'DA', 'QA' # Licenciaturas e Biológicas
        )
        
        # Mantém apenas as matérias que NÃO começam com os prefixos das outras engenharias
        df_filtrado = df_todas[~df_todas['Codigo'].str.startswith(prefixos_ignorados)].copy()
        
        return df_filtrado
        
    except Exception as e:
        print(f"❌ Erro fatal ao ler o PDF: {e}")
        return pd.DataFrame()

def identificar_pendencias(csv_feitas, df_grade_ideal):
    print("⚙️ Cruzando seu histórico com a grade BCT + Aeroespacial...")
    
    try:
        df_feitas = pd.read_csv(csv_feitas)
        codigos_concluidos = set(df_feitas["Codigo"].dropna().tolist())
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo '{csv_feitas}' não foi encontrado.")
        return pd.DataFrame()

    # Identifica o que falta
    df_pendentes = df_grade_ideal[~df_grade_ideal["Codigo"].isin(codigos_concluidos)].copy()
    
    return df_pendentes

if __name__ == "__main__":
    # Teste isolado caso precise rodar apenas este arquivo
    arquivo_grade = "data/ordem_do_dia_-_anexo_1b.pdf"
    arquivo_historico = "OUTPUTS_CSV/materias_feitas.csv"
    
    df_grade = extrair_grade_ideal(arquivo_grade)
    if not df_grade.empty:
        df_faltam = identificar_pendencias(arquivo_historico, df_grade)
        print(f"📚 Total de matérias Aero/BCT encontradas: {len(df_grade)}")
        print(f"🎯 Faltam cursar: {len(df_faltam)}")
        print(df_faltam.head(15))