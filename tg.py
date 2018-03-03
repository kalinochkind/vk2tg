import logging

import telegram

from post import Post


class TelegramPoster:

    def __init__(self, token, channel):
        self.bot = telegram.Bot(token)
        self.channel = channel
        if not self.channel.startswith('@'):
            self.channel = '@' + self.channel

    def new_post(self, post: Post):
        text = post.get_telegram_text()
        msg = self.bot.send_message(chat_id=self.channel, text=text, disable_web_page_preview=True)
        if post.photo:
            media = [telegram.InputMediaPhoto(url) for url in post.photo]
            self.bot.send_media_group(self.channel, media)
        return msg

    def edit_post(self, post: Post):
        text = post.get_telegram_text()
        return self.bot.edit_message_text(chat_id=self.channel, message_id=post.tg_id, text=text,
                                          disable_web_page_preview=True)

    def post(self, post):
        try:
            if post.tg_id:
                self.edit_post(post)
            else:
                post.tg_id = self.new_post(post).message_id
        except Exception:
            logging.exception("TG error")
