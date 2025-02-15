from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

load_dotenv()

def setup_driver():
    download_path = os.getenv("DOWNLOAD_PATH")
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True
    })
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def login(driver):
    try:
        driver.get("https://www.nfse.gov.br/EmissorNacional/Login")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.NAME, "Inscricao"))
        ).send_keys(os.getenv("USERNAME"))
        
        driver.find_element(By.NAME, "Senha").send_keys(os.getenv("PASSWORD"))
        driver.find_element(By.TAG_NAME, "form").submit()

        time.sleep(1)
    except Exception as e:
        raise Exception(f"Erro no login: {e}")

def navigate_to_notas_emitidas(driver, page=1):
    try:
        driver.get(f"https://www.nfse.gov.br/EmissorNacional/Notas/Emitidas?pg={page}")

        time.sleep(3)
    except Exception as e:
        raise Exception(f"Erro ao navegar para 'Notas Emitidas': {e}")

def download_links_paginated(driver):
    page = 1
    while True:
        try:
            print(f"Processando página {page}...")

            no_records_element = driver.find_elements(By.CLASS_NAME, "sem-registros")
            if no_records_element:
                print("Nenhum registro encontrado. Finalizando o processo.")
                break

            download_links = driver.find_elements(
                By.XPATH, "//a[contains(@href, '/Download/NFSe') and @class='list-group-item']"
            )

            if download_links:
                for i, link in enumerate(download_links):
                    download_url = link.get_attribute('href')
                    driver.get(download_url)
                    print(f"Download {i + 1} concluído.")

                    time.sleep(1)
            else:
                print("Nenhum link de download encontrado.")
            
            page += 1
            navigate_to_notas_emitidas(driver, page)
        
        except Exception as e:
            raise Exception(f"Erro ao processar a página {page}: {e}")
            break

def main():
    driver = setup_driver()

    try:
        login(driver)
        navigate_to_notas_emitidas(driver)
        download_links_paginated(driver)
    except Exception as e:
        print(f"Erro no processo geral: {e}")
    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    main()
