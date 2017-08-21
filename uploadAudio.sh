#!/bin/bash

export BOTO_CONFIG=/home/pi/.config/gcloud/legacy_credentials/alexander.b.yao@gmail.com/.boto
/home/pi/Projects/google-cloud-sdk/bin/gsutil cp /home/pi/Projects/translator/speech.wav gs://transcriptionaudio