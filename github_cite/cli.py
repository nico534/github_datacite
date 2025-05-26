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

from citation_translator import GithubRepoDataCite
from exceptions import GithubException
import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog='Github DataCite',
                        description='Get data from a github Repository and parse it using the DataCite schema.')
    parser.add_argument("repoUser")
    parser.add_argument("repoName")
    parser.add_argument("-t", "--token", default=None)
    parser.add_argument("--gitHubUrl", default="https://github.com")
    parser.add_argument("--gitHubApiUrl", default="https://api.github.com")
    args = parser.parse_args()
    try:
        data = GithubRepoDataCite(args.repoUser, args.repoName, githubApiUrl=args.gitHubApiUrl, githubUrl=args.gitHubUrl, barerToken=args.token)
        sys.stdout.write(data.pretty_xml())
    except GithubException as e:
        sys.stderr.write(f"An exception occurred:\n{e.message}")
