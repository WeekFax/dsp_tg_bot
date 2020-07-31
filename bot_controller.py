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
        """
        Get the link to requested file and download it to 'buf' folder
        :param file_id: Unique file id
        :return: Path to the file on disk
        """
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
        """
        Download the file, check for the face on it with the haar cascade
        In case there is the face on the image, save it in the user's folder
        :param user_id: User or chat id
        :param file_id: Unique file id
        :param reply_message_id: Id of the message need to reply to
        """
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
        """
        Download audio file, resample it to 16kHz and save as .wav file in user's folder
        :param user_id: User or chat id
        :param file_id: Unique file id
        :param reply_message_id: Id of the message need to reply to
        """
        if not os.path.isdir('audio'):
            os.mkdir('audio')
        if not os.path.isdir(f'audio/{user_id}'):
            os.mkdir(f'audio/{user_id}')

        file_name = self.download_file(file_id)
        if file_name is not None:
            # Считываем файл и сразу делаем ресемпл до 16кГц
            raw_audio, sr = librosa.load(file_name, 16000)

            # Считаем кол-во файлов в папке пользователя
            file_count = len(os.listdir(f'audio/{user_id}'))

            # Сохраняем аудио файл в папку пользователя
            sf.write(f'audio/{user_id}/audio_message_{file_count}.wav', raw_audio, 16000)
            os.remove(file_name)

            self.request('sendMessage', params={'chat_id': user_id,
                                                'text': f'Аудиозапись скачана как audio_message_{file_count}.wav',
                                                'reply_to_message_id': reply_message_id})

    def process_text(self, user_id, message_text):
        """
        Check incoming message for known commands and reply to it
        :param user_id: User or chad id
        :param message_text: Incoming message text
        """
        if not os.path.isdir('image'):
            os.mkdir('image')
        if not os.path.isdir(f'image/{user_id}'):
            os.mkdir(f'image/{user_id}')
        if not os.path.isdir('audio'):
            os.mkdir('audio')
        if not os.path.isdir(f'audio/{user_id}'):
            os.mkdir(f'audio/{user_id}')

        if message_text == '/help':
            response_text = '/help - Список доступных комманд\n' \
                            '/list - Список загруженных файлов вашим пользователем\n' \
                            '/send <Название файла> - Отправить файл в этот диалог'
            self.request('sendMessage', params={'chat_id': user_id, 'text': response_text})

        # Выводим список файлов, загруженных пользователем
        elif message_text == '/list':
            response_text = 'Audio:\n'
            for file_name in os.listdir(f'audio/{user_id}'):
                response_text += file_name + '\n'

            response_text += 'Photo:\n'
            for file_name in os.listdir(f'image/{user_id}'):
                response_text += file_name + '\n'

            self.request('sendMessage', params={'chat_id': user_id, 'text': response_text})

        # Отправляем пользователю сохраненный в его папке файл
        elif message_text.split(' ')[0] == '/send':
            file_name = message_text.split(' ')[1]

            # Проверяем наличие файла в папке с аудио
            if file_name in os.listdir(f'audio/{user_id}'):
                with open(f'audio/{user_id}/{file_name}', 'rb') as f:
                    file = {'document': f}
                    requests.post(f'https://api.telegram.org/bot{self.token}/sendDocument?chat_id={user_id}', files=file)

            # Проверяем файл в папке с изображениями
            elif file_name in os.listdir(f'image/{user_id}'):
                with open(f'image/{user_id}/{file_name}', 'rb') as f:
                    file = {'document': f}
                    requests.post(f'https://api.telegram.org/bot{self.token}/sendDocument?chat_id={user_id}', files=file)
            else:
                self.request('sendMessage', params={'chat_id': user_id, 'text': 'Такого файла не существует'})

    def check_updates(self):
        """
        Check for new messages that came to bot
        :return:
        """

        # Время ожидания в timeout, номер ожидаемого обновления (нового сообщения) в offset
        result = self.request('getUpdates', params={'timeout': self.timeout, 'offset': self.offset})['result']
        for update in result:
            self.offset = update['update_id'] + 1

            message = update['message']

            message_id = message['message_id']
            user_id = message['chat']['id']
            username = message['chat']['username']

            # Если пришел текст, проверяем на наличие в нем команд
            if 'text' in message:
                text = message['text']
                print(f'[{message_id}] From {username}({user_id}): {text}')
                self.process_text(user_id, text)

            # Если пришел документ, проверяем его тип
            # Если пришло изображение или аудио обрабатываем его соотвествуюущим образом
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
                print(f'[{message_id}] From {username}({user_id}): incoming audio')
                self.process_audio(user_id, voice['file_id'], message_id)

            elif 'photo' in message:
                for photo in message['photo']:
                    print(f'[{message_id}] From {username}({user_id}): incoming image')
                    self.process_image(user_id, photo['file_id'], message_id)

        return result
