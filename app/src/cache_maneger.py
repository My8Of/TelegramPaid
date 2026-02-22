import os

import redis
from dotenv import load_dotenv

from .utils import ColorLogger

load_dotenv()
logger = ColorLogger("Redis manager")


class CacheManeger:
    """
    Uma classe para gerenciar a conexão e operações básicas com um banco de dados Redis.
    """

    def __init__(
        self,
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        db=os.getenv("REDIS_DB"),
    ):
        """
        Inicializa a conexão com o Redis.

        Args:
            host (str): O hostname do servidor Redis.
            port (int): A porta do servidor Redis.
            db (int): O número do banco de dados a ser usado.
        """
        if not all([os.getenv("REDIS_USER"), os.getenv("REDIS_PASSWORD")]):
            raise ValueError(
                "REDIS_USER e REDIS_PASSWORD não encontrados no arquivo .env"
            )
        self.host = host
        self.port = port
        self.db = db
        self.conn = None

        self._connect()

    def _connect(self):
        """Estabelece a conexão com o servidor Redis."""
        try:
            self.conn = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,  # Decodifica bytes para strings automaticamente
                username=os.getenv("REDIS_USER"),
                password=os.getenv("REDIS_PASSWORD"),
            )
            # Tenta uma operação simples para verificar a conexão
            self.conn.ping()
            logger.info("Conexão com o Redis estabelecida com sucesso!")
        except Exception as e:
            logger.error(f"Ocorreu um erro na conexão com o redis: {e}")
            self.conn = None

    def is_connected(self):
        """Verifica se a conexão com o Redis está ativa."""
        return self.conn is not None

    def set_data(self, key, value):
        """
        Salva um par de chave-valor no Redis.

        Args:
            key (str): A chave a ser usada.
            value (str): O valor a ser armazenado.

        Returns:
            bool: True se a operação for bem-sucedida, False caso contrário.
        """
        if not self.is_connected():
            return False

        try:
            self.conn.set(key, value)
            logger.info(f"Dados salvos: '{key}' -> '{value}'")
            return True
        except redis.exceptions.RedisError as e:
            logger.error(f"Erro ao salvar dados: {e}")
            return False

    def get_data(self, key):
        """
        Recupera um valor a partir de uma chave no Redis.

        Args:
            key (str): A chave a ser buscada.

        Returns:
            str: O valor associado à chave, ou None se não encontrado.
        """
        if not self.is_connected():
            return None

        try:
            value = self.conn.get(key)
            if value:
                logger.info(f"Dados encontrados: '{key}' -> '{value}'")
            else:
                logger.info(f"Nenhum dado encontrado para a chave '{key}'.")
            return value
        except redis.exceptions.RedisError as e:
            logger.error(f"Erro ao buscar dados: {e}")
            return None
