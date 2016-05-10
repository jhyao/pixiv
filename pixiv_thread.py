# coding:utf-8
import pixiv
import Queue
import threading
import json
import os
import config
import time
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

member_id_queue = Queue.Queue()
page_queue = Queue.Queue()
page_fail_queue = Queue.Queue()
illust_id_queue = Queue.Queue()
illust_id_fail_queue = Queue.Queue()
image_url_queue = Queue.Queue()
image_url_fail_queue = Queue.Queue()
thread_lock = threading.Lock()

image_info_file = open('image_url.txt', 'w')

signal = {
    'ready': True,
    'member_finish': False,
    'page_finish': False,
    'illust_finish': False,
    'down_finish': False,
}

data_statistic = {
    'member_num': 0,
    'member_finish_num': 0,
    'page_num': 0,
    'page_finish_num': 0,
    'illust_num': 0,
    'illust_finish_num': 0,
    'illust_fail_num': 0,
    'image_num': 0,
    'image_finish_num': 0,
    'image_fail_num': 0,
    'image_dld_num': 0
}

page_time = []
illust_time = []
down_time = []


# data_in:page_queue
# data_out:illust_id_queue
class MemberThread(threading.Thread):
    def __init__(self, thread_id, queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue

    def run(self):
        while not member_id_queue.empty() or not signal['ready']:

            # noinspection PyBroadException
            try:
                member_id = self.queue.get(1, 1)
            except:
                continue
            thread_lock.acquire()
            print 'LOG: MemberThread ', self.thread_id, ' analizing member ', member_id
            thread_lock.release()
            page_list = pixiv.get_member_illust_pages(member_id)

            for item in page_list:
                page_queue.put(item)

        thread_lock.acquire()
        print 'FINISH: memberThread ', self.thread_id, ' work finished'
        thread_lock.release()


# data_in:page_queue
# data_out:illust_id_queue
class PageThread(threading.Thread):
    def __init__(self, thread_id, queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue

    def run(self):
        while not page_queue.empty() or not signal['member_finish']:
            # noinspection PyBroadException
            try:
                page_url = self.queue.get(1, 1)
            except:
                continue
            thread_lock.acquire()
            print 'LOG: pageThread ', self.thread_id, ' analizing page ', page_url
            thread_lock.release()
            time1 = time.time()
            illust_ids = pixiv.deal_page(page_url)
            if illust_ids:
                time2 = time.time()
                page_time.append(time2 - time1)
            else:
                page_fail_queue.put(page_url)

            for item in illust_ids:
                data_statistic['illust_num'] += 1
                illust_id_queue.put(item)

        thread_lock.acquire()
        print 'FINISH: pageThread ', self.thread_id, ' work finished'
        thread_lock.release()


# data_in:illust_id_queue
# data_out:image_url_queue(success)|illust_id_fail_queue(fail)
class IllustThread(threading.Thread):
    def __init__(self, thread_id, queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue

    def run(self):
        while not illust_id_queue.empty() or not signal['page_finish']:
            # noinspection PyBroadException
            try:
                illust_id = self.queue.get(1, 1)
            except:
                continue
            thread_lock.acquire()
            print 'LOG: illustThread ', self.thread_id, ' analizing illust_id ', illust_id
            thread_lock.release()
            time1 = time.time()
            image_info = pixiv.get_original_image_url(illust_id)
            print 'test:INFO: ',image_info
            image_url = image_info[0]
            print 'test:URL: ',image_url
            image_type = image_info[1]
            data_statistic['illust_finish_num'] += 1
            if image_type == 'failed':
                illust_id_fail_queue.put(illust_id)
                data_statistic['illust_fail_num'] += 1
            else:
                time2 = time.time()
                illust_time.append(time2 - time1)
                for item in image_url:
                    print 'test:ITEM: ',item
                    image_info_file.write(json.dumps(item) + '\n')
                for item in image_url:
                    data_statistic['image_num'] += 1
                    image_url_queue.put(item)
                thread_lock.acquire()
                # print 'image_num:', image_url_queue.qsize()
                thread_lock.release()
            print 'PROGRESS: illustThread progress ', data_statistic['illust_finish_num'], '/', data_statistic[
                'illust_num'], ' failed ', data_statistic['illust_fail_num']

        thread_lock.acquire()
        print 'FINISH: illustThread ', self.thread_id, ' work finished'
        thread_lock.release()


# data_in:image_url_queue
# data_out:image file on disk
class DownThread(threading.Thread):
    def __init__(self, thread_id, queue, store_path=None, cover=False):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.store_path = store_path
        self.cover = cover

    def run(self):
        while not image_url_queue.empty() or not signal['illust_finish']:
            # noinspection PyBroadException
            try:
                image_url = self.queue.get(1, 1)
            except:
                continue
            if not self.store_path:
                new_store_path = image_url['store_path']
            else:
                new_store_path = self.store_path
            thread_lock.acquire()
            print 'LOG: download thread ', self.thread_id, ' downloading '
            # print 'image_left:', image_url_queue.qsize()
            thread_lock.release()
            time1 = time.time()
            response = pixiv.download_image(image_url['image_url'], image_url['referer'], new_store_path, self.cover)
            data_statistic['image_finish_num'] += 1
            if response == 'success':
                time2 = time.time()
                down_time.append(time2 - time1)
            elif response == 'fail':
                image_url_fail_queue.put(image_url)
                data_statistic['image_fail_num'] += 1
            elif response == 'dld':
                data_statistic['image_dld_num'] += 1
            print 'PROGRESS: image download progress ', data_statistic['image_finish_num'], '/', data_statistic[
                'image_num'], ' failed:', data_statistic['image_fail_num'], ' downloaded:', data_statistic[
                'image_dld_num']

        thread_lock.acquire()
        print 'FINISH: downThread ', self.thread_id, ' work finished'
        thread_lock.release()


def start_from_state(state=0, member_t_num=2, page_t_num=2, illust_t_num=5, down_t_num=10, store_path=None,
                     cover=False):
    member_t_list = []
    page_t_list = []
    illust_t_list = []
    down_t_list = []

    data_statistic['member_num'] = member_id_queue.qsize()
    data_statistic['page_num'] = page_queue.qsize()
    data_statistic['illust_num'] = illust_id_queue.qsize()
    data_statistic['image_num'] = image_url_queue.qsize()
    if state == 0:
        for i in range(member_t_num):
            mt = MemberThread(i, member_id_queue)
            member_t_list.append(mt)
            mt.start()

    if state == 1 or state == 0:
        for i in range(page_t_num):
            pt = PageThread(i, page_queue)
            page_t_list.append(pt)
            pt.start()

    if state in range(0, 3):
        for i in range(illust_t_num):
            it = IllustThread(i, illust_id_queue)
            illust_t_list.append(it)
            it.start()

    if state in range(0, 4):
        for i in range(down_t_num):
            dt = DownThread(i, image_url_queue, store_path, cover)
            down_t_list.append(dt)
            dt.start()

    for m in member_t_list:
        m.join()
    signal['member_finish'] = True
    print 'FINISH: member analizing all finished'

    for p in page_t_list:
        p.join()
    signal['page_finish'] = True
    print 'FINISH: page analizing all finished'

    for i in illust_t_list:
        i.join()
    signal['illust_finish'] = True
    print 'FINISH: illust analizing all finished'

    for d in down_t_list:
        d.join()
    signal['down_finish'] = True
    print 'FINISH: download all finished'

    page_fail_list = []
    while not page_fail_queue.empty():
        page_fail_list.append(page_fail_queue.get())
    f = open('page_fail.txt', 'w')
    f.write(json.dumps(page_fail_list))
    f.close()

    illust_id_fail_list = []
    while not illust_id_fail_queue.empty():
        illust_id_fail_list.append(illust_id_fail_queue.get())
    f = open('illust_id_fail.txt', 'w')
    f.write(json.dumps(illust_id_fail_list))
    f.close()

    image_url_fail_list = []
    while not image_url_fail_queue.empty():
        image_url_fail_list.append(image_url_fail_queue.get())
    f = open('image_url_fail.txt', 'w')
    f.write(json.dumps(image_url_fail_list))
    f.close()

    image_info_file.close()

    print 'DATA: analized page ', len(page_time)
    if len(page_time)>0:
        print 'DATA: average page time ', sum(page_time) / len(page_time)
    print 'DATA: analized illust ', len(illust_time), 'failed:', data_statistic['illust_fail_num']
    if len(illust_time)>0:
        print 'DATA: average illust time ', sum(illust_time) / len(illust_time)
    print 'DATA: downloaded image ', len(down_time), 'failed:', data_statistic['image_fail_num']
    if len(down_time)>0:
        print 'DATA: average download time ', sum(down_time) / len(down_time)


def download_member_image(member_id_list, member_t_num=5, page_t_num=10, illust_t_num=20, down_t_num=40,
                          store_path=None, cover=False):
    for member_id in member_id_list:
        member_id_queue.put(member_id)
    start_from_state(0, member_t_num, page_t_num, illust_t_num, down_t_num, store_path, cover)


def failed_repeat():
    if os.path.exists('page_fail.txt'):
        f = open('page_fail.txt', 'r')
        page_list = json.loads(f.read())
        f.close()
        for item in page_list:
            page_queue.put(item)
    if os.path.exists('illust_id_fail.txt'):
        f = open('illust_id_fail.txt', 'r')
        illust_list = json.loads(f.read())
        f.close()
        for item in illust_list:
            illust_id_queue.put(item)
    if os.path.exists('image_url_fail.txt'):
        f = open('image_url_fail.txt', 'r')
        image_url_list = json.loads(f.read())
        f.close()
        for item in image_url_list:
            image_url_queue.put(item)
    start_from_state(0)


def down_focus():
    focus_list = pixiv.get_member_focus_list(config.pixiv_id)
    download_member_image(focus_list, illust_t_num=30, down_t_num=50)


def down_from_file():
    if os.path.exists('info\\image_url.txt'):
        f = open('info\\image_url.txt', 'r')
        for line in f.readlines():
            image_l = json.loads(line)
            for item in image_l:
                image_url_queue.put(item)
        f.close()
        start_from_state(3, down_t_num=100)


def test():
    signal['page_finish']=True
    illust_id=53520013
    illust_id_queue.put(illust_id)
    t=IllustThread(1,illust_id_queue)
    t.start()
    t.join()

failed_repeat()