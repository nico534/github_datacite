# GitHubCite

This program can be used to extract a [DataCite](https://schema.datacite.org/meta/kernel-4.5/) xml from GitHub. It also checks if the repository is a fork and adds specific `relatedIdentifiers`.

### Usage
GitHubCite implements a simple cli-interface and a REST-API with a web frontend.

##### CLI interface
For the cli interface first install the python dependencies
```bash
cd github_cite
pip install -r requirements.txt
```

Now run `python cli.py repoUser repoName -t githubToken` to get the DataCite xml.

##### Frontend
To start the REST-API and frontend using docker compose simply run
```bash
docker compose up -d
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)..
