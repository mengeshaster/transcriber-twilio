# Twilio transcriber: A service to receive and transcribe phone calls

## General Description

This is a web-service which inter-operates with Twilio to receive, record and transcribe incoming phone calls.
It subsequently also sends them to transcription using AWS transcribe. The call recordings and their metadata are stored on
AWS S3.

While this code is functional, it's primarily intended as a demonstrator of the following technologies:

* Capturing recordings from conventional phone calls
* Comparative transcription results from 2 services - Twilio and AWS.
* Dual execution mode: the code can execute both as a Flask web-service and as
AWS Lambda functions, using the WSGI support in the Serverless framework.
* Generation of HTML tables in Python.

## Functional Description

This service runs either on AWS Lambda or on WSGI. It allows the content of incoming phone calls to be recorded and transcribed.
It exposes a route, which is meant to be called from Twilio as a webhook when a call starts. It then sends a response to Twilio which
causes the call to be recorded and transcribed by them.

When the recording and transcription by Twilio are complete, other routes are called to indicate that.
Once the recording is complete, it gets downloaded from Twilio into an S3 bucket, and sent to AWS Transcribe for transcription.
Once Twilio finished transcribing the call, it calls us with the content of the transcription, which we retain.

The information about the call, its transcription and a URL for playing the content are made available at
an endpoint, as either JSON or an HTML table.

## Public API

### /call_incoming
_Method:_ POST

The webhook route that is presented to Twilio. It will be called when a call arrives.
It will refer Twilio to subsequent routes which handle webhook callbacks on recording completion
and transcription completion.

### /calls/\<caller\>
_Method:_ GET

List all the calls to a particular number, where the number is given in canonical form including
the country code, but without a leading '+' or '0'. The calls are returned as an HTML table
if the _Accept_ header specifies _text/html_, and JSON otherwise.

## Installation

Deployment to AWS uses the Serverless framework's CLI.
Example of a command to deploy the code to AWS:

```bash
sls deploy --service=my_transcriber --region=eu-west-1 --slot=staging
```

In this example the meaning of all the parameters - _service_, _region_ and _slot_ is defined in serverless.yml
Note that you will likely need to specify additional switches to specify the AWS credentials that you use
to create the resources that this service requires. Please see the _sls_ documentation.

Your account should be able to create roles, S3 buckets and Lambda functions.
