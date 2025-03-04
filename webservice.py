import sys
import os
import argparse
import math
import hashlib 
import mimetypes
import time
import pickle
from datetime import datetime
from decimal import Decimal
import re
from flask import Flask, render_template, request, json, redirect, jsonify
from flask_cors import CORS
from decimal import Decimal
from base64 import b64encode, b64decode
from controller.util import check_or_create

import langmodels.modelregistry as modelRegistry

from util.modelinstance import ModelInstance
from util.entropyresult import EntropyResult, EntropyLine, Token
from controller.project_overview_controller import ProjectOverviewController
from controller.entropy_controller import EntropyController

PORT = 8080
global rootPath
global files
global models

app = Flask(__name__, static_folder='')
# enable CORS for api endpoint
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

models = {}
registeredModels = modelRegistry.query_all_models(cached = False)

for model_description in registeredModels:
    models[model_description.id] = ModelInstance(model_description)

files = {}
rootPath = os.path.dirname(os.path.realpath(__file__))
files_json_path = os.path.join(rootPath, 'files.json')
if os.path.exists(files_json_path):
    with open(files_json_path, 'r') as json_files:
        try:
            files = json.load(json_files)
        except:
            files = {}
        json_files.close()

# controllers
project_overview_controller = ProjectOverviewController(rootPath, files)
entropy_controller = EntropyController(rootPath, models, files)

# API-routes
@app.route('/api/models')
def api_models():
    serialized_models = [models[key].serialize_model() for key in models]
    response = jsonify({
                'models': serialized_models,
            })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/projects', methods = ['GET'])
def api_projects():
    return project_overview_controller.get_projects()
    
@app.route('/api/project/<projecthash>', methods = ['GET'])
def api_project_files(projecthash):
    return project_overview_controller.get_project_files(projecthash)

@app.route('/api/project/<projecthash>/<filehash>', methods = ['GET'])
def api_project_file_detail(projecthash, filehash):
    return project_overview_controller.get_project_file_detail(projecthash, filehash)

@app.route('/api/autocompletion', methods = ['POST'])
def api_autocompletion():
    return entropy_controller.get_predictions(request, models)

@app.route('/api/languagemodel', methods = ['POST'])
def api_languagemodel():
    return entropy_controller.get_entropies(request, models)

@app.route('/api/compare', methods = ['POST'])
def api_compare():
    return entropy_controller.get_compare(request, models)

@app.route('/api/search', methods = ['POST'])
def api_search():
    return entropy_controller.get_search(request, models)

check_or_create(os.path.join(rootPath, 'cache'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', default=False, action='store_false', help='Start the server in debug mode.')
    parser.add_argument('-p', '--port', default=PORT, type=int, action='store', help='Set the port for of the web server.')
    parser.add_argument('-sh', '--serverhost', default='127.0.0.1', type=str, action='store', help='Set the host of the web server.')
    args = parser.parse_args()

    port = args.port
    debug = args.debug
    host = args.serverhost

    print("Starting WebServer on host " + host + ", Port " + str(port))
    print("Debug ", debug)

    app.run(use_reloader=debug, port=port, debug=debug, host=host)
