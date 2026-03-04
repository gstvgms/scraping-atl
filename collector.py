# Módulo principal de coleta de posts do Instagram da APIB (@apiboficial)
# Utiliza a biblioteca instaloader para acessar os posts de forma autenticada

import instaloader
import time
import random
from datetime import date
from config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, TARGET_PROFILE, START_DATE, SLEEP_MIN, SLEEP_MAX
from database import init_db, insert_post


def run_collector(progress_callback=None):
    """
    Coleta posts do Instagram da APIB desde START_DATE definido em config.py.

    Parâmetros:
        progress_callback: função opcional para atualizar interface gráfica (Streamlit).
                           Será chamada com (count, post_date_str) a cada post coletado.

    Retorna:
        Número total de posts coletados nesta execução.
    """
    # Garante que o banco de dados e as tabelas existam
    init_db()

    # Inicializa o Instaloader sem salvar arquivos de mídia localmente
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    # Realiza login com a conta de pesquisa
    try:
        print(f"🔐 Realizando login como @{INSTAGRAM_USERNAME}...")
        loader.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print("✅ Login realizado com sucesso.")
    except instaloader.exceptions.BadCredentialsException:
        print("❌ Erro: usuário ou senha inválidos. Verifique config.py.")
        return 0
    except instaloader.exceptions.InvalidArgumentException as e:
        print(f"❌ Erro de argumento inválido no login: {e}")
        return 0
    except Exception as e:
        print(f"❌ Erro inesperado no login: {e}")
        return 0

    # Carrega o perfil alvo
    try:
        print(f"🔍 Carregando perfil @{TARGET_PROFILE}...")
        profile = instaloader.Profile.from_username(loader.context, TARGET_PROFILE)
        print(f"✅ Perfil carregado: {profile.full_name} ({profile.mediacount} posts no total)")
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"❌ Perfil @{TARGET_PROFILE} não encontrado.")
        return 0
    except Exception as e:
        print(f"❌ Erro ao carregar perfil: {e}")
        return 0

    # Define a data de início da coleta
    start = date.fromisoformat(START_DATE)
    count = 0

    print(f"\n📅 Iniciando coleta de posts a partir de {START_DATE}...\n")

    for post in profile.get_posts():
        try:
            post_date = post.date.date()

            # Para a coleta ao atingir um post anterior à data de início
            if post_date < start:
                print(f"⏹  Post de {post_date} é anterior a {START_DATE}. Coleta finalizada.")
                break

            # Monta o dicionário com os dados do post
            post_data = {
                "shortcode": post.shortcode,
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "date": post_date.isoformat(),
                "caption": post.caption or "",
                "likes": post.likes,
                "comments": post.comments,
                "post_type": post.typename,
            }

            # Insere o post no banco de dados (ignora se já existir)
            insert_post(post_data)
            count += 1
            print(f"[{count}] Post {post_date} coletado: {post_data['url']}")

            # Atualiza a interface gráfica, se houver callback
            if progress_callback:
                progress_callback(count, post_date.isoformat())

            # Pausa aleatória para evitar bloqueio por rate limiting do Instagram
            sleep_time = random.uniform(SLEEP_MIN, SLEEP_MAX)
            time.sleep(sleep_time)

        except instaloader.exceptions.ConnectionException as e:
            # Erro de conexão: aguarda e tenta o próximo post
            print(f"⚠️  Erro de conexão no post {post.shortcode}: {e}. Aguardando 30s...")
            time.sleep(30)
            continue
        except Exception as e:
            # Outros erros: registra e continua
            print(f"⚠️  Erro inesperado no post {getattr(post, 'shortcode', '?')}: {e}. Pulando...")
            continue

    # Resumo final da coleta
    print(f"\n✅ Coleta finalizada. Total: {count} posts coletados.")
    return count


if __name__ == "__main__":
    run_collector()
