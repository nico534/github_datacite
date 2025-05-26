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

from github_client import GithubClient
from xml.dom.minidom import Document, Element

class GithubRepoDataCite:
  """Contains the DataCite format for one repository.
  ...

    Methods
    -------
      pretty_xml()
        Returns the DataCite XML document in pretty format.
  """
  def __init__(self, repoOwner: str, repoName: str, githubApiUrl: str = "https://api.github.com", githubUrl: str = "https://github.com", barerToken: str | None = None):
    """ Constructor, will create the dataCite format

      Parameters
      ----------
        repoOwner: str
          The owner of the repository
        repoName: str
          The name of the repository
        barerToken: str | None, optional
          Authentication token to GitHub, default = None

      Raises
      ------
        GithubException
          If there are any exceptions talking with GitHub
    """
    self.client = GithubClient(repoOwner=repoOwner, repoName=repoName, barerToken=barerToken)
    self.base_data = self.client.get_info()
    # print(self.base_data)
    self.contributers = self.client.get_contributors()
    self.doc = Document()
    self.root = self.doc.createElement('resource')
    self.doc.appendChild(self.root)
    self.__add_base_data__(self.root)

    relatedIdentifiers = self.doc.createElement('relatedIdentifiers')

    # Add release identifiers
    for release in reversed(self.client.list_releases()): # reversed so the newest are at the top
      releaseIdentifier = self.doc.createElement('relatedIdentifier')
      releaseIdentifier.setAttribute("relatedIdentifierType", "URL")
      releaseIdentifier.setAttribute("relationType", "HasVersion")
      releaseIdentifier.appendChild(self.doc.createTextNode(f"{self.client.githubRepoUrl}/releases/tag/{release['tag_name']}"))
      relatedIdentifiers.appendChild(releaseIdentifier)

    # Add branch identifiers
    for branch in self.client.list_branches():
      branchIdentifier = self.doc.createElement('relatedIdentifier')
      branchIdentifier.setAttribute("relatedIdentifierType", "URL")
      branchIdentifier.setAttribute("relationType", "IsVariantFormOf")
      branchIdentifier.appendChild(self.doc.createTextNode(f"{self.client.githubRepoUrl}/tree/{branch['name']}"))
      relatedIdentifiers.appendChild(branchIdentifier)

    self.__add_parent_related_identifiers__(relatedIdentifiers)

    self.root.appendChild(relatedIdentifiers)

    creators = self.doc.createElement("creators")
    self.__add_creators__(creators)
    self.root.appendChild(creators)

  def __add_parent_related_identifiers__(self, relatedIdentifiers: Element):
    if self.__get__data__('parent') == None:
      return
    
    # Add related identifier in the fork context
    forkIdentifier = self.doc.createElement("relatedIdentifier")
    forkIdentifier.setAttribute("relatedIdentifierType", "URL")
    forkIdentifier.setAttribute("relationType", "IsDerivedFrom")
    parentUrl = self.client.githubParentRepoUrl
    forkIdentifier.appendChild(self.doc.createTextNode(parentUrl))
    relatedIdentifiers.appendChild(forkIdentifier)

    # find last release befor commit
    currentRef = self.__get__data__("defaultBranchRef", "prefix") + self.__get__data__("defaultBranchRef", "name")
    parentRef = self.__get__data__("parent", "defaultBranchRef", "prefix") + self.__get__data__("parent", "defaultBranchRef", "name")
    lastCommonCommit = self.client.get_last_common_commit(currentRef, parentRef)
    if lastCommonCommit == None:
      return

    # Add commit as related identifier
    lastCommonCommitIdentifier = self.doc.createElement("relatedIdentifier")
    lastCommonCommitIdentifier.setAttribute("relatedIdentifierType", "URL")
    lastCommonCommitIdentifier.setAttribute("relationType", "IsDerivedFrom")
    lastCommonCommitIdentifier.appendChild(self.doc.createTextNode(f"{self.client.githubParentRepoUrl}/commit/{lastCommonCommit['oid']}"))
    relatedIdentifiers.appendChild(lastCommonCommitIdentifier)

    # Get last common release
    forkedRelease = self.client.get_last_parent_release_before(lastCommonCommit['committedDate'])
    if forkedRelease == None:
      return

    versionIdentifier = self.doc.createElement("relatedIdentifier")
    versionIdentifier.setAttribute("relatedIdentifierType", "URL")
    versionIdentifier.setAttribute("relationType", "IsDerivedFrom")
    # relatedIdentifier.setAttribute("archived", archived)

    relatedIdentifierUrl = f"https://github.com/{self.__get__data__('parent', 'owner', 'login')}/{self.__get__data__('parent', 'name')}/releases/tag/{forkedRelease['tag_name']}"

    versionIdentifier.appendChild(self.doc.createTextNode(relatedIdentifierUrl))
    relatedIdentifiers.appendChild(versionIdentifier)

  def __add_base_data__(self, resourceElement: Element):
    """Add basic information to the resource element"""
    # Add basic schema information
    resourceElement.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    resourceElement.setAttribute("xmlns", "http://datacite.org/schema/kernel-4")
    resourceElement.setAttribute("xsi:schemaLocation", "http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4/metadata.xsd")

    # resource Type is Software
    type = self.doc.createElement("resourceType")
    type.appendChild(self.doc.createTextNode("Software"))
    type.setAttribute("resourceTypeGeneral", "Software")
    resourceElement.appendChild(type)

    # Publisher
    publisher = self.doc.createElement("publisher")
    publisher.appendChild(self.doc.createTextNode("GitHub"))
    resourceElement.appendChild(publisher)

    # For now use last pushed data as publicationYear, to be changed in specification
    publicationYear = self.doc.createElement("publicationYear")
    publicationYear.appendChild(self.doc.createTextNode(self.__get__data__('pushedAt')[:4]))
    resourceElement.appendChild(publicationYear)

    # Add base-repo identifier
    identifier = self.doc.createElement("identifier")
    identifier.setAttribute("identifierType", "URL")
    identifier.appendChild(self.doc.createTextNode(self.__get__data__('url')))
    resourceElement.appendChild(identifier)

    # Add title
    titles = self.doc.createElement("titles")
    title = self.doc.createElement("title")
    title.appendChild(self.doc.createTextNode(self.__get__data__('name')))
    titles.appendChild(title)

    # subtitle
    subtitle = self.doc.createElement("title")
    subtitle.setAttribute("titleType", "Subtitle")
    subtitle.appendChild(self.doc.createTextNode(self.__get__data__("description")))
    titles.appendChild(subtitle)
    resourceElement.appendChild(titles)

    # Add licence
    licenceName = self.__get__data__("licenseInfo", "name")
    if licenceName != None:
      rightsList = self.doc.createElement("rightsList")
      license = self.doc.createElement("rights")
      licenceUrl = self.__get__data__("licenseInfo", "url")
      if licenceUrl != None:
        license.setAttribute("rightsURI", licenceUrl)
      license.setAttribute("rightsIdentifierScheme", "spdx")
      licenceId = self.__get__data__("licenseInfo", "spdxId")
      if licenceId != None:
        license.setAttribute("rightsIdentifier", licenceId)
      license.appendChild(self.doc.createTextNode(licenceName))
      rightsList.appendChild(license)
      resourceElement.appendChild(rightsList)

    # Add dates
    dates = self.doc.createElement("dates")
    createdDate = self.doc.createElement("date")
    createdDate.setAttribute("dateType", "Created")
    createdDate.appendChild(self.doc.createTextNode(self.__get__data__('createdAt')))
    dates.appendChild(createdDate)

    updatedDate = self.doc.createElement("date")
    updatedDate.setAttribute("dateType", "Updated")
    updatedDate.appendChild(self.doc.createTextNode(self.__get__data__('pushedAt')))
    dates.appendChild(updatedDate)
    resourceElement.appendChild(dates)

  def __add_creators__(self, creators: Element):
    # Add Creator
    def create_creator(c):
      creator = self.doc.createElement("creator")
      creatorName = self.doc.createElement("creatorName")
      creatorName.setAttribute("nameType", "Personal")

      if 'name' in c and c['name']:
        creatorName.appendChild(self.doc.createTextNode(c['name']))
        creator.appendChild(creatorName)
        split_name = list(c['name'].split(" "))
        if len(split_name) > 1:
          givenName = self.doc.createElement("givenName")
          givenName.appendChild(self.doc.createTextNode(split_name[0]))
          creator.appendChild(givenName)

          familyName = self.doc.createElement("familyName")
          familyName.appendChild(self.doc.createTextNode(split_name[-1]))
          creator.appendChild(familyName)
      else:
        creatorName.appendChild(self.doc.createTextNode(c['login']))
        creator.appendChild(creatorName)
      return creator
    
    
    for c in self.contributers:
      creators.appendChild(create_creator(c))
  
  def __get__data__(self, *path):
    current = self.base_data
    for step in path:
      if current != None and step in current:
        current = current[step]
      else:
        return None
    return current
  
  def pretty_xml(self):
    """ Returns the DataCity XML in pretty format
    """
    return self.doc.toprettyxml()
