class Post:

    def __init__(self, vk_post):
        self.vk_id = vk_post['id']
        self.owner_id = vk_post['owner_id']
        self.tg_id = None
        self.text = vk_post['text'].strip()
        self.photo = []
        self.video = []
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
            # надо добавить другие типы вложений

    def get_vk_link(self):
        return 'https://vk.com/wall{}_{}'.format(self.owner_id, self.vk_id)

    def get_telegram_text(self):
        text = self.text.strip()
        if self.video:
            text += '\n'
            for video in self.video:
                text += '\nhttps://vk.com/video{}_{}'.format(*video)
        return text + '\n\n' + self.get_vk_link()

    def __eq__(self, other):
        if not isinstance(other, Post):
            return False
        return self.get_telegram_text() == other.get_telegram_text()
