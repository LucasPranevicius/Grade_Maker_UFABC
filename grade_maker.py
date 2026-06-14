import sys
import os
import pandas as pd

# ====================================================================
# ⚙️ PAINEL DE CONTROLO CENTRAL (Altera APENAS aqui a cada quadrimestre!)
# ====================================================================

# 1. Ficheiros Variáveis (Na raiz do projeto)
MEU_HISTORICO_PDF = "historico_11202322044.pdf"
TURMAS_OFERTADAS_PDF = "ajuste_matriculas_2026_2_turmas_v2.pdf"

# 2. Preferências Logísticas da Grade
MEU_CAMPUS = "SBC"       # Opções: "SBC", "SA" ou "AMBOS"
MEU_TURNO = "QUALQUER"    # Opções: "Noturno", "Matutino", "Vespertino" ou "QUALQUER"

# 3. Ficheiros Fixos (Dentro da pasta data/)
GRADE_IDEAL_PDF = "data/ordem_do_dia_-_anexo_1b.pdf"
CATALOGO_PDF = "data/catalogo_disciplinas_graduacao_2024_2025.pdf"

# ====================================================================
# 📂 CONFIGURAÇÃO DE PASTAS DE SAÍDA
# ====================================================================
PASTA_CSV = "OUTPUTS_CSV"
os.makedirs(PASTA_CSV, exist_ok=True)  # Cria a pasta automaticamente se não existir

# Caminhos dos ficheiros gerados com barras universais
CSV_FEITAS = f"{PASTA_CSV}/materias_feitas.csv"
CSV_PENDENTES = f"{PASTA_CSV}/materias_pendentes.csv"
CSV_GRADE = f"{PASTA_CSV}/minha_grade_perfeita.csv"
PLANILHA_EXCEL = f"{PASTA_CSV}/Grade_Pronta_{MEU_TURNO}_{MEU_CAMPUS}.xlsx"

# ====================================================================
# 🚀 MOTOR DE ORQUESTRAÇÃO (Não precisas de mexer daqui para baixo)
# ====================================================================

def iniciar_automacao():
    print("="*70)
    print("🚀 INICIANDO O GRADE MAKER UFABC 🚀".center(70))
    print("="*70)

    # Importando os módulos da pasta 'scripts'
    try:
        from scripts.extrair_historico import extrair_grade_perfeita
        from scripts.gerar_pendentes import extrair_grade_ideal, identificar_pendencias
        from scripts.avaliar_prioridades import extrair_recomendacoes_catalogo, classificar_pendencias
        from scripts.montar_grade import extrair_turmas_ofertadas, simular_montagem_grade
        from scripts.formatura_simulator import gerar_roadmap_formatura

        # Estratégia à prova de falhas para o nome do ficheiro de visualização (com S ou com Z)
        try:
            from scripts.gerar_visualizacao import criar_grade_visual
        except ImportError:
            from scripts.gerar_visualizacao import criar_grade_visual
            
    except ImportError as e:
        print(f"\n❌ Erro de Importação: O Python não encontrou um dos teus scripts na pasta 'scripts/'.")
        print(f"Detalhe do erro: {e}")
        sys.exit(1)

    # ---------------------------------------------------------
    # PASSO 1: Mapear o Histórico
    # ---------------------------------------------------------
    print("\n[1/5] A extrair o teu histórico atualizado...")
    df_feitas = extrair_grade_perfeita(MEU_HISTORICO_PDF)
    if df_feitas.empty:
        print("❌ Falha ao extrair histórico. Verifica o ficheiro.")
        return
    df_feitas.to_csv(CSV_FEITAS, index=False, encoding="utf-8")

    # ---------------------------------------------------------
    # PASSO 2: Cruzar com a Grade Ideal (Aeroespacial)
    # ---------------------------------------------------------
    print("\n[2/5] A calcular disciplinas pendentes para a tua formatura...")
    df_ideal = extrair_grade_ideal(GRADE_IDEAL_PDF)
    df_pendentes = identificar_pendencias(CSV_FEITAS, df_ideal)
    if df_pendentes.empty:
        print("✅ Já concluíste todas as matérias obrigatórias! A abortar montagem.")
        return
    df_pendentes.to_csv(CSV_PENDENTES, index=False, encoding="utf-8")

    # ---------------------------------------------------------
    # PASSO 3: Inteligência de Recomendações (Tranca-Grade)
    # ---------------------------------------------------------
    print("\n[3/5] A analisar catálogo para definir prioridades (Peso 1 e Peso 2)...")
    mapa_recs = extrair_recomendacoes_catalogo(CATALOGO_PDF)
    df_prioridades = classificar_pendencias(CSV_PENDENTES, CSV_FEITAS, mapa_recs)
    df_prioridades.to_csv(CSV_PENDENTES, index=False, encoding="utf-8")

    # ---------------------------------------------------------
    # PASSO 3.5: Planejamento de Longo Prazo (Roadmap Ideal)
    # ---------------------------------------------------------
    gerar_roadmap_formatura(CSV_PENDENTES, CSV_FEITAS, CATALOGO_PDF)

    # ---------------------------------------------------------
    # PASSO 4: Encaixe Guloso no Tabuleiro (Motor de Grade)
    # ---------------------------------------------------------
    print(f"\n[4/5] A caçar ofertas e a montar a grade ({MEU_TURNO} em {MEU_CAMPUS})...")
    df_ofertas = extrair_turmas_ofertadas(TURMAS_OFERTADAS_PDF)
    df_minha_grade = simular_montagem_grade(df_ofertas, CSV_PENDENTES, MEU_CAMPUS, MEU_TURNO)
    
    if df_minha_grade.empty:
        print("\n❌ Não foi possível montar uma grade válida com estes filtros.")
        return
    df_minha_grade.to_csv(CSV_GRADE, index=False, encoding="utf-8")

    # ---------------------------------------------------------
    # PASSO 5: Exportação Visual
    # ---------------------------------------------------------
    print("\n[5/5] A gerar ficheiro Excel interativo...")
    criar_grade_visual(CSV_GRADE, PLANILHA_EXCEL)

    print("\n" + "="*70)
    print("🎉 SUCESSO ABSOLUTO! 🎉".center(70))
    print(f"CSVs e Planilha guardados na pasta: {PASTA_CSV}/".center(70))
    print("="*70)

if __name__ == "__main__":
    iniciar_automacao()