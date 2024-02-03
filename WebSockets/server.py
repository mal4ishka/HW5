import asyncio
import logging
import names
import websockets
from aiofile import async_open
from aiopath import AsyncPath
from datetime import datetime
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            mes = message.split(': ')[1]
            if mes.__contains__('exchange'):
                result = await self.run_currencies_script(mes)
                [await client.send(result) for client in self.clients]
                await self.write_log()
            else:
                [await client.send(message) for client in self.clients]

    async def run_currencies_script(self, mes: str):
        try:
            if mes.__contains__(' '):
                args = mes.split(' ')

                process = await asyncio.create_subprocess_exec(
                    'python', 'currencies.py', f'{args[1]}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:

                process = await asyncio.create_subprocess_exec(
                    'python', 'currencies.py',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return stdout.decode('utf-8')
            else:
                return f"Error occurred: {stderr.decode('utf-8')}"

        except Exception as e:
            return f"Error occurred: {str(e)}"

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
             await self.send_to_clients(f"{ws.name}: {message}")

    async def write_log(self):
        apath = AsyncPath('log.txt')
        async with async_open(apath, 'a') as afd:
            await afd.write(f'{datetime.now()}: Exchange command used\n')


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
