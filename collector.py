"""
collector.py — Módulo de coleta de posts do Instagram da APIB usando Selenium.

Usa um navegador Chrome real para contornar captchas e verificações do Instagram.
O usuário pode intervir manualmente se necessário durante o login.
"""

import time
import random
import logging
from datetime import datetime, date
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD,
    TARGET_PROFILE, START_DATE, SLEEP_MIN, SLEEP_MAX
)
from database import init_db, insert_post

# Configuração de logs salvos em data/coleta.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/coleta.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def _criar_driver(headless: bool = False) -> webdriver.Chrome:
    """
    Cria e retorna uma instância do Chrome WebDriver.
    headless=False mantém a janela visível (necessário para resolver captcha).
    """
    opcoes = Options()
    if headless:
        opcoes.add_argument("--headless=new")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--disable-blink-features=AutomationControlled")
    opcoes.add_experimental_option("excludeSwitches", ["enable-automation"])
    opcoes.add_experimental_option("useAutomationExtension", False)
    opcoes.add_argument("--window-size=1280,900")
    # User-agent de navegador normal para evitar detecção
    opcoes.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servico, options=opcoes)
    # Remove propriedade webdriver do navigator para evitar detecção
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def _aguardar_login_completo(driver: webdriver.Chrome, timeout: int = 120) -> bool:
    """
    Aguarda o login ser concluído.
    Dá até `timeout` segundos para o usuário resolver captcha/verificação manualmente.
    Retorna True se o login foi bem-sucedido, False caso contrário.
    """
    log.info("Aguardando conclusão do login (máx. %d segundos)...", timeout)
    # URLs que indicam login ainda em progresso (aguardar)
    urls_aguardando = ["challenge", "checkpoint", "/login"]
    inicio = time.time()
    while time.time() - inicio < timeout:
        url_atual = driver.current_url
        # Login concluído: está no feed principal ou em etapa final aceitável
        parsed = urlparse(url_atual)
        is_instagram = parsed.hostname in ("instagram.com", "www.instagram.com")
        if is_instagram and not any(x in url_atual for x in urls_aguardando):
            log.info("Login concluído ou em etapa final: %s", url_atual)
            return True
        time.sleep(2)
    log.error("Tempo esgotado aguardando login.")
    return False


def _fazer_login(driver: webdriver.Chrome) -> bool:
    """
    Navega para o Instagram e realiza o login automático.
    Se aparecer captcha ou verificação, aguarda intervenção manual do usuário.
    """
    log.info("Acessando Instagram...")
    driver.get("https://www.instagram.com/")
    time.sleep(random.uniform(4, 6))

    try:
        # Aceitar cookies se o botão aparecer — textos em PT-BR e EN
        try:
            btn_cookies = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(text(),'Permitir') or contains(text(),'Allow') or "
                    "contains(text(),'Aceitar') or contains(text(),'Accept') or "
                    "contains(text(),'Accept All') or contains(text(),'Aceitar tudo')]"
                ))
            )
            btn_cookies.click()
            time.sleep(1)
        except TimeoutException:
            pass  # Botão de cookies não apareceu, tudo bem

        # Preencher usuário — tenta múltiplos seletores (Instagram muda com frequência)
        seletores_usuario = [
            "input[name='username']",
            "input[aria-label='Número de celular, nome de usuário ou email']",
            "input[aria-label='Phone number, username, or email']",
            "input[type='text']",
        ]

        campo_usuario = None
        for seletor in seletores_usuario:
            try:
                campo_usuario = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, seletor))
                )
                log.info("Campo de usuário encontrado com seletor: %s", seletor)
                break
            except TimeoutException:
                continue

        if campo_usuario is None:
            log.error("Não foi possível encontrar o campo de usuário após tentar todos os seletores.")
            return False

        # Clicar no campo antes de digitar
        campo_usuario.click()
        time.sleep(0.5)
        campo_usuario.clear()
        for caractere in INSTAGRAM_USERNAME:
            campo_usuario.send_keys(caractere)
            time.sleep(random.uniform(0.08, 0.18))

        time.sleep(random.uniform(0.5, 1.0))

        # Preencher senha — tenta múltiplos seletores
        seletores_senha = [
            "input[name='password']",
            "input[aria-label='Senha']",
            "input[aria-label='Password']",
            "input[type='password']",
        ]

        campo_senha = None
        for seletor in seletores_senha:
            try:
                campo_senha = driver.find_element(By.CSS_SELECTOR, seletor)
                log.info("Campo de senha encontrado com seletor: %s", seletor)
                break
            except NoSuchElementException:
                continue

        if campo_senha is None:
            log.error("Não foi possível encontrar o campo de senha.")
            return False

        campo_senha.click()
        time.sleep(0.5)
        campo_senha.clear()
        for caractere in INSTAGRAM_PASSWORD:
            campo_senha.send_keys(caractere)
            time.sleep(random.uniform(0.08, 0.18))

        # Clicar em entrar — tenta múltiplos seletores
        time.sleep(random.uniform(0.8, 1.5))
        try:
            btn_entrar = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            btn_entrar.click()
        except NoSuchElementException:
            try:
                # Fallback: botão com texto "Entrar" ou equivalente em inglês
                btn_entrar = driver.find_element(
                    By.XPATH,
                    "//button[contains(text(),'Entrar') or contains(text(),'Log in') or contains(text(),'Log In')]"
                )
                btn_entrar.click()
            except NoSuchElementException:
                log.error("Botão de login não encontrado.")
                return False

        log.info("Credenciais enviadas. Aguardando resposta do Instagram...")
        time.sleep(random.uniform(4, 6))

    except TimeoutException as e:
        log.error("Timeout ao tentar preencher formulário de login: %s", e)
        try:
            driver.save_screenshot("data/debug_login.png")
            log.info("Screenshot de debug salva em data/debug_login.png")
        except Exception:
            pass
        return False

    # Aguarda login completo (com possibilidade de resolução manual de captcha)
    return _aguardar_login_completo(driver, timeout=120)


def _coletar_links_do_perfil(driver: webdriver.Chrome, start_date: date, progress_callback=None) -> list:
    """
    Navega para o perfil da APIB e coleta todos os links de posts.
    Para de rolar quando detecta posts mais antigos que start_date.
    Retorna lista de URLs dos posts.
    """
    url_perfil = f"https://www.instagram.com/{TARGET_PROFILE}/"
    log.info("Navegando para o perfil: %s", url_perfil)
    driver.get(url_perfil)
    time.sleep(random.uniform(3, 5))

    links_coletados = set()
    rolagens_sem_novidade = 0
    max_rolagens_sem_novidade = 5  # Para de rolar após 5 rolagens sem novos posts
    deve_parar = False

    log.info("Iniciando coleta de links do perfil...")

    while not deve_parar:
        # Buscar todos os links de posts visíveis na página
        elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
        novos_encontrados = 0

        for elem in elementos:
            href = elem.get_attribute("href")
            if href and "/p/" in href and href not in links_coletados:
                links_coletados.add(href)
                novos_encontrados += 1

        if novos_encontrados == 0:
            rolagens_sem_novidade += 1
            if rolagens_sem_novidade >= max_rolagens_sem_novidade:
                log.info("Nenhum post novo após %d rolagens. Encerrando coleta de links.", max_rolagens_sem_novidade)
                break
        else:
            rolagens_sem_novidade = 0
            log.info("Total de links coletados até agora: %d", len(links_coletados))

        if progress_callback:
            progress_callback(len(links_coletados), "coletando links...")

        # Rolar para baixo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))

    log.info("Coleta de links finalizada. Total: %d links.", len(links_coletados))
    return list(links_coletados)


def _extrair_dados_do_post(driver: webdriver.Chrome, url: str) -> dict | None:
    """
    Abre um post específico e extrai: data, legenda, likes, comentários, tipo.
    Retorna um dicionário com os dados ou None se falhar.
    """
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))

        # Extrair shortcode da URL
        shortcode = url.rstrip("/").split("/p/")[-1].rstrip("/")

        # Extrair data de publicação
        data_post = None
        try:
            elem_data = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//time[@datetime]"))
            )
            datetime_str = elem_data.get_attribute("datetime")
            data_post = datetime.fromisoformat(datetime_str.replace("Z", "+00:00")).date()
        except (TimeoutException, ValueError):
            log.warning("Não foi possível extrair a data do post: %s", url)
            data_post = date.today()

        # Extrair legenda
        legenda = ""
        try:
            # Tenta expandir "mais" se existir
            try:
                btn_mais = driver.find_element(By.XPATH, "//button[contains(text(),'mais') or contains(text(),'more')]")
                btn_mais.click()
                time.sleep(0.5)
            except NoSuchElementException:
                pass

            elem_legenda = driver.find_element(
                By.XPATH, "//div[contains(@class,'_a9zs') or contains(@class,'C4VMK')]//span"
            )
            legenda = elem_legenda.text
        except NoSuchElementException:
            # Tenta seletor alternativo
            try:
                elem_legenda = driver.find_element(
                    By.XPATH, "//article//div[@role='button']//span"
                )
                legenda = elem_legenda.text
            except NoSuchElementException:
                legenda = ""

        # Extrair likes
        likes = 0
        try:
            texto_likes = driver.find_element(
                By.XPATH, "//section//span[contains(@class,'html-span')]//span"
            ).text
            likes = int(texto_likes.replace(",", "").replace(".", "").strip())
        except (NoSuchElementException, ValueError):
            likes = 0

        # Determinar tipo do post
        tipo = "Photo"
        try:
            driver.find_element(By.XPATH, "//video")
            tipo = "Video"
        except NoSuchElementException:
            pass
        try:
            driver.find_element(By.XPATH, "//*[contains(@aria-label,'Próximo') or contains(@aria-label,'Next')]")
            tipo = "Sidecar"
        except NoSuchElementException:
            pass

        return {
            "shortcode": shortcode,
            "url": url,
            "date": data_post.isoformat(),
            "caption": legenda,
            "likes": likes,
            "comments": 0,  # Comentários não são coletados para evitar muitas requisições
            "post_type": tipo,
        }

    except WebDriverException as e:
        log.error("Erro ao extrair dados do post %s: %s", url, e)
        return None


def run_collector(progress_callback=None):
    """
    Função principal de coleta. Orquestra login, coleta de links e extração de dados.

    progress_callback: função opcional chamada com (count: int, info: str)
                       usada pela interface Streamlit para mostrar progresso.
    """
    init_db()
    start = date.fromisoformat(START_DATE)
    driver = _criar_driver(headless=False)

    try:
        # Etapa 1: Login
        log.info("=== INICIANDO COLETA ===")
        if progress_callback:
            progress_callback(0, "Fazendo login no Instagram...")

        login_ok = _fazer_login(driver)
        if not login_ok:
            log.error("Falha no login. Encerrando coleta.")
            if progress_callback:
                progress_callback(0, "ERRO: Falha no login.")
            return 0

        # Etapa 2: Coletar links do perfil
        if progress_callback:
            progress_callback(0, "Coletando links dos posts...")

        links = _coletar_links_do_perfil(driver, start, progress_callback)

        if not links:
            log.warning("Nenhum link de post encontrado.")
            return 0

        # Etapa 3: Extrair dados de cada post
        count = 0
        ignorados = 0

        for i, url in enumerate(links, 1):
            if progress_callback:
                progress_callback(i, f"Processando post {i} de {len(links)}...")

            dados = _extrair_dados_do_post(driver, url)

            if dados is None:
                log.warning("Post ignorado (falha na extração): %s", url)
                ignorados += 1
                continue

            # Verificar se o post é mais antigo que START_DATE
            data_post = date.fromisoformat(dados["date"])
            if data_post < start:
                log.info("Post de %s é anterior a %s. Ignorando.", data_post, START_DATE)
                ignorados += 1
                continue

            insert_post(dados)
            count += 1
            log.info("[%d/%d] Post %s salvo: %s", i, len(links), dados["date"], url)

            # Espera aleatória entre posts para evitar bloqueio
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

        log.info("=== COLETA FINALIZADA ===")
        log.info("Posts salvos: %d | Ignorados: %d | Total processado: %d", count, ignorados, len(links))
        return count

    except Exception as e:
        log.error("Erro inesperado durante a coleta: %s", e)
        raise
    finally:
        driver.quit()
        log.info("Navegador fechado.")


if __name__ == "__main__":
    run_collector()
