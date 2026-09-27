import requests
import urllib3
import re
from datetime import datetime, timedelta

# Desactiva avisos de segurança SSL (comum no CGNA)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL_PORTAL = "https://portal.cgna.decea.mil.br/"
BASE_URL_DOWNLOAD = "https://portal.cgna.decea.mil.br/files/abas/{data}/painel_rpl/companhias/{ficheiro}"

COMPANHIAS = [
    "Cia_TAM_CS.txt",
    "Cia_GLO_CS.txt",
    "Cia_AZU_CS.txt",
    "Cia_ACN_CS.txt"
]

def extrair_data_ciclo(html):
    # Procura o formato de data DD/MM/AAAA no site
    padrao_data = re.search(r'(\d{2}/\d{2}/\d{4})', html)
    if padrao_data:
        return padrao_data.group(1)
    return None

def tentar_baixar(ficheiro, data_str):
    url_download = BASE_URL_DOWNLOAD.format(data=data_str, ficheiro=ficheiro)
    print(f"Testando URL: {url_download}")
    try:
        res = requests.get(url_download, verify=False, timeout=15)
        if res.status_code == 200:
            with open(ficheiro, 'wb') as f:
                f.write(res.content)
            print(f"✅ {ficheiro} descarregado com sucesso!")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Erro de ligação ao testar URL: {e}")
        return False

def atualizar_malha():
    print("A aceder ao portal do CGNA para localizar o ciclo actual...")
    try:
        resposta = requests.get(URL_PORTAL, verify=False, timeout=30)
        html_portal = resposta.text
    except Exception as e:
        print(f"❌ Falha ao carregar o portal: {e}")
        return

    data_brasileira = extrair_data_ciclo(html_portal)
    
    if not data_brasileira:
        print("❌ Data não encontrada no portal.")
        return

    print(f"🔎 Data de vigência (Domingo) encontrada: {data_brasileira}")
    data_vigencia = datetime.strptime(data_brasileira, "%d/%m/%Y")
    
    # A pasta real no CGNA costuma ser a Quinta-feira (-3 dias)
    data_pasta_provavel = data_vigencia - timedelta(days=3)
    
    for ficheiro in COMPANHIAS:
        # Primeiro, testa a data provável (-3 dias)
        data_str = data_pasta_provavel.strftime("%Y-%m-%d")
        sucesso = tentar_baixar(ficheiro, data_str)
        
        # Se o CGNA publicou noutro dia (ex: Sexta ou Quarta), o script faz uma varredura de segurança
        if not sucesso:
            print(f"⚠️ Pasta {data_str} não encontrada. A iniciar varredura de segurança para {ficheiro}...")
            # Testa todos os dias desde a data de vigência até 6 dias para trás
            for offset in range(0, 7):
                data_tentativa = (data_vigencia - timedelta(days=offset)).strftime("%Y-%m-%d")
                if tentar_baixar(ficheiro, data_tentativa):
                    break

if __name__ == "__main__":
    atualizar_malha()
