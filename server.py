# СЕРВЕРНОЕ приложение

import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: "Server"
    transport: transports.Transport

    def __init__(self, server: "Server"):
        self.server = server

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()
        if self.login is not None:
            if decoded == "Sign out":
                self.transport.close()
                self.send_sys_message(f"User {self.login} has left the chat")
            else:
                self.server.messages.append(f"{self.login}: {decoded}")
                self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                new_user = True
                for user in self.server.clients:
                    if self.login == user.login and user != self:
                        connected_user = user
                        new_user = False
                if new_user:
                    self.send_sys_message(f"New user {self.login} has joined the chat")
                    self.transport.write(f"(-) Wellcome, {self.login}!\n".encode())
                    self.send_history(10)
                else:
                    self.transport.write(f"(-) Login {self.login} is already taken, choose another!\n".encode())
                    connected_user.transport.write(f"Somebody attempted to login under your name, {self.login}!\n".encode())
                    print('(-) Invalid login')
                    self.transport.close()

            else:
                self.transport.write(f"(-) Wrong login\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print(f"(-) New user connected. Total users = {len(self.server.clients)}:")
        for user in self.server.clients:
            print(user.login)

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("(-) User disconnected")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_sys_message(self, content: str):
        message = f"(-SYS-): {content}\n"
        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self, age: int):
        message = f"(-SYS-): last {age} messages:\n"
        self.transport.write(message.encode())
        for message in self.server.messages[-age:]:
            self.transport.write(f"{message}\n".encode())
        else:
            self.transport.write('(-SYS-) End of message history\n'.encode())


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()
        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            5000
        )
        print("(-) SERVER running ...")
        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print('(-)  SERVER Stopped manually')
