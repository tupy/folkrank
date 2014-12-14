'''
Created on 03.11.2009

@author: anamariastoica
'''

from sna.crawler.crawler import CommunityCrawler
import sna.db.dbaccess as dbaccess
import sna.db.services as snaserv
import urllib
import urllib2
import re

defAvatar = 'http://careernetwork.msu.edu/wp-content/themes/cspMSU_v4.1/_images/twitter-logo.png'

class TwitterCrawler(CommunityCrawler):
    '''
    Crawls twitter and updates social network and tagged resources to repository
    '''

    def __init__(self, params):
        self.service = snaserv.TWITTER

        import twython
        self.twapi = twython.core.setup(username=params['username'], password=params['password'])
        self.userBaseUri = 'http://twitter.com/%s'                   # % user screen_name
        self.tagBaseUri = 'http://twitter.com/#search?q=#%s'         # % trend key word

        self.tweetBaseUri = 'http://twitter.com/%s/status/%s'        # % (user screen_name, status id)

        CommunityCrawler.__init__(self)

    @staticmethod
    def getname():
        return self.service
    
    @staticmethod
    def getDefaultAvatar():
        return defAvatar
        
    @staticmethod
    def factory(user, params=None, depth=2, last_added=None, verbose=False):
	    # Twitter crawler
        params = {'username':'ltfll', 'password':'socialnetassistant'}
        twcrawl = TwitterCrawler(params)
        twcrawl.setStartUserId(user)
        twcrawl.setMaxLevel(depth)
        twcrawl.setLastAdded(last_added)
        twcrawl.setVerbose(verbose)
        return twcrawl

    def updateDatabase(self, user_metadata, user_ntw, udate=None):
        username = user_metadata['username']
        userUri = self.userBaseUri % username
        resourceUri = None
        added = 0

        # add user to repository
        dbaccess.User.addToDB(userUri, self.service, username, 
            TwitterCrawler.getDefaultAvatar(), udate=udate)

        # add resources, tags and relations between them to repository
        for resource in user_metadata['data']:
            # add tweet resource to repository
            resourceId = resource['id']
            resourceTitle = resource['text']
            resourceUri = self.tweetBaseUri % (username, resourceId)

            dbaccess.Tweet.addToDB(resourceUri, resourceTitle, udate=udate)
            added += 1

            # add tag(trend) relations to repository
            for tag in self.parseTags(resourceTitle):
                tagUri = self.tagBaseUri % urllib.quote(tag.encode('utf-8'))
                # add tag to repository
                dbaccess.Tag.addToDB(tagUri, tag, udate=udate)
                # add user, resource, tag relation to repository
                dbaccess.UserResourceTag.addToDB(userUri, resourceUri, tagUri, udate=udate)

            # add url relations between the tweet and urls contained
            urls = map(self.getRealUrl, self.parseUrls(resourceTitle))
            for url in urls:
                dbaccess.Bookmark.addToDB(url, None)
                dbaccess.Tweet.addReferenceToDB(resourceUri, url)

        # add user social network relations to repository
        # add friends
        for u in user_ntw['knows']:
            knownUserUri = self.userBaseUri % u
            dbaccess.User.addToDB(knownUserUri, self.service, u, 
                TwitterCrawler.getDefaultAvatar(), udate=udate)
            dbaccess.User.addToDBUserKnowsUser(userUri, knownUserUri, udate=udate)

        # add followers
        for u in user_ntw['fans']:
            otherUserUri = self.userBaseUri % u
            dbaccess.User.addToDB(otherUserUri, self.service, u, 
                TwitterCrawler.getDefaultAvatar(), udate=udate)
            dbaccess.User.addToDBUserKnowsUser(otherUserUri, userUri, udate=udate)

        # return number of added resources and last added resource uri
        return added

    def fetchUserMetadata(self, username):
        # get user tweets (only last 20)
        data = self.twapi.getUserTimeline(screen_name=username)
        return { 'username': username, 'data': data}

    def fetchUserNetwork(self, username):
        chunk_size = 100	# max returned by bulkUserLookup

        # Get Friends
        fids, cursor = [], -1
        while True:
            f = self.twapi.getFriendsIDs(screen_name=username, cursor=cursor)
            fids.extend(f['ids'])
            if f['next_cursor'] == cursor or len(f['ids']) == 0:
                break
            cursor = f['next_cursor']

        # get screen names from ids in chunks of 100
        fchunks = [fids[i:i + chunk_size] for i in range(0, len(fids), chunk_size)]
        screen_names = []
        for chunk in fchunks:
            # get all user data for all user ids
            screen_names.extend([userdata['screen_name'] 
                for userdata in self.twapi.bulkUserLookup(ids=chunk)])

        ntw_knows = screen_names

        # Get Followers
        fids, cursor = [], -1
        while True:
            f = self.twapi.getFollowersIDs(screen_name=username, cursor=cursor)
            fids.extend(f['ids'])
            if f['next_cursor'] == cursor or len(f['ids']) == 0:
                break
            cursor = f['next_cursor']
        
        # get screen names from ids in chunks of 100
        fchunks = [fids[i:i + chunk_size] for i in range(0, len(fids), chunk_size)]
        fan_screen_names = []
        for chunk in fchunks:
            # get all data for all user ids
            fan_screen_names.extend([userdata['screen_name'] 
                for userdata in self.twapi.bulkUserLookup(ids=chunk)])
        
        ntw_fans = fan_screen_names

        return {'knows': ntw_knows, 'fans': ntw_fans}

    def fetchUser(self, username):
        return (self.fetchUserMetadata(username), self.fetchUserNetwork(username))

    def parseTags(self, text):
        '''
        Parses trends from tweet: '#trend #tre#nd ## #trend,two #tren%^& smth,#da #1dc #100 #1dc$ #100^',
        finds trends: trend, tre, trend, tren, da, 1dc, 100, 1dc, 100.
        Text parameter MUST be UNICODE encoded: u'some text'
        '''
        return re.findall('(?<=[\W^#]#)\w+', ' ' + text, re.UNICODE)

    def parseUrls(self, text):
        '''Returns a list of urls from the text.
        '''
        return re.findall('http://\S+', text)

    def getRealUrl(self, url):
        '''Returns the redirected url if *url* parameter is a shortened url (a redirect was produced), 
        or itself if not.
        '''
        try:
            u = urllib2.urlopen(url)
            realurl = u.geturl()
            if realurl == None: 
                raise urllib2.HTTPError('Could not fetch url')
        except:
            realurl = url

        return realurl


if __name__ == '__main__':
    # Twitter crawler
    params = {'username':'ltfll', 'password':'socialnetassistant'}
    twcrawl = TwitterCrawler(params)
    twcrawl.setVerbose(True)
    twcrawl.setStartUserId('anamariast')
    twcrawl.setMaxLevel(1)
    
    twcrawl.crawlUserNetwork()
