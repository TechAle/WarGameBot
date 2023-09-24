import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import socket
import threading
from bs4 import BeautifulSoup
from TooManyRetriesException import tooManyRetriesException
from selenium.webdriver.firefox.options import Options


class Bot:
    WAITING = True
    DEBUG = False
    def __init__(self, email, password, first):
        self.wait = None
        self.socket = None
        self.clients = []
        self.server = first
        self.email = email
        self.password = password

    def setup(self):
        # Open the browser, Open https://www.warzone.com/LogIn, enter the email and password, click on the login button
        options = Options()
        options.set_preference("media.volume_scale", "0.0")
        options.headless = True
        self.driver = webdriver.Firefox(options=options)
        self.driver.get("https://www.warzone.com/LogIn")
        # use find_element that has by has parameters By.ID and "email"
        self.driver.find_element(By.ID, "EmailBox").send_keys(self.email)
        # use find_element that has by has parameters By.ID and "password"
        self.driver.find_element(By.ID, "PasswordBox").send_keys(self.password)
        # use find_element that has by has parameters By.ID and "login"
        self.driver.find_element(By.ID, "EmailSignInBtn").click()
        # Wait for refresh of the page
        self.wait = WebDriverWait(self.driver, 60)
        self.wait.until(
            lambda driver: driver.current_url == "https://www.warzone.com/LogIn")

    def prepareSocket(self, number):
        if self.server:
            self.startAsServer(number)
        else:
            self.startAsClient()

    def startAsClient(self):
        # Create an tcp socket client that connects to localhost on port 9099
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 9099))

    def startAsServer(self, number):
        # Create a tcp socket server that listens on localhost on port 9099
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("localhost", 9099))
        self.socket.listen(number)
        # Create a thread with the function waitForClients
        threading.Thread(target=self.waitForClients, args=(number,)).start()


    '''
    Create a function that, wait for clients to connect and when a client connects add it to a list of clients
    '''
    def waitForClients(self, number):
        self.clients = []
        while len(self.clients) < number:
            client, address = self.socket.accept()
            self.clients.append(client)
            print("New client connected")
        Bot.WAITING = False

    def start(self):
        while self.WAITING:
            time.sleep(1)
        b = False
        while True:
            if Bot.DEBUG:
                print("Starting")
            # If we are the server we have to manage everyone first
            if self.server:
                whatToDo = "create" if b else "join"
            else:
                whatToDo = "join" if b else "create"
            b = not b

            if whatToDo == "join":
                # Wait for a message from the server
                message = None
                if self.server:
                    if Bot.DEBUG:
                        print("Joining server")
                    for client in self.clients:
                        message = client.recv(1024).decode()
                    for client in self.clients:
                        client.send(message.encode())
                else:
                    if Bot.DEBUG:
                        print("Joining client")
                    message = self.socket.recv(1024).decode()

                self.joinGame(message)
            elif whatToDo == "create":
                self.createGame()

    def joinGame(self, url):
        if Bot.DEBUG:
            print("Joining game clients")
        self.driver.get(url)
        # Wait for element to exist //*[@id="ujs_JoinBtn_btn"] and then click it
        if Bot.DEBUG:
            print("Waiting for join button")
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_JoinBtn_btn"]'))
        self.driver.find_element(By.XPATH, '//*[@id="ujs_JoinBtn_btn"]').click()
        if Bot.DEBUG:
            print("Ready state")
        if self.server:
            self.clients[0].recv(1024)
            for client in self.clients:
                client.send("1".encode())
        else:
            self.socket.send("1".encode())
        if Bot.DEBUG:
            print("Finish button waiting")
        # Wait for element //*[@id="ujs_FinishVersusAIBtn_btn"] to exist
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_FinishVersusAIBtn_btn"]'))
        if Bot.DEBUG:
            print("Surrender button present joining")

    def createGame(self):
        if Bot.DEBUG:
            print("Creating game")
        self.driver.get("https://www.warzone.com/MultiPlayer?CreateGame=1")
        if Bot.DEBUG:
            print("Invite via code")
        self.waitToClick("//*[@id='ujs_PlayersModeCode_toggle']")
        if Bot.DEBUG:
            print("Waiting code to load")
        self.waitToClick('//*[@id="ujs_PlayersCodeBox_input"]')
        if Bot.DEBUG:
            print("Waiting create game button")
        self.waitToClick('//*[@id="ujs_CreateGameBtn_btn"]')
        # Wait for url to change
        self.wait.until(lambda driver: driver.current_url != "https://www.warzone.com/MultiPlayer?CreateGame=1")
        # Get the url
        url = self.driver.current_url

        if self.server:
            # Send the url to the clients
            for client in self.clients:
                client.send(url.encode())
            # Wait for the clients to be ready
            for client in self.clients:
                client.recv(1024)
        else:
            self.socket.send(url.encode())
            if Bot.DEBUG:
                print("first waiting")
            self.socket.recv(1024)
            self.socket.send(b"1")
            if Bot.DEBUG:
                print("second waiting")
            self.socket.recv(1024)
        # Start the game
        if Bot.DEBUG:
            print("Start game button")
        time.sleep(5)
        self.waitToClick('//*[@id="ujs_StartGameBtn_btn"]')

        # Wait for xpath //*[@id="ujs_SurrenderBtn_btn"] to exist and click it
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_SurrenderBtn_btn"]'))

        count = 0
        while True:
            try:
                if self.driver.find_element(By.XPATH, '//*[@id="ujs_SurrenderBtn_btn"]') is not None:
                    self.driver.execute_script('document.getElementById("ujs_SurrenderBtn_btn").click()')
                    break
            except:
                count += 1
                time.sleep(1)
                if count > 10:
                    raise Exception("Can't click on the element " + '//*[@id="ujs_SurrenderBtn_btn"]')
                else:
                    print("Failed time " + '//*[@id="ujs_SurrenderBtn_btn"]')
        # Wait for the element //*[@id="ujs_ModalContainer"] to change
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_ModalContainer"]').text != "")
        test = BeautifulSoup(self.driver.page_source, features="html.parser")
        codeDiv = str(test.find("div", {"id": "ujs_ModalContainer"}))
        codeDiv = codeDiv[:codeDiv[:codeDiv.index("Yes,")].rindex('<')]
        codeDiv = codeDiv[codeDiv.rindex("Button") - 4:]
        id = codeDiv[:codeDiv.index("btn") + 3]
        self.driver.execute_script(f'document.getElementById("{id}").click()')
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_FinishVersusAIBtn_btn"]'))
        if Bot.DEBUG:
            print("Finish button present create")


    def waitToClick(self, XPATH):
        self.wait.until(lambda driver: driver.find_element(By.XPATH, XPATH))
        while self.driver.find_element(By.XPATH, XPATH).is_enabled() is False:
            time.sleep(0.1)
        count = 0
        while True:
            try:
                self.driver.find_element(By.XPATH, XPATH).click()
                break
            except:
                count += 1
                time.sleep(1)
                if count > 10:
                    raise tooManyRetriesException("Can't click on the element " + XPATH)
                else:
                    print("Failed time " + XPATH)

    def kill(self):
        self.socket.quit()
        self.driver.quit()



