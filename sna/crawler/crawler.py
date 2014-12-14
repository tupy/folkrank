'''
Created on April 9, 2009

@author: anamariastoica
'''

import sna.db.dbaccess as dbaccess
import time
import threading

class CommunityCrawler(object):
    '''
    Kind of an abstract class for Social Network Crawlers
    Gets resources and friends up to a certain level
    '''

    def __init__(self, max_level=2):
        self.max_level = max_level

    def setStartUserId(self, start_user_id):
        self.start_user_id = start_user_id

    def setMaxLevel(self, max_level):
        self.max_level = max_level

    def setLastAdded(self, last_added):
        self.last_added = last_added

    def updateDatabase(self, user_metadata, user_ntw, udate=None):
        raise NotImplementedError()

    def fetchUser(self, username):
        return (None, {'knows':[], 'fans':[]})

    def getUserUri(self, username):
        return self.userBaseUri % username

    def crawlUserNetwork(self, user_id=None, max_level=0, start_time=None):
        '''
        user_id - an id to uniquely identify a user (can be a username or userid)
        '''
        user_id = user_id or self.start_user_id
        max_level = max_level or self.max_level

        queue = [user_id]               # init queue
        visited = {user_id: 0}          # init visited nodes
        added = 0                       # set number of added resources

        while queue:
            v = queue.pop(0)            # pop next user node
            level = visited[v]          # get their level

            # get user metadata and social network
            user_metadata, user_ntw = self.fetchUser(v)

            # update database with user data, tagged resources and social network relations
            a = self.updateDatabase(user_metadata, user_ntw, udate=start_time)
            added += a

            # explore following nodes
            for w in user_ntw['knows']:
                if w not in visited and level < max_level:
                    queue.append(w)
                    visited[w] = level + 1

        return added

class CommunityCrawlerThread(threading.Thread):

    def __init__(self, communityCrawler, start_time=None):
        '''
        Initialize the thread data.
        Required parameters:
            - communityCrawler - the community crawler; the crawler MUST have 
                set the stating user id
        '''
        self.communityCrawler = communityCrawler
        self.start_time = start_time
        self.result = None

        threading.Thread.__init__(self)

    def run (self):
        self.result = self.communityCrawler.crawlUserNetwork(
            start_time=self.start_time)

class CrawlNetworks():
    '''
    Creates a thread for each of the crawlers and runs them concurrently
    '''
    def __init__(self, crawlers):
        self.crawlers = crawlers

    def crawl(self, start_time=None):
        # create threads for each crawler in list
        cthreads = [CommunityCrawlerThread(c, start_time=start_time) 
            for c in self.crawlers]

        # run all threads
        for cth in cthreads:
            cth.start()

        # wait for all threads to finish
        for cth in cthreads:
            cth.join()

if __name__ == '__main__':
    # create crawlers using user network accounts data
    # Delicious crawler
    from sna.crawler.deliciouscrawler import DeliciousCrawler
    delicrawl = DeliciousCrawler()
    delicrawl.setStartUserId('anamaria0509')
    delicrawl.setMaxLevel(2)

    # Flickr crawler   
    from sna.crawler.flickrcrawler import FlickrCrawler
    params = {'api_key': 'ac91a445a4223af2ceafb06ae50f9a25'}
    fcrawl = FlickrCrawler(params)
    fcrawl.setStartUserId('anamaria stoica')
    fcrawl.setMaxLevel(2)

    # YouTube crawler
    from sna.crawler.youtubecrawler import YouTubeCrawler
    ytcrawl = YouTubeCrawler()
    ytcrawl.setStartUserId('anamaria0509')
    ytcrawl.setMaxLevel(2)

    # SlideShare crawler
    from sna.crawler.slidesharecrawler import SlideShareCrawler
    params = {'api_key': 'hGB0A4by', 'secret_key': '3qjmDPUM'}
    sscrawl = SlideShareCrawler(params)
    sscrawl.setStartUserId('anamaria0509')
    sscrawl.setMaxLevel(2)

    # all crawlers list
    crawlers = [ delicrawl, fcrawl, ytcrawl, sscrawl ]
    t1 = time.clock()
    CrawlNetworks(crawlers).crawl()
    t2 = time.clock()

    print 'Finished in %d seconds' % (t2-t1)
    print len(dbaccess.db)
