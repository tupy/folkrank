'''
Created on 03.11.2009

@author: anamariastoica
'''

from sna.crawler.crawler import CommunityCrawler
import sna.db.dbaccess as dbaccess
import sna.db.services as snaserv
import urllib

defAvatar = 'http://wire.wiscnet.net/wp-content/uploads/2009/04/flickr-logo.png'

class FlickrCrawler(CommunityCrawler):
    '''
    Crawls Flickr and updates social network and tagged resources to repository
    '''

    def __init__(self, params):
        self.service = snaserv.FLICKR

        import flickrapi
        self.fapi = flickrapi.FlickrAPI(params['api_key'], format='etree')

        self.userBaseUri = 'http://www.flickr.com/people/%s'         # % user_id
        self.tagBaseUri = 'http://www.flickr.com/photos/tags/%s'     # % tagname
        self.photoBaseUri = 'http://www.flickr.com/photos/%s/%s'     # % (user_id, photo_id)

        CommunityCrawler.__init__(self)

    @staticmethod
    def getname():
        return self.service

    @staticmethod
    def getDefaultAvatar():
        return defAvatar

    @staticmethod
    def factory(user, depth=2, last_added=None, verbose=False):
        params = {'api_key': 'ac91a445a4223af2ceafb06ae50f9a25'}
        fcrawl = FlickrCrawler(params)
        fcrawl.setStartUserId(user)
        fcrawl.setMaxLevel(depth)
        fcrawl.setLastAdded(last_added)
        fcrawl.setVerbose(verbose)
        return fcrawl

    def updateDatabase(self, user_metadata, user_ntw, udate=None):
        nsid = user_metadata['nsid']
        userUri = self.userBaseUri % nsid
        resourceUri = None
        added = 0

        # add user to repository
        dbaccess.User.addToDB(userUri, self.service, nsid, 
            FlickrCrawler.getDefaultAvatar(), udate=udate)

        # add resources, tags and relations between them to repository
        res = user_metadata['photos_data']
        photos = res.find('photos').findall('photo')
        for photo in photos:
            resourceUri = self.photoBaseUri % (nsid, photo.attrib['id'])
            # add image to repository
            dbaccess.Image.addToDB(resourceUri, photo.attrib['title'], udate=udate)
            added += 1

            tags = photo.attrib['tags']
            if not tags: tags = 'system:unfiled'    # if no tags, put # 'system:unfiled'
            for tag in tags.split(" "):
                tag = tag.encode('utf-8')
                tagUri = self.tagBaseUri % urllib.quote(tag)
                # add tag to repository
                dbaccess.Tag.addToDB(tagUri, tag, udate=udate)
                # add user, resource, tag relation to repository
                dbaccess.UserResourceTag.addToDB(userUri, resourceUri, tagUri, udate=udate)

        # add user social network relations to repository
        for u in user_ntw['knows']:
            knownUserUri = self.userBaseUri % u
            dbaccess.User.addToDB(knownUserUri, self.service, u, 
                FlickrCrawler.getDefaultAvatar(), udate=udate)
            dbaccess.User.addToDBUserKnowsUser(userUri, knownUserUri, udate=udate)

        # return number of added resources and last added resource uri
        return added

    def fetchUserMetadata(self, nsid):
        # get public images for user id
        res2 = self.fapi.people_getPublicPhotos(user_id=nsid, extras='tags')
        if res2.attrib['stat'] != 'ok':
            return None

        return {'nsid': nsid, 'photos_data': res2}

    def fetchUserNetwork(self, nsid):
        res = self.fapi.contacts_getPublicList(user_id=nsid)
        ntw_knows = [c.attrib['nsid'] for c in res.find('contacts').findall('contact')]
        return {'knows': ntw_knows, 'fans': []}

    def fetchUser(self, nsid):
        return (self.fetchUserMetadata(nsid), self.fetchUserNetwork(nsid))

    def crawlUserNetwork(self, user_id=None, max_level=0, last_added=None, start_time=None):
        '''
        user_id - an id to uniquely identify a user (can be a username or userid)
        '''
        user_id = user_id or self.start_user_id

        # get associated user id for the username
        res1 = self.fapi.people_findByUsername(username=user_id)
        nsid = res1.find('user').attrib['nsid']

        return CommunityCrawler.crawlUserNetwork(self, user_id=nsid, 
            max_level=max_level, last_added=last_added, start_time=start_time)

if __name__ == '__main__':
    # Flickr crawler
    params = {'api_key': 'ac91a445a4223af2ceafb06ae50f9a25'}
    fcrawl = FlickrCrawler(params)
    fcrawl.setStartUserId('anamaria stoica')
    fcrawl.setMaxLevel(1)

    fcrawl.crawlUserNetwork()
    