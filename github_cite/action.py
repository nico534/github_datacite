from citation_translator import GithubRepoDataCite
from exceptions import GithubException
import sys
import os

def set_github_action_output(output_name, output_value):
    f = open(os.path.abspath(os.environ["GITHUB_OUTPUT"]), "a")
    f.write(f'{output_name}={output_value}')
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
        set_github_action_output('dataCiteXML', data.pretty_xml())
        
    except GithubException as e:
        sys.stderr.write(f"An exception occurred:\n{e.message}")
