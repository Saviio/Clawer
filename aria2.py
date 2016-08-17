import requests, json
from utils import load_aria, current
import urllib2

class aria2(object):
    def __init__(self):
        self.host = load_aria()

    def push(self, task):
        host = self.host + '?tm=%s' % (current())
        headers = {'content-type': 'application/json'}
        url, filename, gdriveid = (task['lixian_url'], task['filename'], task['gdriveid'])
        rs = requests.post(host, data = self.payload(url, filename, gdriveid), headers = headers)
        print 'Push Task to Nas:\n' + task['filename'] + '  ....Accomplished\n'


    def payload(self, url, filename, gdriveid):
        return json.dumps({
            'jsonrpc' : '2.0',
            'method'  : 'aria2.addUri',
            'id'      : '%s' % current(),
            'params'  : [
                ['%s' % url],
                {
                    'out'    : filename,
                    'header' : 'Cookie: gdriveid=%s' % gdriveid
                }
            ]
        })