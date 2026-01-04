import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from src.utils import ColorLogger
import subprocess

load_dotenv()
logger = ColorLogger()

# Lendo as credenciais do Telegram do arquivo .env
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
NOME_DO_GRUPO = os.getenv("NOME_GRUPO_TELEGRAM")

# Caminho absoluto para o arquivo de sessão do Telegram
SESSION_FILE = '/app/sessao_telegram'

def validar_arquivo_video(caminho_arquivo):
    """Valida se o arquivo existe e é um vídeo"""
    if not os.path.exists(caminho_arquivo):
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        return False

    extensoes_validas = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
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

    Args:
        caminho_video (str): Caminho completo para o arquivo de vídeo
        mensagem_caption (str): Legenda opcional para o vídeo
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

            # Nome do arquivo para exibição
            nome_arquivo = os.path.basename(caminho_video)
            logger.info(f"Iniciando upload do vídeo: {nome_arquivo}")
            logger.info("Isso pode levar alguns minutos dependendo do tamanho do arquivo...")

            # Faz o upload do vídeo
            mensagem_enviada = client.send_file(
                entity=entidade_grupo,
                file=caminho_video,
                caption=mensagem_caption if mensagem_caption else None
            )

            logger.info("✅ Vídeo enviado com sucesso!")
            logger.info(f"ID da mensagem: {mensagem_enviada.id}")
            logger.info(f"Data de envio: {mensagem_enviada.date}")

            return True

        except ValueError:
            logger.error(f"ERRO: Não foi possível encontrar o grupo '{NOME_DO_GRUPO}'.")
            logger.error("Verifique se o nome está escrito exatamente igual ao do Telegram.")
            return False
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado: {e}")
            return False

def subir_video_para_drive(source_folder, drive_remote, drive_folder):
    """
    Executa o comando rclone para mover a pasta local para o Google Drive.
    """
    command = ["rclone", "move", "--progress", source_folder, f"{drive_remote}:{drive_folder}"]
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
        print("\nErro: rclone não foi encontrado. Certifique-se de que ele está instalado e no seu PATH.")
