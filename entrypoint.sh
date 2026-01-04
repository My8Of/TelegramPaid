#!/bin/sh

echo "=== INICIANDO CONFIGURAÇÃO DO CONTAINER ==="
echo "Data/Hora: $(date)"
echo "Usuário atual: $(whoami)"
echo "UID/GID: $(id)"

# Verificar se foi passado argumento para modo de teste
if [ "$1" = "test" ]; then
    echo "🔍 MODO DE TESTE ATIVADO"
    TEST_MODE=true
else
    TEST_MODE=false
fi

echo "Capturando variáveis de ambiente..."
# Salvar variáveis de ambiente, excluindo algumas que podem causar problemas
printenv | grep -v "no_proxy" | grep -v "PWD" | grep -v "SHLVL" > /etc/environment

echo "Variáveis de ambiente capturadas em /etc/environment:"
echo "Número de variáveis salvas: $(wc -l < /etc/environment)"

echo "Mudando para o diretório /app"
cd /app

echo "Diretório atual: $(pwd)"
echo "Conteúdo do diretório /app:"
ls -la

# Verificar se os arquivos de sessão do Telegram existem e configurar permissões
echo "Verificando arquivos de sessão do Telegram..."
if [ -f "/app/sessao_telegram.session" ]; then
    echo "✅ Arquivo sessao_telegram.session encontrado"
    chmod 600 /app/sessao_telegram.session
    ls -la /app/sessao_telegram.session
else
    echo "⚠️  Arquivo sessao_telegram.session não encontrado"
    echo "   Isso é normal se for a primeira execução"
fi

if [ -f "/app/sessao_telegram.session-journal" ]; then
    echo "✅ Arquivo sessao_telegram.session-journal encontrado"
    chmod 600 /app/sessao_telegram.session-journal
    ls -la /app/sessao_telegram.session-journal
else
    echo "⚠️  Arquivo sessao_telegram.session-journal não encontrado"
fi

# Criar diretórios necessários se não existirem
echo "Verificando e criando diretórios necessários..."
mkdir -p /app/videos_brutos
mkdir -p /app/videos_processados
mkdir -p /app/videos_telegram
mkdir -p /app/banco_dados

echo "Diretórios criados/verificados:"
ls -ld /app/videos_* /app/banco_dados 2>/dev/null

# Verificar arquivo .env
if [ -f "/app/.env" ]; then
    echo "✅ Arquivo .env encontrado"
    echo "   Número de linhas: $(wc -l < /app/.env)"
else
    echo "❌ Arquivo .env não encontrado - isso pode causar problemas"
fi

# Verificar se o arquivo cronjob foi configurado corretamente
echo "Verificando configuração do cron..."
if crontab -l > /dev/null 2>&1; then
    echo "✅ Crontab configurado:"
    crontab -l | grep -v "^#" | grep -v "^$" || echo "   Nenhuma entrada ativa encontrada"
else
    echo "❌ Problema com crontab"
fi

# Verificar Python e módulos essenciais
echo "Verificando Python..."
python3 --version
echo "Módulos Python disponíveis (amostra):"
python3 -c "import sys; print('Telethon:', end=' '); import telethon; print('✅')" 2>/dev/null || echo "Telethon: ❌"
python3 -c "import sys; print('dotenv:', end=' '); import dotenv; print('✅')" 2>/dev/null || echo "dotenv: ❌"

# Se modo de teste, executar testes e sair
if [ "$TEST_MODE" = "true" ]; then
    echo "🧪 EXECUTANDO TESTES..."

    # Testar carregamento das variáveis de ambiente
    echo "Testando carregamento de variáveis de ambiente..."
    export $(cat /etc/environment | xargs) 2>/dev/null

    # Executar script de debug se existir
    if [ -f "/app/debug_cron.py" ]; then
        echo "Executando debug_cron.py..."
        python3 /app/debug_cron.py
        DEBUG_RESULT=$?
    else
        DEBUG_RESULT=0
    fi

    # Executar teste de sessão do Telegram se existir
    if [ -f "/app/test_telegram_session.py" ]; then
        echo "Executando test_telegram_session.py..."
        python3 /app/test_telegram_session.py
        TELEGRAM_RESULT=$?
    else
        TELEGRAM_RESULT=0
    fi

    # Executar verificação rápida do Telegram se existir
    if [ -f "/app/check_telegram.py" ]; then
        echo "Executando verificação rápida do Telegram..."
        python3 /app/check_telegram.py
        QUICK_TELEGRAM_RESULT=$?
    else
        QUICK_TELEGRAM_RESULT=0
    fi

    echo "=== RESULTADOS DOS TESTES ==="
    if [ $DEBUG_RESULT -eq 0 ]; then
        echo "✅ Debug geral: PASSOU"
    else
        echo "❌ Debug geral: FALHOU"
    fi

    if [ $TELEGRAM_RESULT -eq 0 ]; then
        echo "✅ Teste Telegram completo: PASSOU"
    else
        echo "❌ Teste Telegram completo: FALHOU"
    fi

    if [ $QUICK_TELEGRAM_RESULT -eq 0 ]; then
        echo "✅ Verificação rápida Telegram: PASSOU"
    else
        echo "❌ Verificação rápida Telegram: FALHOU"
    fi

    if [ $DEBUG_RESULT -eq 0 ] && [ $TELEGRAM_RESULT -eq 0 ] && [ $QUICK_TELEGRAM_RESULT -eq 0 ]; then
        echo "🎉 TODOS OS TESTES PASSARAM!"
        exit 0
    else
        echo "⚠️  ALGUNS TESTES FALHARAM"
        exit 1
    fi
fi

# Testar verificação rápida do Telegram antes de iniciar o cron
echo "Testando verificação rápida do Telegram..."
export $(cat /etc/environment | xargs) 2>/dev/null

if [ -f "/app/check_telegram.py" ]; then
    timeout 30 python3 /app/check_telegram.py > /tmp/telegram_test.log 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Verificação do Telegram passou"
    else
        echo "⚠️  Verificação do Telegram teve problemas - verifique /tmp/telegram_test.log"
        echo "Primeiras linhas do log:"
        head -10 /tmp/telegram_test.log 2>/dev/null || echo "Não foi possível ler o log"
    fi
else
    echo "ℹ️  Script de verificação rápida não encontrado, continuando..."
fi

# Testar uma execução do debug geral
echo "Testando debug geral..."
if [ -f "/app/debug_cron.py" ]; then
    timeout 20 python3 /app/debug_cron.py > /tmp/startup_test.log 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Teste de debug geral passou"
    else
        echo "⚠️  Teste de debug geral teve problemas - verifique /tmp/startup_test.log"
        echo "Primeiras linhas do log:"
        head -10 /tmp/startup_test.log 2>/dev/null || echo "Não foi possível ler o log"
    fi
else
    echo "ℹ️  Script de debug não encontrado, continuando..."
fi

echo "=== CONFIGURAÇÃO CONCLUÍDA ==="
echo "Iniciando o serviço cron em modo daemon..."

# Criar um script wrapper para garantir que o ambiente seja carregado
cat > /app/run_main.sh << 'EOF'
#!/bin/sh
cd /app
export $(cat /etc/environment | xargs) 2>/dev/null
exec python3 /app/main.py "$@"
EOF

chmod +x /app/run_main.sh

echo "Script wrapper criado: /app/run_main.sh"

# Executar cron em foreground para manter o container ativo
exec crond -f -d 8
