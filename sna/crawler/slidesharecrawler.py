'''
Created on 03.11.2009

@author: anamariastoica
'''

from sna.crawler.crawler import CommunityCrawler
import sna.db.dbaccess as dbaccess
import sna.db.services as snaserv
import urllib

defAvatar = 'http://press.slideshare.net/wp-content/uploads/2008/12/slideshare_550x150.png'

class SlideShareCrawler(CommunityCrawler):
    '''
    Crawls SlideShare and updates social network and tagged resources to repository
    '''

    def __init__(self, params):
        self.service = snaserv.SLIDESHARE

        import slideshareapi
        self.ssapi = slideshareapi.SlideShareAPI(params)

        self.userBaseUri = 'http://www.slideshare.net/%s'            # % username
        self.tagBaseUri = 'http://www.slideshare.net/tag/%s'         # % tagname

        CommunityCrawler.__init__(self)

    @staticmethod
    def getname():
        return self.service

    @staticmethod
    def getDefaultAvatar():
        return defAvatar

    @staticmethod
    def factory(user, depth=2, last_added=None, verbose=False):
        params = {'api_key': 'hGB0A4by', 'secret_key': '3qjmDPUM'}
        sscrawl = SlideShareCrawler(params)
        sscrawl.setStartUserId(user)
        sscrawl.setMaxLevel(depth)
        sscrawl.setLastAdded(last_added)
        sscrawl.setVerbose(verbose)
        return sscrawl

    def updateDatabase(self, user_metadata, user_ntw, udate=None):
        username = user_metadata.User.name
        userUri = self.userBaseUri % username
        resourceUri = None
        added = 0

        # add user to repository
        dbaccess.User.addToDB(userUri, self.service, username, 
            SlideShareCrawler.getDefaultAvatar(), udate=udate)

        # add resources, tags and relations between them to repository
        for s in user_metadata.User.Slideshow:
            resourceUri = s.Permalink
            # add slideshow resource to repository
            dbaccess.Document.addToDB(resourceUri,
                resourceUri.rpartition("/")[2].replace("-", " "), udate=udate)
            added += 1

            tags = s.Tags or 'system:unfiled'
            for tag in tags.split(" "):
                tagUri = self.tagBaseUri % urllib.quote(tag.encode('utf-8'))
                # add tag to repository
                dbaccess.Tag.addToDB(tagUri, tag, udate=udate)
                # add user, resource, tag relation to repository
                dbaccess.UserResourceTag.addToDB(userUri, resourceUri, tagUri, udate=udate)

        # add user social network relations to repository
        for u in user_ntw['knows']:
            knownUserUri = self.userBaseUri % u
            dbaccess.User.addToDB(knownUserUri, self.service, u, 
                SlideShareCrawler.getDefaultAvatar(), udate=udate)
            dbaccess.User.addToDBUserKnowsUser(userUri, knownUserUri, udate=udate)

        return added

    def fetchUserMetadata(self, username):
        return self.ssapi.get_slideshow_by_user(username)

    def fetchUserNetwork(self, username):
        ntw = self.ssapi.get_user_contacts(username)
        ntw_knows = [c.Username for c in ntw.Contacts.Contact]
        return {'knows': ntw_knows, 'fans': []}

    def fetchUser(self, username):
        return (self.fetchUserMetadata(username), self.fetchUserNetwork(username))

if __name__ == '__main__':
    # SlideShare crawler
    params = {'api_key': 'hGB0A4by', 'secret_key': '3qjmDPUM'}
    sscrawl = SlideShareCrawler(params)
    sscrawl.setStartUserId('anamaria0509')
    sscrawl.setMaxLevel(1)

    sscrawl.crawlUserNetwork()
    