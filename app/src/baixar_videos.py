#!! CLASSE NÃO UTILIZADA

import os

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeFilename, InputMessagesFilterVideo

from src.utils import ColorLogger

load_dotenv()
logger = ColorLogger()

# Lendo as credenciais do Telegram do arquivo .env
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

PASTA_DOWNLOAD = os.path.join(os.path.dirname(__file__), "../videos_telegram")
NOME_DO_GRUPO = os.getenv("NOME_GRUPO_TELEGRAM")

# Caminho absoluto para o arquivo de sessão do Telegram
SESSION_FILE = os.path.join(os.path.dirname(__file__), "../sessao_telegram")


def baixar_videos_do_grupo():
    """
    Conecta-se a um grupo do Telegram e baixa todos os vídeos para uma pasta local.
    """
    if not all([API_ID, API_HASH]):
        logger.error("API_ID ou API_HASH do Telegram não encontrados no arquivo .env.")
        return

    if not os.path.exists(PASTA_DOWNLOAD):
        os.makedirs(PASTA_DOWNLOAD)
        logger.info(f"Pasta '{PASTA_DOWNLOAD}' criada com sucesso.")

    with TelegramClient(SESSION_FILE, API_ID, API_HASH) as client:
        logger.info("Conectado ao Telegram com sucesso!")

        try:
            # Encontra o grupo pelo nome
            # get_entity é a forma recomendada de obter informações sobre um chat
            entidade_grupo = client.get_entity(NOME_DO_GRUPO)
            logger.info(f"Grupo '{NOME_DO_GRUPO}' encontrado com sucesso.")

            logger.info("\nIniciando a busca por vídeos... Isso pode levar um tempo.")

            # Pega todas as mensagens que são vídeos do grupo
            mensagens = client.iter_messages(
                entidade_grupo, filter=InputMessagesFilterVideo
            )

            # Transforma o iterador em uma lista para poder contar o total
            lista_mensagens = list(mensagens)
            total_videos = len(lista_mensagens)

            if total_videos == 0:
                logger.info("Nenhum vídeo encontrado no grupo.")
                return

            logger.info(
                f"Total de {total_videos} vídeos encontrados. Iniciando o download."
            )

            # Itera sobre a lista e baixa cada vídeo
            for i, mensagem in enumerate(lista_mensagens):
                nome_arquivo = f"video_{mensagem.id}.mp4"  # Define um nome padrão
                # Itera sobre os atributos do documento de vídeo
                for atributo in mensagem.video.attributes:
                    # Se o atributo for do tipo 'DocumentAttributeFilename', pegamos o nome do arquivo
                    if isinstance(atributo, DocumentAttributeFilename):
                        nome_arquivo = atributo.file_name
                        break  # Encontramos o nome, podemos parar de procurar

                caminho_arquivo = os.path.join(PASTA_DOWNLOAD, nome_arquivo)

                logger.info(
                    f"\n[VÍDEO {i + 1}/{total_videos}] Baixando '{nome_arquivo}' (ID: {mensagem.id})..."
                )

                if os.path.exists(caminho_arquivo):
                    logger.info("...arquivo já existe, pulando.")
                    continue

                # A função de download do Telethon já exibe o progresso
                mensagem.download_media(file=caminho_arquivo)

            logger.info("\n--- Download de todos os vídeos concluído! ---")
            logger.info(f"Os vídeos foram salvos na pasta: '{PASTA_DOWNLOAD}'")

        except ValueError:
            logger.error(
                f"\nERRO: Não foi possível encontrar o grupo '{NOME_DO_GRUPO}'."
            )
            logger.error(
                "Verifique se o nome está escrito exatamente igual ao do Telegram."
            )
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado: {e}")
