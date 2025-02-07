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