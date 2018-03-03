import logging

import telegram


class TelegramPoster:

    def __init__(self, token, channel):
        self.bot = telegram.Bot(token)
        self.channel = channel
        if not self.channel.startswith('@'):
            self.channel = '@' + self.channel

    def get_message_text(self, post):
        text = post['text'].strip()
        if 'video' in post:
            text += '\n'
            for video in post['video']:
                text += '\nhttps://vk.com/video{}_{}'.format(*video)
        return text + '\n\n' + post['link']

    def new_post(self, post):
        text = self.get_message_text(post)
        msg = self.bot.send_message(chat_id=self.channel, text=text, disable_web_page_preview=True)
        if 'photo' in post:
            media = [telegram.InputMediaPhoto(url) for url in post['photo']]
            self.bot.send_media_group(self.channel, media)
        return msg

    def edit_post(self, msg_id, post):
        text = self.get_message_text(post)
        return self.bot.edit_message_text(chat_id=self.channel, message_id=msg_id, text=text,
                                          disable_web_page_preview=True)

    def post(self, post):
        try:
            if 'telegram_id' in post:
                self.edit_post(post['telegram_id'], post)
            else:
                post['telegram_id'] = self.new_post(post).message_id
        except Exception:
            logging.exception("TG error")
