import sys
import os
import pandas as pd


MEU_HISTORICO_PDF = "historico_11202322044.pdf"
TURMAS_OFERTADAS_PDF = "ajuste_matriculas_2026_2_turmas_v2.pdf"

MEU_CAMPUS = "SA"       # Opções: "SBC", "SA" ou "AMBOS"
MEU_TURNO = "Noturno"   # Opções: "Noturno", "Matutino", "Vespertino" ou "QUALQUER"
MEU_LIMITE_CREDITOS = 22 # Limite da mochila! A UFABC recomenda entre 20 e 24.

GRADE_IDEAL_PDF = "data/ordem_do_dia_-_anexo_1b.pdf"
CATALOGO_PDF = "data/catalogo_disciplinas_graduacao_2024_2025.pdf"

PASTA_CSV = "OUTPUTS_CSV"
os.makedirs(PASTA_CSV, exist_ok=True) 

CSV_FEITAS = f"{PASTA_CSV}/materias_feitas.csv"
CSV_PENDENTES = f"{PASTA_CSV}/materias_pendentes.csv"
CSV_GRADE = f"{PASTA_CSV}/minha_grade_perfeita.csv"
PLANILHA_EXCEL = f"{PASTA_CSV}/Grade_Pronta_{MEU_TURNO}_{MEU_CAMPUS}.xlsx"


def iniciar_automacao():
    print("="*70)
    print("🚀 INICIANDO O GRADE MAKER UFABC 🚀".center(70))
    print("="*70)

    try:
        from scripts.extrair_historico import extrair_grade_perfeita
        from scripts.gerar_pendentes import extrair_grade_ideal, identificar_pendencias
        from scripts.avaliar_prioridades import extrair_recomendacoes_catalogo, classificar_pendencias
        from scripts.montar_grade import extrair_turmas_ofertadas, simular_montagem_grade
        
        try:
            from scripts.formatura_simulator import gerar_roadmap_formatura
        except ImportError:
            gerar_roadmap_formatura = None

        try:
            from scripts.gerar_visualizacao import criar_grade_visual
        except ImportError:
            from scripts.gerar_vizualizacao import criar_grade_visual
            
    except ImportError as e:
        print(f"\n❌ Erro de Importação na pasta 'scripts/'. Detalhe: {e}")
        sys.exit(1)

    print("\n[1/5] Extraindo seu histórico atualizado...")
    df_feitas = extrair_grade_perfeita(MEU_HISTORICO_PDF)
    if df_feitas.empty:
        print("❌ Falha ao extrair histórico.")
        return
    df_feitas.to_csv(CSV_FEITAS, index=False, encoding="utf-8")

    print("\n[2/5] Calculando disciplinas pendentes...")
    df_ideal = extrair_grade_ideal(GRADE_IDEAL_PDF)
    df_pendentes = identificar_pendencias(CSV_FEITAS, df_ideal)
    if df_pendentes.empty:
        print("✅ Você já concluiu todas as matérias! Abortando.")
        return
    df_pendentes.to_csv(CSV_PENDENTES, index=False, encoding="utf-8")

    print("\n[3/5] Analisando catálogo para definir prioridades...")
    mapa_recs = extrair_recomendacoes_catalogo(CATALOGO_PDF)
    df_prioridades = classificar_pendencias(CSV_PENDENTES, CSV_FEITAS, mapa_recs)
    df_prioridades.to_csv(CSV_PENDENTES, index=False, encoding="utf-8")

    if gerar_roadmap_formatura:
        gerar_roadmap_formatura(CSV_PENDENTES, CSV_FEITAS, CATALOGO_PDF)

    print(f"\n[4/5] Caçando ofertas ({MEU_TURNO} em {MEU_CAMPUS} | Max: {MEU_LIMITE_CREDITOS} Créditos)...")
    df_ofertas = extrair_turmas_ofertadas(TURMAS_OFERTADAS_PDF)
    df_minha_grade = simular_montagem_grade(df_ofertas, CSV_PENDENTES, MEU_CAMPUS, MEU_TURNO, MEU_LIMITE_CREDITOS)
    
    if df_minha_grade.empty:
        print("\n❌ Não foi possível montar uma grade válida com estes filtros.")
        return
    df_minha_grade.to_csv(CSV_GRADE, index=False, encoding="utf-8")

    print("\n" + "-"*65)
    print("🎒 RESUMO DA SUA MOCHILA DE MATÉRIAS".center(65))
    print("-"*65)
    
    materias_unicas = df_minha_grade.drop_duplicates(subset=["Codigo"])
    total_creditos = 0
    
    for _, row in materias_unicas.iterrows():
        codigo = row['Codigo']
        nome = str(row['Nome'])
        
        if len(nome) > 35: 
            nome = nome[:32] + "..." 
            
        creditos = int(row.get('Creditos', 4)) if pd.notnull(row.get('Creditos')) else 4
        total_creditos += creditos
        
        print(f"🔸 {codigo} | {nome:<35} | {creditos} Créditos")
        
    print("-"*65)
    print(f"✅ CARGA TOTAL ALOCADA: {total_creditos} / {MEU_LIMITE_CREDITOS} Créditos".center(65))
    print("-"*65)

    print("\n[5/5] Gerando arquivo Excel interativo...")
    criar_grade_visual(CSV_GRADE, PLANILHA_EXCEL)

    print("\n" + "="*70)
    print("🎉 SUCESSO ABSOLUTO! 🎉".center(70))
    print(f"CSVs e Planilha guardados na pasta: {PASTA_CSV}/".center(70))
    print("="*70)

if __name__ == "__main__":
    iniciar_automacao()