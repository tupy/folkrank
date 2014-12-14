'''
Created on 03.11.2009

@author: anamariastoica
'''

from sna.crawler.crawler import CommunityCrawler
import sna.db.dbaccess as dbaccess
import sna.db.services as snaserv
import urllib

defAvatar = 'http://wire.wiscnet.net/wp-content/uploads/2009/04/delicious-60x60.png'

class DeliciousCrawler(CommunityCrawler):
    '''
    Crawls delicious and updates social network and tagged resources to repository
    '''

    def __init__(self):
        self.service = snaserv.DELICIOUS

        import deliciousapi
        self.dapi = deliciousapi.DeliciousAPI()
        self.userBaseUri = 'http://delicious.com/%s'            # % username
        self.tagBaseUri = 'http://delicious.com/tag/%s'         # % tagname

        CommunityCrawler.__init__(self)

    @staticmethod
    def getname():
        return self.service

    @staticmethod
    def getDefaultAvatar():
        return defAvatar

    @staticmethod
    def factory(user, depth=2, last_added=None, verbose=False):
        delicrawl = DeliciousCrawler()
        delicrawl.setStartUserId(user)
        delicrawl.setMaxLevel(depth)
        delicrawl.setLastAdded(last_added)
        delicrawl.setVerbose(verbose)
        return delicrawl

    def updateDatabase(self, user_metadata, user_ntw, udate=None):
        username = user_metadata.username
        userUri = self.userBaseUri % username
        resourceUri = None
        added = 0

        # add user to repository
        dbaccess.User.addToDB(userUri, self.service, username, 
            DeliciousCrawler.getDefaultAvatar(), udate=udate)

        # add resources, tags and relations between them to repository
        for resourceUri,tags,resourceTitle,_,_ in user_metadata.bookmarks:
            # add bookmark resource to repository
            dbaccess.Bookmark.addToDB(resourceUri, resourceTitle, udate=udate)
            added += 1
            for tag in tags:
                # don't add system:unfiled tag to repository
                if tag == 'system:unfiled':
                    continue

                tagUri = self.tagBaseUri % urllib.quote(tag.encode('utf-8'))
                # add tag to repository
                dbaccess.Tag.addToDB(tagUri, tag, udate=udate)
                # add user, resource, tag relation to repository
                dbaccess.UserResourceTag.addToDB(userUri, resourceUri, tagUri, udate=udate)

        # add user social network relations to repository
        for u in user_ntw['knows']:
            knownUserUri = self.userBaseUri % u
            dbaccess.User.addToDB(knownUserUri, self.service, u, 
                DeliciousCrawler.getDefaultAvatar(), udate=udate)
            dbaccess.User.addToDBUserKnowsUser(userUri, knownUserUri, udate=udate)

        # return number of added resources and last added resource uri
        return added

    def fetchUserMetadata(self, username):
        return self.dapi.get_user(username)

    def fetchUserNetwork(self, username):
        ntw = self.dapi.get_network(username)
        try:
            ntw_knows = [u[0] for u in ntw[0]]
        except:
            ntw_knows = []

        try:
            ntw_fans = [u[1] for u in ntw[1]]
        except:
            ntw_fans = []

        return {'knows': ntw_knows, 'fans': ntw_fans}

    def fetchUser(self, username):
        return (self.fetchUserMetadata(username), self.fetchUserNetwork(username))
    
if __name__ == '__main__':
    # Delicious crawler
    delicrawl = DeliciousCrawler()
    delicrawl.setStartUserId('anamaria0509')
    delicrawl.setMaxLevel(1)

    delicrawl.crawlUserNetwork()
        