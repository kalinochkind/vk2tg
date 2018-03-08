import logging

import telegram

from post import Post


class TelegramPoster:

    def __init__(self, token, channel):
        self.bot = telegram.Bot(token)
        self.channel = channel
        if not self.channel.startswith('@'):
            self.channel = '@' + self.channel

    def build_post_markup(self, post: Post):
        button = telegram.InlineKeyboardButton('Открыть пост', url=post.get_vk_link())
        return telegram.InlineKeyboardMarkup([[button]])

    def new_post(self, post: Post):
        text = post.get_telegram_text()
        msg = self.bot.send_message(chat_id=self.channel, text=text, parse_mode='html',
                                    disable_web_page_preview=not post.get_hidden_link(),
                                    reply_markup=self.build_post_markup(post))
        for title, url in post.doc:
            self.bot.send_document(chat_id=self.channel, document=url, filename=title)
        if len(post.photo) > 1:
            media = [telegram.InputMediaPhoto(url) for url in post.photo]
            self.bot.send_media_group(self.channel, media)
        return msg

    def edit_post(self, post: Post):
        text = post.get_telegram_text()
        return self.bot.edit_message_text(chat_id=self.channel, message_id=post.tg_id, text=text, parse_mode='html',
                                          disable_web_page_preview=not post.get_hidden_link(),
                                          reply_markup=self.build_post_markup(post))

    def post(self, post):
        try:
            if post.tg_id:
                self.edit_post(post)
            else:
                post.tg_id = self.new_post(post).message_id
        except Exception:
            logging.exception("TG error")
