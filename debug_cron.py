#!/usr/bin/env python3
"""
Script de debug para testar a execução no ambiente cron.
Este script verifica todas as condições necessárias para o funcionamento correto
do aplicativo quando executado pelo cron.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def log_with_timestamp(message):
    """Adiciona timestamp às mensagens de log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_environment():
    """Verifica o ambiente de execução"""
    log_with_timestamp("=== VERIFICAÇÃO DO AMBIENTE ===")

    # Diretório atual
    log_with_timestamp(f"Diretório atual: {os.getcwd()}")

    # Usuário atual
    try:
        user = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
        log_with_timestamp(f"Usuário: {user}")
    except:
        log_with_timestamp("Usuário: não determinado")

    # PATH
    path = os.getenv('PATH', '')
    log_with_timestamp(f"PATH: {path}")

    # Python executable
    log_with_timestamp(f"Python executable: {sys.executable}")
    log_with_timestamp(f"Python version: {sys.version}")

    return True

def check_files():
    """Verifica a existência de arquivos importantes"""
    log_with_timestamp("=== VERIFICAÇÃO DE ARQUIVOS ===")

    important_files = [
        '/app/main.py',
        '/app/.env',
        '/app/sessao_telegram.session',
        '/app/sessao_telegram.session-journal',
        '/app/pyproject.toml'
    ]

    all_files_ok = True

    for file_path in important_files:
        if os.path.exists(file_path):
            try:
                stat_info = os.stat(file_path)
                size = stat_info.st_size
                permissions = oct(stat_info.st_mode)
                log_with_timestamp(f"✅ {file_path} (tamanho: {size} bytes, permissões: {permissions})")
            except Exception as e:
                log_with_timestamp(f"⚠️ {file_path} existe mas erro ao obter informações: {e}")
        else:
            log_with_timestamp(f"❌ {file_path} não encontrado")
            if 'session' in file_path:
                # Arquivo de sessão pode não existir inicialmente, não é crítico
                all_files_ok = True
            else:
                all_files_ok = False

    return all_files_ok

def check_directories():
    """Verifica a existência de diretórios importantes"""
    log_with_timestamp("=== VERIFICAÇÃO DE DIRETÓRIOS ===")

    important_dirs = [
        '/app',
        '/app/src',
        '/app/videos_brutos',
        '/app/videos_processados',
        '/app/banco_dados'
    ]

    all_dirs_ok = True

    for dir_path in important_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                # Tentar listar o conteúdo para verificar permissões
                contents = os.listdir(dir_path)
                log_with_timestamp(f"✅ {dir_path} ({len(contents)} itens)")
            except PermissionError:
                log_with_timestamp(f"⚠️ {dir_path} existe mas sem permissão de leitura")
                all_dirs_ok = False
            except Exception as e:
                log_with_timestamp(f"⚠️ {dir_path} erro: {e}")
                all_dirs_ok = False
        else:
            log_with_timestamp(f"❌ {dir_path} não encontrado")
            all_dirs_ok = False

    return all_dirs_ok

def check_environment_variables():
    """Verifica variáveis de ambiente importantes"""
    log_with_timestamp("=== VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE ===")

    important_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
        'NOME_GRUPO_TELEGRAM',
        'LINK_CANAL',
        'API_KEY',
        'API_KEY_SECRET',
        'ACCESS_TOKEN',
        'ACCESS_TOKEN_SECRET'
    ]

    all_vars_ok = True

    for var in important_vars:
        value = os.getenv(var)
        if value:
            # Mascarar valores sensíveis
            if 'api' in var.lower() or 'secret' in var.lower() or 'token' in var.lower() or 'hash' in var.lower():
                masked_value = value[:5] + "*" * (len(value) - 5) if len(value) > 5 else "*" * len(value)
                log_with_timestamp(f"✅ {var}: {masked_value}")
            else:
                log_with_timestamp(f"✅ {var}: {value}")
        else:
            log_with_timestamp(f"❌ {var}: não definida")
            all_vars_ok = False

    return all_vars_ok

def check_python_modules():
    """Verifica se os módulos Python necessários estão disponíveis"""
    log_with_timestamp("=== VERIFICAÇÃO DE MÓDULOS PYTHON ===")

    required_modules = [
        'telethon',
        'dotenv',
        'requests',
        'tweepy',
        'PIL',
        'cv2',
        'redis'
    ]

    all_modules_ok = True

    for module in required_modules:
        try:
            if module == 'cv2':
                import cv2
                log_with_timestamp(f"✅ {module} (OpenCV): {cv2.__version__}")
            elif module == 'PIL':
                from PIL import Image
                log_with_timestamp(f"✅ {module} (Pillow): disponível")
            elif module == 'dotenv':
                from dotenv import load_dotenv
                log_with_timestamp(f"✅ {module}: disponível")
            else:
                imported_module = __import__(module)
                version = getattr(imported_module, '__version__', 'versão desconhecida')
                log_with_timestamp(f"✅ {module}: {version}")
        except ImportError as e:
            log_with_timestamp(f"❌ {module}: não disponível ({e})")
            all_modules_ok = False
        except Exception as e:
            log_with_timestamp(f"⚠️ {module}: erro na verificação ({e})")

    return all_modules_ok

def test_file_operations():
    """Testa operações básicas de arquivo"""
    log_with_timestamp("=== TESTE DE OPERAÇÕES DE ARQUIVO ===")

    test_file = '/app/test_cron_write.tmp'

    try:
        # Teste de escrita
        with open(test_file, 'w') as f:
            f.write("Teste de escrita do cron\n")
        log_with_timestamp("✅ Escrita de arquivo: OK")

        # Teste de leitura
        with open(test_file, 'r') as f:
            content = f.read()
        log_with_timestamp("✅ Leitura de arquivo: OK")

        # Cleanup
        os.remove(test_file)
        log_with_timestamp("✅ Remoção de arquivo: OK")

        return True

    except Exception as e:
        log_with_timestamp(f"❌ Erro em operações de arquivo: {e}")
        return False

def check_network():
    """Verifica conectividade de rede básica"""
    log_with_timestamp("=== VERIFICAÇÃO DE REDE ===")

    try:
        import urllib.request
        urllib.request.urlopen('https://api.telegram.org', timeout=10)
        log_with_timestamp("✅ Conectividade com Telegram API: OK")
        return True
    except Exception as e:
        log_with_timestamp(f"❌ Erro de conectividade: {e}")
        return False

def run_basic_import_test():
    """Testa importação básica dos módulos do projeto"""
    log_with_timestamp("=== TESTE DE IMPORTAÇÃO DO PROJETO ===")

    try:
        # Adicionar o diretório do projeto ao Python path
        sys.path.insert(0, '/app')

        from src.utils import ColorLogger
        log_with_timestamp("✅ src.utils.ColorLogger: OK")

        from src.baixar_videos import baixar_videos_do_grupo
        log_with_timestamp("✅ src.baixar_videos: OK")

        from src.subir_video import subir_video_para_telegram
        log_with_timestamp("✅ src.subir_video: OK")

        return True

    except Exception as e:
        log_with_timestamp(f"❌ Erro na importação do projeto: {e}")
        return False

def main():
    """Função principal do script de debug"""
    log_with_timestamp("🔍 INICIANDO DEBUG CRON")
    log_with_timestamp(f"Script executado em: {datetime.now()}")

    results = []

    results.append(("Ambiente", check_environment()))
    results.append(("Arquivos", check_files()))
    results.append(("Diretórios", check_directories()))
    results.append(("Variáveis de Ambiente", check_environment_variables()))
    results.append(("Módulos Python", check_python_modules()))
    results.append(("Operações de Arquivo", test_file_operations()))
    results.append(("Conectividade", check_network()))
    results.append(("Importações do Projeto", run_basic_import_test()))

    log_with_timestamp("=== RESUMO DOS TESTES ===")

    all_passed = True
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        log_with_timestamp(f"{test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        log_with_timestamp("🎉 TODOS OS TESTES PASSARAM! O ambiente está pronto.")
        return 0
    else:
        log_with_timestamp("⚠️ ALGUNS TESTES FALHARAM. Verifique os problemas acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
