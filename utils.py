# -*- coding: utf-8 -*-
import sys, re, time, json, ConfigParser, urllib, base64, os.path
import requests, requests.utils, pickle, datetime
from ast import literal_eval
from PIL import Image
from StringIO import StringIO

def current():
    return int(time.time() * 1000)

def timestring():
    return time.strftime("%a %b %d %Y %X GMT+0800", time.localtime())

def md5(str):
    import hashlib
    return hashlib.md5(str).hexdigest().lower()


def encypt_password(password):
    if not re.match(r'^[0-9a-f]{32}$', password):
        password = md5(md5(password))
    return password


def current_random():
    from random import randint
    return '%s%06d.%s' % (current(), randint(0, 999999), randint(100000000, 9999999999))


def url_encode(x,utf8 = True):
    import urllib
    def unif8(u):
        if type(u) == unicode:
            u = u.encode('utf-8')
            return u

    def recode(u):
        return u.deoce('gb18030').encode('utf-8')

    if utf8:
        return urllib.urlencode([(unif8(k), unif8(v)) for k, v in x.items()])
    else:
        return urllib.urlencode([(unif8(recode(k)), unif8(recode(v))) for k, v in x.items()])


#Get original title from douban.com
def douban_tranlation(matched_name): 
    import urllib2
    priority = {'movie':10, 'tv':9}
    qs = utils.url_encode({'q': matched_name})
    search_api = 'http://api.douban.com/v2/movie/search?%s' % (qs)
    rs = json.loads(urllib2.urlopen(search_api).read())

    items = rs['subjects']
    ret = None

    for item in items:
        if ret == None or (priority[ret['subtype']] < priority[item['subtype']]):
            ret = {
                'origin'  : item['original_title'], 
                'subtype' : item['subtype']
            }

    return ret

def load_account():
    cf = ConfigParser.ConfigParser()
    cf.read("clawer.conf")

    usr = cf.get("account","USR")
    pwd = cf.get("account","PWD")
    if usr == None or pwd == None:
        raise LookupError("Cannot find account information in clawer.conf.")
    return (usr, pwd)

def load_aria():
    cf = ConfigParser.ConfigParser()
    cf.read("clawer.conf")
    
    port = cf.get('aria', 'PORT')
    addr = cf.get('aria', 'ADDR')
    path = cf.get('aria', 'PATH')

    return addr + ':' + port + path


cf = ConfigParser.ConfigParser()
cf.read("urls.conf")
def load_url(domain, key):
    return cf.get(domain, key)

def load_domain_url(domain):
    return lambda x: cf.get(domain, x)

map = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
padchar = '='
char_map = '0123456789abcdefghijklmnopqrstuvwxyz'

def int2char(n):
    return char_map[n]

def hex2b64(h):
    return base64.encodestring(h.decode('hex')) #.replace("\n", "")

def b642hex(s):
    return base64.b64decode(s).encode('hex')

def safe_cookie(str):
    return urllib.unquote(str)

cookie_path = os.path.join(os.path.dirname(__file__), 'cookies.dmp')
headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586'}

def save_cookies(session):
    with open(cookie_path, 'w') as f:
        pickle.dump(requests.utils.dict_from_cookiejar(session.cookies), f)

def start_session(forceNew = False):
    session = requests.session()
    session.headers.update(headers)
    if os.path.exists(cookie_path) and forceNew != True:
        with open(cookie_path) as f:
            cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            session.cookies.update(cookies)
            session._new_ = False
    else:
        session._new_ = True
    return session


def convert_to_ascii(img):
    return _martix_to_ascii(_image_to_martix(img))

def _image_to_martix(img_data):
    img = Image.open(StringIO(img_data)).convert('L')
    w, h = img.size
    martix = []
    for y in xrange(h / 2):
        row = []
        for x in xrange(w):
            p1 = img.getpixel((x, y * 2))
            p2 = img.getpixel((x, y * 2 + 1))
            if p1 > 192 and p2 > 192:
                row.append(0)
            elif p1 > 192:
                row.append(1)
            elif p2 > 192:
                row.append(2)
            else:
                row.append(3)
        martix.append(row)
    return martix

def _crop_and_border(martix):
    t,b,l,r = 0,0,0,0
    for y in xrange(len(martix)):
        if sum(martix[y]) == 0:
            t += 1
        else: break
    for y in xrange(len(martix)):
        if sum(martix[-1 - y]) == 0:
            b += 1
        else: break
    for x in xrange(len(martix[0])):
        if sum( map(lambda row:row[x], martix) ) == 0:
            l += 1
        else: break
    for x in xrange(len(martix[0])):
        if sum( map(lambda row:row[-1 - x], martix) ) == 0:
            r += 1
        else: break
    w = len(martix[0])
    if t > 0:
        martix = martix[t-1:]
    else:
        martix.insert(0, [0] * w)
    if b > 1:
        martix = martix[:1-b]
    elif b == 0:
        martix.append([0] * w)
    for ri in xrange(len(martix)):
        row = martix[ri]
        if l > 0:
            row = row[l-1:]
        else:
            row.insert(0, 0)
        if r > 1:
            row = row[:1-r]
        elif r == 0:
            row.append(0)
        martix[ri] = row
    return martix


def _martix_to_ascii(martix):
    buf = []
    for row in martix:
        rbuf = []
        for cell in row:
            if cell == 0:
                rbuf.append('#')
            elif cell == 1:
                rbuf.append('"')
            elif cell == 2:
                rbuf.append(',')
            elif cell == 3:
                rbuf.append(' ')
        buf.append(''.join(rbuf))
    return '\n'.join(buf)


def if_necessary(f):
    if_necessary.checkpoint = None
    def apply(*args): 
        if if_necessary.checkpoint == None or (datetime.datetime.now() - if_necessary.checkpoint).seconds > 3600:
            f(*args)
            if_necessary.checkpoint = datetime.datetime.now()
        else:
            return
    return apply

def adjust_cookis(f):
    def apply(*args):
        ctx = args[0]
        try:
            ctx.requests.cookies.clear('','/',name ='VERIFY_KEY')
        except Exception as e:
            pass
        f(*args)
    return apply