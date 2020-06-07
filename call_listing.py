"""Implement app routes for listing calls"""

from collections import defaultdict
from json import load
from typing import Mapping, Any, Generator

import boto3
import botocore.exceptions
from flask import jsonify
from flask_table import Table, Col

from settings import BUCKET, AWS_TRANSCRIBE_RESULTS_BUCKET
from aws_transcribe import get_transcription_content as get_aws_transcription_content

def calls(caller):
    # TODO: Provide sorting, paging
    caller_calls = tuple(
        map(_augment_call_details, _iterate_calls_by_caller(caller)))
    return jsonify(
        caller=caller,
        calls=caller_calls
    )


class CallRecords(Table):
    Caller = Col("Caller")
    RecordingStartTime = Col("Time started")
    RecordingSid = Col("Recording SID")
    CallSid = Col("Call SID")
    Mp3PathTwilio = Col("MP3 Link")
    TranscriptionTextTwilio = Col("Transcription (Twilio)")
    TranscriptionTextAws = Col("Transcription (AWS)")


def calls_html(caller):
    caller_calls = map(_augment_call_details, _iterate_calls_by_caller(caller))
    table = CallRecords(caller_calls, border=True)
    return f"""<html>
<h1>Calls from +{caller}</h1>
<div>
{table.__html__()}
</div>
</html>
"""


def _iterate_calls_by_caller(caller: str) -> Generator[Mapping[str, Any], None, None]:
    bucket = boto3.resource('s3').Bucket(BUCKET)
    for s3_obj in bucket.objects.filter(Prefix=f'by_caller/{caller}'):
        js = load(s3_obj.get()['Body'])
        yield js


def _augment_call_details(call_details: Mapping[str, Any]) -> Mapping[str, Any]:
    sid = call_details["RecordingSid"]
    bucket = boto3.resource('s3').Bucket(BUCKET)
    augmented_details = defaultdict(lambda: None, **call_details)
    try:
        transcription = load(bucket.Object(f"transcriptions/twilio/{sid}.json").get()['Body'])
        augmented_details["TranscriptionTextTwilio"] = transcription["TranscriptionText"]
    except botocore.exceptions.ClientError:
        pass

    augmented_details["TranscriptionTextAws"] = get_aws_transcription_content(sid)
    return augmented_details
