import sys
from xunlei import xunlei
from aria2 import aria2
from urls import urls

reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ =='__main__':
    try:
        aria = aria2()
        xl = xunlei()
        while True:
            url = raw_input("Pls enter the download url.\r\n")
            if url == 'q' or url == 'quit':
                break
            task = xl.add_task(url)
            #xl.sync_tasks()
            aria.push(task)
    except Exception as e:
        print str(e.message)
        raw_input("PRESS ANY KEY TO EXIT")