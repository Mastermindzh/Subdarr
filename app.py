"""Subdarr

Subdarr is a module which listens to post requests with movie/serie information
and downloads subtitles in the languages requested.

"""
import json
import os
import meinheld
import datetime
from datetime import timedelta
from logger.logger import log
from flask import Flask, request, send_file
from babelfish import Language
from subliminal import download_best_subtitles, save_subtitles, scan_video, scan_videos
from concurrent.futures import ThreadPoolExecutor

# Define APP
APP = Flask(__name__, template_folder="templates")

# Define nr of threads (defaults to 5)
executor = ThreadPoolExecutor()

# Define global variables
NO_DATA_RECEIVED = "No data received"
NO_PATH_PROVIDED = "No path provided"
NO_SUBTITLES_FOUND = "No subtitles found"

@APP.route('/', methods=['GET'])
def home():
    """Homepage
    introductionary page (renders the readme.md)
    """
    return '{"version":0.1}'

@APP.route('/connector', methods=['GET'])
def get_connector():
    """Returns the connector script"""
    try:
        return send_file(os.path.join("./connector", "download_subtitles.sh"), as_attachment=True)
    except (TypeError, OSError) as err:
        return error(err, 500)

@APP.route('/scan', methods=["POST"])
def scan():
    """scan for subtitles in a given path

        json:
        {
            "languages": "eng, nld",
            "path":"/path",
            "age": 14 
        }

        age = in days
    """
    if request.json:
        mydata = request.json
    else:
        log(NO_DATA_RECEIVED)

    if not 'path' in mydata or not mydata['path']:
        return error(NO_PATH_PROVIDED, 406)
    if not 'languages' in mydata or not mydata['languages']:
        mydata['languages'] = parse_languages("eng")
    if not 'age' in mydata or not mydata['age']:
        mydata['age'] = 14

    executor.submit(scan_folder_for_subs, mydata['path'],mydata['age'], mydata['languages'])
    return 'Scan has started in the background'

@APP.route("/download", methods=['POST'])
def download_subtitles():
    """Download subtitles"""
    if request.json:
        mydata = request.json
        if not 'path' in mydata: # check if empty
            log(NO_PATH_PROVIDED)
            return error(NO_PATH_PROVIDED, 406)

        # check if languages is empty, if so use english
        if not 'languages' in mydata or not mydata['languages']:
            mydata['languages'] = "eng"

        log(json.dumps(mydata))
        path = mydata['path']
        videos = []
        try:
            videos.append(scan_video(path))
            subtitles = download_best_subtitles(videos, parse_languages(mydata['languages']))
            for video in videos:
                save_subtitles(video, subtitles[video])

            return json.dumps(mydata)
        except Exception:
            log(NO_SUBTITLES_FOUND)
            return error(NO_SUBTITLES_FOUND, 404)
    else:
        log(NO_DATA_RECEIVED)
        return error(NO_DATA_RECEIVED, 406)

def scan_folder_for_subs(path, age,languages):
    dirname = os.path.basename(path)
    log("Processing: " + dirname)

    # scan for videos newer than {age} days and their existing subtitles in a folder
    videos = scan_videos(path, age=timedelta(days=age))
    log("Found the following videos:")
    for v in videos:
        log("  - " + v.name)
    
    # download best subtitles and try to save it
    log("Looking for subtitles..")
    try:
        subtitles = download_best_subtitles(videos, parse_languages(languages))
        
        for v in videos:                
            if(len(subtitles[v]) >= 1):
                log("   Saving subtitle(s) for: " + v.name)
                save_subtitles(v, subtitles[v])
            else:
                log("   No subtitles found for: " + v.name)

    except Exception:
        log("ERROR: - Download failed.")

def parse_languages(csv_languages):
    """Parse languages string

        Keyword arguments:
        csv_languages -- Comma separated string of languages
    """
    my_languages = []

    for lang in csv_languages.split(","):
        my_languages.append(Language(lang))

    return set(my_languages)

def error(text, error_code):
    """Returns the error in json format

        Keyword arguments:
        text -- Human readable text for the error
        error_code -- http status code
    """
    return '{{"Error": "{}"}}'.format(text), error_code

# finally run the script if file is called directly
meinheld.listen(("0.0.0.0", 5500))
meinheld.run(APP)
    