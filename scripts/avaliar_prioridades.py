# pip install PyMuPDF pandas
import re
import pandas as pd
import fitz

def extrair_recomendacoes_catalogo(pdf_catalogo):
    recomendacoes = {}
    print(f"📖 Lendo o catálogo da UFABC (Isso pode levar alguns segundos): {pdf_catalogo}...")
    
    try:
        doc = fitz.open(pdf_catalogo)
        texto_completo = ""
        for pagina in doc:
            texto_completo += pagina.get_text("text") + "\n"
        doc.close()
        
        # Encontra todos os códigos das disciplinas no texto gigante
        codigos = list(re.finditer(r"\b([A-Z]{3,4}\d{3,4}-\d{2})\b", texto_completo))
        
        for i, match in enumerate(codigos):
            codigo = match.group(1)
            inicio = match.end()
            # Delimita o bloco de texto até a próxima disciplina
            fim = codigos[i+1].start() if i + 1 < len(codigos) else len(texto_completo)
            bloco = texto_completo[inicio:fim]
            
            # Pega exatamente o que está entre "RECOMENDAÇÃO:" e "OBJETIVOS:"
            match_rec = re.search(r"RECOMENDA[ÇC][ÃA]O:\s*(.*?)(?=OBJETIVOS:|$)", bloco, re.DOTALL | re.IGNORECASE)
            
            if match_rec:
                rec_texto = match_rec.group(1).replace('\n', ' ').strip()
                
                # Ignora se for livre de recomendações
                if rec_texto.lower() in ["não se aplica", "nao se aplica", "-", "nenhuma", ""]:
                    recomendacoes[codigo] = []
                else:
                    # Quebra a string "Matéria A; Matéria B" em uma lista
                    recs = [r.strip() for r in rec_texto.split(";") if r.strip()]
                    recomendacoes[codigo] = recs
            else:
                recomendacoes[codigo] = []
                
    except Exception as e:
        print(f"❌ Erro ao ler o catálogo: {e}")
        
    return recomendacoes

def classificar_pendencias(csv_pendentes, csv_feitas, map_recs):
    print("\n⚙️ Cruzando recomendações com o seu histórico...")
    
    df_pendentes = pd.read_csv(csv_pendentes)
    df_feitas = pd.read_csv(csv_feitas)
    
    # Passa tudo para minúsculo para facilitar o "Match" dos nomes
    nomes_feitas = df_feitas['Materia'].str.lower().tolist()
    
    pesos = []
    status_recs = []
    
    for _, row in df_pendentes.iterrows():
        codigo = row['Codigo']
        recs_exigidas = map_recs.get(codigo, [])
        
        if not recs_exigidas:
            pesos.append(1)
            status_recs.append("Sem Recomendações (Livre)")
            continue
            
        todas_atendidas = True
        for rec in recs_exigidas:
            # Limpa lixos como "Requisito:" ou "Co-requisito:" do catálogo
            rec_limpa = re.sub(r"^(requisitos?|co-requisitos?|recomenda-se|disciplinas?):\s*", "", rec, flags=re.IGNORECASE).strip().lower()
            
            # Verifica se o nome da recomendação aparece no seu histórico de matérias feitas
            atendida = any(rec_limpa in nf or nf in rec_limpa for nf in nomes_feitas)
            
            if not atendida:
                todas_atendidas = False
                break
        
        if todas_atendidas:
            pesos.append(1)  # Prioridade Máxima
            status_recs.append("Todas Atendidas ✅")
        else:
            pesos.append(2)  # Prioridade Secundária
            status_recs.append("Faltam Recomendações ⚠️")
            
    df_pendentes['Status_Recomendacao'] = status_recs
    df_pendentes['Peso'] = pesos
    
    # Ordena deixando as de Peso 1 no topo
    df_pendentes = df_pendentes.sort_values(by=['Peso', 'Codigo'])
    return df_pendentes

if __name__ == "__main__":
    arquivo_catalogo = "data\catalogo_disciplinas_graduacao_2024_2025.pdf"
    arquivo_pendentes = "OUTPUTS_CSV\materias_pendentes.csv"
    arquivo_feitas = "OUTPUTS_CSV\materias_feitas.csv"
    
    mapa_recs = extrair_recomendacoes_catalogo(arquivo_catalogo)
    
    if mapa_recs:
        df_final = classificar_pendencias(arquivo_pendentes, arquivo_feitas, mapa_recs)
        
        # Sobrescreve o arquivo de pendências, agora "turbinado" com os pesos
        df_final.to_csv(arquivo_pendentes, index=False, encoding="utf-8")
        
        print("\n✅ Matérias pendentes atualizadas com pesos de prioridade!")
        print("\n--- Suas Próximas Matérias (Prioridade Máxima / Peso 1) ---")
        print(df_final[df_final['Peso'] == 1].head(15).to_string(index=False))