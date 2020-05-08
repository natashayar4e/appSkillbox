import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                # Понимаю, что следующий кусок можно проще, нет времени на эксперименты
                count = 0
                for client in self.server.clients:
                    if client.login == self.login:
                        count += 1
                if count == 1:
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()
                else:
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой".encode()
                    )
                    self.transport.close()
        else:
            self.send_message(decoded)
            self.server.logList.append(f"<{self.login}> {decoded} \n")

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        self.transport.write(f"Last messages:\n".encode())
        for logMessage in self.server.logList[-10:]:
            encoded = logMessage.encode()
            self.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    logList: list

    def __init__(self):
        self.clients = []
        self.logList = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888,
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
