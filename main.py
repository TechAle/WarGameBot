from BotManager import BotManager
import os



def main():
    botManager = BotManager()
    botManager.setup()
    botManager.prepareSockets()
    botManager.start()




if __name__ == "__main__":
    main()
