import os
import time

import backoff
import tweepy
from dotenv import load_dotenv

from app.utils.logger import ColorLogger

logger = ColorLogger()
load_dotenv()

logger = ColorLogger()

# --- NOSSOS NOVOS HANDLERS DE LOG ---


def log_backoff_attempt(details):
    """
    Função de log a ser chamada pela biblioteca backoff a cada nova tentativa.
    """
    # Extrai informações úteis do dicionário 'details'
    tentativa = details["tries"]
    erro = details["exception"]
    delay = details["wait"]
    args_chamada = details["args"]

    logger.warning(
        f"BACKOFF: Tentativa nº {tentativa} falhou. "
        f"Erro: [{type(erro).__name__}: {erro}]. "
        f"Argumentos da chamada: {args_chamada}. "
        f"Nova tentativa em {delay:.1f} segundos."
    )


def log_giveup(details):
    """
    Função de log a ser chamada pela biblioteca backoff quando todas as tentativas falham.
    """
    tentativa = details["tries"]
    erro = details["exception"]
    args_chamada = details["args"]

    logger.critical(
        f"BACKOFF: A função falhou após {tentativa} tentativas e não tentará novamente (desistindo). "
        f"Erro final: [{type(erro).__name__}: {erro}]. "
        f"Argumentos da chamada: {args_chamada}."
    )


@backoff.on_exception(
    backoff.expo,  # Estratégia de backoff exponencial
    exception=tweepy.errors.TweepyException,  # Tupla de exceções que acionam a retentativa
    max_tries=3,  # Número máximo de tentativas
    jitter=backoff.full_jitter,  # Adiciona um fator aleatório ao delay (boa prática)
    on_backoff=log_backoff_attempt,
    on_giveup=log_giveup,
)
def postar_video_no_twitter(
    API_KEY,
    API_KEY_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET,
    caminho_do_video,
    texto_do_tweet,
):
    """
    Faz o upload de um vídeo (API v1.1) e o posta (API v2).

    :param caminho_do_video: O caminho completo para o arquivo de vídeo.
    :param texto_do_tweet: O texto que acompanhará o vídeo.
    :return: True se foi bem-sucedido, False caso contrário.
    """
    if not all([API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        logger.error(
            "Uma ou mais chaves da API do Twitter não foram encontradas no arquivo .env."
        )
        return False

    if not os.path.exists(caminho_do_video):
        logger.error(f"Arquivo de vídeo não encontrado em '{caminho_do_video}'")
        return False

    # ---- MUDANÇA PRINCIPAL AQUI ----
    # 1. Autenticação v1.1 para UPLOAD de mídia
    auth = tweepy.OAuth1UserHandler(
        API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
    )
    api_v1 = tweepy.API(auth)
    logger.info("Autenticado na API v1.1 para upload de mídia.")

    # 2. Cliente v2 para PUBLICAR o tweet
    client_v2 = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_KEY_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
    )
    logger.info("Cliente da API v2 criado para publicação.")
    # ---- FIM DA MUDANÇA ----

    logger.info(f"Iniciando upload do vídeo '{caminho_do_video}' via API v1.1...")
    media = api_v1.media_upload(
        filename=caminho_do_video, chunked=True, media_category="tweet_video"
    )
    logger.info("Upload do vídeo concluído. Aguardando processamento...")

    while media.processing_info["state"] == "pending":
        logger.info("Vídeo ainda está pendente, aguardando 10 segundos...")
        time.sleep(10)
        media = api_v1.get_media_status(media.media_id)

    if media.processing_info["state"] == "failed":
        logger.error(
            f"O processamento do vídeo pelo Twitter falhou: {media.processing_info['error']}"
        )
        return False

    logger.info("Vídeo processado com sucesso!")

    logger.info("Publicando o tweet via API v2...")
    # Usa o cliente v2 para criar o tweet, passando o ID da mídia
    client_v2.create_tweet(text=texto_do_tweet, media_ids=[media.media_id])

    logger.info("✅ SUCESSO! Vídeo postado no Twitter.")
    return True
