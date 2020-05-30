# Derived from an example here: https://www.twilio.com/blog/transcribe-voicemails-python-flask-twilio

import os

from flask import Flask, request, abort
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from requests import get
from urllib.parse import urlparse
from json import dumps
import boto3
import pprint


app = Flask(__name__)

SLOT = 'dev'

class LoggingMiddleware(object):
    def __init__(self, app):
        self._app = app

    def __call__(self, env, resp):
        errorlog = env['wsgi.errors']
        pprint.pprint(('REQUEST', env), stream=errorlog)

        def log_response(status, headers, *args):
            pprint.pprint(('RESPONSE', status, headers), stream=errorlog)
            return resp(status, headers, *args)

        return self._app(env, log_response)

@app.route("/call_incoming", methods=["POST"])
def call_incoming():
    """ Returns TwiML which prompts the caller to record a message"""
    # Define TwiML response object
    response = VoiceResponse()

    # Make sure this is the first call to our URL and record and transcribe
    if 'RecordingSid' not in request.form:
        # Use <Say> verb to provide an outgoing message
        response.say("Hello, please leave your message after the tone.")

        # Use <Record> verb to record incoming message and set the transcribe argument to true
        response.record(
            recording_status_callback="/record_complete",
            transcribe_callback="/twilio_transcription_complete",
            transcribe=True)

        sid = request.form['CallSid']
        capture_json(f"transcribe-twilio-{SLOT}-content", f"calls/{sid}.json", request.form)
    else:
        # Hang up the call
        print("Hanging up...")
        response.hangup()
    return str(response)

@app.route("/record_complete", methods=["POST"])
def record_complete():
    "Handle record completion"

    sid = request.form['RecordingSid']
    capture_json(f"transcribe-twilio-{SLOT}-content", f"recordings/{sid}.json", request.form)

    if 'RecordingUrl' in request.form:
        _save_twilio_recording_content(request.form)

    return request.form['RecordingSid']

# FIXME: Rename this to reflect the intent
@app.route("/twilio_transcription_complete", methods=["POST"])
def twilio_transcription_complete():
    """Store the transcription received from Twilio. If non was given,
    attempt to fetch it"""

    if not 'TranscriptionSid' in request.form:
        abort(400, "No recordings received")

    content = dict(**request.form)
    sid = content['TranscriptionSid']
    if 'TranscriptionText' not in request.form:
        content['TranscriptionText'] = _fetch_twilio_transcription(sid)

    sid = request.form['RecordingSid']
    capture_json(f"transcribe-twilio-{SLOT}-content", f"transcriptions/twilio/{sid}.json", content)
    return str(sid)

def _save_twilio_recording_content(args: dict):
    mp3_url = args['RecordingUrl'] + ".mp3"
    content = get(mp3_url).content
    s3_obj = boto3.resource('s3').Object(
        f"transcribe-twilio-{SLOT}-content",
        f"recordings/{args['RecordingSid']}.mp3"
    )
    s3_obj.put(Body=content)
    return

def _fetch_twilio_transcription(sid) -> str:
    # Note: the code below was never successfully tested.
    # For now it's kept as for reference only
    # At the very least it requires access to Twilio keys
    client = Client()
    #fetch the transcription and assign it
    return client.transcriptions(sid).fetch()

# TODO: Move the functions below into a persistence component


def capture_json(bucket: str, path: str, content: dict):
    content_str = dumps(content)
    s3_obj = boto3.resource('s3').Object(bucket, path)
    s3_obj.put(Body=content_str)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.wsgi_app = LoggingMiddleware(app.wsgi_app)
    app.run()
