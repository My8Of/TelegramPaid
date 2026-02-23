import logging
import os
import time

import tweepy

# Configuração do Logger conforme seu padrão
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_x_test():
    try:
        # Autenticação (Usando OAuth 1.0a para Post/Delete)
        auth = tweepy.OAuth1UserHandler(
            os.getenv("X_API_KEY"),
            os.getenv("X_API_SECRET"),
            os.getenv("X_ACCESS_TOKEN"),
            os.getenv("X_ACCESS_SECRET"),
        )
        api = tweepy.API(auth)
        client = tweepy.Client(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_SECRET"),
        )

        logger.info("Criando post de teste no X...")
        tweet = client.create_tweet(text="Teste de pipeline CI/CD - Forgejo")
        tweet_id = tweet.data["id"]
        logger.info(f"Post criado com ID: {tweet_id}")

        # Pequeno delay para a API processar
        time.sleep(5)

        logger.info(f"Removendo post {tweet_id}...")
        client.delete_tweet(id=tweet_id)
        logger.info("Post removido com sucesso.")

    except Exception as e:
        logger.error(f"Erro no ciclo do X: {e}")
        exit(1)  # Força o erro na esteira CI


if __name__ == "__main__":
    run_x_test()
