import requests
import re
import os
import webbrowser

# ==================== CONFIGURAÇÕES INICIAIS ====================
COOKIE_NAVEGADOR = ""

CHAMADOS = """
60006403741	ANTONIO VILELA JUNIOR PROFESSOR
60006403743	ANTONIO VILELA JUNIOR PROFESSOR
60006403746	ANTONIO VILELA JUNIOR PROFESSOR
70014820780	MUNIRA G ESTEVES *vence amanhã as 12:00*
60006405568	APM DA EE DA VILA OLIM
"""

SALVAR_RATS = False
# ================================================================

print("===============================================")
print("         BAIXADOR DE RATs - ASSIST             ")
print("===============================================")

# 1. VALIDAÇÃO DO COOKIE
if not COOKIE_NAVEGADOR or len(COOKIE_NAVEGADOR.strip()) < 10:
    seu_cookie = input("👉 Cole o seu PHPSESSID atual do navegador: ").strip()
else:
    seu_cookie = COOKIE_NAVEGADOR.strip()
    print("✓ Cookie carregado automaticamente a partir das configurações.")

# 2. VALIDAÇÃO DOS CHAMADOS
texto_chamados = ""

if not CHAMADOS.strip():
    print("\n👉 Cole ou digite a lista de chamados.")
    print("Pode conter nomes ou textos juntos, o sistema filtrará apenas os 11 números.")
    print("⚠️ IMPORTANTE: Quando terminar de colar, pressione ENTER numa linha EM BRANCO para iniciar:\n")
    
    linhas_chamados = []
    while True:
        linha = input()
        # CORREÇÃO AQUI: Mudança para a sintaxe padrão compatível com todas as versões
        linha_limpa = linha.strip()
        if not linha_limpa:
            break
        linhas_chamados.append(linha_limpa)
    texto_chamados = " ".join(linhas_chamados)
else:
    texto_chamados = CHAMADOS
    print("✓ Lista de chamados carregada automaticamente a partir das configurações.")

# Filtro inteligente: Extrai apenas sequências de exatamente 11 números
lista_chamados = re.findall(r'\d{11}', texto_chamados)

if not lista_chamados:
    print("\n❌ Nenhum chamado válido de 11 dígitos foi identificado. O programa foi encerrado.")
    exit()

# Configuração de pastas
pasta_do_script = os.path.dirname(os.path.abspath(__file__))
pasta_downloads = os.path.join(pasta_do_script, "Download RATs")

if SALVAR_RATS:
    if not os.path.exists(pasta_downloads):
        os.makedirs(pasta_downloads)
        print(f"📂 Nova pasta criada em: {pasta_downloads}")
    else:
        print(f"📂 Os ficheiros serão guardados na pasta existente: {pasta_downloads}")
else:
    print("🌐 Modo de visualização ativo: Os links serão abertos diretamente no seu navegador.")

print(f"🔍 Identificados {len(lista_chamados)} chamados para processamento.")
print("-" * 50)

url_busca = "https://assist.positivotecnologia.com.br/bin/at/pesq_os.php?executarQuery=TRUE&page=1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": f"PHPSESSID={seu_cookie}"
}

# 3. Execução do Loop de busca e download/abertura
for i, chamado in enumerate(lista_chamados, 1):
    print(f"[{i}/{len(lista_chamados)}] Processando chamado: {chamado}")
    
    payload = {
        "atendimento_numOs": chamado,
        "atendimento_NomeCli": "", "atendimento_CPF": "", "atendimento_NTC": "",
        "atendimento_IMEI": "", "atendimento_serialmec": "", "atendimento_LocGuarda": "",
        "eticket": "", "observacao": ""
    }
    
    try:
        response = requests.post(url_busca, data=payload, headers=headers)
        match = re.search(r'osAbertura_id=(\d+)', response.text)
        
        if match:
            os_id = match.group(1)
            url_pdf = f"https://assist.positivotecnologia.com.br/bin/at/comprovantes/gerarRatPdf.php?os_id={os_id}&mostraStatus=1"
            
            if SALVAR_RATS:
                print(f"   -> ID Interno {os_id} localizado. Descarregando PDF...")
                pdf_response = requests.get(url_pdf, headers=headers)
                
                if pdf_response.status_code == 200 and b"%PDF" in pdf_response.content:
                    nome_arquivo = f"RAT_{chamado}.pdf"
                    caminho_completo = os.path.join(pasta_downloads, nome_arquivo)
                    
                    with open(caminho_completo, "wb") as f:
                        f.write(pdf_response.content)
                    print(f"   ✓ Guardado com sucesso: Download RATs/{nome_arquivo}")
                else:
                    print(f"   ❌ Falha ao descarregar o ficheiro. A sessão pode ter expirado.")
            else:
                print(f"   -> ID Interno {os_id} localizado. A abrir no navegador...")
                webbrowser.open(url_pdf)
                print(f"   ✓ Link enviado para o navegador.")
                
        else:
            print(f"   ❌ Chamado não encontrado no sistema ASSIST.")
            
    except Exception as e:
        print(f"   ❌ Erro de conexão/comunicação: {e}")
        
    print("-" * 50)

print("\n🎉 Processo finalizado para todos os chamados listados!")