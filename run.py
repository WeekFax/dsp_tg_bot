from bot_controller import BotController

bot = BotController('1251641214:AAHUb6HRDcHNHq57O33pUmHjnkvLQ0HqWUU')

if __name__ == '__main__':
    try:
        while True:
            bot.check_updates()
    except KeyboardInterrupt:
        exit()
