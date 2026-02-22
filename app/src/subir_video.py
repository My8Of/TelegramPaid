import os
import random
import re
import subprocess

from dotenv import load_dotenv
from telethon import functions, types
from telethon.sync import TelegramClient

from app.src.editor_de_videos import cortar_video
from app.utils.logger import ColorLogger

load_dotenv()
logger = ColorLogger()

# Lendo as credenciais do Telegram do arquivo .env
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
NOME_DO_GRUPO = os.getenv("NOME_GRUPO_TELEGRAM")
NOME_DO_CANAL = os.getenv("NOME_CANAL_TELEGRAM")

# Caminho absoluto para o arquivo de sessão do Telegram
SESSION_FILE = "app/sessions/sessao_telegram.session"


def validar_arquivo_video(caminho_arquivo):
    """Valida se o arquivo existe e é um vídeo"""
    if not os.path.exists(caminho_arquivo):
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        return False

    extensoes_validas = [
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
    ]
    _, extensao = os.path.splitext(caminho_arquivo)

    if extensao.lower() not in extensoes_validas:
        logger.error(f"Formato de arquivo não suportado: {extensao}")
        logger.info(f"Formatos suportados: {', '.join(extensoes_validas)}")
        return False

    return True


def obter_tamanho_arquivo(caminho_arquivo):
    """Retorna o tamanho do arquivo em MB"""
    tamanho_bytes = os.path.getsize(caminho_arquivo)
    tamanho_mb = tamanho_bytes / (1024 * 1024)
    return tamanho_mb


def subir_video_para_telegram(caminho_video, mensagem_caption=""):
    """
    Conecta-se ao Telegram e faz upload de um vídeo para o grupo especificado.

    Suporta upload de Conteúdo Pago se o arquivo começar com 'paid_{valor}_'.
    Para conteúdo pago, gera e envia uma prévia antes do arquivo pago.
    """
    if not all([API_ID, API_HASH]):
        logger.error("API_ID ou API_HASH do Telegram não encontrados no arquivo .env.")
        return False

    if not validar_arquivo_video(caminho_video):
        return False

    # Verificar tamanho do arquivo (Telegram tem limite de 50MB para bots, 2GB para usuários)
    tamanho_mb = obter_tamanho_arquivo(caminho_video)
    logger.info(f"Tamanho do arquivo: {tamanho_mb:.2f} MB")

    if tamanho_mb > 2000:  # 2GB
        logger.error("Arquivo muito grande. O Telegram tem limite de 2GB para uploads.")
        return False

    with TelegramClient(SESSION_FILE, API_ID, API_HASH) as client:
        logger.info("Conectado ao Telegram com sucesso!")

        try:
            # Encontra o grupo pelo nome
            entidade_grupo = client.get_entity(NOME_DO_GRUPO)
            logger.info(f"Grupo '{NOME_DO_GRUPO}' encontrado com sucesso.")

            # Nome do arquivo para exibição e verificação de padrão
            nome_arquivo = os.path.basename(caminho_video)

            # Verificar se é conteúdo pago
            match_pago = re.match(r"^paid_(\d+)_", nome_arquivo)

            if match_pago:
                estrelas = int(match_pago.group(1))
                logger.info(f"💰 Conteúdo PAGO detectado! Valor: {estrelas} estrelas.")

                # Verificar se o canal está configurado
                if not NOME_DO_CANAL:
                    logger.error(
                        "NOME_CANAL_TELEGRAM não configurado no .env para mídia paga."
                    )
                    return False

                # Obter entidade do canal
                try:
                    entidade_canal = client.get_entity(NOME_DO_CANAL)
                    logger.info(f"Canal '{NOME_DO_CANAL}' encontrado com sucesso.")
                except ValueError:
                    logger.error(
                        f"ERRO: Não foi possível encontrar o canal '{NOME_DO_CANAL}'."
                    )
                    return False

                # --- UPLOAD DO CONTEÚDO PAGO NO CANAL ---
                logger.info(f"Iniciando upload do vídeo pago no CANAL: {nome_arquivo}")

                # Para mídia paga, precisamos fazer upload do arquivo primeiro para obter o handle
                logger.info("Fazendo upload do arquivo bruto...")
                arquivo_upload = client.upload_file(caminho_video)

                # Criar o InputMedia apropriado para o vídeo
                from telethon.utils import get_attributes

                atributos, mime_type = get_attributes(caminho_video)

                # Forçar supports_streaming=True para que o vídeo seja streamável
                for attr in atributos:
                    if isinstance(attr, types.DocumentAttributeVideo):
                        attr.supports_streaming = True

                input_media_video = types.InputMediaUploadedDocument(
                    file=arquivo_upload, mime_type=mime_type, attributes=atributos
                )

                logger.info("Enviando solicitação de Mídia Paga para o CANAL...")
                updates = client(
                    functions.messages.SendMediaRequest(
                        peer=entidade_canal,
                        media=types.InputMediaPaidMedia(
                            stars_amount=estrelas, extended_media=[input_media_video]
                        ),
                        message=mensagem_caption if mensagem_caption else "",
                    )
                )

                # Recuperar a mensagem enviada (para encaminhar depois)
                # Updates geralmente contém a lista de mensagens ou atualizações
                msg_id_canal = None
                for update in updates.updates:
                    if isinstance(update, types.UpdateNewChannelMessage):
                        msg_id_canal = update.message.id
                        break
                    elif isinstance(update, types.UpdateNewMessage):
                        msg_id_canal = update.message.id
                        break

                logger.info(
                    f"✅ Vídeo PAGO enviado para o CANAL com sucesso! ID: {msg_id_canal}"
                )

                # --- LÓGICA DE PRÉVIA NO GRUPO ---
                logger.info("Gerando prévia do vídeo pago para o GRUPO...")
                caminho_previa = os.path.join(
                    os.path.dirname(caminho_video),
                    f"previa_paid_{random.randint(1000, 9999)}.mp4",
                )

                status_corte = cortar_video(caminho_video, caminho_previa)

                if status_corte == "SUCESSO":
                    logger.info("Prévia gerada com sucesso. Enviando para o GRUPO...")
                    try:
                        client.send_file(
                            entity=entidade_grupo,
                            file=caminho_previa,
                            caption=f"👀 Prévia do Conteúdo Exclusivo ({estrelas} ⭐️)\n\nAdquira o vídeo completo abaixo! 👇",
                            supports_streaming=True,
                        )
                        logger.info("✅ Prévia enviada para o GRUPO com sucesso!")
                    except Exception as e:
                        logger.error(f"Erro ao enviar prévia: {e}")
                    finally:
                        # Limpar arquivo de prévia
                        if os.path.exists(caminho_previa):
                            os.remove(caminho_previa)
                else:
                    logger.warning(
                        f"Não foi possível gerar a prévia (Status: {status_corte}). Ignorando etapa de prévia."
                    )

                # --- ENCAMINHAR VÍDEO PAGO PARA O GRUPO ---
                if msg_id_canal:
                    logger.info("Encaminhando vídeo pago do Canal para o Grupo...")
                    try:
                        client.forward_messages(
                            entity=entidade_grupo,
                            messages=msg_id_canal,
                            from_peer=entidade_canal,
                        )
                        logger.info(
                            "✅ Vídeo pago encaminhado para o GRUPO com sucesso!"
                        )
                    except Exception as e:
                        logger.error(f"Erro ao encaminhar mensagem: {e}")
                else:
                    logger.error(
                        "Não foi possível identificar o ID da mensagem no canal para encaminhar."
                    )

            else:
                # Fluxo normal (GRATUITO)
                logger.info(f"Iniciando upload do vídeo (Gratuito): {nome_arquivo}")
                logger.info(
                    "Isso pode levar alguns minutos dependendo do tamanho do arquivo..."
                )

                # Faz o upload do vídeo
                mensagem_enviada = client.send_file(
                    entity=entidade_grupo,
                    file=caminho_video,
                    caption=mensagem_caption if mensagem_caption else None,
                    supports_streaming=True,
                )

                logger.info("✅ Vídeo enviado com sucesso!")
                logger.info(f"ID da mensagem: {mensagem_enviada.id}")
                logger.info(f"Data de envio: {mensagem_enviada.date}")

            return True

        except ValueError:
            logger.error(f"ERRO: Não foi possível encontrar o grupo '{NOME_DO_GRUPO}'.")
            logger.error(
                "Verifique se o nome está escrito exatamente igual ao do Telegram."
            )
            return False
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado: {e}")
            return False


def subir_video_para_drive(source_folder, drive_remote, drive_folder):
    """
    Executa o comando rclone para mover a pasta local para o Google Drive.
    """
    command = [
        "rclone",
        "move",
        "--progress",
        source_folder,
        f"{drive_remote}:{drive_folder}",
    ]
    print(f"\nIniciando o movimento dos arquivos com o rclone...")
    print(f"Comando: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print("\nMovimento concluído com sucesso!")
        print("Saída do rclone:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("\nErro no movimento do rclone.")
        print(f"Erro: {e.stderr}")
    except FileNotFoundError:
        print(
            "\nErro: rclone não foi encontrado. Certifique-se de que ele está instalado e no seu PATH."
        )
