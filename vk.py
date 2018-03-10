import pickle
import requests
import time
import logging

from post import Post


class VkMonitor:

    API_VERSION = '5.73'

    def __init__(self, config_dict, post_changed_callback):
        self.token = config_dict['token']
        self.groups = config_dict['groups']
        self.check_interval = int(config_dict['check_interval'])
        self.db_path = config_dict['db_path']
        self.db = {}
        self.load_db()
        self.callback = post_changed_callback
        for group in self.groups:
            if group not in self.db:
                self.db[group] = {'last': None}

    def load_db(self):
        try:
            with open(self.db_path, 'rb') as f:
                self.db = pickle.load(f)
        except Exception:
            logging.exception('Load error')

    def save_db(self):
        with open(self.db_path, 'wb') as f:
            pickle.dump(self.db, f)

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
            changed = 0
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
                            changed += self.process_post(group, post)
                        else:
                            changed += self.process_post(group, post, edit_only=True)
                    max_existing_post = max(post['id'] for post in response['items'])
                    if max_post_id is None:
                        self.db[group]['last'] = max_existing_post
                        changed += 1
                    elif max_existing_post > max_post_id:
                        self.db[group]['last'] = max_existing_post
                        changed += 1
            except Exception:
                logging.exception('Monitor error')
            if changed:
                self.save_db()
            time.sleep(self.check_interval)

    def process_post(self, group, vk_post, edit_only=False):
        post = Post(vk_post)
        if post.vk_id in self.db[group]:
            if post == self.db[group][post.vk_id]:
                return False
            post.tg_id = self.db[group][post.vk_id].tg_id
        if edit_only and not post.tg_id:
            return False
        self.db[group][post.vk_id] = post
        self.callback(post)
        return True
