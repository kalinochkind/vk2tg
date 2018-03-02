import telegram

class TelegramPoster:

    def __init__(self, token, channel):
        self.bot = telegram.Bot(token)
        self.channel = channel
        if not self.channel.startswith('@'):
            self.channel = '@' + self.channel

    def get_message_text(self, post):
        return post['text'].strip() + '\n\n' + post['link']

    def new_post(self, post):
        text = self.get_message_text(post)
        if post.get('photo'):
            return self.bot.send_photo(chat_id=self.channel, photo=post['photo'], caption=text)
        else:
            return self.bot.send_message(chat_id=self.channel, text=text, disable_web_page_preview=True)

    def edit_post(self, msg_id, post):
        text = self.get_message_text(post)
        if post.get('photo'):
            return self.bot.edit_message_caption(chat_id=self.channel, message_id=msg_id, caption=text)
        else:
            return self.bot.edit_message_text(chat_id=self.channel, message_id=msg_id, text=text,
                                              disable_web_page_preview=True)

    def post(self, post):
        if 'telegram_id' in post:
            self.edit_post(post['telegram_id'], post)
        else:
            post['telegram_id'] = self.new_post(post).message_id
