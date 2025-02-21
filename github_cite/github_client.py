from gql import gql, Client
from graphql import DocumentNode
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError, TransportServerError
from aiohttp.client_exceptions import ClientResponseError
import requests
from datetime import datetime

from exceptions import GithubException

class GithubClient:
  """
  The access point to GitHub to retrieve required information for the DataCite format.
  ...
    Attributes
    ----------
    githubUrl
      The URL to the Github repository
    githubRepoUrl
    githubParentRepoUrl

    Methods
    -------
      get_info()
        Returns basic information for DataCite
      get_contributors()
        Returns a list of all the contributors working on the GitHub repository
      get_last_common_commit(self, ref: str, parentRef: str)
        Returns last common commit between ref and parentRef
      get_last_parent_release_before(self, after_date: str)
        Returns the last release before the given Date from the parent repository
      list_parent_release(self, after: str | None)
        Fetch one page of releases from the parent repository
      list_commits(self, ref: str, after: str | None, parent: bool = False)
        Fetch one page of commits
  """
  def __init__(self, repoOwner: str, repoName: str, githubApiUrl: str = "https://api.github.com", githubUrl: str = "https://github.com", barerToken: str | None = None):
    """ Constructor

    Parameters:
    ----------
    repoOwner: str
      The owner of the GitHub repository
    repoName: str
      The name of the GitHub repository
    githubUrl: str, optional
      The URL to the GitHub instance. Default https://api.github.com
    barerToken: str | None, optional
      GitHub token used for authentication
    """

    self.githubUrl = githubUrl
    self.githubRepoUrl = f"{githubUrl}/{repoOwner}/{repoName}"
    self.githubParentRepoUrl = ""

    self.rSession = requests.Session()
    self.restBaseUrl = f"{githubApiUrl}/repos/{repoOwner}/{repoName}"
    if barerToken and barerToken != "":
      self.transport = AIOHTTPTransport(url=f"{githubApiUrl}/graphql", headers={'Authorization': f'Bearer {barerToken}'})
      self.rSession.headers.update({'Authorization': f'Bearer {barerToken}'})
    else:
      self.transport = AIOHTTPTransport(url=f"{githubApiUrl}/graphql")
    self.client = Client(transport=self.transport, fetch_schema_from_transport=True)
    self.repoOwner = repoOwner
    self.repoName = repoName
    self.checked_parent_branches = False

  def __send_request__(self, query: DocumentNode, options=None):
    """Execute a GraphQL api request

      The repository and owner are added to the options and can be accessed with
      $repoOwner and $repoName

      Parameters
      ----------
        query: DocumentNode
          The GraphQL query
        options: str | None, optional
          Additional options

      Raises
      ------
        GithubException
          If there are any issues with the request.
    """
    params = {"repoOwner": self.repoOwner, "repoName": self.repoName}
    if options:
      params.update(options)

    try:
      result = self.client.execute(query, variable_values=params)
      return result
    except ClientResponseError as e:
      raise GithubException(e.message, e.status)
    except TransportServerError as e:
      message = e.__str__()
      if e.code == 403:
        message = "GitHub rate limit exceeded. Please us a GitHub API token or try again later."
      raise GithubException(message, e.code)
    except TransportQueryError as e:
      raise GithubException(e.args[0], 500)



  def get_info(self):
    """Returns basic information from the GitHub repository

      Raises
      ------
        GithubException
          If there are any issues with the GraphQL request.
    """
    query = gql(
        """
      query ReleaseInfo($repoOwner: String!, $repoName: String!) {
        repository (owner: $repoOwner, name: $repoName) {
          ...RepoInfo
          parent {
            defaultBranchRef {
              prefix
              name
            }
            name
            isArchived
            owner {
              login
            }
          }
        }
      }
      fragment RepoInfo on Repository {
        description
        url
          licenseInfo {
            name
            url
            spdxId
          }
          createdAt
          defaultBranchRef {
            prefix
            name  
          }
          isArchived
          isFork
          name
          owner {
            ... on User {
              name
            }
            ... on Organization {
              name
            }
          }
          pushedAt
      }
        """
    )
    data = self.__send_request__(query)['repository']
    if data['parent'] != None:
      self.githubParentRepoUrl = f"{self.githubUrl}/{data['parent']['owner']['login']}/{data['parent']['name']}"
    return data


  def get_contributors(self):
    """
    Returns
    -------
    list
      A list of all contributors
    """
    r = self.rSession.get(
      f"{self.restBaseUrl}/contributors?sort=contributions"
    )
    return list(map(lambda d: self.rSession.get(d['url']).json(), r.json()))

  def get_last_common_commit(self, ref: str, parentRef: str):
    """Get last common commit between ref and parentRef

      Parameters
      ----------
        ref: str
          start point of current
        parentRef: str
          start point of parent
          
      Raises
      ------
        GithubException
          If there are any issues with the GraphQL request.
          
      Returns
      -------
        commit
          the last common commit
    """
    historyOne = self.list_commits(ref, None)
    historyTwo = self.list_commits(parentRef, None, parent=True)
    historyOneIter = iter(historyOne['nodes'])
    historyTwoIter = iter(historyTwo['nodes'])
    historyOneCurr = next(historyOneIter)
    historyTwoCurr = next(historyTwoIter)
    while historyOneCurr['oid'] != historyTwoCurr['oid']:
      if datetime.fromisoformat(historyOneCurr['committedDate']) < datetime.fromisoformat(historyTwoCurr['committedDate']):
        try:
          historyTwoCurr = next(historyTwoIter)
        except StopIteration:
          if historyTwo['pageInfo']['hasNextPage']:
            historyTwo = self.list_commits(ref, historyTwo['pageInfo']['endCursor'], parent=True)
            historyTwoIter = iter(historyTwo['nodes'])
            historyTwoCurr = next(historyTwoIter)
          else:
            return None
      else:
        try:
          historyOneCurr = next(historyOneIter)
        except StopIteration:
          if historyOne['pageInfo']['hasNextPage']:
            historyOne = self.list_commits(ref, historyOne['pageInfo']['endCursor'])
            historyOneIter = iter(historyOne['nodes'])
            historyOneCurr = next(historyOneIter)
          else:
            return None
    return historyOneCurr
  
  def get_last_parent_release_before(self, after_date: str):
    """Get the las release before the given Date from the parent repository
    
      Parameters
      ----------
        after_date: str
          date that specifies the release
          
      Raises
      ------
        GithubException
          If there are any issues with the GraphQL request.

      Returns
      -------
        release
          The release object
    """
    releases = self.list_parent_release(None)
    while True:
      for r in releases['edges']:
        if datetime.fromisoformat(after_date) < datetime.fromisoformat(r['committedDate']):
          return r
      if releases['pageInfo']['hasNextPage']:
        releases = self.list_parent_release(releases['pageInfo']['endCursor'])
      else:
        return None
      
  def list_branches(self):
    """
    Lists all branch names from the repository
    """
    page = self.__fetch_branch_page__(None)
    branches = page['nodes']
    while page['pageInfo']['hasNextPage']:
      page = self.__fetch_branch_page__(after=page['pageInfo']['endCursor'])
      branches = branches + page['nodes']
    return branches
    

  def __fetch_branch_page__(self, after: str | None):
    query = gql(
      """
      query FetchBranches($repoOwner: String!, $repoName: String!, $after: String){
        repository (owner: $repoOwner, name: $repoName) {
          refs(refPrefix:"refs/heads/", first: 100, after: $after){
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              name
            }
          }
        }
      }
    """
    )
    options = None
    if after != None:
      options = {"after": after}
    return self.__send_request__(query, options)['repository']['refs']
  

  def list_releases(self):
    """
    List all releases from the repository.
    
    Returns
    -------
    A list of releases. 
    
    A release object will look like this (json format):
    {
      "release_name": str,
      "tag_name": str,
      "committedDate": str,
      "oid": str

    }
    """
    releasePage = self.__fetch_releases__(None)
    releases = releasePage['edges']
    while(releasePage['pageInfo']['hasNextPage']):
      releasePage = self.__fetch_releases__(releasePage['pageInfo']['endCursor'])
      releases = releases + releasePage['edges']
    return releases
      
  def __fetch_releases__(self, after: str | None):
    query = gql(
      """
      query FetchRelease($repoOwner: String!, $repoName: String!, $after: String){
        repository (owner: $repoOwner, name: $repoName) {
          releases (first: 100, after: $after, orderBy: {field: CREATED_AT, direction: ASC} ){
            pageInfo {
              endCursor
              hasNextPage
            } 
            edges {
              node {
                name
                tag {
                  name
                  target {
                    ... on Commit {
                      committedDate
                      oid
                    }
                  }
                }
              }
            }
          }
        }
      }
    """
    )
    options = None
    if after:
      options = {"after": after}
    resp = self.__send_request__(query, options)
    resp = resp['repository']['releases']
    resp['edges'] = list(filter(lambda a: 'committedDate' in a['node']['tag']['target'], resp['edges']))
    resp['edges'] = list(map(lambda a: {"release_name": a['node']['name'], 'tag_name': a['node']['tag']['name'], 'committedDate': a['node']['tag']['target']['committedDate'], 'oid': a['node']['tag']['target']['oid']}, resp['edges']))
    return resp
  
  def list_parent_release(self, after: str | None):
    """Fetch one page of releases from the parent repository
    
      Parameters
      ----------
        after: str | None
          Cursor for the next 100 releases.
          
      Raises
      ------
        GithubException
          If there are any issues with the GraphQL request.

      Returns
      -------
        releasesPage
          releases with pageInfo and at most 100 release edges
    
    """
    query = gql(
      """
      query FetchParrentRelease($repoOwner: String!, $repoName: String!, $after: String){
        repository (owner: $repoOwner, name: $repoName) {
          parent {
            releases (first: 100, after: $after, orderBy: {field: CREATED_AT, direction: ASC} ){
              pageInfo {
                endCursor
                hasNextPage
              } 
              edges {
                node {
                  name
                  tag {
                    name
                    target {
                      ... on Commit {
                        committedDate
                        oid
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
      """)
    options = None
    if after:
      options = {"after": after}
    resp = self.__send_request__(query, options)
    resp = resp['repository']['parent']['releases']
    resp['edges'] = list(map(lambda a: {"release_name": a['node']['name'], "tag_name": a['node']['tag']['name'], "committedDate": a['node']['tag']['target']['committedDate'], "oid": a['node']['tag']['target']['oid']}, resp['edges']))
    return resp

  def list_commits(self, ref: str, after: str | None, parent: bool = False):
    """Fetch one page of commits

      Parameters
      ----------
        ref: str
          BaseRef to fetch the release history from. For example refs/heads/main
        after: str | None
          Cursor for the next 100 commits.
        parent: bool, optional
          If the commits should come from the parent.
          
      Raises
      ------
        GithubException
          If there are any issues with the GraphQL request.

      Returns
      -------
        releasesPage
          releases with pageInfo and at most 100 release edges
    """
    query = gql(
      """
      query FetchCommits($repoOwner: String!, $repoName: String!, $ref: String!, $after: String){
        repository (owner: $repoOwner, name: $repoName) {
          ref(qualifiedName: $ref) {
            target {
              ... on Commit {
                history (first: 100, after: $after) {
                  pageInfo {
                    endCursor
                    hasNextPage
                  }
                  nodes {
                    oid
                    committedDate
                  }
                }
              }
            }
          }
        }
      }
      """
    )
    if parent:
      query = gql(
        """
        query FetchCommits($repoOwner: String!, $repoName: String!, $ref: String!, $after: String){
          repository (owner: $repoOwner, name: $repoName) {
            parent {
              ref(qualifiedName: $ref) {
                target {
                  ... on Commit {
                    history (first: 100, after: $after) {
                      pageInfo {
                        endCursor
                        hasNextPage
                      }
                      nodes {
                        oid
                        committedDate
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
      )
    options = {
      "ref": ref
    }
    if after:
      options['after'] = after
    resp = self.__send_request__(query, options)['repository']
    if parent:
      resp = resp['parent']
    return resp['ref']['target']['history']
