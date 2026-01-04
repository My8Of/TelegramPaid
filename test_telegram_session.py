#!/usr/bin/env python3
"""
Script de teste para verificar se a configuração do Telegram está funcionando corretamente.
Este script verifica:
1. Se as variáveis de ambiente estão configuradas
2. Se o arquivo de sessão está acessível
3. Se a conexão com o Telegram funciona
4. Se consegue acessar o grupo configurado
"""

import os
import sys
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from src.utils import ColorLogger

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
    session_file = '/app/sessao_telegram'
    session_file_with_ext = '/app/sessao_telegram.session'
    journal_file = '/app/sessao_telegram.session-journal'

    logger.info(f"Procurando por arquivos de sessão em /app/...")

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
    logger.info("\n4. Listando arquivos em /app:")
    try:
        for item in os.listdir('/app'):
            if 'session' in item.lower() or 'telegram' in item.lower():
                item_path = os.path.join('/app', item)
                if os.path.isfile(item_path):
                    file_stats = os.stat(item_path)
                    logger.info(f"   📄 {item} ({file_stats.st_size} bytes, {oct(file_stats.st_mode)})")
                else:
                    logger.info(f"   📁 {item}")
    except Exception as e:
        logger.error(f"Erro ao listar /app: {e}")

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

def main():
    """Função principal para execução independente do script"""
    success = verificar_sessao_telegram_completa()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
