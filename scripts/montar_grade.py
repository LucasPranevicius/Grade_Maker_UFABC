# pip install PyMuPDF pandas
import re
import pandas as pd
import fitz

def extrair_turmas_ofertadas(pdf_path):
    turmas = []
    print(f"🔍 Extraindo ofertas em Modo Bloco Contínuo: {pdf_path}...")
    
    try:
        doc = fitz.open(pdf_path)
        for pagina in doc:
            texto = pagina.get_text("text")
            texto_corrido = texto.replace('\n', ' ')

            matches_codigo = list(re.finditer(r"([A-Z]{3,4}\d{3,4}-\d{2})", texto_corrido))

            for i, match in enumerate(matches_codigo):
                codigo = match.group(1)
                
                inicio_bloco = match.end()
                fim_bloco = matches_codigo[i+1].start() if i + 1 < len(matches_codigo) else len(texto_corrido)
                bloco = texto_corrido[inicio_bloco:fim_bloco]

                turno = "Noturno" if "Noturno" in bloco else ("Matutino" if "Matutino" in bloco else "Vespertino")
                campus = "SBC" if "SBC" in bloco or " SB" in bloco else ("SA" if "SA" in bloco else "SBC")

                padrao_horario = r"(segunda|ter[çc]a|quarta|quinta|sexta|s[áa]bado)\s+(?:das|stas)?\s*(\d{2}:\d{2})\s*(?:[àáa]s)?\s*(\d{2}:\d{2})\s*,?\s*(semanal|quinzenal\s*I{1,2})"
                horarios = re.finditer(padrao_horario, bloco, re.IGNORECASE)

                for h in horarios:
                    dia = h.group(1).capitalize()
                    if dia == "Terca": dia = "Terça"
                    if dia == "Sabado": dia = "Sábado"

                    hora_inicio = h.group(2)
                    hora_fim = h.group(3)
                    freq = h.group(4).lower()

                    quinzena = "Semanal"
                    if "quinzenal i" in freq and "ii" not in freq:
                        quinzena = "I"
                    elif "quinzenal ii" in freq:
                        quinzena = "II"

                    turmas.append({
                        "Codigo": codigo,
                        "Dia": dia,
                        "Horario": f"{hora_inicio}-{hora_fim}",
                        "Quinzena": quinzena,
                        "Turno": turno,
                        "Campus": campus
                    })
        doc.close()
    except Exception as e:
        print(f"❌ Erro fatal ao ler ofertas: {e}")
        
    df_turmas = pd.DataFrame(turmas)
    return df_turmas.drop_duplicates() if not df_turmas.empty else df_turmas

def simular_montagem_grade(df_ofertadas, csv_pendentes, pref_campus, pref_turno):
    print(f"⚙️  Iniciando Motor de Grade (Filtro: {pref_turno} em {pref_campus})...")
    
    try:
        df_pendentes = pd.read_csv(csv_pendentes)
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo '{csv_pendentes}' não foi encontrado.")
        return pd.DataFrame()

    turmas_uteis = pd.merge(df_ofertadas, df_pendentes, on="Codigo")
    
    if turmas_uteis.empty:
        print("⚠️ Nenhuma matéria pendente sua está sendo ofertada neste quadrimestre.")
        return pd.DataFrame()

    # --- APLICAÇÃO DOS FILTROS PERSONALIZADOS ---
    if pref_turno.upper() != "QUALQUER":
        turmas_uteis = turmas_uteis[turmas_uteis['Turno'].str.upper() == pref_turno.upper()]
        
    if pref_campus.upper() != "AMBOS":
        turmas_uteis = turmas_uteis[turmas_uteis['Campus'].str.upper() == pref_campus.upper()]

    if turmas_uteis.empty:
        print(f"⚠️ As matérias que você precisa até estão sendo ofertadas, mas NÃO no turno {pref_turno} ou campus {pref_campus}.")
        return pd.DataFrame()

    if 'Materia_Ideal' in turmas_uteis.columns:
        turmas_uteis['Nome'] = turmas_uteis['Materia_Ideal']
    else:
        turmas_uteis['Nome'] = "Disciplina UFABC"

    # --- IDENTIFICA O PESO DAS RECOMENDAÇÕES ---
    nome_coluna_peso = 'Peso' if 'Peso' in turmas_uteis.columns else ('Peso_y' if 'Peso_y' in turmas_uteis.columns else 'Peso_x')
    if nome_coluna_peso not in turmas_uteis.columns:
        turmas_uteis[nome_coluna_peso] = 1 # Fallback caso não tenha rodado o script de recomendações
        
    turmas_tentativas = turmas_uteis.sort_values(by=[nome_coluna_peso, 'Codigo'])

    # --- CALENDÁRIO COMPLETO UFABC ---
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
    horarios_ufabc = [
        "08:00-10:00", "10:00-12:00", 
        "14:00-16:00", "16:00-18:00", 
        "19:00-21:00", "21:00-23:00"
    ]
    
    calendario = {
        dia: {hora: {"I": None, "II": None} for hora in horarios_ufabc} 
        for dia in dias
    }

    grade_final = []
    materias_alocadas = set()

    for _, turma in turmas_tentativas.iterrows():
        codigo = turma['Codigo']
        dia = turma['Dia']
        horario = turma['Horario']
        quinzena = turma['Quinzena']
        
        if codigo in materias_alocadas and quinzena == "Semanal": 
            continue

        if dia not in calendario or horario not in calendario[dia]:
            continue 
            
        slot = calendario[dia][horario]
        pode_encaixar = False
        
        if quinzena == "Semanal":
            if slot["I"] is None and slot["II"] is None:
                pode_encaixar = True
                slot["I"] = codigo
                slot["II"] = codigo
        elif quinzena == "I":
            if slot["I"] is None:
                pode_encaixar = True
                slot["I"] = codigo
        elif quinzena == "II":
            if slot["II"] is None:
                pode_encaixar = True
                slot["II"] = codigo
                
        if pode_encaixar:
            grade_final.append(turma)
            materias_alocadas.add(codigo)

    df_grade_final = pd.DataFrame(grade_final)
    
    if not df_grade_final.empty:
        ordem_dias = {d: i for i, d in enumerate(dias)}
        df_grade_final['Dia_Num'] = df_grade_final['Dia'].map(ordem_dias)
        df_grade_final = df_grade_final.sort_values(by=['Dia_Num', 'Horario'])
        df_grade_final = df_grade_final.drop(columns=['Dia_Num', nome_coluna_peso])

    return df_grade_final

if __name__ == "__main__":
    # ====================================================================
    # ⚙️ PAINEL DE CONFIGURAÇÃO (Altere aqui de forma fácil)
    # ====================================================================
    arquivo_oferta_pdf = "ajuste_matriculas_2026_2_turmas_v2.pdf"
    arquivo_pendentes_csv = "materias_pendentes.csv"
    
    MEU_CAMPUS = "SA"       # Opções: "SBC", "SA" ou "AMBOS"
    MEU_TURNO = "Noturno"    # Opções: "Noturno", "Matutino", "Vespertino" ou "QUALQUER"
    # ====================================================================
    
    df_ofertas = extrair_turmas_ofertadas(arquivo_oferta_pdf)
    
    if not df_ofertas.empty:
        print(f"✅ O extrator mapeou {len(df_ofertas)} horários ofertados.")
        
        df_minha_grade = simular_montagem_grade(df_ofertas, arquivo_pendentes_csv, MEU_CAMPUS, MEU_TURNO)
        
        print("\n" + "="*70)
        print("🎓 SUA GRADE IDEAL MONTADA SEM CONFLITOS".center(70))
        print("="*70)
        
        if not df_minha_grade.empty:
            df_minha_grade.to_csv("minha_grade_perfeita.csv", index=False, encoding="utf-8")
            visualizacao = df_minha_grade[['Dia', 'Horario', 'Quinzena', 'Codigo', 'Nome', 'Campus', 'Turno']]
            print(visualizacao.to_string(index=False))
            print(f"\n✅ Grade salva no arquivo 'minha_grade_perfeita.csv'!")
        else:
            print(f"\n❌ Nenhuma matéria coube na sua grade para {MEU_TURNO} em {MEU_CAMPUS}.")
            print("   Dica: Altere as variáveis MEU_CAMPUS ou MEU_TURNO para 'AMBOS' ou 'QUALQUER'.")
    else:
        print("\n⚠️ O extrator não conseguiu ler as turmas.")