'''
Created on 03.11.2009

@author: anamariastoica
'''

from sna.crawler.crawler import CommunityCrawler
import sna.db.dbaccess as dbaccess
import sna.db.services as snaserv
import urllib
import feedparser

defAvatar = 'http://www.christmastree.org/youtube.jpg'

class YouTubeCrawler(CommunityCrawler):
    '''
    YouTube Crawler
    '''

    def __init__(self):
        self.service = snaserv.YOUTUBE

        import gdata.youtube.service
        self.ytapi = gdata.youtube.service.YouTubeService()
        self.ytapi.ssl = False

        self.userBaseUri = 'http://gdata.youtube.com/feeds/api/users/%s'                                # % username
        self.tagBaseUri = 'http://www.youtube.com/results?search_query=%s&search=tag'                   # ??? % tag
        self.videoBaseUri = 'http://gdata.youtube.com/feeds/api/videos/%s'                              # % videoID

        self.videosFeedBaseUri = 'http://gdata.youtube.com/feeds/api/users/%s/uploads'                  # % username
        self.subscriptionsFeedBaseUri = 'http://gdata.youtube.com/feeds/api/users/%s/subscriptions'     # % username
        self.contactsFeedBaseUri = 'http://gdata.youtube.com/feeds/api/users/%s/contacts'               # % username

        CommunityCrawler.__init__(self)

    @staticmethod
    def getname():
        return self.service

    @staticmethod
    def getDefaultAvatar():
        return defAvatar

    @staticmethod
    def factory(user, depth=2, last_added=None, verbose=False):
        ytcrawl = YouTubeCrawler()
        ytcrawl.setStartUserId(user)
        ytcrawl.setMaxLevel(depth)
        ytcrawl.setLastAdded(last_added)
        ytcrawl.setVerbose(verbose)
        return ytcrawl

    def updateDatabase(self, user_metadata, user_ntw, udate=None):
        userUri = user_metadata['profile']['id']
        username = user_metadata['profile']['username']
        resourceUri = None
        added = 0

        # add user to repository
        dbaccess.User.addToDB(userUri, self.service, username, YouTubeCrawler.getDefaultAvatar(), udate=udate)

        # add resources, tags and relations between them to repository
        for entry in user_metadata['videos'].entry:
            # add resource to repository
            resourceUri = entry.id.text
            # entry.media.title.text                        # rdfs.label | dc.title # entry.media.payer.url / entry.GetSwfUrl()     (watch page / flash player URL)
            dbaccess.Video.addToDB(resourceUri, entry.title.text, udate=udate)
            added += 1

            tags = entry.media.keywords.text.split(", ")
            for tag in tags:
                tagUri = self.tagBaseUri % urllib.quote(tag.encode('utf-8'))
                # add tag to repository
                dbaccess.Tag.addToDB(tagUri, tag, udate=udate)
                # add user, resource, tag relation to repository
                dbaccess.UserResourceTag.addToDB(userUri, resourceUri, tagUri, udate=udate)

        # add user social network relations to repository
        for u in user_ntw['knows']:
            knownUserUri = self.userBaseUri % u
            dbaccess.User.addToDB(knownUserUri, self.service, u, YouTubeCrawler.getDefaultAvatar(), udate=udate)
            dbaccess.User.addToDBUserKnowsUser(userUri, knownUserUri, udate=udate)

        return added

    def fetchUser(self, username):
        userUri = self.userBaseUri % username
        videosFeedUri = self.videosFeedBaseUri % username

        # get profile data ---> could be also fetched from YouTube : 
        # user_entry = self.ytapi.GetYouTubeUserEntry(username='username')
        profile_feed = {'username': username, 'id': userUri}
        # get video data
        videos_feed = self.ytapi.GetYouTubeVideoFeed(videosFeedUri)

        # create user_metadata object
        user_metadata = {'profile': profile_feed, 'videos': videos_feed}

        # get user subscriptions
        subscription_uri = self.subscriptionsFeedBaseUri % username
        contacts = []
        doc = feedparser.parse(subscription_uri)
        for entry in doc.entries:
            contacts.append(entry.yt_username)

        # create user social network object
        user_ntw = {'knows': contacts}

        return (user_metadata, user_ntw)

if __name__ == '__main__':
    # YouTube crawler
    ytcrawl = YouTubeCrawler()
    ytcrawl.setStartUserId('anamaria0509')
    ytcrawl.setStartUserId('HDCYT')
    ytcrawl.setMaxLevel(1)

    ytcrawl.crawlUserNetwork()
