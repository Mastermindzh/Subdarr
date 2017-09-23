"""Subdarr

Subdarr is a module which listens to post requests with movie/serie information
and downloads subtitles in the languages requested.

"""
import json
import os
import meinheld
from logger.logger import log
from flask import Flask, request, send_file
from babelfish import Language
from subliminal import download_best_subtitles, save_subtitles, scan_video

# Define APP
APP = Flask(__name__, template_folder="templates")

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

@APP.route("/download", methods=['POST'])
def download_subtitles():
    """Download subtitles"""
    if request.json:
        mydata = request.json
        if not 'path' in mydata: # check if empty
            log("No path provided")
            return error("No path provided.", 406)

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
            log("No subtitles found")
            return error("No subtitles found", 404)

    else:
        log("No data received")
        return error("No data received", 406)

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
    return '{{"Error:": "{}"}}'.format(text), error_code

# finally run the script if file is called directly
meinheld.listen(("0.0.0.0", 5500))
meinheld.run(APP)
    