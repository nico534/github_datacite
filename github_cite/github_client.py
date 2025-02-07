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
      fetch_parent_release(self, after: str | None)
        Fetch one page of releases from the parent repository
      fetch_commits(self, ref: str, after: str | None, parent: bool = False)
        Fetch one page of commits
  """
  def __init__(self, repoOwner: str, repoName: str, githubUrl: str = "https://api.github.com", barerToken: str | None = None):
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
    self.rSession = requests.Session()
    self.restBaseUrl = f"{githubUrl}/repos/{repoOwner}/{repoName}"
    if barerToken and barerToken != "":
      self.transport = AIOHTTPTransport(url=f"{githubUrl}/graphql", headers={'Authorization': f'Bearer {barerToken}'})
      self.rSession.headers.update({'Authorization': f'Bearer {barerToken}'})
    else:
      self.transport = AIOHTTPTransport(url=f"{githubUrl}/graphql")
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

    return self.__send_request__(query)


  def get_contributors(self):
    """Returns a list of all contributors
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
    history_one = self.fetch_commits(ref, None)
    history_two = self.fetch_commits(parentRef, None, parent=True)
    history_one_iter = iter(history_one["nodes"])
    history_two_iter = iter(history_two["nodes"])
    history_one_curr = next(history_one_iter)
    history_two_curr = next(history_two_iter)
    while history_one_curr["oid"] != history_two_curr["oid"]:
      if datetime.fromisoformat(history_one_curr["committedDate"]) < datetime.fromisoformat(history_two_curr["committedDate"]):
        try:
          history_two_curr = next(history_two_iter)
        except StopIteration:
          if history_two["pageInfo"]["hasNextPage"]:
            history_two = self.fetch_commits(ref, history_two["pageInfo"]["endCursor"], parent=True)
            history_two_iter = iter(history_two["nodes"])
            history_two_curr = next(history_two_iter)
          else:
            return None
      else:
        try:
          history_one_curr = next(history_one_iter)
        except StopIteration:
          if history_one["pageInfo"]["hasNextPage"]:
            history_one = self.fetch_commits(ref, history_one["pageInfo"]["endCursor"])
            history_one_iter = iter(history_one["nodes"])
            history_one_curr = next(history_one_iter)
          else:
            return None
    return history_one_curr
  
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
    releases = self.fetch_parent_release(None)
    while True:
      for r in releases["edges"]:
        if datetime.fromisoformat(after_date) < datetime.fromisoformat(r["committedDate"]):
          return r
      if releases["pageInfo"]["hasNextPage"]:
        releases = self.fetch_parent_release(releases["pageInfo"]["endCursor"])
      else:
        return None
  
  def fetch_parent_release(self, after: str | None):
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
    resp = resp["repository"]["parent"]["releases"]
    resp["edges"] = map(lambda a: {"release_name": a["node"]["name"], "tag_name": a["node"]["tag"]["name"], "committedDate": a["node"]["tag"]["target"]["committedDate"], "oid": a["node"]["tag"]["target"]["oid"]}, resp["edges"])
    return resp

  def fetch_commits(self, ref: str, after: str | None, parent: bool = False):
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
      options["after"] = after
    resp = self.__send_request__(query, options)["repository"]
    if parent:
      resp = resp["parent"]
    return resp["ref"]["target"]["history"]
