'''
Created on April 21, 2009

@author: anamariastoica
'''

import urllib
import urllib2
import hashlib
import time
import sna.etc.xml2dict as xml2dict

class SlideShareAPI(object):
    
    def __init__(self, params):
        """
        params dictionary must have at least api_key, and secret_key values
        """
        self.service_url = {
            'slideshow_by_user' : 'http://www.slideshare.net/api/1/get_slideshow_by_user',
            'get_user_contacts' : 'http://www.slideshare.net/api/2/get_user_contacts',
        }
        self.params = params

    def get_slideshow_by_user(self, username_for):
        """
        Method to get all slideshows created by an user
        Requires: username_for
        """
        data = self.make_call('slideshow_by_user', username_for=username_for)
        try: 
            data.User.Slideshow
        except:
            data.User['Slideshow'] = []
        return data

    def get_user_contacts(self, username_for):
        data = self.make_call('get_user_contacts', username_for=username_for)
        try:
            if not isinstance(data.Contacts.Contact, list):
                data.Contacts.Contact = [data.Contacts.Contact]
        except:
            data.Contacts.Contact = []
        return data

    def make_call(self, service_type, **args):
        """
        Makes the api call
        """
        params = self.get_ss_params(**args)
        data = urllib2.urlopen(self.service_url[service_type], params).read()
        json = self.parsexml(data)

        return self.return_data(json)

    def get_ss_params(self, **args):
        """
        Method which returns the parameters required for an api call
        """
        ts = int(time.time())
        tmp_params_dict = {
            'api_key' : self.params['api_key'],
            'ts' : ts,
            'hash' : hashlib.sha1(self.params['secret_key'] + str(ts)).hexdigest()
        }
        # Add method specific parameters to the dict
        for arg in args:
            if args[arg] and isinstance(args[arg], str):
                tmp_params_dict[arg]=args[arg]

        ss_params = urllib.urlencode(tmp_params_dict)
        return ss_params

    def parsexml(self, xml):
        return xml2dict.XML2Dict().fromstring(xml)

    def return_data(self, json):
        """
        Method to trap slideshare error messages and return data if there are no errors
        """
        if json and hasattr(json, 'SlideShareServiceError'):
            data = object()
            data.User = {}
            data.Contacts = object()
            return data
        return json

if __name__ == '__main__':
    sshparams = {'api_key': 'hGB0A4by', 'secret_key': '3qjmDPUM'}
    sshapi = SlideShareAPI(sshparams)

    slides = sshapi.get_slideshow_by_user('vladposea')
    print slides
    print slides.User.name                  # username
    for ssh in slides.User.Slideshow:       # slideshow list
        print ssh.Permalink
        tags = ssh.Tags or 'system:undefined'
        print tags.split(" ")

    contacts = sshapi.get_user_contacts('stagiipebune')
    for c in contacts.Contacts.Contact:
        print c.Username
