import websockets
import asyncio
import json
import threading
import sys
import os
from .websockethandler import websockethandler
from .classes.class_handling import *
class discordhandler:
    def __init__(self,token):
        self.token=token
        self.guilds=[]
        self.channels=[]
        self.eventlist = ["OnReady", "OnMessage", "OnReactionAdd", "OnReactionRemove","OnChannelRemove","OnChannelCreate","OnChannelUpdate","OnUserLeave","OnUserJoin"]
        self.resonders={}
        async def _(*args,**kwargs): return None
        for i in self.eventlist:
            self.resonders[i]=_#lambda *args,**kwargs:None
        self.websocket=None
        self.apiurl='wss://gateway.discord.gg/?v=9&encoding=json'
    def run(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())#weird windows issue with errors, sus indeed
        asyncio.get_event_loop().run_until_complete(self._run())
        #asyncio.run(self._run())

    async def _run(self):
        self.websocket=websockethandler(self.handlemessage,self.handleclose)
        await self.websocket.connect(self.apiurl)
    async def handlemessage(self,message):
        message=json.loads(message)
        if message["op"]==10:
            await self.login()
            await self.heartbeat(message["d"]["heartbeat_interval"])
        elif message['op']==11:
            pass#heartbeat recived
        elif message["op"]==0:
            #print(message)
            if message["t"] == "READY":
                await asyncio.sleep(1)
                await self.resonders["OnReady"](message["d"]["user"])
            elif message["t"] == "MESSAGE_CREATE":
                if "content" in message["d"]:
                    await self.resonders["OnMessage"](Message(message["d"],self.token))
            elif message["t"] == "MESSAGE_REACTION_ADD":
                await self.resonders['OnReactionAdd'](Reaction(message["d"],self.token))
            elif message["t"] == "MESSAGE_REACTION_REMOVE":
                await self.resonders['OnReactionRemove'](Reaction(message["d"],self.token))
            elif message['t']=='GUILD_CREATE':
                self.guilds.append(message['d'])
                self.channels=self.channels+message['d']["channels"]
                
            elif message['t']=='GUILD_REMOVE':#MAY BE WRONG TEST BY LEAVING A GUILD/BEING KICKED
                for i in self.guilds:
                    if i["guild_id"]==message["d"]["id"]:
                        self.guilds.remove(i)
                        break
            elif message['t']=='GUILD_UPDATE':
                guild_id=message["d"]['id']
                temp={}
                for i in self.guilds:
                    if i['id']==guild_id:
                        for c in message["d"]:
                            if c in i.keys():
                                self.guilds[self.guilds.index(i)][c]=message["d"][c]
                                temp=self.guilds[self.guilds.index(i)]
                #add a guild update
            elif message["t"]=="CHANNEL_CREATE":
                self.channels=self.channels+[message["d"]]
                for i in self.guilds:
                    if i["id"]==message["d"]['guild_id']:
                        self.guilds[self.guilds.index(i)]["channels"].append(message["d"])
                        break
                await self.resonders['OnChannelCreate'](Channel(message["d"],self.token))
            elif message["t"]=="CHANNEL_DELETE":
                for i in self.channels:
                    if i["id"]==message["d"]["id"]:
                        self.channels.remove(i)
                        break
                for i in self.guilds:
                    if i["id"]==message["d"]['guild_id']:
                        self.guilds[self.guilds.index(i)]["channels"].remove([c for c in self.guilds[self.guilds.index(i)]["channels"] if c["id"]==message["d"]["id"]][0])
                        break
                await self.resonders['OnChannelRemove'](Channel(message["d"],self.token))
            elif message["t"]=="CHANNEL_UPDATE":
                guild_id=message["d"]["guild_id"]
                temp={}
                for i in self.channels:
                    if i["id"]==message["d"]["id"]:
                        for c in self.channels[self.channels.index(i)].keys():
                            if c in message["d"].keys():
                                self.channels[self.channels.index(i)][c]=message["d"][c]
                                temp=self.channels[self.channels.index(i)]
                    #self.channels[self.channels.index(i)]=temp
                for i in self.guilds:
                    if i["id"]==guild_id:
                        for c in self.guilds[self.guilds.index(i)]["channels"]:
                            if c["id"]==message["d"]["id"]:
                                self.guilds[self.guilds.index(i)]["channels"][self.guilds[self.guilds.index(i)]["channels"].index(c)]=temp
                await self.resonders['OnChannelUpdate'](Channel(temp,self.token))
            elif message["t"]=="GUILD_MEMBER_REMOVE":
                await self.resonders['OnUserLeave'](Member(message["d"],self.token))
            elif message["t"]=="GUILD_MEMBER_ADD":
                await self.resonders['OnUserJoin'](Member(message["d"],self.token))
            else:
                print(message)
                pass
            #dealing with guilds and channels tbil (to be implemented later)
        else:
            print(message)
            print('??????')
    def get_guilds(self):
        return [Guild(i["id"],self.token,self.guilds) for i in self.guilds]
    def GetUserRoles(self, guildid, userid):
        guild=self.get_guild(guildid)
        userclass=None
        for i in guild.members:
            if i.user.id==userid:
                userclass=i
                break
        else:
            raise Exception("unknown user")
        temp=[]
        for i in guild.roles:
            if i.id in userclass.roles:
                temp.append(i)
        return temp
    async def fetch_user(self,user_id):
        headers={
            "Authorization": "Bot "+self.token
        }
        session=aiohttp.ClientSession()
        data=await(await session.get("https://discord.com/api/v9/users/"+user_id,headers=headers)).json()
        await session.close()
        return User(data,self.token)
    def get_guild(self, guild_id):
        return Guild(guild_id,self.token,self.guilds)
    
    def get_channel(self, channelid):
        return Channel(channelid,self.token,self.channels)
    async def fetch_channel(self, channel_id):
        headers={
            "Authorization": "Bot "+self.token
        }
        session=aiohttp.ClientSession()
        data=await(await session.get("https://discord.com/api/v9/channels/"+channel_id, headers=headers)).json()
        await session.close()
        return Channel(data,self.token)
    async def fetch_guild(self, guild_id):
        headers={
            "Authorization": "Bot "+self.token
        }
        session=aiohttp.ClientSession()
        data=await(await session.get("https://discord.com/api/v9/guilds/"+guild_id, headers=headers)).json()
        await session.close()
        return Guild(data,self.token)
    async def handleclose(self):
        print("no right?")
        #not needed rn
        pass
    async def set_presence(self, since=0, game='', status="online",afk=False):
        payload={
          "op": 3,
          "d": {
            "since": since,
            "activities": [
                {
                  "name": game,
                  "type": 0
                }
            ],
            "status": status,
            "afk": afk
          }
        }
        await self.websocket.send(json.dumps(payload))
    async def login(self,intents=32767):
        response={}
        data={}
        devicedata={}
        response["op"]=2
        data["token"]=self.token
        data["intents"]=intents
        devicedata["os"]="linux"
        devicedata["browser"]="discord_slim"
        devicedata["device"]="discord_slim"
        data["properties"]=devicedata
        response["d"]=data
        responsetext=json.dumps(response)
        await self.websocket.send(responsetext)

    async def heartbeat(self,wait):
        response={}
        response["op"]=1
        response["d"]=5
        responsetext=json.dumps(response)
        while True:
            await asyncio.sleep(wait*0.001)
            await self.websocket.send(responsetext)
            
    def event(self, func):
        for i in self.eventlist:
            if func.__name__.lower() == i.lower():
                self.resonders[i]=func
                break
        else:
            raise Exception("Unknown Function at: "+func.__name__)
        def _(*args,**kwargs):
            func(*args,**kwargs)
        return _