import pandas as pd
import re
import os

def gerar_roadmap_formatura(csv_pendentes, csv_feitas, pdf_catalogo, output_csv="OUTPUTS_CSV/trilha_formatura.csv"):
    print("\n🔮 Iniciando a simulação do Roadmap de Formatura...")
    
    try:
        df_pendentes = pd.read_csv(csv_pendentes)
        df_feitas = pd.read_csv(csv_feitas)
    except FileNotFoundError:
        print("❌ Erro: CSVs não encontrados. Rode os passos iniciais primeiro.")
        return pd.DataFrame()

    # Guarda os nomes das matérias que você já fez em minúsculo para dar "match" nas recomendações
    feitas_nomes = set(df_feitas['Materia'].str.lower().tolist())

    # Tenta importar o extrator de recomendações que criamos no avaliar_prioridades.py
    try:
        from scripts.avaliar_prioridades import extrair_recomendacoes_catalogo
        mapa_recs = extrair_recomendacoes_catalogo(pdf_catalogo)
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível carregar as recomendações. Usando ordem padrão. ({e})")
        mapa_recs = {}

    pendentes = df_pendentes.to_dict('records')
    quadrimestres = []
    num_quad = 1
    
    # Limites logísticos
    max_materias_noturno = 5
    max_materias_misto = 6 # Misto aguenta uma carga maior

    while pendentes:
        # Define o perfil do Quadrimestre simulado
        if num_quad == 1:
            limite = max_materias_noturno
            nome_quad = "Quadrimestre 1 (Noturno)"
        else:
            limite = max_materias_misto
            nome_quad = f"Quadrimestre {num_quad} (Misto)"

        disponiveis = []
        
        # Procura quais matérias você já tem bagagem para fazer
        for mat in pendentes:
            codigo = mat['Codigo']
            recs = mapa_recs.get(codigo, [])
            
            atendidas = True
            for r in recs:
                r_limpa = re.sub(r"^(requisitos?|co-requisitos?|recomenda-se|disciplinas?):\s*", "", r, flags=re.IGNORECASE).strip().lower()
                # Se a recomendação não estiver na sua lista de feitas, a matéria fica trancada
                if not any(r_limpa in f or f in r_limpa for f in feitas_nomes):
                    atendidas = False
                    break
                    
            if atendidas:
                disponiveis.append(mat)

        # Sistema anti-travamento: Se o catálogo tiver um "tranca-grade" que a regex não pegou bem,
        # e nenhuma matéria ficar disponível, ele força a liberação das matérias do topo da lista
        if not disponiveis:
            disponiveis = pendentes[:limite]

        # Seleciona as matérias até o limite do quadrimestre
        escolhidas = disponiveis[:limite]

        # Injeta as OLs para completar a carga horária se você tiver poucas obrigatórias liberadas
        vagas_sobrando = limite - len(escolhidas)
        if pendentes: # Só adiciona OL se você ainda não estiver no final do curso
            for _ in range(vagas_sobrando):
                escolhidas.append({"Codigo": "OL", "Materia_Ideal": "Opção Limitada / Livre"})

        creditos_quad = 0
        
        for mat in escolhidas:
            # Na UFABC a média é 4 créditos por matéria (algumas 2, algumas 6)
            creditos = 4 
            creditos_quad += creditos
            
            nome_disciplina = mat.get('Materia_Ideal', mat.get('Nome', 'OL'))
            
            quadrimestres.append({
                "Quadrimestre": nome_quad,
                "Codigo": mat['Codigo'],
                "Disciplina": nome_disciplina,
                "Creditos_Estimados": creditos
            })
            
            # O pulo do gato: Adiciona a matéria na lista de "feitas" para que 
            # no próximo loop do quadrimestre ela destranque as cadeias seguintes!
            if mat['Codigo'] != "OL":
                pendentes.remove(mat)
                feitas_nomes.add(str(nome_disciplina).lower())

        # Adiciona uma linha de resumo do quadrimestre
        quadrimestres.append({
            "Quadrimestre": nome_quad,
            "Codigo": "---",
            "Disciplina": f"✅ TOTAL ESTIMADO: {creditos_quad} CRÉDITOS",
            "Creditos_Estimados": creditos_quad
        })

        num_quad += 1
        if num_quad > 20: # Trava de segurança para loop infinito
            break

    df_trilha = pd.DataFrame(quadrimestres)
    df_trilha.to_csv(output_csv, index=False, encoding="utf-8")
    
    print(f"✅ Roadmap completo gerado! Salvo em: {output_csv}")
    
    # Imprime os dois primeiros quadrimestres no terminal para você ter um gosto
    print("\n" + "="*60)
    print("🎓 PREVISÃO DOS SEUS PRÓXIMOS PASSOS".center(60))
    print("="*60)
    resumo = df_trilha[df_trilha['Quadrimestre'].str.contains("1 |2 ")]
    print(resumo[['Quadrimestre', 'Codigo', 'Disciplina']].to_string(index=False))
    print("="*60)
    
    return df_trilha

if __name__ == "__main__":
    gerar_roadmap_formatura(
        "OUTPUTS_CSV/materias_pendentes.csv", 
        "OUTPUTS_CSV/materias_feitas.csv", 
        "data/catalogo_disciplinas_graduacao_2024_2025.csv"
    )