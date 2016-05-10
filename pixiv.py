# coding:utf-8
import socket
import sys
import urllib
import urllib2
import cookielib
import os
import re
import json
from bs4 import BeautifulSoup
import time
import config

reload(sys)
sys.setdefaultencoding('utf-8')

data_statistic = {
    'open_num': 0,
    'open_fail_time': 0
}
cookie = cookielib.MozillaCookieJar()
cookie.load(config.cookie_path, ignore_discard=True, ignore_expires=True)
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))


def login():
    print 'logining...'
    cookie = cookielib.MozillaCookieJar(config.cookie_path)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    postdata = urllib.urlencode(config.login_data)
    request = urllib2.Request(config.login_url, postdata, config.header)
    response = opener.open(request)
    cookie.save(ignore_discard=True, ignore_expires=True)
    request.close()
    response.close()


def login_if_not():
    if os.path.exists(config.cookie_path):
        print 'Has logined'
    else:
        print 'Logining...'
        login()


def lc():
    postdata = urllib.urlencode(config.lc_data)
    request = urllib2.Request(config.lc_url, postdata, config.header)
    urllib2.urlopen(request)


def visit_pixiv_without_login():
    response = urllib2.urlopen(config.pixiv_url)
    return response


def get_text(url, referer=None, timeout=30, count=0):
    socket.setdefaulttimeout(timeout)

    header = config.header
    if referer:
        header['Referer'] = referer
    request = urllib2.Request(url, None, header)

    # noinspection PyBroadException
    try:
        response = opener.open(request)
        text = response.read()
        response.close()
    except:
        if count < 10:
            print 'failed,try again!'
            count += 1
            text = get_text(url, referer, timeout, count)
        else:
            text = 'failed'

    return text


def get_text_old(url, referer=None, timeout=30, count=0):
    socket.setdefaulttimeout(timeout)
    cookie2 = cookielib.MozillaCookieJar()
    cookie2.load(config.cookie_path, ignore_discard=True, ignore_expires=True)
    opener2 = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie2))
    header = config.header
    if referer:
        header['Referer'] = referer
    request = urllib2.Request(url, None, header)

    # noinspection PyBroadException
    try:
        response = opener.open(request)
        text = response.read()
        response.close()
    except:
        if count < 10:
            print 'failed,try again!'
            count += 1
            text = get_text(url, referer, timeout, count)
        else:
            text = 'failed'

    return text


def deal_page(page_url):
    # page_url:str:http://www.pixiv.net/member_illust.php?id=6662895&type=all&p=2
    # print 'dealing page ', page_url.split('=')[-1]
    page_html = get_text(page_url)
    if page_html != '':
        soup = BeautifulSoup(page_html, 'html.parser', from_encoding='utf-8')
        # images_list = soup.select('.work')
        images_list = soup.find_all('a', class_='work')
        images_url = [str(item['href']) for item in images_list]
        pattern = re.compile(r'\d+')
        illust_ids = [pattern.findall(item)[0] for item in images_url]
    else:
        illust_ids = []
    # print 'get ',len(illust_ids),' illustrations'
    return illust_ids


def get_original_image_url(illust_id, timeout=30):
    original_image_list = []
    image_html = get_text(config.illust_url(illust_id), timeout=timeout)
    if image_html == '':
        illust_type = 'failed'
        store_path = None
    else:
        soup = BeautifulSoup(image_html, 'html.parser', from_encoding='utf-8')
        author_info = soup.find('a', class_='user-link')
        pattern = re.compile(r'\d+')
        author_id = pattern.findall(author_info['href'])[0]
        author_name = author_info.find('h1', class_='user').string
        store_path = config.store_path(author_id, author_name)

        select = soup.select('.original-image')
        if select:
            t = {
                'image_url': select[0]['data-src'],
                'referer': config.illust_url(illust_id),
                'store_path': store_path
            }
            illust_type = 'medium'
            original_image_list.append(t)

        else:
            select = soup.select('.multiple')
            if select:
                manga_page_url = config.pixiv_url + '/' + str(select[0]['href'])
                manga_html = get_text(manga_page_url, timeout=timeout)
                manga_soup = BeautifulSoup(manga_html, 'html.parser', from_encoding='utf-8')
                manga_select = manga_soup.select('.ui-scroll-view')
                page_num = len(manga_select)
                pattern = re.compile(r'\d+$')
                manga_id = pattern.findall(manga_page_url)[0]
                for page in range(0, page_num):
                    manga_big_url = config.manga_big_url(manga_id, page)
                    manga_big_html = get_text(manga_big_url, timeout=timeout)
                    manga_big_soup = BeautifulSoup(manga_big_html, 'html.parser', from_encoding='utf-8')
                    manga_big_select = manga_big_soup.select('img')
                    original_image_url = manga_big_select[0]['src']
                    t = {
                        'image_url': original_image_url,
                        'referer': manga_big_url,
                        'store_path': store_path
                    }
                    original_image_list.append(t)
                illust_type = 'manga'
            else:
                illust_type = 'Unknown style'
    return [original_image_list, illust_type]


def download_image(url, referer, path=None, cover=False, timeout=60):
    if not path:
        path = config.default_store_path
    if not os.path.isdir(path):
        try:
            os.mkdir(path)
        except:
            return 'failed'
    filename = str(url).split('/')[-1]
    filepath = path + '\\' + filename
    if os.path.exists(filepath) and not cover:
        # print 'downloaded'
        return 'dld'
    else:
        text = get_text(url, referer, timeout=timeout)
        if text != 'failed':
            f = open(filepath, 'wb')
            # print 'downloading'
            f.write(text)
            f.close()
            return 'success'
        else:
            return 'fail'


def get_member_name(member_id):
    page_html = get_text(config.member_url(member_id))
    soup = BeautifulSoup(page_html, 'html.parser', from_encoding='utf-8')
    select = soup.select('.td2')
    member_name = 'NONE'
    if select:
        member_name = select[0].string
    return member_name


def get_member_illust_num(member_id):
    page_html = get_text(config.member_url(member_id))
    soup = BeautifulSoup(page_html, 'html.parser', from_encoding='utf-8')
    select = soup.find('div', class_='_more')
    num_info = select.contents[0].string
    pattern = re.compile(r'\d+')
    illust_num = pattern.findall(num_info)[0]
    return int(illust_num)


def get_member_illust_pages(member_id):
    illust_num = get_member_illust_num(member_id)
    page_num = illust_num / 20 + 1
    illust_pages = [config.member_illust_page(member_id, i) for i in range(1, page_num + 1)]
    return illust_pages


def get_member_info(member_id):
    member_name = get_member_name(member_id)
    member_illust_ids = get_member_illust_ids_(member_id)
    member_illust_num = len(member_illust_ids)
    member_illust_info_list = []
    for illust_id in member_illust_ids:
        member_illust_info_list.append(get_illust_info(illust_id))

    update_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    print 'member_name:', member_name
    print 'member_illust_ids:', member_illust_ids
    print 'member_illust_num:', member_illust_num
    print 'member_illust_info_list:', member_illust_info_list
    print 'update_time:', update_time
    member_info = config.member_info_format(member_id, member_name, member_illust_num, member_illust_info_list,
                                            update_time)

    print member_info

    f = open('info//' + str(member_id) + '.txt', 'w')
    f.write(json.dumps(member_info, encoding='utf-8', ensure_ascii=False))
    f.close()

    return member_info


def get_illust_info(illust_id):
    print 'illust_id:', illust_id
    page_html = get_text(config.illust_url(illust_id))
    soup = BeautifulSoup(page_html, 'html.parser', from_encoding='utf-8')

    work_info = soup.find(class_='work-info')
    illust_title = work_info.find('h1', class_='title').string
    meta = work_info.find('ul', class_='meta')
    illust_date = meta.contents[0].string
    illust_pixels = meta.contents[1].string

    print 'illust_title:', illust_title
    print 'illust_date:', illust_date
    print 'illust_pixels:', illust_pixels

    user_reaction = work_info.find('div', class_='user-reaction')
    illust_view_count = user_reaction.find(class_='view-count').string
    illust_score = user_reaction.find(class_='score-count').string

    print 'illust_view_count:', illust_view_count
    print 'illust_score:', illust_score

    select = soup.find_all(class_='tags')
    tags_select = select[0].find_all('a', class_='text')
    illust_tags = []
    for item in tags_select:
        tag = item.string
        illust_tags.append(tag)
    print 'illust_tags:', illust_tags

    original_image_url = get_original_image_url(illust_id)
    illust_original_images = original_image_url[0]
    illust_image_num = len(original_image_url)
    illust_type = original_image_url[1]
    print 'illust_type:', illust_type
    print 'illust_num:', illust_image_num
    print 'illust_original_images:', illust_original_images

    illust_info = config.illust_info_format(illust_id, illust_title, illust_date, illust_pixels, illust_view_count,
                                            illust_score, illust_tags, illust_type, illust_original_images)

    print illust_info
    return illust_info


def download_image_from_id(illust_id, page, path, cover):
    image_info = get_original_image_url(illust_id)[0]
    for i in page:
        download_image(image_info[i]['image_url'], image_info[i]['referer'], path, cover)


# 单线程废弃
def get_member_illust_ids_(member_id):
    print 'getting member illust list...'
    mi_html = get_text(config.member_illust_url(member_id))

    soup = BeautifulSoup(mi_html, 'html.parser', from_encoding='utf-8')
    select = soup.select('.page-list')
    pages_num = 1
    if select:
        pages_num = len(select[0])
    pages_list = [config.member_illust_page(member_id, i) for i in range(1, pages_num + 1)]
    images_list = []
    count = 1
    for page in pages_list:
        print 'dealing page ', count, '/', pages_num
        count += 1
        images_list.extend(deal_page(page))
    print 'pages finished,get ', len(images_list), ' illustrations'

    return images_list


def get_member_focus_num(member_id):
    page_html = get_text(config.member_url(member_id))
    soup = BeautifulSoup(page_html, 'html.parser', from_encoding='utf-8')
    select = soup.find('div', class_='unit-count')
    if select:
        focus_num = int(select.string)
    else:
        focus_num = 0
    return focus_num


def get_member_focus_list(member_id):
    focus_num = get_member_focus_num(member_id)
    page_num = focus_num / 48 + 1
    page_list = [config.member_focus_url(member_id, p) for p in range(1, page_num + 1)]
    focus_list = []
    for page in page_list:
        page_html = get_text(page)
        soup = BeautifulSoup(page_html, 'html.parser', from_encoding='utf-8')
        select = soup.find_all('div', class_='usericon')
        for item in select:
            icon = item.find('a', class_='ui-profile-popup')
            focus_id = icon['data-user_id']
            focus_list.append(focus_id)
    return focus_list





