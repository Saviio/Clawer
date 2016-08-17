from utils import current_random, current, timestring
import urllib, time

class urls():
    def __init__():
        return None

    @staticmethod
    def verify_usr(usr):
        return "http://login.xunlei.com/check/?u=%s&business_type=108&cachetime=%d&" % (usr, current())

    @staticmethod
    def login():
        return "http://login.xunlei.com/sec2login/"

    @staticmethod
    def main():
        return "http://dynamic.lixian.vip.xunlei.com/login?cachetime=%d&from=0" % current()

    @staticmethod
    def task_check(url):
        return "http://dynamic.cloud.vip.xunlei.com/interface/task_check?callback=queryCid&url=%s&random=%s&tcache=%s" % (urllib.quote(url), current_random(), current())

    @staticmethod
    def task_commit():
        return "http://dynamic.cloud.vip.xunlei.com/interface/task_commit"

    @staticmethod
    def task_list(num):
        timestamp  = int(time.mktime(time.localtime()))
        return ("http://dynamic.cloud.vip.xunlei.com/interface/showtask_unfresh?callback=jsonp%s&t=%s&type_id=4&page=1&tasknum=%s&p=1&interfrom=task" % (timestamp, timestring(), num)).replace(' ','%20')

    @staticmethod
    def verify_img():
        return "http://verify2.xunlei.com/image?t=MVA&cachetime=%s" % current()