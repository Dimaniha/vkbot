import datetime
import time
import os
import vk_api
import var
from pixivpy3 import *
import re
import json


def download(api, idx, illust):
    image_url = illust.meta_single_page.get('original_image_url', illust.image_urls.large)
    tags(illust)
    if idx == 0:
        api.download(image_url, path=var.photo_folder, name=None)
    elif idx == 1:
        url_basename = os.path.basename(image_url)
        extension = os.path.splitext(url_basename)[1]
        name = "%d_%s%s" % (illust.id, illust.title, extension)
        api.download(image_url, path=var.photo_folder, name=name)
    elif idx == 2:
        api.download(image_url, path=var.photo_folder, fname='%s.jpg' % (illust.id))
    else:
        api.download(image_url, path='/foo/bar',
                     fname=open('%s/%s.jpg' % (var.photo_folder, illust.id), 'wb'))

def red_letter_day(today):
    api = AppPixivAPI()
    api.auth(refresh_token=var.refresh_token)
    json_result = api.search_illust(f'{var.red_letter_days[today]}', search_target='partial_match_for_tags')
    with open(var.history_file, 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        illust_to_add = []
        for idx, illust in enumerate(json_result.illusts):
            len_lines = len(lines)
            if len(lines) > 0:
                for t in range(0, len_lines):
                    if re.search(rf'{str(illust.id)}', str(lines[t])):
                        break
                    else:
                        if t == len_lines - 1:
                            illust_to_add.append(str(illust.id))
                            download(api, idx, illust)
            else:
                illust_to_add.append(str(illust.id))
                download(api, idx, illust)
        for i in illust_to_add:
            f.write(str(i) + '\n')
    prepare_to_post()

def tags(illust):
    tag_file = var.tag_dir + "/" + str(illust.id) + ".txt"
    tags_to_write = []
    with open(tag_file, 'w+', encoding='utf-8') as f:
        for i in illust.tags:
            bookmark = re.search(r'.ookmarks', str(i.translated_name))
            if i.translated_name == None:
                continue
            elif bookmark:
                continue
            else:
                tags_to_write.append(i.translated_name)
        sorted_list = list(set(tags_to_write))
        last_sorted_list_item = len(sorted_list)
        for i in range(0, last_sorted_list_item):
            if i == last_sorted_list_item - 1:
                tag = re.sub(r'\s', '_', str(sorted_list[i]))
                f.write("#" + str(tag))
            else:
                tag = re.sub(r'\s', '_', str(sorted_list[i]))
                f.write("#" + str(tag) + " | ")

def prefered_tags_sort(illust, api, idx, illust_to_add):
    last_item_prefered_tags = len(var.prefered_tags)
    last_item_tags = len(illust.tags)
    for prefered_tag in range(0, last_item_prefered_tags):
        for tag in range(0, last_item_tags):
            if re.search(rf'{var.prefered_tags[prefered_tag]}',
                         str(illust.tags[tag].translated_name)):
                download(api, idx, illust)
            break
        break
    illust_to_add.append(str(illust.id))

def pixiv_download():
    api = AppPixivAPI()
    api.auth(refresh_token=var.refresh_token)
    json_result = api.illust_recommended()
    with open(var.history_file, 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        illust_to_add = []
        for idx, illust in enumerate(json_result.illusts):
            len_lines = len(lines)
            if len(lines) > 0:
                for t in range(0, len_lines):
                    if re.search(rf'{str(illust.id)}', str(lines[t])):
                        break
                    else:
                        if t == len_lines - 1:
                            prefered_tags_sort(illust, api, idx, illust_to_add)
            else:
                prefered_tags_sort(illust, api, idx, illust_to_add)
        for i in illust_to_add:
            f.write(str(i) + '\n')
    prepare_to_post()

def vk_post(tags, path):
    vk_session = vk_api.VkApi(token=var.token)
    upload = vk_api.VkUpload(vk_session)
    photo = upload.photo(path, album_id=var.album_id, group_id=var.OWNER_ID)
    vk_photo_url = 'photo{}_{}'.format(photo[0]['owner_id'], photo[0]['id'])
    vk_session.method('wall.post', {
        'owner_id': var.GROUP_OWNER,
        'message': str(tags),
        'attachments': vk_photo_url
    })


#def tg_post():
def date_check():
    today = datetime.datetime.today().strftime('%d.%m')
    for day in var.red_letter_days.keys():
        if today == day:
            clear_last()
            red_letter_day(today)
        else:
            if len(os.listdir(var.photo_folder)) == 0:
                pixiv_download()
            else:
                prepare_to_post()

def prepare_to_post():
    for pic in os.listdir(var.photo_folder):
        path = var.photo_folder + "/" + str(pic)
        match = re.match(r'\d+', str(pic))
        pic = re.sub(r'\s+', '', str(pic))
        pic = re.sub(r'\S+', str(match.group(0)), str(pic))
        tag_file = var.tag_dir + "/" + str(pic) + ".txt"
        print(match.group(0))
        print(pic)
        with open(tag_file, 'r') as f:
            tags = f.readline()
        vk_post(tags, path)
        #tg_post()
        os.remove(path)
        os.remove(tag_file)
        if len(os.listdir(var.photo_folder)) == 0:
            time.sleep(1750)
            date_check()
        else:
            time.sleep(1800)

def clear_last():
    if len(os.listdir(var.photo_folder)) > 0:
        photo_folder_content = os.listdir(var.photo_folder)
        tags_dir_content = os.listdir(var.tag_dir)
        for x in tags_dir_content:
            os.remove(var.tag_dir + "/" + str(x))
        with open(var.history_file, 'r+', encoding='utf-8') as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate(0)
            len_lines = len(lines)
            print(lines)
            numbers_list = []
            for i in photo_folder_content:
                match = re.match(r'\d+', str(i))
                for number, line in enumerate(lines):
                    if re.search(rf'{str(match.group(0))}', str(line)):
                        numbers_list.append(number)
                        os.remove(var.photo_folder + "/" + str(i))
            for i in range(0, len_lines):
                if i not in numbers_list:
                    f.write(str(lines[i]))

if __name__ == "__main__":
    if os.path.exists(var.history_file) == False:
        with open(var.history_file, 'x', encoding='utf-8') as f:
            pass
    date_check()
