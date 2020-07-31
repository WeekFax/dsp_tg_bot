from bot_controller import BotController

with open('bot_token.txt', 'r') as f:
    bot_token = f.readline()

bot = BotController(bot_token)

if __name__ == '__main__':
    try:
        while True:
            bot.check_updates()

    except KeyboardInterrupt:
        exit()
