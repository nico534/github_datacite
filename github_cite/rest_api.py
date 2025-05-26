# MIT License
# 
# Copyright (c) 2025 Nicolai Hüning
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
