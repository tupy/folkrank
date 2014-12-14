'''
Created on April 9, 2009

@author: anamariastoica
'''

from rdfalchemy.sparql.sesame2 import SesameGraph
from rdflib import Namespace, Literal, URIRef, BNode
from datetime import date
import dbaccess_cfg as config
import time
import urllib
import sna.db.services as snaserv

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# import the sesame repository
db = SesameGraph(config.rep)

# namespaces
BOOKMARK = Namespace("http://www.w3.org/2002/01/bookmark#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
SCOT = Namespace("http://scot-project.org/scot/ns#")
VIDEO = Namespace("http://digitalbazaar.com/media/video#")
TAGS = Namespace("http://www.holygoat.co.uk/owl/redwood/0.1/tags/")
DC = Namespace("http://purl.org/dc/elements/1.1/")
SIOC = Namespace("http://rdfs.org/sioc/types#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")


def dbAdd(triplet, msg=None, tries=0):
    '''Adds triplet to repositry and prints a message.
    '''
    if tries < config.TRIES:
        try:
            if msg is not None:
                print msg
            db.add(triplet)
        except:
            print 'Error adding to database'
            time.sleep(config.WAIT)
            dbAdd(triplet, msg, tries+1)


def dbAddReification(statement, reifs, msg=None):
    '''Adding reification for the statement. The additional info is present in reifs 
    dictionary, with the keys being the predicate, and values the objects.
    '''
    print 'adding reification', reifs
    s, p, o = statement
    reifUri = '%s/%s/%s' % (str(s), urllib.quote(str(p)), urllib.quote(str(o)))
    print reifUri
    
    dbAdd((URIRef(reifUri), RDF.type, RDF.Statement), 
        'db.add((%s, %s, %s)' % (URIRef(reifUri), RDF.type, RDF.Statement))
    dbAdd((URIRef(reifUri), RDF.subject, s),
        'db.add((%s, %s, %s)' % (URIRef(reifUri), RDF.subject, s))
    dbAdd((URIRef(reifUri), RDF.predicate, p),
        'db.add((%s, %s, %s)' % (URIRef(reifUri), RDF.predicate, p))
    dbAdd((URIRef(reifUri), RDF.object, o),
        'db.add((%s, %s, %s)' % (URIRef(reifUri), RDF.object, o))

    for pred, obj in reifs:
        dbAdd((URIRef(reifUri), pred, obj),
            'db.add((%s, %s, %s)' % (URIRef(reifUri), pred, obj))


def dbAddCreatedDate(resourceUri, udate):
    '''Add DC.created date relation to resourceUri only if it doesn't already exist.
    '''
    a = 0
    for t in db.triples((URIRef(resourceUri), DC.created, None)):
        a = 1
        break
    if a == 0:
        dbAdd((URIRef(resourceUri), DC.created, Literal(udate)),
            'db.add((%s, %s, %s)' % (URIRef(resourceUri), DC.created, Literal(udate)))

class User:
    '''
        Fetches Users from repository
    '''
    def setUsers(self, users):
        self.users = users
        self.dict = {}
        count = 0
        for u in users:
            self.dict[u] = count
            count = count + 1

    def fetchFromDB(self):
        self.users = []
        self.dict = {}
        
        # get triples from repository
        triples = db.triples((None, RDF.type, FOAF.Person))
        
        # create list of URIs and a dictionary
        count = 0;
        for t in triples:
            u_uri = str(t[0])                # get user URI
            self.users.append(u_uri)         # add to list
            self.dict[u_uri] = count         # add to dictionary
            count = count + 1

    @staticmethod
    def addToDB(userUri, account, accountName, userAvatar, t=0, udate=None):
        dbAdd((URIRef(userUri), RDF.type, FOAF.Person),
              'db.add((%s, %s, %s))' % (URIRef(userUri), RDF.type, FOAF.Person))
        dbAdd((URIRef(userUri), FOAF.image, URIRef(userAvatar)),
              'db.add((%s, %s, %s))' % (URIRef(userUri), FOAF.image, URIRef(userAvatar)))
        
        # add account details
        accountUri = snaserv.serviceUri[account]
        dbAdd((URIRef(userUri), FOAF.account, URIRef(accountUri)),
                  'db.add((%s, %s, %s))' % (URIRef(userUri), FOAF.account, URIRef(accountUri)))
        dbAdd((URIRef(userUri), DC.identifier, Literal(accountName)),
                  'db.add((%s, %s, %s))' % (URIRef(userUri), DC.identifier, URIRef(accountName)))
    
        if not udate: udate = date.today()
        dbAddCreatedDate(userUri, udate)

    @staticmethod
    def addToDBUserKnowsUser(userUri1, userUri2, t=0, udate=None):
        statement = (URIRef(userUri1), FOAF.knows, URIRef(userUri2))
        dbAdd(statement, 'addUserKnowsUserRelation(%s, %s)' % (userUri1, userUri2))
        dbAddReification(statement, [(DC.created, Literal(udate))])

    @staticmethod
    def fetchUsersFromNetwork(account):
        '''
           account - account name, one of db.services.DELICIOUS, FLICKR, etc.
        '''
        account_uri = snaserv.serviceUri[account]
        q = 'SELECT ?u WHERE { \
                ?u rdf:type foaf:Person . \
                ?u foaf:account <%s> \
            }' % account_uri
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, dc=DC)
        res = db.query(q, initNs=ns)

        # create list
        users_uri = [str(r[0]) for r in res]
        
        return users_uri

    @staticmethod
    def fetchUser(username, account):
        '''username - user name from the account
           account - account name, one of db.services.DELICIOUS, FLICKR, etc.
        '''
        accountUri = snaserv.serviceUri[account]
        q = 'SELECT ?u WHERE { \
                ?u rdf:type foaf:Person . \
                ?u dc:identifier "%s" . \
                ?u foaf:account <%s> \
            }' % (username, accountUri)
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, dc=DC)
        res = db.query(q, initNs=ns)

        # create list of URIs and a dictionary
        u_uri = None
        for r in res:
            u_uri = str(r[0])                   # get resource URI
            break

        return u_uri

    @staticmethod
    def fetchFriends(userUri):
        friendUris = []
        for t in db.triples((URIRef(userUri), FOAF.knows, None)):
            friendUris.append(str(t[2]))
        return friendUris
    
    @staticmethod
    def fetchCommonFriends(user_uri1, user_uri2):
        sparql_query = 'SELECT DISTINCT ?u WHERE { \
                ?u rdf:type foaf:Person . \
                <%s> foaf:knows ?u. \
                <%s> foaf:knows ?u.\
            }' % (user_uri1, user_uri2)
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, dc=DC)
        res = db.query(sparql_query, initNs=ns)

        # create list
        friends_uri = [str(r[0]) for r in res]
        return friends_uri
    
    @staticmethod
    def fetchUnionFriends(user_uri1, user_uri2):
        sparql_query = 'SELECT DISTINCT ?u WHERE {  { \
                ?u rdf:type foaf:Person . \
                <%s> foaf:knows ?u. } \
                UNION { \
                ?u rdf:type foaf:Person .\
                <%s> foaf:knows ?u.\
            } }' % (user_uri1, user_uri2)
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, dc=DC)
        res = db.query(sparql_query, initNs=ns)

        # create list
        friends_uri = [str(r[0]) for r in res]
        return friends_uri

    @staticmethod
    def fetchFollowers(userUri):
        followerUris = []
        for t in db.triples((None, FOAF.knows, URIRef(userUri))):
            followerUris.append(str(t[0]))
        return followerUris
    
    @staticmethod
    def fetchCommonFollowers(user_uri1, user_uri2):
        sparql_query = 'SELECT DISTINCT ?u WHERE { \
                ?u rdf:type foaf:Person . \
                ?u foaf:knows <%s>. \
                ?u foaf:knows <%s>.\
            }' % (user_uri1, user_uri2)
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, dc=DC)
        res = db.query(sparql_query, initNs=ns)

        # create list
        followers_uri = [str(r[0]) for r in res]
        return followers_uri
    
    @staticmethod
    def fetchUnionFollowers(user_uri1, user_uri2):
        sparql_query = 'SELECT DISTINCT ?u WHERE {  { \
                ?u rdf:type foaf:Person . \
                ?u foaf:knows <%s>. } \
                UNION { \
                ?u rdf:type foaf:Person .\
                ?u foaf:knows <%s>.\
            } }' % (user_uri1, user_uri2)
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, dc=DC)
        res = db.query(sparql_query, initNs=ns)

        # create list
        followers_uri = [str(r[0]) for r in res]
        return followers_uri

    @staticmethod
    def is_friend_with(userUri, otherUserUri):
        is_friend = False
        for t in db.triples((URIRef(userUri), FOAF.knows, URIRef(otherUserUri))):
            is_friend = True
            break
        return is_friend

    def getUsers(self):
        return self.users
    
    def getDict(self):
        return self.dict
    
    def getNumber(self):
        return len(self.users)
    
    def __repr__(self):
        users_sorted = [(v,k) for k,v in self.dict.items()]
        users_sorted.sort()
        s = "<Users> total = %s\n" % (self.getNumber(),)
        for (v,k) in users_sorted:
            s += "\t%s %s\n" % (v, k)
        return s


class Tag:
    '''
        Fetches Tags from repository
    '''
    
    def __init__(self):
        pass    
    
    def setTags(self, tags):
        self.tags = tags
        self.dict = {}
        count = 0
        for t in tags:
            self.dict[t] = count
            count = count + 1   
    
    def fetchFromDB(self):
        self.tags = []
        self.dict = {}
        
        # get triples from repository
        triples = db.triples((None, RDF.type, TAGS.Tag))
        
        # create list of URIs and a dictionary
        count = 0
        try:
            for t in triples:
                u_uri = str(t[0])           # get tag URI
                self.tags.append(u_uri)         # add to list
                self.dict[u_uri] = count        # add to dictionary
                count = count + 1
        except:
            print 'Error reading record'
    
    @staticmethod
    def addToDB(tagUri, tagName, t=0, udate=None):
        dbAdd((URIRef(tagUri), RDF.type, TAGS.Tag))
        dbAdd((URIRef(tagUri), TAGS.tagName, Literal(tagName)))

        if not udate: udate = date.today()
        dbAddCreatedDate(tagUri, udate)
    
    def getTags(self):
        return self.tags
    
    def getDict(self):
        return self.dict
    
    def getNumber(self):
        return len(self.tags)
    
    def __repr__(self):
        tags_sorted = [(v,k) for k,v in self.dict.items()]
        tags_sorted.sort()
        s = "<Tags> total = %s\n" % (self.getNumber(),)
        for (v,k) in tags_sorted:
            s += "\t%s %s\n" % (v, k)
        return s


class Resource:
    '''
        Fetches Resources from repository
    '''
    
    def __init__(self):
        self.q_all = 'SELECT ?r WHERE { {?r rdf:type bookmark:Bookmark} \
                        UNION {?r rdf:type foaf:Image} \
                        UNION {?r rdf:type video:Recording} \
                        UNION {?r rdf:type sioc:Microblog} \
                        UNION {?r rdf:type foaf:Document} }'
        self.q_del = 'SELECT ?r WHERE { ?r rdf:type bookmark:Bookmark}'
        self.q_img = 'SELECT ?r WHERE {?r rdf:type foaf:Image}'
        self.q_yt = 'SELECT ?r WHERE {?r rdf:type video:Recording}'
        self.q_tw = 'SELECT ?r WHERE {?r rdf:type sioc:Microblog}'
        self.q_doc = 'SELECT ?r WHERE {?r rdf:type foaf:Document}'
        
    def setResources(self, resources):
        self.resources = resources
        self.dict = {}
        count = 0
        for r in resources:
            self.dict[r] = count
            count = count + 1

    def fetchFromDB(self):
        self.fetchFromDB_query(self.q_all)

    def fetchFromDB_query(self, query):
        self.resources = []
        self.dict = {}
        
        # get resources from repository
        ns = dict(rdf=RDF, bookmark=BOOKMARK, video=VIDEO, foaf=FOAF, sioc=SIOC)
        res = db.query(query, initNs=ns)
        
        # create list of URIs and a dictionary
        count = 0;
        for r in res:
            u_uri = str(r[0])                   # get resource URI
            self.resources.append(u_uri)        # add to list
            self.dict[u_uri] = count            # add to dictionary
            
            #print r
            #print u_uri
            
            count = count + 1
    
    def getResources(self):
        return self.resources
    
    def getDict(self):
        return self.dict
    
    def getNumber(self):
        return len(self.resources)
    
    def __repr__(self):
        resources_sorted = [(v,k) for k,v in self.dict.items()]
        resources_sorted.sort()
        s = "<Resources> total = %s\n" % (self.getNumber(),)
        for (v,k) in resources_sorted:
            s += "\t%s %s\n" % (v, k)
        return s

    @staticmethod
    def addToDB(resourceUri, resourceTitle, t=0, udate=None):
        # if no date provided, assume current date
        if not udate: udate = date.today()

        if resourceTitle is not None:
            dbAdd((URIRef(resourceUri), DC['title'], Literal(resourceTitle)),
                  'db.add((%s, %s, %s))' % (URIRef(resourceUri), DC['title'], Literal(resourceTitle)))
        
        dbAdd((URIRef(resourceUri), DC.identifier, Literal(resourceUri)),
              'db.add((%s, %s, %s))' % (URIRef(resourceUri), DC.identifier, Literal(resourceUri)))

        dbAddCreatedDate(resourceUri, udate)

    @staticmethod
    def unify(resourceUri, otherResourceUri):
        '''Making resourceUri OWL:sameAs the otherResourceUri (representing the same resource).
        '''
        dbAdd((URIRef(resourceUri), OWL['sameAs'], URIRef(otherResourceUri)), 
            'db.add((%s, %s, %s))' % (URIRef(resourceUri), OWL['sameAs'], URIRef(otherResourceUri)))

    @staticmethod
    def unify_all(resourceUris):
        '''Unify each resource with eachother
        '''
        for ruri in resourceUris:
            for oruri in resourceUris:
                if ruri != oruri: 
                    Resource.unify(ruri, oruri)


class Bookmark(Resource):
    
    def fetchFromDB(self):
        self.fetchFromDB_query(self.q_del)

    @staticmethod
    def addToDB(resourceUri, resourceTitle, t=0, udate=None):
        dbAdd((URIRef(resourceUri), RDF.type, BOOKMARK.Bookmark),
              'db.add((%s, %s, %s))' % (URIRef(resourceUri), RDF.type, BOOKMARK.Bookmark))
        Resource.addToDB(resourceUri, resourceTitle, udate=udate)
            

class Image(Resource):
    
    def fetchFromDB(self):
        self.fetchFromDB_query(self.q_img)

    @staticmethod
    def addToDB(resourceUri, resourceTitle, t=0, udate=None):
        dbAdd((URIRef(resourceUri), RDF.type, FOAF.Image),
              'adding image %s resource to repository' % resourceUri)
        Resource.addToDB(resourceUri, resourceTitle, udate=udate)


class Video(Resource):

    def fetchFromDB(self):
        self.fetchFromDB_query(self.q_yt)

    @staticmethod
    def addToDB(resourceUri, resourceTitle, t=0, udate=None):
        dbAdd((URIRef(resourceUri), RDF.type, VIDEO.Recording),
              'adding video %s resource to repository' % resourceUri)
        Resource.addToDB(resourceUri, resourceTitle, udate=udate)


class Document(Resource):

    def fetchFromDB(self):
        self.fetchFromDB_query(self.q_doc)

    @staticmethod
    def addToDB(resourceUri, resourceTitle, t=0, udate=None):
        dbAdd((URIRef(resourceUri), RDF.type, FOAF.Document),
              'adding document %s resource to repository' % resourceUri)
        Resource.addToDB(resourceUri, resourceTitle, udate=udate) 


class Tweet(Resource):

    def fetchFromDB(self):
        self.fetchFromDB_query(self.q_tw)

    @staticmethod
    def addToDB(resourceUri, resourceTitle, t=0, udate=None):
        dbAdd((URIRef(resourceUri), RDF.type, SIOC.Microblog),
              'adding tweet %s resource to repository' % resourceUri)
        Resource.addToDB(resourceUri, resourceTitle, udate=udate)

    @staticmethod
    def addReferenceToDB(resourceUri, referenceUri, t=0, udate=None):
        dbAdd((URIRef(resourceUri), RDFS.seeAlso, URIRef(referenceUri)),
              'adding reference %s for tweet %s resource to repository' % (referenceUri, resourceUri))


class UserResourceTag:
    '''
        Fetch User Resource Tag relations from repository
    '''
    
    def __init__(self, users, resources, tags):
        self.users = users
        self.resources = resources
        self.tags = tags
        self.q_all = 'SELECT ?u ?r ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedResource ?r . \
                ?tagging tags:taggedBy ?u . \
                ?tagging tags:associatedTag ?t . }'
        self.q_all2 = 'SELECT ?u ?r ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedResource ?r . \
                {{?r rdf:type bookmark:Bookmark } UNION {?r rdf:type video:Recording}} . \
                ?tagging tags:taggedBy ?u . \
                ?u rdf:type foaf:Person . \
                ?tagging tags:associatedTag ?t . \
                ?t rdf:type tags:Tag . }'
        self.q_del = 'SELECT ?u ?r ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedResource ?r . \
                ?r rdf:type bookmark:Bookmark . \
                ?tagging tags:taggedBy ?u . \
                ?tagging tags:associatedTag ?t . }'
        self.q_yt = 'SELECT ?u ?r ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedResource ?r . \
                ?r rdf:type video:Recording . \
                ?tagging tags:taggedBy ?u . \
                ?tagging tags:associatedTag ?t . }'
        self.q_img = 'SELECT ?u ?r ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedResource ?r . \
                ?r rdf:type foaf:Image . \
                ?tagging tags:taggedBy ?u . \
                ?tagging tags:associatedTag ?t . }'
        self.q_doc = 'SELECT ?u ?r ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedResource ?r . \
                ?r rdf:type foaf:Document . \
                ?tagging tags:taggedBy ?u . \
                ?tagging tags:associatedTag ?t . }'
        self.q_tw = 'SELECT ?u ?r ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedResource ?r . \
                ?r rdf:type sioc:Microblog . \
                ?tagging tags:taggedBy ?u . \
                ?tagging tags:associatedTag ?t . }'
        
    def setRelations(self, relations=[], urt=[]):
        self.urt = []
        if urt:
            self.urt = urt
        elif relations:
            for u_uri, r_uri, t_uri in relations:
                u_no, r_no, t_no = self.users.dict[str(u_uri)], self.resources.dict[str(r_uri)], self.tags.dict[str(t_uri)]
                self.urt.append((u_no, r_no, t_no))

    def fetchFromDB(self, log=False):
        self.fetchFromDB_query(self.q_all)
            
    def fetchFromDB_query(self, query, log=False):
        self.urt = []
        
        # query the repository
        ns = dict(tags=TAGS, rdf=RDF, bookmark=BOOKMARK, video=VIDEO, foaf=FOAF, sioc=SIOC)
        relations = db.query(query, initNs=ns)
        
        # convert to integer representation of the URIs
        if log: f = open('relatii.txt', 'w')
        for u_uri, r_uri, t_uri in relations:
            try:
                u_no, r_no, t_no = self.users.dict[str(u_uri)], self.resources.dict[str(r_uri)], self.tags.dict[str(t_uri)]
                self.urt.append((u_no, r_no, t_no))

                if log:
                    f.write("(%s, %s, %s)\n" % (u_uri, r_uri, t_uri))
                    f.write("(%s, %s, %s)\n" % (u_no, r_no, t_no))
            except:
                pass
        if log: f.close()
    
    @staticmethod
    def addToDB(userUri, resourceUri, tagUri, t=0, udate=None):
        # tagging resource
        taggingUri = '%s/user/%s' % (resourceUri, userUri)
        tagging = URIRef(taggingUri)
        
        dbAdd((tagging, RDF.type, TAGS.Tagging))
        dbAdd((tagging, TAGS.taggedResource, URIRef(resourceUri)))
        dbAdd((tagging, TAGS.associatedTag, URIRef(tagUri)))
        dbAdd((tagging, TAGS.taggedBy, URIRef(userUri)))
        # inverse relations for resource
        #db.add((URIRef(resourceUri), TAGS.tag, tagging))
        #db.add((URIRef(resourceUri), TAGS.taggedWithTag, URIRef(tagUri)))
        #db.add((URIRef(tagUri), TAGS.isTagOf, URIRef(resourceUri)))
        
        if not udate: udate = date.today()
        dbAddCreatedDate(taggingUri, udate)

    @staticmethod
    def fetchUserTags(user_uri):
        tags_query = 'SELECT DISTINCT ?t WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedBy <%s> . \
                ?tagging tags:associatedTag ?t . }' % \
                user_uri

        # get tags from repository
        ns = dict(rdf=RDF, tags=TAGS)
        results = db.query(tags_query, initNs=ns)
        return [str(result[0]) for result in results]

       
    @staticmethod
    def fetchUnionUsersTags(user_uri1, user_uri2):
        sparql_query = 'SELECT DISTINCT ?t WHERE {  { \
                ?tagging1 rdf:type tags:Tagging . \
                ?tagging1 tags:taggedBy <%s>. \
                ?tagging1 tags:associatedTag ?t.\
                } \
                UNION { \
                ?tagging2 rdf:type tags:Tagging .\
                ?tagging2 tags:taggedBy <%s>. \
                ?tagging2 tags:associatedTag ?t. \
                } }' % (user_uri1, user_uri2)
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, tags=TAGS)
        results = db.query(sparql_query, initNs=ns)

        # create list
        return [str(result[0]) for result in results]

    @staticmethod
    def fetchUserResources(user_uri):
        resources_query = 'SELECT DISTINCT ?r WHERE { \
                ?tagging rdf:type tags:Tagging . \
                ?tagging tags:taggedBy <%s> . \
                ?tagging tags:taggedResource ?r . }' % \
                user_uri

        # get resources from repository
        ns = dict(rdf=RDF, tags=TAGS)
        results = db.query(resources_query, initNs=ns)
        return [str(result[0]) for result in results]
    
    @staticmethod
    def fetchUnionUsersResources(user_uri1, user_uri2):
        sparql_query = 'SELECT DISTINCT ?r WHERE {  { \
                ?tagging1 rdf:type tags:Tagging . \
                ?tagging1 tags:taggedBy <%s>. \
                ?tagging1 tags:taggedResource ?r.\
                } \
                UNION { \
                ?tagging2 rdf:type tags:Tagging .\
                ?tagging2 tags:taggedBy <%s>. \
                ?tagging2 tags:taggedResource ?r. \
                } }' % (user_uri1, user_uri2)
        
        # get resources from repository
        ns = dict(rdf=RDF, foaf=FOAF, tags=TAGS)
        results = db.query(sparql_query, initNs=ns)

        # create list
        return [str(result[0]) for result in results]

    def getUsersNumber(self):
        return self.users.getNumber()
    
    def getResourcesNumber(self):
        return self.resources.getNumber()
    
    def getTagsNumber(self):
        return self.tags.getNumber()
    
    def __repr__(self):
        s = "<UserResourceTagRelation> total = %d\n" % len(self.urt)
        for (u, r, t) in self.urt:
            s += "(%s , %s, %s)\n" % (u, r, t)
        return s

def init_db():
    '''Creates online Accounts (foaf:Account) for the services: Flickr, Slideshare, Delicious, etc.
    Must be called on an empty repository.
    '''
    for serv in snaserv.services:
        suri = snaserv.serviceUri[serv]
        dbAdd((URIRef(suri), RDF.type, FOAF.OnlineAccount), 
            'adding service %s with type: %s' % (suri, FOAF.OnlineAccount))


if __name__ == '__main__':
    f = open('../logs/log_dbaccess_resource_repr.log', 'w')

    #f.write('\n\n\nUSERS\n\n\n')
    #u = User()
    #u.fetchFromDB()
    #f.write(repr(u))

    #f.write('\n\n\nRESOURCES\n\n\n')
    #r = Resource()
    #r.fetchFromDB()
    #f.write(repr(r))
    #print r.dict

    #f.write('\n\n\nTAAAAGS\n\n\n')
    #t = Tag()
    #t.fetchFromDB()
    #f.write(repr(t))

    #urt = UserResourceTag(u, r, t)
    #urt.fetchFromDB()

    user_uri = User.fetchUser("vladposea", "delicious")
    resources = UserResourceTag.fetchUserResources(user_uri)
    print "Number of resources " + str(len(resources))
    print "Resource sample: " + resources[0]
