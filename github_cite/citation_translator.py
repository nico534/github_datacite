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
  def __init__(self, repoOwner: str, repoName: str, barerToken: str | None = None):
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
    if self.__get__data__('repository', 'parent') != None:
      # Add related identifier in the fork context
      relatedIdentifiers = self.doc.createElement('relatedIdentifiers')
      forkIdentifier = self.doc.createElement("relatedIdentifier")
      forkIdentifier.setAttribute("relatedIdentifierType", "URL")
      forkIdentifier.setAttribute("relationType", "IsDerivedFrom")
      parentUrl = f"https://github.com/{self.__get__data__('repository', 'parent', 'owner', 'login')}/{self.__get__data__('repository', 'parent', 'name')}"
      forkIdentifier.appendChild(self.doc.createTextNode(parentUrl))
      relatedIdentifiers.appendChild(forkIdentifier)
      self.root.appendChild(relatedIdentifiers)
      
      if self.__get__data__('repository','parent', 'isArchived') != None:
        archived = "false"
      else:
        archived = "true"
      # find last release befor commit
      currentRef = self.__get__data__("repository", "defaultBranchRef", "prefix") + self.__get__data__("repository", "defaultBranchRef", "name")
      parentRef = self.__get__data__("repository", "parent", "defaultBranchRef", "prefix") + self.__get__data__("repository", "parent", "defaultBranchRef", "name")
      lastCommonCommit = self.client.get_last_common_commit(currentRef, parentRef)
      if lastCommonCommit != None:
        # Get last common release
        releaseAfetCommit = self.client.get_last_parent_release_before(lastCommonCommit["committedDate"])

        versionIdentifier = self.doc.createElement("relatedIdentifier")
        versionIdentifier.setAttribute("relatedIdentifierType", "URL")
        versionIdentifier.setAttribute("relationType", "HasVersion")
        # relatedIdentifier.setAttribute("archived", archived)

        relatedIdentifierUrl = f"https://github.com/{self.__get__data__('repository', 'parent', 'owner', 'login')}/{self.__get__data__('repository', 'parent', 'name')}/releases/tag/{releaseAfetCommit['tag_name']}"

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
    publicationYear.appendChild(self.doc.createTextNode(self.__get__data__('repository', 'pushedAt')[:4]))
    resourceElement.appendChild(publicationYear)

    # Add base-repo identifier
    identifier = self.doc.createElement("identifier")
    identifier.setAttribute("identifierType", "URL")
    identifier.appendChild(self.doc.createTextNode(self.__get__data__('repository', 'url')))
    resourceElement.appendChild(identifier)

    # Add title
    titles = self.doc.createElement("titles")
    title = self.doc.createElement("title")
    title.appendChild(self.doc.createTextNode(self.__get__data__('repository', 'name')))
    titles.appendChild(title)

    # subtitle
    subtitle = self.doc.createElement("title")
    subtitle.setAttribute("titleType", "Subtitle")
    subtitle.appendChild(self.doc.createTextNode(self.__get__data__("repository", "description")))
    titles.appendChild(subtitle)
    resourceElement.appendChild(titles)

    # Add licence
    rightsList = self.doc.createElement("rightsList")
    license = self.doc.createElement("rights")
    license.setAttribute("rightsURI", self.__get__data__("repository", "licenseInfo", "url"))
    license.setAttribute("rightsIdentifierScheme", "spdx")
    license.setAttribute("rightsIdentifier", self.__get__data__("repository", "licenseInfo", "spdxId"))
    license.appendChild(self.doc.createTextNode(self.__get__data__("repository", "licenseInfo", "name")))
    rightsList.appendChild(license)
    resourceElement.appendChild(rightsList)

    # Add dates
    dates = self.doc.createElement("dates")
    createdDate = self.doc.createElement("date")
    createdDate.setAttribute("dateType", "Created")
    createdDate.appendChild(self.doc.createTextNode(self.__get__data__('repository', 'createdAt')))
    dates.appendChild(createdDate)

    updatedDate = self.doc.createElement("date")
    updatedDate.setAttribute("dateType", "Updated")
    updatedDate.appendChild(self.doc.createTextNode(self.__get__data__('repository', 'pushedAt')))
    dates.appendChild(updatedDate)
    resourceElement.appendChild(dates)


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
    
    creators = self.doc.createElement("creators")
    for c in self.contributers:
      creators.appendChild(create_creator(c))
    resourceElement.appendChild(creators)
  
  def __get__data__(self, *path):
    current = self.base_data
    for step in path:
      current = current[step]
    return current
  
  def pretty_xml(self):
    """ Returns the DataCity XML in pretty format
    """
    return self.doc.toprettyxml()