import requests
import os


class BotController:
    def __init__(self, bot_token):
        self.token = bot_token

    def request(self, method_name, params=None):
        if params is None:
            params = {}
        req_ans = requests.post(f'https://api.telegram.org/bot{self.token}/{method_name}', params=params)

        return req_ans.json()


bot = BotController('1251641214:AAHUb6HRDcHNHq57O33pUmHjnkvLQ0HqWUU')
print(bot.request('getMe'))
