# FIXME: Don't hard-code anything. Get the resource names from the environment

APP_NAME="transcribe-twilio"
SLOT = 'dev'
BUCKET = f"{APP_NAME}-{SLOT}-content"
AWS_TRANSCRIBE_RESULTS_BUCKET = f"{APP_NAME}-{SLOT}-aws-transcriptions"
