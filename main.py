import time
import os
import vk_api
import var
from pixivpy3 import *
import re
import json


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

def history(illust):
    with open(var.history_file, 'a+', encoding='utf-8') as f:
        for i in f.readlines():
            if i == illust.id:
                break
        f.write(str(illust.id) + '\n')

def pixiv_download():
    api = AppPixivAPI()
    api.auth(refresh_token=var.refresh_token)
    json_result = api.illust_recommended()
    for idx, illust in enumerate(json_result.illusts):
        last_item_prefered_tags = len(var.prefered_tags) - 1
        last_item_tags = len(illust.tags) - 1
        for prefered_tag in range(0, last_item_prefered_tags):
            for tag in range(0, last_item_tags):
                if re.search(rf'{var.prefered_tags[prefered_tag]}', str(illust.tags[tag].translated_name)):
                    image_url = illust.meta_single_page.get('original_image_url', illust.image_urls.large)
                    tags(illust)
                    history(illust)
                    if idx == 0:
                        api.download(image_url, path=var.photo_folder, name=None)
                        break
                    elif idx == 1:
                        url_basename = os.path.basename(image_url)
                        extension = os.path.splitext(url_basename)[1]
                        name = "%d_%s%s" % (illust.id, illust.title, extension)
                        api.download(image_url, path=var.photo_folder, name=name)
                        break
                    elif idx == 2:
                        api.download(image_url, path=var.photo_folder, fname='%s.jpg' % (illust.id))
                        break
                    else:
                        api.download(image_url, path='/foo/bar', fname=open('%s/%s.jpg' % (var.photo_folder, illust.id), 'wb'))
                        break
            continue
    wall_post()

def wall_post():
    vk_session = vk_api.VkApi(token=var.token)
    for pic in os.listdir(var.photo_folder):
        path = var.photo_folder + "/" + str(pic)
        match = re.match(r'\d+', str(pic))
        pic = re.sub(r'\S+', str(match.group(0)), str(pic))
        tag_file = var.tag_dir + "/" + str(pic) + ".txt"
        print(match.group(0))
        print(pic)
        with open(tag_file, 'r') as f:
            tags = f.readline()
        upload = vk_api.VkUpload(vk_session)
        photo = upload.photo(path, album_id=var.album_id, group_id=var.OWNER_ID)
        vk_photo_url = 'photo{}_{}'.format(photo[0]['owner_id'], photo[0]['id'])
        vk_session.method('wall.post', {
            'owner_id': var.GROUP_OWNER,
            'message': str(tags),
            'attachments': vk_photo_url
        })
        os.remove(path)
        os.remove(tag_file)
        if len(os.listdir(var.photo_folder)) == 0:
            time.sleep(1750)
            pixiv_download()
        else:
            time.sleep(1800)

if __name__ == "__main__":
    if len(os.listdir(var.photo_folder)) == 0:
        pixiv_download()
    else:
        wall_post()
