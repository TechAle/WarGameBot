import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import socket
import threading
from bs4 import BeautifulSoup


class Bot:
    def __init__(self, email, password, first):
        self.wait = None
        self.socket = None
        self.server = first
        self.email = email
        self.password = password

    def setup(self):
        # Open the browser, Open https://www.warzone.com/LogIn, enter the email and password, click on the login button
        self.driver = webdriver.Firefox()
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

    def start(self):
        while True:
            whatToDo = None
            # If we are the server we have to manage everyone first
            if self.server:
                whatToDo = "create"
            else:
                whatToDo = "join"

            if whatToDo == "join":
                # Wait for a message from the server
                message = self.socket.recv(1024).decode()
                self.joinGame(message)
            elif whatToDo == "create":
                self.createGame()

    def joinGame(self, url):
        self.driver.get(url)
        # Wait for element to exist //*[@id="ujs_JoinBtn_btn"] and then click it
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_JoinBtn_btn"]'))
        self.driver.find_element(By.XPATH, '//*[@id="ujs_JoinBtn_btn"]').click()
        # Say to the server that we are ready
        self.socket.send("1".encode())
        # Wait for element //*[@id="ujs_FinishVersusAIBtn_btn"] to exist
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_FinishVersusAIBtn_btn"]'))

    def createGame(self):
        self.driver.get("https://www.warzone.com/MultiPlayer?CreateGame=1")
        self.waitToClick("//*[@id='ujs_PlayersModeCode_toggle']")
        self.waitToClick('//*[@id="ujs_PlayersCodeBox_input"]')
        self.waitToClick('//*[@id="ujs_CreateGameBtn_btn"]')
        # Wait for url to change
        self.wait.until(lambda driver: driver.current_url != "https://www.warzone.com/MultiPlayer?CreateGame=1")
        # Get the url
        url = self.driver.current_url
        # Send the url to the clients
        for client in self.clients:
            client.send(url.encode())
        # Wait for the clients to be ready
        for client in self.clients:
            client.recv(1024).decode()
        # Start the game
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
        b = 0
        test = BeautifulSoup(self.driver.page_source, features="html.parser")
        codeDiv = str(test.find("div", {"id": "ujs_ModalContainer"}))
        codeDiv = codeDiv[:codeDiv[:codeDiv.index("Yes,")].rindex('<')]
        codeDiv = codeDiv[codeDiv.rindex("Button") - 4:]
        id = codeDiv[:codeDiv.index("btn") + 3]
        self.driver.execute_script(f'document.getElementById("{id}").click()')
        self.wait.until(lambda driver: driver.find_element(By.XPATH, '//*[@id="ujs_FinishVersusAIBtn_btn"]'))


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
                    raise Exception("Can't click on the element " + XPATH)
                else:
                    print("Failed time " + XPATH)



