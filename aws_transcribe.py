import logging
from urllib.parse import urlparse
from os.path import basename, splitext

import boto3
import botocore

from settings import AWS_TRANSCRIBE_RESULTS_BUCKET

logger = logging.getLogger(__name__)


def transcribe_recording(
    audio_url: str,
    language_code="en-US"
) -> None:
    audio_path = urlparse(audio_url).path
    recording_id, extension = splitext(basename(audio_path))
    client = boto3.client("transcribe")

    try:
        response = client.start_transcription_job(
            TranscriptionJobName=recording_id,
            LanguageCode=language_code,
            MediaFormat=extension.lstrip(".").lower(),
            Media={
                "MediaFileUri": audio_url
            },
            OutputBucketName=AWS_TRANSCRIBE_RESULTS_BUCKET,
        )

        # FIXME: Retrieve the HTTP status correctly! This code doesn't seem to work ...
        if (response["ResponseMetadata"]["HTTPStatusCode"] != 200) or (
            response["TranscriptionJob"]["TranscriptionJobStatus"] not in ("IN_PROGRESS", "COMPLETED")):
            logging.error("Failed transcription request %s", response)
        else:
            logging.info("Submitted transcription: %s", response)

    except botocore.exceptions.ClientError:
        logging.exception("Failed to submit the transcription")

    return
