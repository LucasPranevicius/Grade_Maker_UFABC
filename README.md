# QuadriSync (Grade Maker UFABC)

O **QuadriSync** é um motor logístico e algoritmo de resolução de dependências desenvolvido para automatizar a montagem da grade horária ideal para os alunos de UFABC.

Cruzando o seu histórico, projeto pedagógico e as turmas ofertadas, o sistema resolve conflitos de horários, respeita limites de créditos e prioriza matérias estrategicamente **(focando primeiro em completar as matérias obrigatórias do Bacharelado Interdiscplinar).** O resultado final é exportado como uma planilha em Excel.

---

## 1. Pré-requisitos e Instação

Antes de rodar o projeto, você precisa ter o **Python 3** instalado em sua máquina e baixar as bibliotecas necessárias.

Abra o terminal (ou o terminal do VS code/PyCharm) na pasta raiz do projeto e execute o comando abaixo.

```bash
pip install pandas numpy PyMuPDF pdfplumber openpyxl
```

## 2. Estrutura do Projeto (Onde mexer e onde **NÃO** mexer)

Para o algoritmo funcionar, a organização das pastas deve ser rigorosamente esta:
```
📦 QuadriSync
 ┣ 📂 data/                    👉 (NÃO MEXER) PDFs oficiais (Catálogo e Projeto Pedagógico).
 ┣ 📂 scripts/                 👉 (NÃO MEXER) O "motor" do sistema.
 ┃ ┣ 📜 __init__.py            # Arquivo obrigatório para o Python ler a pasta.
 ┃ ┣ 📜 extrair_historico.py   # Motor Híbrido de leitura do seu histórico.
 ┃ ┣ 📜 gerar_pendentes.py     # Cruzamento de dados com o anexo 1b.
 ┃ ┣ 📜 avaliar_prioridades.py # Ditador de Hierarquia (BCT > Comum > Específica).
 ┃ ┣ 📜 montar_grade.py        # Algoritmo guloso e restrição de mochila.
 ┃ ┗ 📜 gerar_visualizacao.py  # Exportador para Excel (.xlsx).
 ┣ 📂 OUTPUTS_CSV/             👉 (GERADO AUTOMATICAMENTE) Onde sua grade pronta vai aparecer.
 ┣ 📜 historico.pdf            👉 (VOCÊ ATUALIZA) Seu histórico baixado do SIGAA.
 ┣ 📜 turmas_ofertadas.pdf     👉 (VOCÊ ATUALIZA) PDF com as turmas do quadrimestre.
 ┗ 📜 grade_maker.py           👉 (ÚNICO ARQUIVO QUE VOCÊ VAI EDITAR) O Maestro do projeto.
```

### Regra de Ouro
**NUNCA altere nenhum arquivo da pasta ```scripts/```. Eles contêm lógicas complexas de extração de tabelas, fallback de falhas de PDF e validação de matriz de horários. Mexer ali pode corromper a alocação de créditos.

## 3. Como configurar (O Painel de Controle)

Você só precisa interagir com um único arquivo: ```grade_maker.py```.
Abra este arquivo e olhe as linhas iniciais. É o seu **Painel de Controle**. A cada novo qadrimestre, você só precisa atualizar estas variáveis:

```bash
# 1. Arquivos Variáveis
MEU_HISTORICO_PDF = "historico_seu_ra_aqui.pdf"
TURMAS_OFERTADAS_PDF = "ajuste_matriculas_2026_2_turmas.pdf"

# 2. Preferências Logísticas da Grade
MEU_CAMPUS = "SBC"       # Opções: "SBC", "SA" ou "AMBOS"
MEU_TURNO = "QUALQUER"   # Opções: "Noturno", "Matutino", "Vespertino" ou "QUALQUER"
MEU_LIMITE_CREDITOS = 22 # Limite de peso da sua "Mochila".
```

## 4. Passo a Passo de Uso 

1. **Baixe seu histórico:** Vá no SIGAA, gere o seu histórico atualizado em PDF e jogue na pasta raiz do projeto.
2. **Baixe as ofertas de matrícula:** Coloque o PDF oficial de turmas ofertadas da UFABC na mesma pasta.
3. **Configure:** Abra o ```Grade_maker.py``` e coloque os nomes exatos dos PDF's que você acabou de baixar no Painel de Controle, além de escolher seu campus e turno de preferência.
4. **Rode o código**
5. **Acompanhe o resultado:** O terminal vai te mostrar um log passo a passo. No final, ele exibirá um resumo da sua **Mochila de Matérias**, listando exatamente quais disciplinas couberam na sua grade e a soma total dos créditos alocados.
6. **Pegue sua Grade:** Vá na pasta ```OUTPUTS_CSV/```. Lá dentro haverá um arquivo chamado ```Grade_Pronta_turno_campus.xlsx```. Nele estará sua semana mapeada.

---

**Se a sua grade sair com poucas matérias, é porque as disciplinas de maior prioridade que você precisa estão sofrendo conflito de horários entre si ou não foram ofertadas no campus/turno que você filtrou**
