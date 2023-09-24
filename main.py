import os
import time

from BotManager import BotManager
from TooManyRetriesException import tooManyRetriesException



def main():
    while True:
        try:
            os.system('pkill -f "Firefox"')
            botManager = BotManager()
            botManager.setup()
            botManager.prepareSockets()
            botManager.start()
        except tooManyRetriesException as e:
            botManager.kill()
            print(e)
            time.sleep(10)
        except Exception as e:
            print(e)
            break




if __name__ == "__main__":
    main()
