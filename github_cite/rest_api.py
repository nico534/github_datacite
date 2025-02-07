# app.py
from flask import Flask, request
from flask_cors import CORS
from citation_translator import GithubRepoDataCite
import sys
from exceptions import GithubException

"""
Starts a simple Flask REST-Api server with one POST endpoint /generate
to create the DataCite xml file.
"""

app = Flask(__name__)
port = 80

CORS(app, origins="*")
@app.post("/generate")
def add_country():
    if request.is_json:
        metadata = request.get_json()
        try:
            repo_data = GithubRepoDataCite(metadata["owner"], metadata["project"], barerToken=metadata["apiToken"])
            xml = repo_data.doc.toprettyxml()
            return xml, 201
        except GithubException as e:
            return e.message, e.code

    return "Request must be JSON", 415

if __name__ == '__main__':
    if sys.argv.__len__() > 1:
        port = sys.argv[1]
        print("Api running on port : {} ".format(port))
    # Run the app on localhost, port 5000
    app.run(host="0.0.0.0", port=port, debug=False)
