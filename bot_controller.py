import requests


class BotController:
    def __init__(self, bot_token):
        self.token = bot_token
        self.offset = None
        self.timeout = 30

    def request(self, method_name, params=None):
        if params is None:
            params = {}
        req_ans = requests.post(f'https://api.telegram.org/bot{self.token}/{method_name}', params=params)

        return req_ans.json()

    def check_updates(self):
        result = self.request('getUpdates', params={'timeout': self.timeout, 'offset': self.offset})['result']
        for message in result:
            self.offset = message['update_id']

            message_id = message['message']['message_id']
            user_id = message['message']['chat']['id']

            text = message['message']['text']
            print(f'[{message_id}] From {user_id}: {text}')
        return result

