import pdfplumber

arquivo = "historico_11202322044.pdf"

print("Lendo o formato bruto do PDF...\n")
print("-" * 50)

with pdfplumber.open(arquivo) as pdf:
    # Pega apenas a primeira página
    primeira_pagina = pdf.pages[2]
    
    # Extrai o texto do jeito que a máquina lê
    texto_bruto = primeira_pagina.extract_text()
    
    # Imprime os primeiros 1500 caracteres para não floodar sua tela
    print(texto_bruto[:50000000])
    
print("\n" + "-" * 50)