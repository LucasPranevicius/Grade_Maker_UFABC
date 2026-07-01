# pip install pdfplumber pandas
import re
import pandas as pd
import pdfplumber
import os

def extrair_grade_perfeita(pdf_path):
    materias_finais = {}

    situacoes_validas = [
        "APR", "APRN", "REP", "REPF", "REPMF", "REPN", "REPNF",
        "MATR", "CUMP", "DISP", "TRANS", "INCORP", "CANC", "TRANC"
    ]
    situacoes_reprovacao = [
        "REP", "REPF", "REPMF", "REPN", "REPNF", "CANC", "TRANC"
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
                        t = re.sub(r"([A-Z]{3,4}\d{3,4})\s*\n*\s*-\s*\n*\s*(\d{2})", r"\1-\2", t)
                        t = re.sub(r"([A-Z]{3,4}\d{2,3})\s*\n*\s*(\d{1,2})\s*-\s*(\d{2})", r"\1\2-\3", t)

                        linhas_celula = [x.strip() for x in t.split('\n') if x.strip()]
                        colunas_texto.append(linhas_celula)

                    idx_comp = -1
                    idx_sit = -1
                    idx_conc = -1

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

                    linhas_comp = colunas_texto[idx_comp]
                    code_indices = []
                    for i, linha_str in enumerate(linhas_comp):
                        if re.match(r"^[A-Z]{3,4}\d{3,4}-\d{2}$", linha_str):
                            code_indices.append((i, linha_str))

                    nomes_map = {}
                    claimed = set()

                    for idx, (linha_idx, codigo) in enumerate(code_indices):
                        start_bound = code_indices[idx-1][0] if idx > 0 else -1
                        end_bound = code_indices[idx+1][0] if idx < len(code_indices)-1 else len(linhas_comp)

                        lines_before = [i for i in range(start_bound+1, linha_idx)]
                        lines_after = [i for i in range(linha_idx+1, end_bound)]

                        if lines_before and not lines_after:
                            txt_before = [linhas_comp[i] for i in lines_before if not re.search(r"(PROF\.|PROFA\.|DOCENTE|DR\.|DRA\.)", linhas_comp[i], re.IGNORECASE)]
                            nomes_map[codigo] = " ".join(txt_before) if txt_before else "Disciplina UFABC"
                            claimed.update(lines_before)
                        elif lines_after and not lines_before:
                            txt_after = [linhas_comp[i] for i in lines_after if not re.search(r"(PROF\.|PROFA\.|DOCENTE|DR\.|DRA\.)", linhas_comp[i], re.IGNORECASE)]
                            nomes_map[codigo] = " ".join(txt_after) if txt_after else "Disciplina UFABC"
                            claimed.update(lines_after)

                    for idx, (linha_idx, codigo) in enumerate(code_indices):
                        if codigo in nomes_map and nomes_map[codigo] != "Disciplina UFABC": continue

                        start_bound = code_indices[idx-1][0] if idx > 0 else -1
                        end_bound = code_indices[idx+1][0] if idx < len(code_indices)-1 else len(linhas_comp)

                        unc_before = [i for i in range(start_bound+1, linha_idx) if i not in claimed]
                        unc_after = [i for i in range(linha_idx+1, end_bound) if i not in claimed]

                        if unc_before:
                            txt_before = [linhas_comp[i] for i in unc_before if not re.search(r"(PROF\.|PROFA\.|DOCENTE|DR\.|DRA\.)", linhas_comp[i], re.IGNORECASE)]
                            nomes_map[codigo] = " ".join(txt_before) if txt_before else "Disciplina UFABC"
                            claimed.update(unc_before)
                        elif unc_after:
                            txt_after = [linhas_comp[i] for i in unc_after if not re.search(r"(PROF\.|PROFA\.|DOCENTE|DR\.|DRA\.)", linhas_comp[i], re.IGNORECASE)]
                            nomes_map[codigo] = " ".join(txt_after) if txt_after else "Disciplina UFABC"
                            claimed.update(unc_after)
                        else:
                            if codigo not in nomes_map:
                                nomes_map[codigo] = "Disciplina UFABC"

                    nomes_validos = sum(1 for v in nomes_map.values() if len(v) > 4 and v != "Disciplina UFABC")
                    if nomes_validos < len(code_indices):
                        idx_nome = -1
                        max_len = 0
                        for i, col in enumerate(colunas_texto):
                            if i in [idx_comp, idx_sit, idx_conc]: continue
                            textos_validos = [x for x in col if len(x) > 4 and not re.match(r"^[A-Z]{3,4}\d{3,4}-\d{2}$", x) and not re.search(r"(PROF\.|PROFA\.|DOCENTE|DR\.|DRA\.)", x, re.IGNORECASE)]
                            if textos_validos:
                                avg_len = sum(len(x) for x in textos_validos) / len(textos_validos)
                                if avg_len > max_len:
                                    max_len = avg_len
                                    idx_nome = i
                        
                        if idx_nome != -1:
                            linhas_nome = [x for x in colunas_texto[idx_nome] if len(x) > 3 and not re.search(r"(PROF\.|PROFA\.|DOCENTE|DR\.|DRA\.)", x, re.IGNORECASE)]
                            for i, (linha_idx, codigo) in enumerate(code_indices):
                                if i < len(linhas_nome):
                                    nomes_map[codigo] = linhas_nome[i]

                    situacoes = [x for x in colunas_texto[idx_sit] if x in situacoes_validas]
                    conceitos = []
                    if idx_conc != -1:
                        conceitos = [x for x in colunas_texto[idx_conc] if x in ["A", "B", "C", "D", "F", "O"]]

                    for k, (linha_idx, codigo) in enumerate(code_indices):
                        nome = nomes_map.get(codigo, "Disciplina UFABC")
                        
                        nome = re.sub(r"(OBR|OL|LIV|CH|Cred|Teoria|Prática)", "", nome).strip()

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
        try:
            caminho_anexo = "data/ordem_do_dia_-_anexo_1b.pdf"
            if os.path.exists(caminho_anexo):
                from scripts.gerar_pendentes import extrair_grade_ideal
                df_ideal = extrair_grade_ideal(caminho_anexo)
                if not df_ideal.empty:
                    mapa_nomes_oficiais = dict(zip(df_ideal["Codigo"], df_ideal["Materia_Ideal"]))
                    df["Materia"] = df["Codigo"].map(mapa_nomes_oficiais).fillna(df["Materia"])
        except Exception as e:
            print(f"⚠️ Nota: Não foi possível sincronizar com os nomes do anexo_1b ({e})")
            
    return df

if __name__ == "__main__":
    arquivo = "historico_11202322044.pdf"
    pasta_saida = "OUTPUTS_CSV"
    os.makedirs(pasta_saida, exist_ok=True)
    caminho_csv = os.path.join(pasta_saida, "materias_feitas.csv")

    try:
        df_historico = extrair_grade_perfeita(arquivo)

        if not df_historico.empty:
            df_historico.to_csv(caminho_csv, index=False, encoding="utf-8")
            print(f"\n✅ Sucesso! Extraídas {len(df_historico)} matérias aprovadas.")
            print(df_historico.to_string(index=False))
        else:
            print("\n⚠️ Nenhuma matéria validada foi capturada.")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")