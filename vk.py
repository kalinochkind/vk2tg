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
                self.db[group] = {}

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
            for group in self.groups:
                params = {'count': 5}
                if group.lstrip('-').isdigit():
                    params['owner_id'] = group
                else:
                    params['domain'] = group
                response = self.api_call('wall.get', params)
                if response is None:
                    continue
                for post in response['items']:
                    self.process_post(group, post)
                if len(self.db[group]) > 20:
                    self.cleanup(group)
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
            for attachment in post.get('attachments', []):
                if attachment['type'] == 'photo':
                    # что делать, если фоток несколько?
                    max_size = max(int(param.split('_')[1])
                                   for param in attachment['photo']
                                   if param.startswith('photo_'))
                    post_dict['photo'] = attachment['photo'].get('photo_' + str(max_size))
                # надо добавить другие типы вложений
            self.db[group][post['id']] = post_dict
        else:
            old_post = self.db[group][post['id']]
            if post['text'] == old_post['text']:
                # возможно, нужно проверять не только текст
                return
            old_post['text'] = post['text']
        try:
            self.callback(self.db[group][post['id']])
        except Exception:
            logging.exception('Callback error')
