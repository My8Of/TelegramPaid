import io
import os

import google.auth.transport.requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm

from app.utils.logger import ColorLogger

load_dotenv()
logger = ColorLogger()


class DriveManeger:
    def __init__(self):
        base_dir = os.path.dirname(
            os.path.abspath(__file__)
        )  # Garantindo que use o caminho absoluto
        # Se modificar os scopes, delete o arquivo token.json.
        self.scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        self.folder_id = os.getenv("FOLDER_ID")
        self.client_secrets_file = os.path.join(
            base_dir,
            "oauth/client_secret_477730350957-vsrp76iaj876gan3psbrll2r0cr3130u.apps.googleusercontent.com.json",
        )
        self.token_path = os.path.join(base_dir, "oauth/token.json")

    def authenticate_google_drive(self):
        """Autentica o usuário e retorna o serviço da API do Google Drive."""
        creds = None
        # O arquivo token.json armazena as credenciais de acesso do usuário.
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        # Se não houver credenciais válidas, o usuário precisará fazer o login.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            # Salva as credenciais para as próximas execuções.
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    def find_videos_in_folder(self, service):
        """Encontra e retorna uma lista de vídeos em uma pasta específica."""
        query = f"'{self.folder_id}' in parents and mimeType contains 'video/'"
        results = (
            service.files()
            .list(q=query, fields="nextPageToken, files(id, name,size)")
            .execute()
        )

        items = results.get("files", [])
        if not items:
            logger.warning("Nenhum vídeo encontrado na pasta.")
            return []

        return items

    def _download_video_from_drive(self, service, file_id, file_name, file_size):
        """Baixa um arquivo do Google Drive com barra de progresso."""
        request = service.files().get_media(fileId=file_id)

        # Converte o tamanho do arquivo para inteiro, caso venha como string
        try:
            file_size_int = int(file_size)
        except (TypeError, ValueError):
            logger.warning(
                f"Aviso: Não foi possível obter o tamanho exato do arquivo '{file_name}'. A barra de progresso pode não ser precisa."
            )
            file_size_int = 0  # Define como 0 para ter uma barra de progresso genérica

        fh = io.FileIO(file_name, "wb")
        downloader = MediaIoBaseDownload(
            fh, request, chunksize=1024 * 1024
        )  # Ajusta o tamanho do chunk para a barra de progresso

        done = False
        downloaded_bytes = 0

        # Inicializa a barra de progresso
        with tqdm(
            total=file_size_int, unit="B", unit_scale=True, desc=file_name, ncols=80
        ) as pbar:
            while done is False:
                status, done = downloader.next_chunk()

                # Calcula quantos bytes foram baixados neste chunk
                current_downloaded = int(file_size_int * status.progress())
                bytes_this_chunk = current_downloaded - downloaded_bytes
                downloaded_bytes = current_downloaded

                pbar.update(bytes_this_chunk)  # Atualiza a barra de progresso

        logger.info(f"\nDownload de '{file_name}' completo!")

    def download(self, service, selected_video, output_folder):
        # Define o nome do arquivo de saída
        output_file_name = os.path.join(output_folder, selected_video["name"])
        file_id = selected_video["id"]
        file_size = selected_video.get("size")  # Pega o tamanho do arquivo

        # Executa o download com barra de progresso
        self._download_video_from_drive(service, file_id, output_file_name, file_size)
