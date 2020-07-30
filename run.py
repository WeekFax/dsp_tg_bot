from bot_controller import BotController

bot = BotController('1251641214:AAHUb6HRDcHNHq57O33pUmHjnkvLQ0HqWUU')


def main():
    print(bot.check_updates())


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()


