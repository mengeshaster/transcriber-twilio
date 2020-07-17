import logging
from typing import Optional
from urllib.parse import urlparse
from os.path import basename, splitext
from json import load

import boto3
import botocore

from settings import AWS_TRANSCRIBE_RESULTS_BUCKET

logger = logging.getLogger(__name__)


def transcribe_recording(
    audio_url: str,
    language_code="he-IL"
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

def get_transcription_content(recording_id: str) -> Optional[str]:
    s3 = boto3.resource('s3')
    recording = s3.Object(AWS_TRANSCRIBE_RESULTS_BUCKET, recording_id + ".json")
    try:
        js = load(recording.get()["Body"])
    except botocore.exceptions.ClientError:
        logger.info("No transcription for %s", recording_id)
        return None

    transcripts = js["results"]["transcripts"]
    if not transcripts:
        logger.warning(
            "Transcription result for recording %s contains no transcripts",
            recording_id)
    else:
        if len(transcripts) > 1:
            logger.warning(
                "Transcription result for recording %s contains %d transcripts. Only considerting the first",
                recording_id, len(transcripts))
        return transcripts[0]["transcript"]

    return None
