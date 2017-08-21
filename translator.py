#!/usr/bin/env python

import RPi.GPIO as GPIO
import Adafruit_SSD1306
import subprocess
import time
import json
import math
import sys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

GPIO.setmode(GPIO.BCM)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used

disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# First define some constants to allow easy resizing of shapes.
projectPath = "/home/pi/Projects/translator/"
padding = 2
top = padding
bottom = height-padding
fontName = projectPath + 'VCR_OSD_MONO_1.001.ttf'

def ClearText():
    SetText("", "")

def SetText(line1, line2):
    fontSize = 16
    fontNextLine = fontSize

    # Load default font.
    # font = ImageFont.load_default()

    # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
    # Some other nice fonts to try: http://www.dafont.com/bitmap.php
    # font = ImageFont.truetype('Minecraftia.ttf', 8)

    font = ImageFont.truetype(fontName, fontSize)

    #font = ImageFont.truetype('advanced_pixel_lcd-7.ttf', 16)
    #font = ImageFont.truetype('VCR_OSD_MONO_1.001.ttf', 21)
    #font = ImageFont.truetype('Minecraftia-Regular.ttf', 16)

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    draw.text((0, top), line1, font=font, fill=255)
    draw.text((0, top + fontNextLine), line2, font=font, fill=255)

    disp.image(image)
    disp.display()

def ScrollText(text):
    fontScroll = ImageFont.truetype(fontName, 26)

    # Get display width and height.
    maxwidth, unused = draw.textsize(text, font=fontScroll)

    # Set animation parameters.
    velocity = -10
    startpos = width
    y = padding

    # Animate text moving in sine wave.
    pos = startpos
    while pos >= -maxwidth:
        # Clear image buffer by drawing a black filled box.
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        # Enumerate characters and draw them offset vertically based on a sine wave.
        x = pos
        for i, c in enumerate(text):
            # Stop drawing if off the right side of screen.
            if x > width:
                break
            # Calculate width but skip drawing if off the left side of screen.
            if x < -10:
                char_width, char_height = draw.textsize(c, font=fontScroll)
                x += char_width
                continue
            # Draw text.
            draw.text((x, y), c, font=fontScroll, fill=255)
            # Increment x position based on chacacter width.
            char_width, char_height = draw.textsize(c, font=fontScroll)
            x += char_width
        # Draw the image buffer.
        disp.image(image)
        disp.display()
        # Move position for next frame.
        pos += velocity

    draw.rectangle((0,0,width,height), outline=0, fill=0)
    disp.image(image)
    disp.display()

def ShowStats():
    fontStats = ImageFont.load_default()
    topStats = -2

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "hostname -I | cut -d\' \' -f1"
    IP = subprocess.check_output(cmd, shell = True )
    cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell = True )
    cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    MemUsage = subprocess.check_output(cmd, shell = True )
    cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
    Disk = subprocess.check_output(cmd, shell = True )

    draw.text((0, topStats),       "IP: " + str(IP),  font=fontStats, fill=255)
    draw.text((0, topStats+8),     str(CPU), font=fontStats, fill=255)
    draw.text((0, topStats+16),    str(MemUsage),  font=fontStats, fill=255)
    draw.text((0, topStats+25),    str(Disk),  font=fontStats, fill=255)

    # Display image.
    disp.image(image)
    disp.display()

def ShowSplashScreen():
    datePart = time.strftime("%a %b %d %y", time.localtime())
    timePart = time.strftime("%I:%M:%S %p", time.localtime())
    SetText(datePart, timePart)

def RecordAudio():
    SetText("Recording", "Start")
    cmd = "arecord -D plughw:1,0 -f S16_LE -r 16000 -d 5 " + projectPath + "speech.wav"
    subprocess.check_output(cmd, shell = True)
    SetText("Recording", "Done")

def UploadAudio():
    SetText("Uploading", "Start")
    cmd = "sudo " + projectPath + "uploadAudio.sh"
    subprocess.check_output(cmd, shell = True)
    SetText("Uploading", "Done")

def TranscribeAudio():
    #SetText("Transcribing", "Setting Auth")
    #cmdAuth = "export GOOGLE_APPLICATION_CREDENTIALS=PiriVoiceAssistant-86cac20997e5.json"
    #subprocess.check_output(cmdAuth, shell = True )

    #SetText("Transcribing", "Getting Token")
    #cmdGetToken = "/home/pi/Projects/google-cloud-sdk/bin/gcloud auth application-default print-access-token"
    #token = subprocess.check_output(cmdGetToken, shell = True )

    SetText("Transcribing", "Getting Token")
    cmdGetToken = projectPath + "getToken.sh"
    token = subprocess.check_output(cmdGetToken, shell = True)

    SetText("Transcribing", "Recognizing")
    cmdRecognize = "curl -s -H \"Content-Type: application/json\" -H \"Authorization: Bearer " + token + " \" \"https://speech.googleapis.com/v1/speech:recognize\" -d @" + projectPath + "sync-request.json"
    response = subprocess.check_output(cmdRecognize, shell = True)

    responseData = json.loads(response)
    print responseData

    responseText = responseData["results"][0]["alternatives"][0]["transcript"]
    SetText("Transcribing", "Done")

    return responseText

responseText = ""
lastRefresh = 0
showTime = True
latestStats = False
showText = False

while True:
    try:
        if showText:
            #responseText = "the quick brown fox jumps over the lazy dog near the bank of the river"
            ScrollText(responseText)

            if (int(round(time.time())) - lastRefresh > 10):
                showText = False
        else:
            if showTime:
                ShowSplashScreen()
            else:
                if not latestStats:
                    ShowStats()
                    latestStats = True

            if (int(round(time.time())) - lastRefresh > 5):
                showTime = not showTime
                latestStats = False
                lastRefresh = int(round(time.time()))

        button1 = GPIO.input(15)
        button2 = GPIO.input(18)
        button3 = GPIO.input(23)
        button4 = GPIO.input(24)

        #busy = not (button1 and button2 and button3 and button4)

        if button1 == False:
            RecordAudio()
            UploadAudio()
            responseText = TranscribeAudio()
            ScrollText(responseText)

        if button2 == False:
            showText = True
            lastRefresh = int(round(time.time()))

        if button3 == False:
            responseText = TranscribeAudio()
            ScrollText(responseText)

        if button4 == False:
            ClearText()
            subprocess.check_output("sudo shutdown now", shell = True)

        #time.sleep(.1)
    except Exception as ex:
        ScrollText(str(ex))