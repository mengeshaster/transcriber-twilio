import os

APP_NAME = os.environ["APP_NAME"]
SLOT = os.environ.get("SLOT", "dev")

BUCKET = f"{APP_NAME}-{SLOT}-content"
AWS_TRANSCRIBE_RESULTS_BUCKET = f"{APP_NAME}-{SLOT}-aws-transcriptions"
