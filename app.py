# Derived from an example here: https://www.twilio.com/blog/transcribe-voicemails-python-flask-twilio

import os

from flask import Flask, request, abort
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from requests import head
from smart_open import open as sopen
from json import dump
import boto3
import pprint


app = Flask(__name__)

SLOT = 'dev'

# Move to .env!!

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
        obj_name = f"s3://transcribe-twilio-{SLOT}-content/calls/{sid}.json"
        capture_json(obj_name, request.form)
    else:
        # Hang up the call
        print("Hanging up...")
        response.hangup()
    return str(response)

@app.route("/record_complete", methods=["POST"])
def record_complete():
    "Handle record completion"

    sid = request.form['RecordingSid']
    obj_name = f"s3://transcribe-twilio-{SLOT}-content/recordings/{sid}.json"
    capture_json(obj_name, request.form)

    if 'RecordingUrl' in request.form:
        rsp = head(request.form['RecordingUrl'])
        if rsp.status_code != 200:
            print("Unable to fetch the recording")
        else:
            print("The recording is available")

    return request.form['RecordingSid']


# FIXME: Rename this to reflect the intent
@app.route("/twilio_transcription_complete", methods=["POST"])
def twilio_transcription_complete():
    """ Creates a client object print the transcription text"""
    #create a client object and pass it our secure authentication variables
    client = Client()
    if not 'TranscriptionSid' in request.form:
        abort(400, "No recordings received")

    content = request.form
    sid = request.form['TranscriptionSid']
    if 'TranscriptionText' not in request.form:
        #fetch the transcription and assign it
        content['TranscriptionText'] = client.transcriptions(sid).fetch()

    sid = request.form['RecordingSid']
    obj_name = f"s3://transcribe-twilio-{SLOT}-content/transcriptions/twilio/{sid}.json"
    capture_json(obj_name, content)
    return str(sid)


# TODO: Move the functions below into a persistence component


def capture_json(obj_name: str, content: dict):
    # TODO: Allow the session to be re-used
    session = boto3.Session(
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
    )
    url = obj_name
    with sopen(url, 'wt', transport_params={'session': session}) as fout:
        dump(content, fout, indent=2)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.wsgi_app = LoggingMiddleware(app.wsgi_app)
    app.run()
