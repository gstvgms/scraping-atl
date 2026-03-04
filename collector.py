"""
collector.py — Coleta posts do Instagram da APIB usando Instaloader com sessão persistente.

Na primeira execução: faz login com usuário/senha e salva a sessão em data/session.
Nas execuções seguintes: carrega a sessão salva (sem pedir login).
Se a sessão expirar: faz login novamente automaticamente.
"""

import time
import random
import logging
import os
from datetime import date
from pathlib import Path

import instaloader

from config import (
    INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD,
    TARGET_PROFILE, START_DATE, SESSION_FILE,
    SLEEP_MIN, SLEEP_MAX, RATE_LIMIT_SLEEP
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


def _criar_loader() -> instaloader.Instaloader:
    """Cria e configura uma instância do Instaloader."""
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )
    return L


def _fazer_login(L: instaloader.Instaloader) -> bool:
    """
    Tenta carregar sessão salva. Se não existir ou estiver expirada,
    faz login com usuário/senha e salva a nova sessão.
    Retorna True se autenticado com sucesso.
    """
    session_path = Path(SESSION_FILE)

    # Tenta carregar sessão existente
    if session_path.exists():
        try:
            L.load_session_from_file(INSTAGRAM_USERNAME, str(session_path))
            # Verifica se a sessão ainda é válida tentando acessar o próprio perfil
            instaloader.Profile.from_username(L.context, INSTAGRAM_USERNAME)
            log.info("Sessão carregada com sucesso: %s", SESSION_FILE)
            return True
        except Exception as e:
            log.warning("Sessão expirada ou inválida (%s). Fazendo novo login...", e)

    # Faz login com usuário e senha
    try:
        log.info("Fazendo login com usuário: %s", INSTAGRAM_USERNAME)
        L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        # Salva a sessão para uso futuro
        session_path.parent.mkdir(parents=True, exist_ok=True)
        L.save_session_to_file(str(session_path))
        log.info("Login realizado e sessão salva em: %s", SESSION_FILE)
        return True
    except instaloader.exceptions.BadCredentialsException:
        log.error("ERRO: Usuário ou senha incorretos. Verifique config.py.")
        return False
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        log.error("ERRO: A conta exige verificação em dois fatores. Desative o 2FA na conta do Instagram.")
        return False
    except instaloader.exceptions.ConnectionException as e:
        log.error("ERRO de conexão ao fazer login: %s", e)
        return False
    except Exception as e:
        log.error("ERRO inesperado ao fazer login: %s", e)
        return False


def run_collector(progress_callback=None):
    """
    Função principal de coleta. Orquestra login, iteração de posts e salvamento no banco.

    progress_callback: função opcional chamada com (count: int, info: str)
                       usada pela interface Streamlit para mostrar progresso.
    """
    init_db()
    start = date.fromisoformat(START_DATE)

    # Etapa 1: Criar loader e autenticar
    log.info("=== INICIANDO COLETA ===")
    if progress_callback:
        progress_callback(0, "Autenticando no Instagram...")

    L = _criar_loader()
    login_ok = _fazer_login(L)

    if not login_ok:
        log.error("Falha na autenticação. Encerrando coleta.")
        if progress_callback:
            progress_callback(0, "ERRO: Falha na autenticação. Verifique as credenciais.")
        return 0

    # Etapa 2: Carregar perfil
    if progress_callback:
        progress_callback(0, "Carregando perfil @apiboficial...")

    try:
        profile = instaloader.Profile.from_username(L.context, TARGET_PROFILE)
        log.info("Perfil carregado: @%s (%d posts no total)", TARGET_PROFILE, profile.mediacount)
    except instaloader.exceptions.ProfileNotExistsException:
        log.error("Perfil @%s não encontrado.", TARGET_PROFILE)
        if progress_callback:
            progress_callback(0, f"ERRO: Perfil @{TARGET_PROFILE} não encontrado.")
        return 0
    except Exception as e:
        log.error("Erro ao carregar perfil: %s", e)
        if progress_callback:
            progress_callback(0, f"ERRO ao carregar perfil: {e}")
        return 0

    # Etapa 3: Iterar posts
    count = 0
    ignorados = 0
    i = 0

    for post in profile.get_posts():
        try:
            i += 1
            post_date = post.date_utc.date()

            # Para quando chega em posts anteriores a START_DATE
            if post_date < start:
                log.info("Post de %s é anterior a %s. Encerrando coleta.", post_date, START_DATE)
                break

            if progress_callback:
                progress_callback(count, f"Processando post {i}: {post_date} ...")

            # Trata legenda None
            legenda = post.caption if post.caption else ""

            # Determina tipo do post
            if post.is_video:
                tipo = "Video"
            elif post.typename == "GraphSidecar":
                tipo = "Sidecar"
            else:
                tipo = "Photo"

            dados = {
                "shortcode": post.shortcode,
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "date": post_date.isoformat(),
                "caption": legenda,
                "likes": post.likes,
                "comments": post.comments,
                "post_type": tipo,
            }

            insert_post(dados)
            count += 1
            log.info("[%d] Post %s salvo: /p/%s/", i, post_date, post.shortcode)

            # Espera aleatória para evitar rate limiting
            sleep_time = random.uniform(SLEEP_MIN, SLEEP_MAX)
            time.sleep(sleep_time)

        except instaloader.exceptions.QueryReturnedBadRequestException:
            log.warning("Rate limit (BadRequest) no post %d. Aguardando %ds...", i, RATE_LIMIT_SLEEP)
            time.sleep(RATE_LIMIT_SLEEP)
            continue
        except instaloader.exceptions.TooManyRequestsException:
            log.warning("Rate limit (TooManyRequests) no post %d. Aguardando %ds...", i, RATE_LIMIT_SLEEP)
            time.sleep(RATE_LIMIT_SLEEP)
            continue

    log.info("=== COLETA FINALIZADA ===")
    log.info("Posts salvos: %d | Ignorados: %d | Total iterado: %d", count, ignorados, i)

    if progress_callback:
        progress_callback(count, f"Coleta finalizada! {count} posts salvos.")

    return count


if __name__ == "__main__":
    run_collector()

