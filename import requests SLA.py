import requests
import re
import os
import webbrowser
from datetime import datetime

# ==================== CONFIGURAÇÕES ====================
COOKIE_NAVEGADOR = ""
CHAMADOS = """

"""
SALVAR_RATS = False      # True = Salva na pasta / False = Abre abas
GERAR_RESUMO = True     # True = Busca SLA/Detalhes e gera HTML
# ========================================================

print("===============================================")
print("     AUTOMATIZADOR ASSIST - MODO AVANÇADO      ")
print("===============================================")

# 1. VALIDAÇÃO COOKIE
if not COOKIE_NAVEGADOR or len(COOKIE_NAVEGADOR.strip()) < 10:
    seu_cookie = input("👉 Cole o seu PHPSESSID: ").strip()
else:
    seu_cookie = COOKIE_NAVEGADOR.strip()

# 2. VALIDAÇÃO CHAMADOS (LÓGICA APERFEIÇOADA)
if not CHAMADOS.strip():
    print("\n👉 A lista de chamados está vazia.")
    print("Cole os números abaixo e pressione ENTER duas vezes numa linha em branco para processar:")
    linhas = []
    while True:
        try:
            line = input()
            if not line.strip(): # Pressionar Enter em linha vazia para
                break
            linhas.append(line.strip())
        except EOFError:
            break
    texto_chamados = "\n".join(linhas)
else:
    texto_chamados = CHAMADOS.strip()

lista_chamados = re.findall(r'\d{11}', texto_chamados)

if not lista_chamados:
    print("\n❌ Nenhum chamado válido foi identificado. Encerrando.")
    exit()

dados = [{"chamado": c, "cliente": "N/A", "equipamento": "N/A", "sla": "N/A", "classe": "sla-normal", 
          "status_download": "Pendente", "link_os": "#", "pep": "N/A", "cidade": "N/A", "serial": "N/A", "segmento": "N/A"} 
         for c in lista_chamados]

# Preparar pastas
pasta_downloads = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Download RATs")
if SALVAR_RATS and not os.path.exists(pasta_downloads): os.makedirs(pasta_downloads)

headers = {"User-Agent": "Mozilla/5.0", "Cookie": f"PHPSESSID={seu_cookie}"}

# 3. LOOP DE PROCESSAMENTO
for i, item in enumerate(dados, 1):
    print(f"[{i}/{len(dados)}] Processando: {item['chamado']}")
    res = requests.post("https://assist.positivotecnologia.com.br/bin/at/pesq_os.php?executarQuery=TRUE&page=1", 
                        data={"atendimento_numOs": item['chamado']}, headers=headers)
    os_id_match = re.search(r'osAbertura_id=(\d+)', res.text)
    
    if os_id_match:
        os_id = os_id_match.group(1)
        item["link_os"] = f"https://assist.positivotecnologia.com.br/bin/at/comprovantes/gerarRatPdf.php?os_id={os_id}&mostraStatus=1"
        
        if GERAR_RESUMO:
            res_sla = requests.get(f"https://assist.positivotecnologia.com.br/bin/at/detalhes_painelSLA.php?os_id={os_id}", headers=headers)
            
            # Extração de campos
            def get_f(pattern, txt): 
                m = re.search(pattern, txt, re.IGNORECASE | re.DOTALL)
                return m.group(1).strip() if m else "N/A"
            
            item["cliente"] = get_f(r'Detentor:</th>\s*<td[^>]*>(.*?)</td>', res_sla.text)
            item["pep"] = get_f(r'PEP:</th>\s*<td[^>]*>(.*?)</td>', res_sla.text)
            item["cidade"] = get_f(r'Cidade/UF:</th>\s*<td[^>]*>(.*?)</td>', res_sla.text)
            item["serial"] = get_f(r'Serial:</th>\s*<td[^>]*>(.*?)</td>', res_sla.text)
            
            # Limpeza Modelo
            raw_mod = get_f(r'Modelo:</th>\s*<td[^>]*>(.*?)</td>', res_sla.text)
            item["equipamento"] = re.sub(r'H\d-\d{5}|(\(.*?\))', '', raw_mod).strip()
            
            # SLA
            data = re.search(r'Data Limite:</th>\s*<td[^>]*>(.*?)</td>', res_sla.text, re.IGNORECASE | re.DOTALL)
            if data:
                d_str = data.group(1).strip()
                try:
                    dt = datetime.strptime(d_str, "%d/%m/%Y %H:%M")
                    diff = (dt - datetime.now()).total_seconds() / 3600
                    venc = f"Vence: {d_str}"
                    if diff < 0: item["sla"], item["classe"] = f"❌ ESTOURADO (há {abs(int(diff))}h) - {venc}", "sla-critico"
                    elif diff <= 6: item["sla"], item["classe"] = f"⚠️ CRÍTICO ({int(diff)}h restantes) - {venc}", "sla-urgente"
                    else: item["sla"], item["classe"] = f"✅ OK ({int(diff)}h restantes) - {venc}", "sla-ok"
                except: item["sla"] = d_str

        # Download/Abertura
        if SALVAR_RATS:
            pdf = requests.get(item["link_os"], headers=headers)
            if pdf.status_code == 200 and b"%PDF" in pdf.content:
                with open(os.path.join(pasta_downloads, f"RAT_{item['chamado']}.pdf"), "wb") as f: f.write(pdf.content)
                item["status_download"] = "✅ Salvo"
            else: item["status_download"] = "❌ Erro"
        else:
            webbrowser.open(item["link_os"])
            item["status_download"] = "🌐 Aberto"
    else:
        item["status_download"] = "⚠️ Não encontrado"

# 4. GERAR HTML
if GERAR_RESUMO:
    html = """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
        body{font-family:sans-serif; background:#f4f4f4; padding:20px;} table{width:100%; border-collapse:collapse; background:white;}
        th,td{padding:10px; border:1px solid #ddd;} .sla-critico{color:red; font-weight:bold;} .sla-urgente{color:orange; font-weight:bold;} .sla-ok{color:green; font-weight:bold;}
        summary{cursor:pointer; font-weight:bold;} details p{margin:5px 0; color:#555; font-size:0.9em;}
    </style></head><body><h1>Painel SLA</h1><table>
    <tr><th>Chamado</th><th>Cliente</th><th>Equipamento</th><th>SLA</th><th>Ação</th></tr>"""
    for it in dados:
        html += f"""<tr><td><strong>{it['chamado']}</strong></td>
        <td><details><summary>{it['cliente']}</summary><p><b>Cidade:</b> {it['cidade']}<br><b>PEP:</b> {it['pep']}<br><b>Serial:</b> {it['serial']}</p></details></td>
        <td>{it['equipamento']}</td><td class='{it.get('classe')}'>{it['sla']}</td><td>{it['status_download']}</td></tr>"""
    html += "</table></body></html>"
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Painel_SLA.html")
    with open(caminho, "w", encoding="utf-8") as f: f.write(html)
    webbrowser.open(caminho)

print("\n🎉 Processo concluído!")