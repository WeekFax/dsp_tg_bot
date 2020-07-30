import requests
import librosa
import soundfile as sf
import os
import shutil
import cv2 as cv


class BotController:
    def __init__(self, bot_token):
        self.token = bot_token
        self.offset = 0
        self.timeout = 30
        self.face_cascade = cv.CascadeClassifier()
        self.face_cascade.load('haarcascade_frontalface_alt.xml')

    def request(self, method_name, params=None):
        if params is None:
            params = {}
        req_ans = requests.post(f'https://api.telegram.org/bot{self.token}/{method_name}', params=params)

        return req_ans.json()

    def download_file(self, file_id):
        req_ans = self.request('getFile', params={'file_id': file_id})
        if req_ans['ok']:
            tg_file_path = req_ans['result']['file_path']
            file_name = tg_file_path.split('/')[-1]
            local_file_path = './buf/' + file_name

            if not os.path.isdir('buf'):
                os.mkdir('buf')

            with open(local_file_path, 'wb') as f:
                f.write(requests.get(f'https://api.telegram.org/file/bot{self.token}/{tg_file_path}').content)

            return local_file_path
        else:
            print(req_ans['description'])
            return None

    def process_image(self, user_id, file_id, reply_message_id):
        if not os.path.isdir('image'):
            os.mkdir('image')
        if not os.path.isdir(f'image/{user_id}'):
            os.mkdir(f'image/{user_id}')

        file_name = self.download_file(file_id)
        if file_name is not None:
            src = cv.imread(file_name)
            frame_gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
            frame_gray = cv.equalizeHist(frame_gray)

            faces = self.face_cascade.detectMultiScale(frame_gray)
            if len(faces) > 0:
                print('Найдено лицо')
                file_count = len(os.listdir(f'image/{user_id}'))
                new_file_name = f'face_image_{file_count}.' + file_name.split('.')[-1]

                shutil.copy(file_name, f'image/{user_id}/{new_file_name}')
                self.request('sendMessage',
                             params={'chat_id': user_id,
                                     'text': f'Лицо найдено, картинка скачана как {new_file_name}',
                                     'reply_to_message_id': reply_message_id})
            else:
                print('Лица нет')
                self.request('sendMessage',
                             params={'chat_id': user_id,
                                     'text': 'Лицо не найдено',
                                     'reply_to_message_id': reply_message_id})

            os.remove(file_name)

    def process_audio(self, user_id, file_id, reply_message_id):
        if not os.path.isdir('audio'):
            os.mkdir('audio')
        if not os.path.isdir(f'audio/{user_id}'):
            os.mkdir(f'audio/{user_id}')

        file_name = self.download_file(file_id)
        if file_name is not None:
            raw_audio, sr = librosa.load(file_name, 16000)

            file_count = len(os.listdir(f'audio/{user_id}'))

            sf.write(f'audio/{user_id}/audio_message_{file_count}.wav', raw_audio, 16000)
            os.remove(file_name)

            self.request('sendMessage', params={'chat_id': user_id,
                                                'text': f'Аудиозапись скачана как audio_message_{file_count}.wav',
                                                'reply_to_message_id': reply_message_id})

    def check_updates(self):
        result = self.request('getUpdates', params={'timeout': self.timeout, 'offset': self.offset})['result']
        # result = self.request('getUpdates')['result']
        for update in result:
            self.offset = update['update_id'] + 1

            message = update['message']

            message_id = message['message_id']
            user_id = message['chat']['id']
            username = message['chat']['username']

            if 'text' in message:
                text = message['text']
                print(f'[{message_id}] From {username}({user_id}): {text}')

            elif 'document' in message:
                document = message['document']
                if 'image' in document['mime_type']:
                    print(f'[{message_id}] From {username}({user_id}): incoming image')
                    self.process_image(user_id, document['file_id'], message_id)
                if 'audio' in document['mime_type']:
                    print(f'[{message_id}] From {username}({user_id}): incoming audio')
                    self.process_audio(user_id, document['file_id'], message_id)

            elif 'voice' in message:
                voice = message['voice']
                if 'audio' in voice['mime_type']:
                    print(f'[{message_id}] From {username}({user_id}): incoming audio')
                    self.process_audio(user_id, voice['file_id'], message_id)

        return result
