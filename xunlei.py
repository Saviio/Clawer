import requests, urllib, json, zlib, datetime
from utils import *
from ast import literal_eval
from urls import urls
from Crypto.PublicKey import RSA
#from Crypto.Hash import SHA
#from Crypto.Cipher import PKCS1_v1_5, PKCS1_OAEP
#from base64 import b64decode
#from PIL import Image
#from StringIO import StringIO
#from to_ascii import convert_to_ascii

# todo: verify code hit issue
# todo: rsa_encode module

class xunlei(object):

    def __init__(self, username = "", password = ""):
        if username != "" and password != "":
            self.usr = username
            self.pwd = password
        else:
            (self.usr, self.pwd) = load_account()
        self.requests = start_session()
        self.tasks = []
        #self.try_enter()
        
    def login(self, relogin = False):
        try:
            rs = self.requests.get(urls.verify_usr(self.usr))
            captcha = rs.cookies['check_result'][2:].upper()
            N = safe_cookie(rs.cookies['check_n'])
            E = safe_cookie(rs.cookies['check_e'])
        
            param = (
                long(b642hex(N), 16),
                long(b642hex(E), 16)
            )

            keyPub = RSA.construct(param)
            ciphertext = keyPub.encrypt(md5(self.pwd) + captcha, None)[0]
            pwd = hex2b64(ciphertext.encode('hex')).replace('\n','')

            payload = {
                'u': self.usr,
                'p': pwd,
                'n': N,
                'e': E,
                'v': 100,
                'verifycode': captcha,
                'login_enable': 0,
                'business_type': 108,
                'cachetime': int(time.time() * 1000)
            }
            
            rs = self.requests.post(urls.login(), data = payload)
            self.usrid = rs.cookies['userid']
            print "[*] Login lixian.xunlei.com successfully."
            if self.requests._new_: self.requests._new_ = False
            return
        except Exception as e:
            raise Exception("[Exception]: " + str(e.message) + ", Login failed(1001).")

    @if_necessary
    def try_enter(self):
        index = 0
        retry = 3
        while index < retry:
            try:
                if self.requests._new_:
                    self.login()
                else:
                    rs = self.requests.get(urls.main())
                    self.gdriveid = re.search(r'ck=(.*)&at', rs.text).group(1)
                    status = rs.cookies['vip_isvip'] == '1'
                    if status: 
                        self.usrid = self.requests.cookies['userid']
                        save_cookies(self.requests)
                        return
            except Exception as e:
                print str(e.message)
                self.requests = start_session(True)
            index = index + 1
        else:
            raise Exception("[Exception]: Retry count exceeded, num > " + str(retry) + ", Login failed(1002).")


    def task_check(self, url):
        rs = self.requests.get(urls.task_check(url))
        rs.encoding = 'utf-8'
        return {
            'url' : url,
            'qcid': literal_eval(re.match(r'^queryCid(\(.+\))\s*$', rs.text).group(1))
        }
        
    def add_task(self, url):
        self.try_enter()
        task = self.task_check(url)

        if task['qcid'] != None:
            qcid = task['qcid']
            if len(qcid) == 8:
                cid, gcid, size_required, filename, goldbean_need, silverbean_need, is_full, random = qcid
            elif len(qcid) == 9:
                cid, gcid, size_required, filename, goldbean_need, silverbean_need, is_full, random, ext = qcid
            elif len(qcid) == 10:
                cid, gcid, size_required, some_key, filename, goldbean_need, silverbean_need, is_full, random, ext = qcid
            elif len(qcid) > 10:
                cid, gcid, size_required, some_key, filename, goldbean_need, silverbean_need, is_full, random, ext, usless_keys = qcid

            url = task['url']
            if url.startswith('http://') or url.startswith('ftp://'):
                task_type = 0
            elif url.startswith('ed2k://'):
                task_type = 2
            else:
                task_type = 0

            filename = filename.decode('utf-8')

            payload = {
					'callback'  : 'ret_task',
					'uid'       : self.usrid,
					'cid'       : cid,
					'gcid'      : gcid,
					'size'      : size_required,
					'goldbean'  : goldbean_need,
					'silverbean': silverbean_need,
					't'         : filename.decode('utf-8'),
					'url'       : url,
					'type'      : task_type,
					'o_page'    : 'history',
					'o_taskid'  : '0',
                    'interfrom' : 'task',
                    'database'  : None,
                    'time'      : timestring(),
                    'noCacheIE' : current()
			}

            self._commit_(payload)
            return self._sync_(1).pop()
        else:
            raise Exception('[Exception]: Adding task failed(1003).')
    
    @adjust_cookis
    def _commit_(self, payload, acc = 0):
        if acc < 5:
            rs = self.requests.get(urls.task_commit(), params = payload)
            if re.match(r"ret_task\('-1[1|2]'\,.*\)$", rs.text):
                img = self.requests.get(urls.verify_img())
                print convert_to_ascii(img.content)
                code = raw_input('verify code? \n')
                payload.update({ 
                    'verify_code' : code,
                    'time'        : timestring(),
                    'noCacheIE'   : current()
                })
                self._commit_(payload, acc + 1)
        else:
            aw = raw_input("[Warning]: Already tried 5 times, do you want to continue?")
            if aw == 'y' or aw == 'yes': 
                self._commit_(payload, 0)
            else:
                raise Exception('[Exception]: Commit task failed(1004).')

        
    
    def sync_tasks(self, num = 30):
        self.tasks = self._sync_(num)

    def _sync_(self, num):
        rs = self.requests.get(urls.task_list(num), headers = {'Accept-Encoding': 'gzip, deflate'})
        rs.encoding = 'utf-8'
        tasks = self._unwrap_(rs.text)['info']['tasks']
        return [{
            'filename'   : task['taskname'],
            'size'       : task['filesize'],
            'progress'   : task['progress'],
            'lixian_url' : task['lixian_url'],
            'url'        : task['url'],
            'gdriveid'   : self.gdriveid
        } for task in tasks]

    def _unwrap_(self, data):
        return json.loads(re.match(r'jsonp\d*\((.*)\)$', data).group(1))

