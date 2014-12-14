import sys, time

from sna.db.dbaccess import Resource

from sna.crawler.deliciouscrawler import DeliciousCrawler
from sna.crawler.flickrcrawler import FlickrCrawler
from sna.crawler.slidesharecrawler import SlideShareCrawler
from sna.crawler.twittercrawler import TwitterCrawler
from sna.crawler.youtubecrawler import YouTubeCrawler

from sna.crawler.crawler import CrawlNetworks
from sna.db.services import DELICIOUS, FLICKR, SLIDESHARE, TWITTER, YOUTUBE

def parse_accounts(fin):
    """
    username=erikduval; delicious=erikduval; youtube=erikduval; 
    slideshare=erik.duval; flickr=erikduval; twitter=erikduval 
    =>
    {erikduval: {delicious:erikduval, youtube:erikduval, slideshare:erik.duval, 
    flickr:erikduval, twitter:erikduval}, ...}
    """
    accounts = {}
    for line in fin:
        acclist = line.strip().split(';')

        account = {}
        for acc in acclist:
            acc_type, acc_username = acc.strip().split('=')
            if acc_type == 'username':
                account_id = acc_username
            else:
                account[acc_type] = acc_username

        accounts[account_id] = account

    return accounts

def update_network(accounts, depth):
    for account_id in accounts.keys():
        print '\tupdating user:', account_id

        # start time of update
        sdate = time.time()

        acclist = accounts.get(account_id)
        crawlers, personUris = [], []
        for acc_type in acclist:
            acc_username = acclist[acc_type]
            print '\t\tupdating', acc_type, 'account:', acc_username

            if acc_username == '': continue

            if acc_type == DELICIOUS:
                crawl = DeliciousCrawler.factory(acc_username, depth=depth) 
            elif acc_type == FLICKR:
                crawl = FlickrCrawler.factory(acc_username, depth=depth)
            elif acc_type == SLIDESHARE:
                crawl = SlideShareCrawler.factory(acc_username, depth=depth)
            elif acc_type == TWITTER:
                crawl = TwitterCrawler.factory(acc_username, depth=depth)
            elif acc_type == YOUTUBE:
                crawl = YouTubeCrawler.factory(acc_username, depth=depth)

            personUris.append(crawl.getUserUri(acc_username))
            crawlers.append(crawl)

        # create crawlers using user network accounts data
        t1 = time.clock()
        CrawlNetworks(crawlers).crawl(start_time=sdate)
        t2 = time.clock()

        # link resources to each other
        Resource.unify_all(personUris)

        print 'Finished in %d seconds' % (t2 - t1)

if __name__ == '__main__':  
    depth = int(sys.argv[1])
    fname = 'people.in'

    # parse accounts from file
    print 'Parsing accounts from input file...'
    accounts = parse_accounts(open(fname))

    # update network for accounts
    print 'Updating network...'
    update_network(accounts, depth)
    print 'Done updating!'
