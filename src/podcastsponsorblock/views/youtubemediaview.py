import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Sequence, Optional

from flask import send_file, current_app, Response
from flask.typing import ResponseReturnValue

from flask.views import MethodView
from yt_dlp import YoutubeDL as YoutubeDLP, DownloadError

from ..helpers import leniently_validate_youtube_id
from googleapiclient.discovery import build as build_google_api_client
import threading

from ..models import ServiceConfig


def download_m4a_audio(
    video_id: str, output_path: Path, categories_to_remove: Sequence[str]
):
    logging.info(f"Preparing to download audio for video ID: {video_id}")
    youtube_dlp_options = {
        "quiet": False,
        "outtmpl": str(output_path.absolute().resolve()),
        "format": "bestaudio[ext=m4a]",
        "postprocessors": [
            {"key": "SponsorBlock", "categories": categories_to_remove},
            {
                "key": "ModifyChapters",
                "remove_sponsor_segments": categories_to_remove,
            },
        ],
    }
    logging.debug(f"YoutubeDL options: {youtube_dlp_options}")
    with YoutubeDLP(youtube_dlp_options) as youtube_dlp_client:
        logging.info(f"Starting download for video ID: {video_id}")
        try:
            youtube_dlp_client.download((f"https://www.youtube.com/watch?v={video_id}",))
            logging.info(f"Successfully completed download for video ID: {video_id}")
        except Exception as e:
            logging.error(f"Error occurred while downloading video ID {video_id}: {e}")
            raise


def validate_youtube_video_id(video_id: str, config: ServiceConfig) -> Optional[str]:
    logging.info(f"Validating YouTube video ID: {video_id}")
    youtube_client = build_google_api_client(
        "youtube", "v3", developerKey=config.youtube_api_key, cache_discovery=False
    )
    video_request = youtube_client.videos().list(part="id", id=video_id)
    try:
        video_response = video_request.execute()
        video_objects = video_response["items"]
        if len(video_objects) == 0:
            logging.warning(f"No video found for ID: {video_id}")
            return None
        logging.info(f"Video ID {video_id} is valid.")
        return video_objects[0]["id"]
    except Exception as e:
        logging.error(f"Error occurred while validating video ID {video_id}: {e}")
        return None


class YoutubeMediaView(MethodView):
    def __init__(self):
        self.video_download_locks = defaultdict(threading.Lock)

    def get(self, video_id: str) -> ResponseReturnValue:
        # Apple podcasts requires the file extension, but we don't want it and need to remove it if present
        video_id = video_id.removesuffix(".m4a")
        if not leniently_validate_youtube_id(video_id):
            return Response("Invalid video ID", status=400)
        config: ServiceConfig = current_app.config["PODCAST_SERVICE_CONFIG"]
        validated_video_id = validate_youtube_video_id(video_id, config)
        if validated_video_id is None:
            return Response("Video ID does not exist", status=400)
        audio_output_path = config.data_path / "audio" / f"{validated_video_id}.m4a"
        if audio_output_path.exists() and audio_output_path.is_file():
            return send_file(audio_output_path)
        # We need a per-video_id lock here to prevent two requests from causing the same video to download twice
        with self.video_download_locks[validated_video_id]:
            if audio_output_path.exists() and audio_output_path.is_file():
                return send_file(audio_output_path)
            logging.info(f"Downloading audio from YouTube video {validated_video_id}")
            try:
                download_m4a_audio(
                    validated_video_id,
                    audio_output_path,
                    categories_to_remove=config.categories_to_remove,
                )
                time.sleep(3)
                return send_file(audio_output_path)
            except DownloadError as exception:
                logging.exception(
                    f"Failed to download audio for YouTube video {validated_video_id}",
                    exception,
                )
                return Response("Failed to download audio", status=500)
