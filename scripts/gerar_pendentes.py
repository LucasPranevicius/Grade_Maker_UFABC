# pip install PyMuPDF pandas
import re
import pandas as pd
import fitz

def extrair_grade_ideal(pdf_path):
    grade_ideal = {}
    print(f"Lendo o projeto pedagógico com PyMuPDF: {pdf_path}...")
    
    try:
        doc = fitz.open(pdf_path)
        texto_completo = ""
        for pagina in doc:
            texto_completo += pagina.get_text("text") + "\n"
        doc.close()
        
        # 1. Encontra onde começa a tabela de Obrigatórias
        inicio_match = re.search(r"ROL DE DISCIPLINAS OBRIGAT[ÓO]RIAS", texto_completo, re.IGNORECASE)
        
        if not inicio_match:
            print("⚠️ Não encontrei o marcador 'ROL DE DISCIPLINAS OBRIGATÓRIAS' no documento.")
            return pd.DataFrame()
        
        inicio = inicio_match.start()
        
        # 2. Encontra onde a tabela acaba (início das Limitadas ou do Ementário)
        fim_match = re.search(r"ROL DE DISCIPLINAS DE OP[ÇC][ÃA]O LIMITADA|EMENT[ÁA]RIO", texto_completo[inicio:], re.IGNORECASE)
        
        if fim_match:
            fim = inicio + fim_match.start()
            trecho_tabela = texto_completo[inicio:fim]
        else:
            trecho_tabela = texto_completo[inicio:] # Se não achar o fim, vai até o final
            
        print("✅ Seção de Obrigatórias isolada com sucesso!")
        texto_corrido = trecho_tabela.replace('\n', ' ')
        
        # 3. Extrai apenas os códigos e nomes que estão dentro dessa fatia
        codigos = re.finditer(r"\b([A-Z]{3,4}\d{3,4}-\d{2})\b", texto_corrido)
        
        for match in codigos:
            codigo = match.group(1)
            pos_start = match.end()
            
            # Pega uma janela de texto logo após o código
            janela = texto_corrido[pos_start:pos_start+150].strip()
            
            # Captura o nome da matéria parando antes dos números (T-P-I, créditos)
            match_nome = re.search(r"^([A-Za-zÀ-ÖØ-öø-ÿ\s\-]+)", janela)
            
            if match_nome:
                nome = match_nome.group(1).strip()
                # Limpeza extra para evitar que cabeçalhos entrem no nome
                nome = re.sub(r"\s*(OBR|OL|LIV|CH|Cred|T\s*P\s*I).*$", "", nome, flags=re.IGNORECASE).strip()
                
                if len(nome) > 3:
                    grade_ideal[codigo] = nome
                    
    except Exception as e:
        print(f"❌ Erro fatal ao ler o PDF: {e}")
        return pd.DataFrame()
        
    df_ideal = pd.DataFrame(list(grade_ideal.items()), columns=["Codigo", "Materia_Ideal"])
    return df_ideal

def identificar_pendencias(feitas_csv, df_grade_ideal):
    print("\nCruzando seu histórico com a grade de Engenharia Aeroespacial...")
    
    try:
        df_feitas = pd.read_csv(feitas_csv)
        codigos_concluidos = set(df_feitas["Codigo"].dropna().tolist())
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo '{feitas_csv}' não foi encontrado.")
        return pd.DataFrame()

    # Filtra mantendo só o que você ainda não fez
    df_pendentes = df_grade_ideal[~df_grade_ideal["Codigo"].isin(codigos_concluidos)].copy()
    
    return df_pendentes

if __name__ == "__main__":
    arquivo_grade = "data\ordem_do_dia_-_anexo_1b.pdf"
    arquivo_historico_csv = "OUTPUTS_CSV\materias_feitas.csv"
    
    try:
        df_grade = extrair_grade_ideal(arquivo_grade)
        
        if not df_grade.empty:
            df_faltam = identificar_pendencias(arquivo_historico_csv, df_grade)
            
            df_faltam.to_csv("OUTPUTS_CSV\materias_pendentes.csv", index=False, encoding="utf-8")
            
            print(f"\n✅ Cruzamento concluído com sucesso!")
            print(f"📚 Obrigatórias totais da grade: {len(df_grade)}")
            print(f"🎯 Faltam cursar: {len(df_faltam)} matérias.")
            print("\n--- Próximas matérias obrigatórias pendentes ---")
            print(df_faltam.head(20).to_string(index=False))
        else:
            print("\n⚠️ Nenhuma matéria foi extraída da seção.")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")