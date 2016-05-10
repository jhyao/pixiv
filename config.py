# coding:utf-8

import sys

import re

reload(sys)
sys.setdefaultencoding('utf-8')

pixiv_id = '******'
email = '**********'
password = '********'

pixiv_url = 'http://www.pixiv.net'
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
    'Referer': 'http://www.pixiv.net'
}

login_url = 'https://www.pixiv.net/login.php'
login_data = {
    'mode': 'login',
    'return_to': '/',
    'pixiv_id': email,
    'pass': password,
    'skip': '1'
}

lc_url = 'http://www.pixiv.net/rpc_language_setting.php'

lc_data = {
    'mode': 'set',
    'tt': 'd6958f23fd56cef4f63701f1b14ba9b7',
    'user_language': 'zh'
}

cookie_path = 'cookie.txt'
default_store_path = 'G:\\pixiv'


def member_url(member_id):
    return 'http://www.pixiv.net/member.php?id=' + str(member_id)


def member_illust_url(member_id):
    return 'http://www.pixiv.net/member_illust.php?id=' + str(member_id)


def member_bookmark_url(member_id):
    return 'http://www.pixiv.net/bookmark.php?id=' + str(member_id)


def illust_url(illust_id):
    return 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(illust_id)


def member_illust_page(member_id, page):
    return 'http://www.pixiv.net/member_illust.php?id=' + str(member_id) + '&type=all&p=' + str(page)


def manga_page_url(illust_id):
    return 'http://www.pixiv.net/member_illust.php?mode=manga&illust_id=' + str(illust_id)


def manga_big_url(illust_id, page):
    return 'http://www.pixiv.net/member_illust.php?mode=manga_big&illust_id=' + str(illust_id) + '&page=' + str(page)


def store_path(member_id, member_name=None):
    if not member_name:
        member_name = ''
    pattern=re.compile('\\\|/|:|\?|<|>|\*|"|\|')
    name=re.sub(pattern,'-',member_name)
    return 'G:\\pixiv\\' + str(member_id) + '-' + name


def member_info_path(member_id):
    return 'E:\\python\\pa\\info\\' + str(member_id) + '.txt'


def member_info_format(member_id, name, illust_num, illust_info_list, time):
    info = {
        'member_id': member_id,
        'member_name': name,
        'member_illust_num': illust_num,
        'member_illust_list': illust_info_list,
        'update_time': time
    }
    return info


def illust_info_format(illust_id, title, date, pixels, view_count, score, tags, type, original_images):
    info = {
        'illust_id': illust_id,
        'illust_title': title,
        'illust_date': date,
        'illust_pixels': pixels,
        'illust_view_count': view_count,
        'illust_score': score,
        'illust_tags': tags,
        'illust_type': type,
        'illust_original_images': original_images,
    }
    return info


'''
参数说明
word
s_mode=s_tag(标签)|s_tc(标题简介)|s_tag_full(完全一致) 默认s_tag
r_18=1(只有r18)
ratio=0.5(横版)|-0.5(竖版)|0(正方)
blt=最小收藏数,bgt=最大收藏数
order=popular_d(按热门度排序)|date(按旧排序) 默认空(按新排序)
scd=搜索开始日期
p=页数

'''


def search_url(word, page=1, ratio='', blt='0', bgt='*', order='popular_d', scd=''):
    return 'http://www.pixiv.net/search.php?word=' + str(word) + '&order=' + str(order) + '&ratio=' + str(
        ratio) + '&blt=' + str(blt) + '&p=' + str(page)


def member_focus_url(member_id, page, rest='show'):
    return 'http://www.pixiv.net/bookmark.php?type=user&id=' + str(member_id) + '&rest=' + rest + '&p=' + str(page)

