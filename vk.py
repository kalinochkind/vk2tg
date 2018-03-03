import shelve

import requests
import time
import logging

class VkMonitor:

    API_VERSION = '5.73'

    def __init__(self, config_dict, post_changed_callback):
        self.token = config_dict['token']
        self.groups = config_dict['groups']
        self.check_interval = int(config_dict['check_interval'])
        self.db = shelve.open(config_dict['db_path'], writeback=True)
        self.callback = post_changed_callback
        for group in self.groups:
            if group not in self.db:
                self.db[group] = {'last': None}

    def api_call(self, method, params):
        params['v'] = self.API_VERSION
        params['access_token'] = self.token
        try:
            response = requests.get('https://api.vk.com/method/' + method, params=params)
            time.sleep(0.35)  # ограничения вк
            return response.json()['response']
        except Exception:
            logging.exception('VK error')
            return None

    def monitor_forever(self):
        while True:
            try:
               for group in self.groups:
                    params = {'count': 10}
                    if group.lstrip('-').isdigit():
                        params['owner_id'] = group
                    else:
                        params['domain'] = group
                    response = self.api_call('wall.get', params)
                    if response is None:
                        continue
                    max_post_id = self.db[group]['last']
                    for post in sorted(response['items'], key=lambda x: x['id']):
                        if max_post_id is not None and max_post_id < post['id']:
                            self.process_post(group, post)
                        if 'telegram_id' in self.db[group].get(post['id'], ''):
                            self.process_post(group, post)
                    max_existing_post = max(post['id'] for post in response['items'])
                    if max_post_id is None:
                        self.db[group]['last'] = max_existing_post
                    else:
                        self.db[group]['last'] = max(max_existing_post, max_post_id)
                    if len(self.db[group]) > 20:
                        self.cleanup(group)
            except Exception:
                logging.exception('Monitor error')
            self.db.sync()
            time.sleep(self.check_interval)

    def cleanup(self, group):
        old_post_ids = sorted(map(int, self.db[group].keys()))[:-20]
        for post_id in old_post_ids:
            del self.db[group][post_id]

    def generate_post_link(self, post):
        return 'https://vk.com/wall{owner_id}_{id}'.format(**post)

    def process_post(self, group, post):
        if post['id'] not in self.db[group]:
            post_dict = {'link': self.generate_post_link(post), 'text': post['text']}
            self.fill_attachments(post, post_dict)
            self.db[group][post['id']] = post_dict
        else:
            old_post = self.db[group][post['id']]
            if post['text'] == old_post['text']:
                # возможно, нужно проверять не только текст
                return
            old_post['text'] = post['text']
        self.callback(self.db[group][post['id']])


    def fill_attachments(self, vk_post, post_dict):
        for attachment in vk_post.get('attachments', []):
            if attachment['type'] == 'photo':
                max_size = max(int(param.split('_')[1])
                               for param in attachment['photo']
                               if param.startswith('photo_'))
                post_dict.setdefault('photo', []).append(attachment['photo'].get('photo_' + str(max_size)))
            elif attachment['type'] == 'video':
                post_dict.setdefault('video', []).append((attachment['video']['owner_id'], attachment['video']['id']))
            # надо добавить другие типы вложений
