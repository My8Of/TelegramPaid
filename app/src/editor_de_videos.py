import json
import os
import subprocess

from app.utils.logger import ColorLogger  # Usando o logger personalizado

logger = ColorLogger()


def get_video_duration(caminho_video):
    """
    Usa o ffprobe para obter a duração de um vídeo em segundos.
    """
    comando_ffprobe = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        caminho_video,
    ]
    try:
        # --- CORREÇÃO APLICADA AQUI ---
        # Removido o parâmetro "text=True"
        resultado = subprocess.run(comando_ffprobe, check=True, capture_output=True)
        # Agora, resultado.stdout é garantidamente um objeto de BYTES
        stdout_bytes = resultado.stdout

        # O resto do seu código agora funcionará perfeitamente
        try:
            logger.debug("Tentando decodificar a saída do ffprobe como UTF-8...")
            json_string = stdout_bytes.decode("utf-8")

        except UnicodeDecodeError:
            logger.warning(
                f"Falha ao decodificar a saída do ffprobe como UTF-8 para o vídeo '{caminho_video}'. "
                "Usando 'latin-1' como fallback."
            )
            json_string = stdout_bytes.decode("latin-1")

        metadata = json.loads(json_string)

        if "format" in metadata and "duration" in metadata["format"]:
            return float(metadata["format"]["duration"])
        elif (
            "streams" in metadata
            and len(metadata["streams"]) > 0
            and "duration" in metadata["streams"][0]
        ):
            return float(metadata["streams"][0]["duration"])
        else:
            logger.warning(
                "Não foi possível encontrar a informação de duração no metadata do vídeo."
            )
            return None

    except Exception as e:
        logger.error(f"Falha ao obter a duração do vídeo com ffprobe: {e}")
        return None


def cortar_video(
    caminho_entrada,
    caminho_saida,
    inicio_corte_segundos=120,
    duracao_corte_segundos=120,
):
    """
    Verifica a duração de um vídeo e, se for maior que 5 minutos,
    corta um trecho de 2 minutos começando no segundo minuto.

    :param caminho_entrada: Caminho completo para o vídeo original.
    :param caminho_saida: Caminho onde o vídeo cortado será salvo.
    :param inicio_corte_segundos: Ponto de início do corte em segundos (padrão: 120s).
    :param duracao_corte_segundos: Duração do corte em segundos (padrão: 120s).
    :return: 'SUCESSO', 'IGNORADO' ou 'ERRO'.
    """
    if not os.path.exists(caminho_entrada):
        logger.error(f"Arquivo de entrada não encontrado: {caminho_entrada}")
        return "ERRO"

    # 1. VERIFICAR A DURAÇÃO DO VÍDEO
    logger.info(f"Verificando a duração de '{os.path.basename(caminho_entrada)}'...")
    duracao_total = get_video_duration(caminho_entrada)

    if duracao_total is None:
        return "ERRO"  # Falha ao ler a duração

    # 2. IGNORAR SE FOR MENOR QUE 5 MINUTOS (300 segundos)
    if duracao_total < 300:
        logger.warning(
            f"Vídeo ignorado. Duração ({int(duracao_total)}s) é menor que 5 minutos."
        )
        return "IGNORADO"

    logger.info(
        f"Duração total: {int(duracao_total)}s. O vídeo é elegível para o corte."
    )
    logger.info(
        f"Iniciando o corte a partir de {inicio_corte_segundos}s com duração de {duracao_corte_segundos}s."
    )

    # Comando FFmpeg com o novo ponto de início (-ss)
    # -ss: seek (pular para) o tempo especificado
    comando_ffmpeg = [
        "ffmpeg",
        "-ss",
        str(inicio_corte_segundos),  # Ponto de início do corte
        "-i",
        caminho_entrada,
        "-t",
        str(duracao_corte_segundos),  # Duração do corte
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-y",
        caminho_saida,
    ]

    try:
        resultado = subprocess.run(
            comando_ffmpeg, check=True, capture_output=False, text=True
        )
        logger.info(f"Vídeo cortado com sucesso e salvo em: '{caminho_saida}'")
        return "SUCESSO"

    except FileNotFoundError:
        logger.error(
            "ERRO CRÍTICO: O comando 'ffmpeg' ou 'ffprobe' não foi encontrado."
        )
        return "ERRO"
    except subprocess.CalledProcessError as e:
        logger.error("O FFmpeg retornou um erro durante o processamento.")
        logger.error(f"Comando executado: {' '.join(comando_ffmpeg)}")
        logger.error(f"Saída do FFmpeg (stderr):\n{e.stderr}")
        return "ERRO"
