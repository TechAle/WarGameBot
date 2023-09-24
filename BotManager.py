import json
import threading
from Bot import Bot



class BotManager:
    def __init__(self):
        # Open the file accounts.json, for every keys in the file, print the key and the value
        self.Bots = []
        first = True
        with open("accounts.json", "r") as file:
            data = json.load(file)["accounts"]
            for key in data:
                # Now add in the array Bots a class Bot with the email and password
                self.Bots.append(Bot(key, data[key], first))
                first = False

    def setup(self):
        for bot in self.Bots:
            bot.setup()

    def prepareSockets(self):
        # start bots
        for bot in self.Bots:
            bot.prepareSocket(len(self.Bots) - 1)

    def start(self):
        # Start every bot in a thread and then wait for the thread to finish
        threads = []
        for bot in self.Bots:
            threads.append(threading.Thread(target=bot.start))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
