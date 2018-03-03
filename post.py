import html
import re


MENTION_RE = re.compile(r'\[id(\d+) ?\|([^\]]+)\]')


def replace_vk_mentions(text):
    return MENTION_RE.sub(r'<a href="https://vk.com/id\1">\2</a>', text)


class Post:

    def __init__(self, vk_post):
        self.vk_id = vk_post['id']
        self.owner_id = vk_post['owner_id']
        self.tg_id = None
        self.text = vk_post['text'].strip()
        self.photo = []
        self.links = []
        self.video = []
        self.doc = []
        self.fill_attachments(vk_post)

    def fill_attachments(self, vk_post):
        for attachment in vk_post.get('attachments', []):
            if attachment['type'] == 'photo':
                max_size = max(int(param.split('_')[1])
                               for param in attachment['photo']
                               if param.startswith('photo_'))
                self.photo.append(attachment['photo'].get('photo_' + str(max_size)))
            elif attachment['type'] == 'video':
                self.video.append((attachment['video']['owner_id'], attachment['video']['id']))
            elif attachment['type'] == 'doc':
                self.doc.append((attachment['doc']['title'], attachment['doc']['url']))
            elif attachment['type'] == 'link':
                if attachment['link']['url'].rstrip('/') not in self.text:
                    self.links.append(attachment['link']['url'])
            # надо добавить другие типы вложений

    def get_vk_link(self):
        return 'https://vk.com/wall{}_{}'.format(self.owner_id, self.vk_id)

    def get_telegram_text(self):
        text = replace_vk_mentions(html.escape(self.text.strip()))
        if self.links:
            text += '\n'
            for link in self.links:
                text += '\n' + link
        if self.video:
            text += '\n'
            for video in self.video:
                text += '\nhttps://vk.com/video{}_{}'.format(*video)
        return text + '\n\n' + self.get_vk_link()

    def __eq__(self, other):
        if not isinstance(other, Post):
            return False
        return self.get_telegram_text() == other.get_telegram_text()
