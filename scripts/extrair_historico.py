# pip install pdfplumber pandas
import re
import pandas as pd
import pdfplumber

def extrair_grade_perfeita(pdf_path):
    materias_finais = {}

    situacoes_validas = [
        "APR", "APRN", "REP", "REPF", "REPMF", "REPN", "REPNF",
        "MATR", "CUMP", "DISP", "TRANS", "INCORP", "CANC", "TRANC"
    ]
    situacoes_reprovacao = [
        "REP", "REPF", "REPMF", "REPN", "REPNF",
        "MATR", "CANC", "TRANC"
    ]

    print(f"Lendo e alinhando colunas do histórico: {pdf_path}...")

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()

            for tabela in tabelas:
                for linha in tabela:
                    if not linha or len(linha) < 5:
                        continue

                    colunas_texto = []
                    for celula in linha:
                        if not celula:
                            colunas_texto.append([])
                            continue

                        t = str(celula)
                        # Corrige códigos fragmentados pelas quebras de linha do SIGAA
                        t = re.sub(r"([A-Z]{3,4}\d{3,4})\s*\n*\s*-\s*\n*\s*(\d{2})", r"\1-\2", t)
                        t = re.sub(r"([A-Z]{3,4}\d{2,3})\s*\n*\s*(\d{1,2})\s*-\s*(\d{2})", r"\1\2-\3", t)

                        linhas_celula = [x.strip() for x in t.split('\n') if x.strip()]
                        colunas_texto.append(linhas_celula)

                    idx_comp = -1
                    idx_sit = -1
                    idx_conc = -1

                    # Identifica as colunas chaves
                    for i, col in enumerate(colunas_texto):
                        if any(re.match(r"^[A-Z]{3,4}\d{3,4}-\d{2}$", x) for x in col):
                            idx_comp = i
                        if any(x in situacoes_validas for x in col):
                            idx_sit = i

                    for i, col in enumerate(colunas_texto):
                        if i in [idx_comp, idx_sit]: continue
                        validos_conceito = [x for x in col if x in ["A", "B", "C", "D", "F", "O"]]
                        total_preenchidos = len([x for x in col if x])
                        if validos_conceito and total_preenchidos > 0:
                            if len(validos_conceito) >= total_preenchidos / 2:
                                idx_conc = i
                                break

                    if idx_comp == -1 or idx_sit == -1:
                        continue

                    # --- Novo Sistema de Posse para os Nomes das Disciplinas ---
                    linhas_comp = colunas_texto[idx_comp]
                    code_indices = []
                    for i, linha_str in enumerate(linhas_comp):
                        if re.match(r"^[A-Z]{3,4}\d{3,4}-\d{2}$", linha_str):
                            code_indices.append((i, linha_str))

                    nomes_map = {}
                    claimed = set()

                    # Fase 1: Matérias que estão isoladas nas quebras de linha
                    for idx, (linha_idx, codigo) in enumerate(code_indices):
                        start_bound = code_indices[idx-1][0] if idx > 0 else -1
                        end_bound = code_indices[idx+1][0] if idx < len(code_indices)-1 else len(linhas_comp)

                        lines_before = [i for i in range(start_bound+1, linha_idx)]
                        lines_after = [i for i in range(linha_idx+1, end_bound)]

                        if lines_before and not lines_after:
                            nomes_map[codigo] = " ".join([linhas_comp[i] for i in lines_before])
                            claimed.update(lines_before)
                        elif lines_after and not lines_before:
                            nomes_map[codigo] = " ".join([linhas_comp[i] for i in lines_after])
                            claimed.update(lines_after)

                    # Fase 2: Matérias muito próximas (pegando o texto restante da célula)
                    for idx, (linha_idx, codigo) in enumerate(code_indices):
                        if codigo in nomes_map: continue

                        start_bound = code_indices[idx-1][0] if idx > 0 else -1
                        end_bound = code_indices[idx+1][0] if idx < len(code_indices)-1 else len(linhas_comp)

                        unc_before = [i for i in range(start_bound+1, linha_idx) if i not in claimed]
                        unc_after = [i for i in range(linha_idx+1, end_bound) if i not in claimed]

                        if unc_before:
                            nomes_map[codigo] = " ".join([linhas_comp[i] for i in unc_before])
                            claimed.update(unc_before)
                        elif unc_after:
                            nomes_map[codigo] = " ".join([linhas_comp[i] for i in unc_after])
                            claimed.update(unc_after)
                        else:
                            nomes_map[codigo] = "Disciplina UFABC"

                    # Fallback de segurança: Se os nomes estiverem numa coluna totalmente separada
                    nomes_validos = sum(1 for v in nomes_map.values() if len(v) > 4 and v != "Disciplina UFABC")
                    if nomes_validos < len(code_indices):
                        idx_nome = -1
                        max_len = 0
                        for i, col in enumerate(colunas_texto):
                            if i in [idx_comp, idx_sit, idx_conc]: continue
                            textos_validos = [x for x in col if len(x) > 4 and not re.match(r"^[A-Z]{3,4}\d{3,4}-\d{2}$", x)]
                            if textos_validos:
                                avg_len = sum(len(x) for x in textos_validos) / len(textos_validos)
                                if avg_len > max_len:
                                    max_len = avg_len
                                    idx_nome = i
                        
                        if idx_nome != -1:
                            linhas_nome = [x for x in colunas_texto[idx_nome] if len(x) > 3]
                            for i, (linha_idx, codigo) in enumerate(code_indices):
                                if i < len(linhas_nome):
                                    nomes_map[codigo] = linhas_nome[i]

                    # --- Montagem Final da Base ---
                    situacoes = [x for x in colunas_texto[idx_sit] if x in situacoes_validas]
                    conceitos = []
                    if idx_conc != -1:
                        conceitos = [x for x in colunas_texto[idx_conc] if x in ["A", "B", "C", "D", "F", "O"]]

                    for k, (linha_idx, codigo) in enumerate(code_indices):
                        nome = nomes_map.get(codigo, "Disciplina UFABC")
                        
                        # Limpa possíveis sujeiras do final do nome
                        nome = re.sub(r"(OBR|OL|LIV|CH|Cred)", "", nome).strip()

                        sit = situacoes[k] if k < len(situacoes) else None
                        conc = conceitos[k] if k < len(conceitos) else sit

                        if sit and sit not in situacoes_reprovacao:
                            materias_finais[codigo] = {
                                "Codigo": codigo,
                                "Materia": nome,
                                "Conceito": conc,
                                "Situacao": sit
                            }

    df = pd.DataFrame(list(materias_finais.values()))
    if not df.empty:
        df = df.sort_values(by="Codigo")
    return df

if __name__ == "__main__":
    arquivo = "historico_11202322044.pdf"

    try:
        df_historico = extrair_grade_perfeita(arquivo)

        if not df_historico.empty:
            df_historico.to_csv("materias_feitas.csv", index=False, encoding="utf-8")
            print(f"\n✅ Sucesso! Extraídas {len(df_historico)} matérias aprovadas.")
            print("\n--- Suas matérias concluídas (Salvas em materias_feitas.csv) ---")
            print(df_historico.to_string(index=False))
        else:
            print("\n⚠️ Nenhuma matéria validada foi capturada.")

    except FileNotFoundError:
        print(f"❌ Arquivo '{arquivo}' não encontrado na pasta.")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")