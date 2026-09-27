import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime

# Desactivar avisos de segurança SSL (comum no CGNA)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL_PORTAL = "https://portal.cgna.decea.mil.br/"
BASE_URL_DOWNLOAD = "https://portal.cgna.decea.mil.br/files/abas/{data}/painel_rpl/companhias/{ficheiro}"

# Ficheiros que o seu painel lê (index (2).html)
COMPANHIAS = [
    "Cia_TAM_CS.txt",
    "Cia_GLO_CS.txt",
    "Cia_AZU_CS.txt",
    "Cia_ACN_CS.txt"
]

def extrair_data_ciclo(html):
    """
    Procura a data no HTML da página principal.
    A imagem mostra: "RPL vigente em 27/09/2026".
    Vamos procurar este padrão ou padrões semelhantes de data.
    """
    # Procura por "RPL vigente em DD/MM/AAAA" ou "Edição DD/MM/AAAA a DD/MM/AAAA"
    # Este regex procura qualquer data no formato DD/MM/AAAA que apareça na página
    padrao_data = re.search(r'(\d{2}/\d{2}/\d{4})', html)
    
    if padrao_data:
        data_brasileira = padrao_data.group(1) # Extrai "24/09/2026"
        print(f"🔎 Data do ciclo encontrada no portal: {data_brasileira}")
        
        # O link do CGNA usa o formato internacional: AAAA-MM-DD
        data_obj = datetime.strptime(data_brasileira, "%d/%m/%Y")
        data_link = data_obj.strftime("%Y-%m-%d")
        return data_link
    return None

def actualizar_malha():
    print("A aceder ao portal do CGNA para localizar o ciclo actual...")
    try:
        resposta = requests.get(URL_PORTAL, verify=False, timeout=30)
        html_portal = resposta.text
    except Exception as e:
        print(f"❌ Falha ao carregar o portal: {e}")
        return

    data_ciclo = extrair_data_ciclo(html_portal)

    if not data_ciclo:
        print("❌ Não foi possível encontrar a data do ciclo na página principal.")
        # Pode tentar usar a data de hoje como fallback, caso o HTML tenha mudado
        data_ciclo = datetime.now().strftime("%Y-%m-%d")
        print(f"⚠️ A usar a data de hoje como tentativa: {data_ciclo}")

    # Faz o download de cada companhia
    for ficheiro in COMPANHIAS:
        url_download = BASE_URL_DOWNLOAD.format(data=data_ciclo, ficheiro=ficheiro)
        print(f"Baixando {ficheiro} de {url_download}...")
        
        try:
            res_ficheiro = requests.get(url_download, verify=False, timeout=30)
            
            if res_ficheiro.status_code == 200:
                with open(ficheiro, 'wb') as f: # Substitui o TXT antigo
                    f.write(res_ficheiro.content)
                print(f"✅ {ficheiro} descarregado com sucesso!")
            else:
                print(f"❌ Ficheiro não encontrado para esta data ({res_ficheiro.status_code}).")
                # Se falhar, pode ser que a data no URL seja diferente da data exibida no site
                # Ex: "vigente em 27/09" mas a pasta é "2026-09-24".
                
        except Exception as e:
            print(f"❌ Erro de ligação ao descarregar {ficheiro}: {e}")

if __name__ == "__main__":
    actualizar_malha()