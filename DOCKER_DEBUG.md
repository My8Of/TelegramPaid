# Docker Debug Guide

Este documento fornece instruções para debugar e resolver problemas com o container Docker que executa a aplicação de integração com Telegram.

## Problema: Sessão do Telegram não acessível pelo Cron

### Sintomas
- O programa funciona quando executado manualmente
- Falha quando executado pelo cron com erro relacionado ao arquivo `sessao_telegram.session`

### Soluções Implementadas

#### 1. Caminhos Absolutos
Os arquivos `baixar_videos.py` e `subir_video.py` foram atualizados para usar caminhos absolutos:
```python
SESSION_FILE = '/app/sessao_telegram'
```

#### 2. Configuração Robusta do Cron
O arquivo `cronjob` foi melhorado com:
- Definição explícita de SHELL, PATH e HOME
- Carregamento correto das variáveis de ambiente
- Definição do diretório de trabalho

#### 3. Entrypoint Aprimorado
O `entrypoint.sh` agora:
- Verifica e configura permissões dos arquivos de sessão
- Cria diretórios necessários
- Valida a configuração antes de iniciar o cron
- Oferece modo de teste

#### 4. Scripts de Debug
Foram criados scripts para facilitar o troubleshooting:
- `debug_cron.py`: Verifica ambiente completo
- `test_telegram_session.py`: Testa especificamente a conexão com Telegram

## Como Usar

### 1. Build e Execução Normal
```bash
docker build -t magnet-stream-integrations .
docker run -d --name integrations magnet-stream-integrations
```

### 2. Modo de Teste
Para testar a configuração sem iniciar o cron:
```bash
docker run --rm magnet-stream-integrations test
```

### 3. Debug Interativo
Para acessar o container e debugar manualmente:
```bash
# Container em execução
docker exec -it integrations /bin/sh

# Container temporário para debug
docker run --rm -it magnet-stream-integrations /bin/sh
```

## Scripts de Debug Disponíveis

### debug_cron.py
Verifica todos os aspectos do ambiente:
```bash
python3 /app/debug_cron.py
```

### test_telegram_session.py
Testa especificamente a conexão com Telegram:
```bash
python3 /app/test_telegram_session.py
```

### Execução Manual do Script Principal
Para testar o script principal manualmente:
```bash
cd /app
export $(cat /etc/environment | xargs)
python3 main.py
```

## Checklist de Troubleshooting

### 1. Verificar Arquivos de Sessão
```bash
ls -la /app/sessao_telegram*
```
- Arquivos devem existir
- Permissões devem ser 600
- Tamanho deve ser > 0 bytes

### 2. Verificar Variáveis de Ambiente
```bash
cat /etc/environment | grep TELEGRAM
```
- TELEGRAM_API_ID deve estar definida
- TELEGRAM_API_HASH deve estar definida
- NOME_GRUPO_TELEGRAM deve estar definida

### 3. Verificar Crontab
```bash
crontab -l
```
- Deve mostrar a entrada configurada
- Verificar sintaxe do cronjob

### 4. Verificar Logs do Cron
```bash
tail -f /var/log/cron.log
```

### 5. Testar Python e Módulos
```bash
python3 -c "import telethon; print('Telethon OK')"
python3 -c "from dotenv import load_dotenv; print('dotenv OK')"
```

## Problemas Comuns e Soluções

### 1. "ModuleNotFoundError"
- **Causa**: Módulos Python não instalados corretamente
- **Solução**: Reconstruir imagem Docker, verificar pyproject.toml

### 2. "FileNotFoundError: sessao_telegram.session"
- **Causa**: Arquivo de sessão não encontrado ou sem permissão
- **Solução**: 
  1. Verificar se arquivo foi copiado para o container
  2. Executar `chmod 600 /app/sessao_telegram.session*`
  3. Re-autenticar se necessário

### 3. "ValueError: Could not find the input entity"
- **Causa**: Nome do grupo Telegram incorreto ou sem acesso
- **Solução**: Verificar NOME_GRUPO_TELEGRAM no .env

### 4. Cron não executa
- **Causa**: Variáveis de ambiente não carregadas
- **Solução**: Verificar se /etc/environment está populado

### 5. Permissões Negadas
- **Causa**: Container executando com usuário/permissões incorretas
- **Solução**: Verificar Dockerfile, comandos chown/chmod

## Logs e Monitoramento

### Logs do Container
```bash
docker logs integrations
```

### Logs do Cron
```bash
docker exec integrations tail -f /var/log/cron.log
```

### Logs da Aplicação
Os logs da aplicação são direcionados para stdout/stderr do container:
```bash
docker logs -f integrations
```

## Estrutura de Arquivos Importante

```
/app/
├── main.py                          # Script principal
├── debug_cron.py                    # Script de debug
├── test_telegram_session.py         # Teste de sessão Telegram
├── entrypoint.sh                    # Script de inicialização
├── cronjob                          # Configuração do cron
├── .env                             # Variáveis de ambiente
├── sessao_telegram.session          # Sessão do Telegram
├── sessao_telegram.session-journal  # Journal da sessão
├── src/                             # Código fonte
│   ├── baixar_videos.py
│   ├── subir_video.py
│   └── ...
├── videos_brutos/                   # Vídeos baixados
├── videos_processados/              # Vídeos processados
└── banco_dados/                     # Banco de dados
```

## Variáveis de Ambiente Necessárias

Certifique-se de que o arquivo `.env` contém:
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
NOME_GRUPO_TELEGRAM=@your_group
LINK_CANAL=your_channel_link
API_KEY=twitter_api_key
API_KEY_SECRET=twitter_api_secret
ACCESS_TOKEN=twitter_access_token
ACCESS_TOKEN_SECRET=twitter_access_secret
```

## Próximos Passos para Debug

1. Execute o modo de teste primeiro
2. Se o teste falhar, use os scripts de debug
3. Verifique logs detalhadamente
4. Teste componentes individualmente
5. Reconstrua a imagem se necessário

## Contato e Suporte

Para problemas persistentes:
1. Colete logs completos
2. Execute todos os scripts de debug
3. Documente os passos que levaram ao erro
4. Verifique se todas as variáveis de ambiente estão configuradas