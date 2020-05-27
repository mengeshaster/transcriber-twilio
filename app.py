# Derived from an example here: https://www.twilio.com/blog/transcribe-voicemails-python-flask-twilio

from flask import Flask, request, abort
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import pprint


app = Flask(__name__)


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

@app.route("/record", methods=["POST"])
def record():
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
            transcribe_callback="/message",
            transcribe=True)

        #return status message
        print(str(response))
    else:
        # Hang up the call
        print("Hanging up...")
        response.hangup()
    return str(response)


@app.route("/record_complete", methods=["POST"])
def record_complete():
    "Handle record completion"
    print(request.form)
    return request.form['RecordingSid']


@app.route("/message", methods=["POST"])
def message():
    """ Creates a client object print the transcription text"""
    #create a client object and pass it our secure authentication variables
    client = Client()
    print(request.form)
    if not 'TranscriptionSid' in request.form:
        abort(400, "No recordings received")

    sid = request.form['TranscriptionSid']
    if 'TranscriptionText' in request.form:
        print(request.form['TranscriptionText'])
    else:
        #fetch the transcription and assign it
        t = client.transcriptions(sid).fetch()
        print(t.transcription_text)

    print(sid)
    return str(sid)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.wsgi_app = LoggingMiddleware(app.wsgi_app)
    app.run()
