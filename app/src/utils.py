import csv
import hashlib
import logging
import os

import colorlog


class ColorLogger:
    def __init__(self, name="minha_app"):
        # 1. Pega o logger e evita adicionar handlers duplicados em recargas
        self.log = logging.getLogger(name)
        self.log.setLevel(logging.DEBUG)  # Define o nível de log mais baixo

        # Se o logger já tiver handlers, limpe-os para evitar logs duplicados
        if self.log.hasHandlers():
            self.log.handlers.clear()

        # 2. Cria um handler do colorlog
        handler = colorlog.StreamHandler()

        # 3. Cria um formatter com cores
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )

        # 4. CONFIGURAÇÃO ESSENCIAL QUE FALTAVA
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

        # 5. A SOLUÇÃO: Desativa a propagação para o logger raiz
        self.log.propagate = False

    # 6. MÉTODOS PARA FAZER O LOG
    def info(self, message):
        self.log.info(message)

    def warning(self, message):
        self.log.warning(message)

    def error(self, message):
        self.log.error(message)

    def debug(self, message):
        self.log.debug(message)

    def critical(self, message):
        self.log.critical(message)


class VideoHashManager:
    """
    Classe para gerenciar hashes de títulos de vídeos e salvar em CSV.
    """

    def __init__(
        self, pasta_videos, pasta_banco="banco_dados", nome_csv="mapeamento_titulos.csv"
    ):
        """
        Inicializa o gerenciador de hashes de vídeos.

        Args:
            pasta_videos (str): Caminho para a pasta contendo os vídeos
            pasta_banco (str): Pasta onde será salvo o arquivo CSV
            nome_csv (str): Nome do arquivo CSV
        """
        self.pasta_videos = pasta_videos
        self.pasta_banco = pasta_banco
        self.arquivo_csv = os.path.join(pasta_banco, nome_csv)
        self.logger = ColorLogger("VideoHashManager")

        # Criar pasta do banco se não existir
        if not os.path.exists(pasta_banco):
            os.makedirs(pasta_banco)
            self.logger.info(f"Pasta '{pasta_banco}' criada com sucesso.")

    def gerar_hash_md5(self, texto):
        """
        Gera hash MD5 de um texto.

        Args:
            texto (str): Texto para gerar o hash

        Returns:
            str: Hash MD5 em hexadecimal
        """
        return hashlib.md5(texto.encode("utf-8")).hexdigest()

    def carregar_csv_existente(self):
        """
        Carrega dados existentes do CSV.

        Returns:
            dict: Dicionário com os dados existentes
        """
        dados = {}
        if os.path.exists(self.arquivo_csv):
            try:
                with open(self.arquivo_csv, "r", encoding="utf-8") as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        dados[row["titulo_original"]] = {
                            "hash_md5": row["hash_md5"],
                            "nome_arquivo_original": row["nome_arquivo_original"],
                            "nome_arquivo_hash": row["nome_arquivo_hash"],
                        }
                self.logger.info(
                    f"CSV existente carregado: {len(dados)} registros encontrados."
                )
            except Exception as e:
                self.logger.error(f"Erro ao carregar CSV: {e}")
        return dados

    def salvar_no_csv(self, dados):
        """
        Salva dados no CSV.

        Args:
            dados (dict): Dicionário com os dados a serem salvos
        """
        try:
            with open(self.arquivo_csv, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "titulo_original",
                        "hash_md5",
                        "nome_arquivo_original",
                        "nome_arquivo_hash",
                    ]
                )
                for titulo, info in dados.items():
                    writer.writerow(
                        [
                            titulo,
                            info["hash_md5"],
                            info["nome_arquivo_original"],
                            info["nome_arquivo_hash"],
                        ]
                    )
            self.logger.info(f"Dados salvos no CSV: {self.arquivo_csv}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")

    def processar_e_renomear_videos(self):
        """
        Processa todos os vídeos da pasta, gera hashes, salva no CSV e renomeia os arquivos.

        Returns:
            dict: Dicionário com todos os dados processados
        """
        if not os.path.exists(self.pasta_videos):
            self.logger.error(f"Pasta '{self.pasta_videos}' não encontrada.")
            return {}

        # Carregar dados existentes
        dados_existentes = self.carregar_csv_existente()
        dados_novos = {}

        # Extensões de vídeo suportadas
        extensoes_video = [
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
        ]

        # Listar arquivos na pasta
        arquivos = [
            f
            for f in os.listdir(self.pasta_videos)
            if os.path.isfile(os.path.join(self.pasta_videos, f))
            and any(f.lower().endswith(ext) for ext in extensoes_video)
        ]

        if not arquivos:
            self.logger.warning(
                f"Nenhum arquivo de vídeo encontrado na pasta '{self.pasta_videos}'."
            )
            return dados_existentes

        self.logger.info(
            f"Encontrados {len(arquivos)} arquivos de vídeo para processar."
        )

        # Processar cada arquivo
        for i, nome_arquivo in enumerate(arquivos, 1):
            # Obter nome base e extensão
            nome_base, extensao = os.path.splitext(nome_arquivo)

            # Verificar se já existe no CSV
            if nome_base in dados_existentes:
                self.logger.info(
                    f"[{i}/{len(arquivos)}] '{nome_arquivo}' já existe no banco de dados."
                )
                continue

            # Gerar hash MD5 do nome
            hash_md5 = self.gerar_hash_md5(nome_base)
            nome_hash = f"{hash_md5}{extensao}"

            dados_novos[nome_base] = {
                "hash_md5": hash_md5,
                "nome_arquivo_original": nome_arquivo,
                "nome_arquivo_hash": nome_hash,
            }

            self.logger.info(
                f"[{i}/{len(arquivos)}] Processado: '{nome_arquivo}' -> '{nome_hash}'"
            )

        # Combinar dados existentes com novos
        dados_completos = {**dados_existentes, **dados_novos}

        # Salvar no CSV se houver novos dados
        if dados_novos:
            self.salvar_no_csv(dados_completos)
            self.logger.info(
                f"Processamento concluído: {len(dados_novos)} novos registros adicionados."
            )

            # Renomear arquivos para hash
            arquivos_renomeados = 0
            for titulo_base, info in dados_novos.items():
                nome_original = info["nome_arquivo_original"]
                nome_hash = info["nome_arquivo_hash"]

                caminho_original = os.path.join(self.pasta_videos, nome_original)
                caminho_hash = os.path.join(self.pasta_videos, nome_hash)

                if os.path.exists(caminho_original) and not os.path.exists(
                    caminho_hash
                ):
                    try:
                        os.rename(caminho_original, caminho_hash)
                        self.logger.info(
                            f"Renomeado: '{nome_original}' -> '{nome_hash}'"
                        )
                        arquivos_renomeados += 1
                    except Exception as e:
                        self.logger.error(f"Erro ao renomear '{nome_original}': {e}")
                elif os.path.exists(caminho_hash):
                    self.logger.info(f"Arquivo já renomeado: '{nome_hash}'")
                else:
                    self.logger.warning(f"Arquivo não encontrado: '{nome_original}'")

            self.logger.info(
                f"Renomeação concluída: {arquivos_renomeados} arquivos renomeados."
            )
        else:
            self.logger.info("Nenhum novo arquivo para processar.")

        return dados_completos
