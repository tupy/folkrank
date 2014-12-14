import sys
from sna.db.dbaccess import User, Bookmark, Image, Document, Tweet, Video, \
Resource, Tag, db, UserResourceTag
from sna.study import network

from sna.db.services import DELICIOUS, FLICKR, SLIDESHARE, TWITTER, YOUTUBE

DEFAULT = 'DEFAULT'
RESOURCE_TYPES = {
    DELICIOUS: Bookmark(),
    FLICKR: Image(),
    SLIDESHARE: Document(),
    TWITTER: Tweet(),
    YOUTUBE: Video(),
    DEFAULT: Resource(),
}

def get_total_no_users():
    return len(User().fetchFromDB().users)

def get_total_no_resources(rtype=DEFAULT):
    r = RESOURCE_TYPES[rtype or DEFAULT]
    return len(r.fetchFromDB().resources)

def get_total_no_tags():
    return len(Tag().fetchFromDB().tags)

def get_total_no_urt(rtype=None, urt=None):
    if not urt: 
        u, r, t = User(), Resource(), Tag()
        u.fetchFromDB()
        r.fetchFromDB()
        t.fetchFromDB()
        urt = UserResourceTag(User(), Resource(), Tag())

    if rtype == DELICIOUS:
        q = urt.q_del
    elif rtype == FLICKR:
        q = urt.q_img
    elif rtype == SLIDESHARE:
        q = urt.q_doc
    elif rtype == TWITTER:
        q = urt.q_tw
    elif rtype == YOUTUBE:
        q = urt.q_yt
    else:
        q = urt.q_all   # all

    urt.fetchFromDB_query(q)
    return len(urt.urt)

def user_LCC(username, account):
    '''Local Clustering Coeffiecient for a user. 
    The of the graph vertices are the users, and the edges the foaf:knows relations.
    '''
    userUri = User.fetchUser(username, account)     # vertex (vi)

    if not userUri:
        raise ValueError('User %s for network %s not found' % (username, account))

    outv = User.fetchFriends(userUri)               # out vertices
    inv = User.fetchFollowers(userUri)              # in vertices

    neigh = set(outv + inv)                         # Neighbourhood - all vertices linked to vi
    k = len(neigh)

    # get edges in the neighbourhood (neigh) ejk = (vj,vk), where vj, vk are in neigh
    e = 0   # no of total edges found
    for vj in neigh:
        for vk in neigh:
            if vj != vk:
                ejk = (vj, vk)
                if User.is_friend_with(vj, vk):
                    e = e + 1

    lcc = float(e) / k * (k - 1) if k > 1 else 0
    info = (len(outv), len(inv), k, e)

    return (lcc, info)

def print_LCC_stats_for_user(acc_username, acc_type):
    print '\nLCC for', acc_username, 'in network', acc_type,':'

    try:
        lcc, info = user_LCC(acc_username, acc_type)
        print 'lcc =', lcc
        print '(friends=%s,followers=%s,neighbourhood size(k)=%s,edges in neigh=%s)' % info
    except ValueError, e:
        print 'ERROR(failed to calculate LCC):', e

def print_LCC_stats():
    print 'Local Clustering Coefficients:'
    accounts = network.parse_accounts(open('people.in'))

    for account in accounts:
        pers_accounts = accounts[account]
        for acc_type in pers_accounts:
            acc_username = pers_accounts[acc_type]
            print_LCC_stats_for_user(acc_username, acc_type)

def print_stats():
    print 'Total triples =', len(db)

    print 'Total no of users =', get_total_no_users()

    print 'Total no of resources =', get_total_no_resources()

    print '\tTotal no of Bookmarks(Delicious) =', get_total_no_resources(rtype=DELICIOUS)

    print '\tTotal no of Documents(SlideShare) =', get_total_no_resources(rtype=SLIDESHARE)

    print '\tTotal no of Images(Flickr) =', get_total_no_resources(rtype=FLICKR)

    print '\tTotal no of Tweets(Twitter) =', get_total_no_resources(rtype=TWITTER)

    print '\tTotal no of Videos(YouTube) =', get_total_no_resources(rtype=YOUTUBE)

    print 'Total no of tags =', get_total_no_tags()

    # fetch data to use in all next calls
    u, r, t = User(), Resource(), Tag()
    u.fetchFromDB(), r.fetchFromDB(), t.fetchFromDB()
    urt = UserResourceTag(u, r, t)

    print 'Total no of taggings =', get_total_no_urt(urt=urt)

    print '\tTotal no of taggings(Delicious) =', get_total_no_urt(rtype=DELICIOUS, urt=urt)

    print '\tTotal no of taggings(Slideshare) =', get_total_no_urt(rtype=SLIDESHARE, urt=urt)

    print '\tTotal no of taggings(Flickr) =', get_total_no_urt(rtype=FLICKR, urt=urt)

    print '\tTotal no of taggings(Twitter) =', get_total_no_urt(rtype=TWITTER, urt=urt)

    print '\tTotal no of taggings(YouTube) =', get_total_no_urt(rtype=YOUTUBE, urt=urt)

if __name__ == '__main__':
    print_stats()
    print_LCC_stats()
    print_LCC_stats_for_user('gapox', YOUTUBE)
