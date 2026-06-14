import pandas as pd
import re

def gerar_roadmap_formatura(csv_pendentes, csv_feitas, pdf_catalogo, output_csv="OUTPUTS_CSV/trilha_formatura.csv"):
    print("\n🔮 Iniciando a simulação do Roadmap de Formatura...")
    
    try:
        df_pendentes = pd.read_csv(csv_pendentes)
        df_feitas = pd.read_csv(csv_feitas)
    except FileNotFoundError:
        print("❌ Erro: CSVs não encontrados. Rode os passos iniciais primeiro.")
        return pd.DataFrame()

    feitas_nomes = set(df_feitas['Materia'].str.lower().str.strip().tolist())

    try:
        from scripts.avaliar_prioridades import extrair_recomendacoes_catalogo
        mapa_recs = extrair_recomendacoes_catalogo(pdf_catalogo)
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível carregar as recomendações. Usando ordem padrão. ({e})")
        mapa_recs = {}

    pendentes = df_pendentes.to_dict('records')
    quadrimestres = []
    num_quad = 1
    
    max_materias_noturno = 5
    max_materias_misto = 6 

    while pendentes:
        if num_quad == 1:
            limite = max_materias_noturno
            nome_quad = "Quadrimestre 1 (Noturno)"
        else:
            limite = max_materias_misto
            nome_quad = f"Quadrimestre {num_quad} (Misto)"

        disponiveis = []
        
        for mat in pendentes:
            codigo = mat['Codigo']
            recs = mapa_recs.get(codigo, [])
            
            atendidas = True
            for r in recs:
                r_limpa = re.sub(r"^(requisitos?|co-requisitos?|recomenda-se|disciplinas?):\s*", "", r, flags=re.IGNORECASE).strip().lower()
                if not any(r_limpa in f or f in r_limpa for f in feitas_nomes):
                    atendidas = False
                    break
                    
            if atendidas:
                disponiveis.append(mat)

        if not disponiveis:
            disponiveis = pendentes[:limite]

        escolhidas = disponiveis[:limite]

        vagas_sobrando = limite - len(escolhidas)
        if pendentes: 
            for _ in range(vagas_sobrando):
                escolhidas.append({
                    "Codigo": "OL", 
                    "Materia_Ideal": "Opção Limitada / Livre", 
                    "Creditos": 4 # OL média
                })

        creditos_quad = 0
        
        for mat in escolhidas:
            # Agora puxamos o crédito REAL do PDF (ou 4 para as OLs geradas na hora)
            creditos = int(mat.get('Creditos', 4))
            creditos_quad += creditos
            
            nome_disciplina = mat.get('Materia_Ideal', mat.get('Nome', 'OL'))
            
            quadrimestres.append({
                "Quadrimestre": nome_quad,
                "Codigo": mat['Codigo'],
                "Disciplina": nome_disciplina,
                "Creditos": creditos
            })
            
            if mat['Codigo'] != "OL":
                pendentes.remove(mat)
                feitas_nomes.add(str(nome_disciplina).lower())

        quadrimestres.append({
            "Quadrimestre": nome_quad,
            "Codigo": "---",
            "Disciplina": f"✅ TOTAL ESTIMADO DO QUADRIMESTRE",
            "Creditos": creditos_quad
        })

        num_quad += 1
        if num_quad > 20: 
            break

    df_trilha = pd.DataFrame(quadrimestres)
    df_trilha.to_csv(output_csv, index=False, encoding="utf-8")
    
    print(f"✅ Roadmap completo gerado! Salvo em: {output_csv}")
    
    print("\n" + "="*60)
    print("🎓 PREVISÃO DOS SEUS PRÓXIMOS PASSOS".center(60))
    print("="*60)
    resumo = df_trilha[df_trilha['Quadrimestre'].str.contains("1 |2 ")]
    print(resumo[['Quadrimestre', 'Codigo', 'Disciplina', 'Creditos']].to_string(index=False))
    print("="*60)
    
    return df_trilha