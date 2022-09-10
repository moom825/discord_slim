import websockets
import threading
import asyncio
class websockethandler:
    def __init__(self,onmessage,onclose):
        self.onmessage=onmessage
        self.onclose=onclose
        self.connected=False
        self.websocket=None
    async def connect(self, url):
        async for websocket in websockets.connect(url):
            self.websocket=websocket
            self.connected=True
            try:
                while True:
                    recived=await websocket.recv()
                    threading.Thread(None,target=asyncio.run, args=(self.onmessage(recived),)).start()
            except:
               self.connected=False
               await self.onclose()
               break
    async def send(self,message):
        await self.websocket.send(message)