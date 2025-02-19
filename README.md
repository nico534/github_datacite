# GitHub DataCite action

Action to generate DataCite xml from a GitHub repository.

Example usage in workflows:
```yaml
name: Create GitHub DataCite xml file
on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'
jobs:
  createCite:
    name: Create a DataCite XML
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Extract repoOwner and repoName
        run: |
          REPO_FULL_NAME="${{ github.repository }}"
          REPO_OWNER=$(echo "$REPO_FULL_NAME" | cut -d'/' -f1)
          REPO_NAME=$(echo "$REPO_FULL_NAME" | cut -d'/' -f2)
          echo "REPO_OWNER=$REPO_OWNER" >> $GITHUB_ENV
          echo "REPO_NAME=$REPO_NAME" >> $GITHUB_ENV

      - name: Get DataCite xml file
        uses: nico534/github_datacite@main
        id: datacite-xml
        with:
          apiToken: ${{ secrets.GITHUB_TOKEN }}
          repoOwner: ${{ env.REPO_OWNER }}
          repoName: ${{ env.REPO_NAME }}
      - name: Create data-cite xml file
        uses: 1arp/create-a-file-action@0.4.5
        with:
          file: "data-cite.xml"
          content: ${{ steps.datacite-xml.outputs.datacitexml }}

      - name: Commit file
        run: |
          git config --local user.name "github-actions[bot]"
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git add data-cite.xml
          git commit -m "Add data-cite file"
          git push
```
