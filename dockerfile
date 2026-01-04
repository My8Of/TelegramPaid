FROM python:3.10-alpine

WORKDIR /app

# Instalar dependências do sistema
RUN apk update && \
    apk add --no-cache ffmpeg

RUN apk add --no-cache dos2unix


# Copiar e instalar dependências Python primeiro
COPY pyproject.toml .
RUN pip install .

# Copiar código fonte
COPY . .

# Converter arquivos para formato Unix
RUN dos2unix entrypoint.sh cronjob

# Configurar cron
COPY cronjob /etc/cron.d/cronjob
RUN chmod 0644 /etc/cron.d/cronjob && \
    crontab /etc/cron.d/cronjob && \
    touch /var/log/cron.log

# Configurar permissões do entrypoint
RUN chmod +x entrypoint.sh

# Criar diretórios necessários com permissões corretas
RUN mkdir -p /app/videos_brutos \
             /app/videos_processados \
             /app/videos_telegram \
             /app/banco_dados && \
    chmod 755 /app/videos_brutos \
              /app/videos_processados \
              /app/videos_telegram \
              /app/banco_dados

# Configurar permissões base da aplicação
RUN chown -R root:root /app && \
    chmod -R 755 /app && \
    chmod +x /app/*.py 2>/dev/null || true

# Configurar permissões específicas para arquivos de sessão do Telegram
# (se existirem - não falhará se não existirem)
RUN if [ -f "/app/sessao_telegram.session" ]; then \
        chmod 600 /app/sessao_telegram.session && \
        echo "Permissões configuradas para sessao_telegram.session"; \
    else \
        echo "Arquivo sessao_telegram.session não encontrado (normal na primeira execução)"; \
    fi

RUN if [ -f "/app/sessao_telegram.session-journal" ]; then \
        chmod 600 /app/sessao_telegram.session-journal && \
        echo "Permissões configuradas para sessao_telegram.session-journal"; \
    else \
        echo "Arquivo sessao_telegram.session-journal não encontrado (normal na primeira execução)"; \
    fi

# Garantir que scripts Python sejam executáveis
RUN chmod +x /app/main.py \
             /app/debug_cron.py \
             /app/test_telegram_session.py 2>/dev/null || true

# Configurar timezone (opcional, mas útil para logs)
ENV TZ=America/Sao_Paulo

ENTRYPOINT [ "/app/entrypoint.sh" ]
