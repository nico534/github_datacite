# GitHub DataCite action

GitHub action to generate [DataCite](https://schema.datacite.org/meta/kernel-4.5/) xml from a GitHub repository. It also checks if the repository is a fork and adds specific `relatedIdentifiers`.

## Usage
Available inputs:
- `repoOwner` The owner of the repository
- `repoName` The name of the repository
- `apiToken` The API token to access GitHubs API
- `githubUrl` URL to the GitHub instance. Default: `https://github.com`
- `githubApiUrl` URL to the GitHub API. Dafault: `https://api.github.com`

This action will generate the DataCite xml and save it in the output `datacitexml`. This output can now for example be used as artifact for a GitHub release.

## Example
Example usage to generate a `data-cite.xml` file on the main branch and as an artifact ready to download:
```yaml
name: Create GitHub DataCite xml file
on:
  workflow_dispatch:

jobs:
  createCite:
    name: Create a DataCite XML
    runs-on: ubuntu-latest

    permissions:
      # Give the default GITHUB_TOKEN write permission to commit and push the changed files back to the repository.
      contents: write
    steps:
      # Checkout the repository
      - uses: actions/checkout@v4
        name: Checkout repository
        with:
          ref: main

      # Seperate repository owner and name
      - name: Extract repoOwner and repoName
        run: |
          REPO_FULL_NAME="${{ github.repository }}"
          REPO_OWNER=$(echo "$REPO_FULL_NAME" | cut -d'/' -f1)
          REPO_NAME=$(echo "$REPO_FULL_NAME" | cut -d'/' -f2)
          echo "REPO_OWNER=$REPO_OWNER" >> $GITHUB_ENV
          echo "REPO_NAME=$REPO_NAME" >> $GITHUB_ENV

      # Generate the DataCite xml file
      - name: Get DataCite xml file
        uses: nico534/github_datacite@v1
        id: datacite-xml
        with:
          apiToken: ${{ secrets.GITHUB_TOKEN }}
          repoOwner: ${{ env.REPO_OWNER }}
          repoName: ${{ env.REPO_NAME }}

      # Save the DataCite XML to a file
      - name: Create data-cite xml file
        uses: 1arp/create-a-file-action@0.4.5
        with:
          file: "data-cite.xml"
          content: ${{ steps.datacite-xml.outputs.datacitexml }}

      # Upload to artifact to make it available as download
      - name: Save data-cite.xml as artifact
        uses: actions/upload-artifact@v4
        with:
          name: data-cite-xml
          path: data-cite.xml
          compression-level: 0

      # Commit the file to the main branch
      - name: Commit and push data-cite.xml to the repository
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: Automatically added data-cite.xml
          file_pattern: 'data-cite.xml'
          branch: main
```

## Usage beyond GitHub actions
GitHub DataCite also implements a simple to us python cli-interface and a REST-API that can be used with the provided frontend.

#### CLI interface
For the cli interface first install the python dependencies
```bash
cd github_cite
pip install -r requirements.txt
```
Now run `python cli.py repoUser repoName -t githubToken` to get the DataCite xml.

#### Frontend
To start the REST-API and frontend using docker compose simply run
```bash
docker compose up -d
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)..
