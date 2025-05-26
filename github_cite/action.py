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


# Python script executed using GitHub actions.
from citation_translator import GithubRepoDataCite
from exceptions import GithubException
import sys
import os

def set_github_action_output(output_name, output_value):
    f = open(os.path.abspath(os.environ["GITHUB_OUTPUT"]), "a")
    f.write(f'{output_name}<<EOF\n{output_value}\nEOF\n')
    f.close()

if __name__ == "__main__":
    repo_owner = os.environ["INPUT_REPOOWNER"]
    repo_name = os.environ["INPUT_REPONAME"]
    api_token = os.environ["INPUT_APITOKEN"]
    github_url = os.environ["INPUT_GITHUBURL"]
    github_api_url = os.environ["INPUT_GITHUBAPIURL"]
    try:
        data = GithubRepoDataCite(repo_owner, repo_name, githubApiUrl=github_api_url, githubUrl=github_url, barerToken=api_token)
        sys.stdout.write(data.pretty_xml())
        set_github_action_output('datacitexml', data.pretty_xml())
        
    except GithubException as e:
        sys.stderr.write(f"An exception occurred:\n{e.message}")
