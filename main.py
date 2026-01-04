import os
import random
import select
import sys
import traceback
from dotenv import load_dotenv
from random import randint
from datetime import date
from telethon.sync import TelegramClient


# Importando nossas funções e o logger
from src.utils import ColorLogger
from src.utils import VideoHashManager
from src.baixar_videos import baixar_videos_do_grupo
from src.editor_de_videos import cortar_video
from src.X_poster import postar_video_no_twitter
from src.subir_video import subir_video_para_telegram
from src.drive_maneger import DriveManeger
from src.cache_maneger import CacheManeger

import os


# Configuração inicial
load_dotenv()
logger = ColorLogger()

# Constantes do projeto
PASTA_DOWNLOADS = os.path.join(os.path.dirname(__file__), "videos_brutos")
PASTA_PROCESSADOS = os.path.join(os.path.dirname(__file__), "videos_processados")
NOME_GRUPO_TELEGRAM = os.getenv("NOME_GRUPO_TELEGRAM", "@Feet_Brasil_archive")
LINK_CANAL = os.getenv("LINK_CANAL")
DRIVE_REMOTE = "MeuDrive"
DRIVE_FOLDER = "36bc32ce5dae4cf7fe13d306ec977f36"
API_KEY = os.getenv("API_KEY")
API_KEY_SECRET = os.getenv("API_KEY_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")


if not all([NOME_GRUPO_TELEGRAM, LINK_CANAL, DRIVE_REMOTE, DRIVE_FOLDER, API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
    logger.error("Uma ou mais variáveis de configuração obrigatórias estão ausentes. Verifique seu .env e as constantes do script.")
    sys.exit(1)



def verificar_sessao_telegram_completa(logger=None):
    """
    Versão completa da verificação de sessão do Telegram.
    Pode ser usada tanto como função independente quanto integrada.
    """
    if logger is None:
        logger = ColorLogger()

    logger.info("=== TESTE DE CONFIGURAÇÃO DO TELEGRAM ===")

    # Carregar variáveis de ambiente
    load_dotenv()

    # Verificar variáveis de ambiente
    API_ID = os.getenv("TELEGRAM_API_ID")
    API_HASH = os.getenv("TELEGRAM_API_HASH")
    NOME_DO_GRUPO = os.getenv("NOME_GRUPO_TELEGRAM")

    logger.info("1. Verificando variáveis de ambiente...")

    if not API_ID:
        logger.error("❌ TELEGRAM_API_ID não encontrado")
        return False
    else:
        logger.info(f"✅ TELEGRAM_API_ID: {API_ID}")

    if not API_HASH:
        logger.error("❌ TELEGRAM_API_HASH não encontrado")
        return False
    else:
        logger.info(f"✅ TELEGRAM_API_HASH: {API_HASH[:10]}...")

    if not NOME_DO_GRUPO:
        logger.error("❌ NOME_GRUPO_TELEGRAM não encontrado")
        return False
    else:
        logger.info(f"✅ NOME_GRUPO_TELEGRAM: {NOME_DO_GRUPO}")

    # Verificar diretório atual
    logger.info(f"\n2. Diretório atual: {os.getcwd()}")

    # Verificar arquivos de sessão
    logger.info("\n3. Verificando arquivos de sessão...")
    session_file = 'sessao_telegram'
    session_file_with_ext = 'sessao_telegram.session'
    journal_file = 'sessao_telegram.session-journal'

    logger.info(f"Procurando por arquivos de sessão em {os.getcwd()}...")

    if os.path.exists(session_file_with_ext):
        logger.info(f"✅ Arquivo de sessão encontrado: {session_file_with_ext}")
        file_stats = os.stat(session_file_with_ext)
        logger.info(f"   Tamanho: {file_stats.st_size} bytes")
        logger.info(f"   Permissões: {oct(file_stats.st_mode)}")
    else:
        logger.warning(f"⚠️  Arquivo de sessão não encontrado: {session_file_with_ext}")

    if os.path.exists(journal_file):
        logger.info(f"✅ Arquivo journal encontrado: {journal_file}")
    else:
        logger.warning(f"⚠️  Arquivo journal não encontrado: {journal_file}")

    # Listar todos os arquivos em /app para debug
    logger.info(f"\n4. Listando arquivos em {os.getcwd()}:")
    try:
        for item in os.listdir(os.getcwd()):
            if 'session' in item.lower() or 'telegram' in item.lower():
                item_path = os.path.join(os.getcwd(), item)
                if os.path.isfile(item_path):
                    file_stats = os.stat(item_path)
                    logger.info(f"   📄 {item} ({file_stats.st_size} bytes, {oct(file_stats.st_mode)})")
                else:
                    logger.info(f"   📁 {item}")
    except Exception as e:
        logger.error(f"Erro ao listar {os.getcwd()}: {e}")

    # Tentar conectar ao Telegram
    logger.info("\n5. Testando conexão com o Telegram...")
    try:
        with TelegramClient(session_file, API_ID, API_HASH) as client:
            logger.info("✅ Conexão estabelecida com sucesso!")

            # Obter informações do usuário logado
            me = client.get_me()
            logger.info(f"   Usuário logado: {me.first_name} {me.last_name or ''} (@{me.username or 'sem_username'})")

            # Tentar encontrar o grupo
            logger.info(f"\n6. Tentando acessar o grupo '{NOME_DO_GRUPO}'...")
            try:
                entidade_grupo = client.get_entity(NOME_DO_GRUPO)
                logger.info(f"✅ Grupo encontrado: {entidade_grupo.title}")
                logger.info(f"   ID do grupo: {entidade_grupo.id}")
                logger.info(f"   Tipo: {type(entidade_grupo).__name__}")

                # Contar mensagens recentes
                message_count = 0
                for _ in client.iter_messages(entidade_grupo, limit=10):
                    message_count += 1

                logger.info(f"   Últimas mensagens acessíveis: {message_count}")

            except ValueError:
                logger.error(f"❌ Grupo '{NOME_DO_GRUPO}' não encontrado ou não acessível")
                logger.error("   Verifique se o nome está correto e se você tem acesso ao grupo")
                return False
            except Exception as e:
                logger.error(f"❌ Erro ao acessar grupo: {e}")
                return False

    except Exception as e:
        logger.error(f"❌ Erro na conexão com Telegram: {e}")
        logger.error("   Possíveis causas:")
        logger.error("   - Arquivo de sessão corrompido ou inacessível")
        logger.error("   - API_ID ou API_HASH incorretos")
        logger.error("   - Problemas de rede")
        return False

    logger.info("\n=== ✅ TODOS OS TESTES PASSARAM! ===")
    logger.info("A configuração do Telegram está funcionando corretamente.")
    return True

def rotina_upload():
    for video in os.listdir(PASTA_DOWNLOADS):
        caminho_video = os.path.join(PASTA_DOWNLOADS, video)
        if os.path.isfile(caminho_video) and video.endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')):
            subir_video_para_telegram(caminho_video)

def rotina_download_telegram():
    """Rotina 1: Baixa os vídeos do Telegram."""
    logger.info("--- INICIANDO ROTINA DE DOWNLOAD ---")
    baixar_videos_do_grupo()
    logger.info("--- ROTINA DE DOWNLOAD CONCLUÍDA ---")

def rotina_postagem():
    """Rotina 2: Escolhe um vídeo, corta e posta no X."""
    logger.info("--- INICIANDO ROTINA DE POSTAGEM ---")

    if not os.path.exists(PASTA_DOWNLOADS):
        logger.error(f"A pasta de downloads '{PASTA_DOWNLOADS}' não existe. Execute a rotina de download primeiro.")
        return

    if not os.path.exists(PASTA_PROCESSADOS):
        os.makedirs(PASTA_PROCESSADOS)
        logger.info(f"Pasta de vídeos processados '{PASTA_PROCESSADOS}' criada.")

    # 1. Escolher um vídeo aleatório que ainda não foi processado
    videos_disponiveis = [f for f in os.listdir(PASTA_DOWNLOADS) if f.endswith(('.mp4', '.mov', '.mkv'))]
    if not videos_disponiveis:
        logger.warning("Nenhum vídeo novo para processar na pasta de downloads.")
        return

    video_escolhido = random.choice(videos_disponiveis)
    caminho_video_original = os.path.join(PASTA_DOWNLOADS, video_escolhido)
    caminho_video_cortado = os.path.join(PASTA_DOWNLOADS, f"previa_temp_{randint(1, 100)}.mp4")

    logger.info(f"Vídeo aleatório selecionado: {video_escolhido}")

    # 2. Cortar o vídeo
    status_corte = cortar_video(caminho_video_original, caminho_video_cortado)

    if status_corte == 'SUCESSO':
        logger.info("Corte do vídeo bem-sucedido. Preparando para postar.")

        # 3. Postar o vídeo cortado no X
        texto_tweet = f"Novo video postado! 🔥\n\nPara ver o vídeo completo e muito mais, acesse nosso canal: {LINK_CANAL}"
        status_postagem = postar_video_no_twitter(API_KEY,API_KEY_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET,caminho_video_cortado, texto_tweet)

        if status_postagem:
            logger.info("Postagem no X concluída. Movendo vídeo original para processados.")
            # 4. Mover o vídeo original para a pasta de processados para não ser escolhido de novo
            os.rename(caminho_video_original, os.path.join(PASTA_PROCESSADOS, video_escolhido))
        else:
            logger.error("Falha ao postar no X. O vídeo original não será movido.")

        # 5. Limpar o arquivo de prévia temporário
        os.remove(caminho_video_cortado)

    elif status_corte == 'IGNORADO':
        logger.warning("O vídeo foi ignorado pela rotina de corte (curto demais). Movendo para processados.")
        os.rename(caminho_video_original, os.path.join(PASTA_PROCESSADOS, video_escolhido))
    else: # ERRO
        logger.error("Falha na rotina de corte. O processo para este vídeo foi abortado.")

    logger.info("--- ROTINA DE POSTAGEM CONCLUÍDA ---")

def rotina_sycn():
    logger.info("-------INICIANDO ROTINA DE TRASFERENCIA PARA O DRIVE-------")
    try:
        logger.info("Obfuscando titulos do video")
        VideoHashManager.processar_e_renomear_videos()
        logger.info("Trasferindo videos para o google drive")
        # move_rclone(PASTA_DOWNLOADS,DRIVE_REMOTE,DRIVE_FOLDER)
    except Exception as e:
        logger.error(f"Erro ao trasferir arquivos{e}")
    logger.info("-------ROTINA DE TRASFRENCIA FINALIZADA-------")

def rotina_baixar_drive(select_video_name = None):
    """
    Baixa um vídeo do Google Drive, tratando os seguintes casos:
    1. Se um nome de vídeo é especificado, baixa ele.
    2. Se não, baixa um vídeo aleatório que ainda não esteja no cache.
    3. Lida com erros como vídeo não encontrado ou todos os vídeos já baixados.
    """
    logger.info("-------INICIANDO ROTINA DE DOWNLOAD DO DRIVE---------")

    driver = DriveManeger()
    cache = CacheManeger(db=0)
    service = driver.authenticate_google_drive()
    video_list_drive = driver.find_videos_in_folder(service)

    if not video_list_drive:
        logger.warning("Nenhum vídeo foi encontrado na pasta do Drive. Encerrando.")
        logger.info("-------ROTINA DE DOWNLOAD FINALIZADA---------")
        return

    video_selecionado = None

    # CASO 1: Um nome de vídeo específico foi passado como parâmetro
    if select_video_name:
        logger.info(f"Buscando pelo vídeo específico: '{select_video_name}'")

        # Procura o objeto do vídeo na lista que veio do Drive
        for video_obj in video_list_drive:
            if video_obj['name'] == select_video_name:
                video_selecionado = video_obj
                break

        if not video_selecionado:
            logger.error(f"O vídeo '{select_video_name}' foi solicitado mas não encontrado no Drive. Encerrando.")
            logger.info("-------ROTINA DE DOWNLOAD FINALIZADA---------")
            return

    # CASO 2: Nenhum vídeo específico, vamos selecionar um aleatório e disponível
    else:
        logger.info("Buscando um vídeo aleatório que ainda não foi baixado...")

        # 1. Filtra a lista, removendo vídeos que já estão no cache.
        videos_disponiveis = [
            video for video in video_list_drive
            if not cache.get_data(video['name'])
        ]

        # Notificação por email se houver poucos vídeos
        if len(videos_disponiveis) < 3:
            logger.warning(f"Atenção: Existem menos de 3 vídeos disponíveis para serem baixados do Drive. Atualmente, há {len(videos_disponiveis)} vídeo(s) na fila.")

        # 2. Verifica se sobrou algum vídeo para baixar
        if not videos_disponiveis:
            logger.warning("Todos os vídeos da pasta do Drive já foram baixados. Nada a fazer.")
            logger.info("-------ROTINA DE DOWNLOAD FINALIZADA---------")
            return

        # 3. Escolhe aleatoriamente da lista de vídeos JÁ FILTRADA
        video_selecionado = random.choice(videos_disponiveis)

    # --- LÓGICA DE DOWNLOAD ---
    # Neste ponto, `video_selecionado` é garantidamente um objeto de vídeo válido para download.
    logger.info(f"Vídeo selecionado para download: {video_selecionado['name']} (ID: {video_selecionado['id']})")

    # Baixa o vídeo
    driver.download(service, video_selecionado, PASTA_DOWNLOADS)

    # Salva o nome do vídeo no cache para não baixá-lo novamente
    cache.set_data(video_selecionado['name'], f"Video baixado em {date.today()}")

    logger.info("-------ROTINA DE DOWNLOAD FINALIZADA---------")

if __name__ == "__main__":
    logger.info("🚀 INICIANDO APLICAÇÃO")
    try:
        # Primeiro, verificar se a sessão do Telegram está funcionando
        logger.info("Verificando configuração do Telegram antes de iniciar as rotinas...")

        if not verificar_sessao_telegram_completa():
            logger.error("❌ FALHA NA VERIFICAÇÃO DO TELEGRAM")
            logger.error("A aplicação não pode continuar sem uma sessão válida do Telegram.")
            logger.error("Verifique:")
            logger.error("  - Se o arquivo sessao_telegram.session existe e não está corrompido")
            logger.error("  - Se as variáveis TELEGRAM_API_ID e TELEGRAM_API_HASH estão corretas")
            logger.error("  - Se você tem acesso ao grupo configurado")
            logger.error("  - Se há conectividade com a internet")
            sys.exit(1)

        logger.info("✅ Verificação do Telegram passou! Iniciando rotinas...")

        # Baixa o video do drive
        rotina_baixar_drive(os.getenv("VIDEO"))
        logger.info("-------ROTINA DE DOWNLOAD FINALIZADO")
        # Faz o upload do video para o telegram
        rotina_upload()
        logger.info("-------ROTINA DE UPLOAD FINALIZADO")
        # Posta o video no X
        rotina_postagem()
        logger.info("-------ROTINA DE POSTAGEM FINALIZADO")

        logger.info("🎉 APLICAÇÃO FINALIZADA COM SUCESSO")

    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado na execução principal: {e}")
        # Captura o traceback completo
        tb_str = traceback.format_exc()

        # Log final antes de sair
        logger.error("A aplicação será encerrada.")
        sys.exit(1)
