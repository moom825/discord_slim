import json
import httpx
import copy
import asyncio
import urllib.parse
import aiohttp
import random
import string
def fetch_channel_raw(token, channel_id):
    headers={
        "Authorization": "Bot "+token
    }
    data=httpx.get("https://discord.com/api/v9/channels/"+channel_id, headers=headers).json()
    return data
def fetch_message_raw(token, channel_id,message_id):
    headers={
        "Authorization": "Bot "+token
    }
    data=httpx.get(f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}", headers=headers).json()
    return data
def Merge(dict1, dict2):
    for i in dict2.keys():
        dict1[i]=dict2[i]
    return dict1
def _RandomBoundery(stringdata):
    returnme=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    while returnme in stringdata:
        returnme=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return returnme
def _generatereq(data,attachments):
    stringdata=json.dumps(data)
    boundery=_RandomBoundery(stringdata).encode("utf8")
    temp=[]
    file_id=0
    bottomlayer=b''
    for i in attachments:
        tempdata={}
        tempdata["id"]=file_id
        tempdata["filename"]=i["filename"]
        temp.append(tempdata)
        bottomlayer+=b"\n--"+boundery+"\nContent-Disposition: form-data; name=\"files[{filenum}]\"; filename=\"{filename}\"\n".format(filenum=str(file_id),filename=i["filename"]).encode("utf8")+b'\n'+i["bytes"]
        file_id+=1
    data["attachments"]=temp
    stringdata=json.dumps(data)
    done=b"\n--"+boundery+b"\nContent-Disposition: form-data; name=\"payload_json\"\nContent-Type: application/json\n"+b'\n'+stringdata.encode()+bottomlayer+b"\n--"+boundery+b"--"
    returnme={}
    returnme["data"]=done
    returnme["boundery"]=boundery.decode()
    return returnme
class Message:
    def __init__(self, message, token):
        self.token=token
        self.message=copy.deepcopy(message)
        self.message["author"]["bot"]="bot" in self.message["author"]
        self.message["author"]=User(self.message["author"],token)
        self.__dict__=Merge(self.__dict__,self.message)
        self.__dict__["_rawmessage"]=self.message
        self.__dict__["channel"] = Channel(fetch_channel_raw(self.token,self.message['channel_id']),self.token)
    async def reply(self, message=None,embed=None,ping=False,attachments=[]):
        if "channel_id" not in self.__dict__:
            raise Exception("The message has no origin")
        url=f"https://discord.com/api/v9/channels/{self.message['channel_id']}/messages"
        payload={}
        if message!=None:
            payload["content"]=message
        if embed!=None:
            payload["embeds"]=embed
        data={"parse":["users","roles","everyone"],"replied_user":ping}
        reply={}
        reply['channel_id']=self.message['channel_id']
        reply["message_id"]=self.message["id"]
        payload["message_reference"]=reply
        payload["allowed_mentions"]=data   
        session=aiohttp.ClientSession()
        data=_generatereq(payload,attachments)
        headers = {'content-type': 'multipart/form-data; boundary='+data["boundery"]}
        headers["authorization"]="Bot "+self.token
        response=await session.post(url,data=data['data'],headers=headers)
        await session.close()
        returndata=await response.json()
        try:   
            return Message(returndata,self.token)
        except:
            return Error(returndata)
    async def edit(self, message=None,embed=None,ping=False,attachments=[]):
        if "channel_id" not in self.__dict__:
            raise Exception("The message has no origin")
        url=f"https://discord.com/api/v9/channels/{self.message['channel_id']}/messages/{self.message['id']}"
        payload={}
        if message!=None:
            payload["content"]=message
        if embed!=None:
            payload["embeds"]=embed
        data={"parse":["users","roles","everyone"],"replied_user":ping}
        reply={}
        reply['channel_id']=self.message['channel_id']
        reply["message_id"]=self.message["id"]
        payload["message_reference"]=reply
        payload["allowed_mentions"]=data   
        session=aiohttp.ClientSession()
        data=_generatereq(payload,attachments)
        headers = {'content-type': 'multipart/form-data; boundary='+data["boundery"]}
        headers["authorization"]="Bot "+self.token
        response=await session.patch(url,data=data['data'],headers=headers)
        await session.close()
        returndata=await response.json()
        try:   
            return Message(returndata,self.token)
        except:
            return Error(returndata)
    async def delete(self):
        headers={
                    "Authorization": "Bot "+self.token
                }
        url=f"https://discord.com/api/v9/channels/{self.message['channel_id']}/messages/{self.message['id']}"
        session=aiohttp.ClientSession()
        response=await session.delete(url,headers=headers)
        await session.close()
        returndata=await response.json()
        try:   
            return Message(returndata,self.token)
        except:
            return Error(returndata)

class Channel:
    def __init__(self, channelid, token, CurrentChannels=None):
        self.token=token
        self.perm_editor=Permissions()
        if CurrentChannels!=None:
            self.channelid=channelid
            for i in copy.deepcopy(CurrentChannels):
                if i["id"] == channelid:
                    self.__dict__=Merge(self.__dict__,i)
                    self.__dict__["_rawmessage"]=i
                    break
            else:
                raise Exception("Unknown channel")
        else:
            self.channelid=channelid["id"]
            self.__dict__=Merge(self.__dict__,channelid)
            self.__dict__["_rawmessage"]=channelid
    async def send(self, channel_id=None, message=None,embed=None,message_reference=None,message_reference_ping=False, attachments=[]):
        if channel_id==None:
            channel_id=self.channelid
        url=f"https://discord.com/api/v9/channels/{channel_id}/messages"
        payload={}
        if message!=None:
            payload["content"]=message
        if embed!=None:
            payload["embeds"]=embed
        if message_reference!=None:
            data={"parse":["users","roles","everyone"],"replied_user":message_reference_ping}
            payload["message_reference"]=message_reference
            payload["allowed_mentions"]=data
        
        session=aiohttp.ClientSession()
        data=_generatereq(payload,attachments)
        headers = {'content-type': 'multipart/form-data; boundary='+data["boundery"]}
        headers["authorization"]="Bot "+self.token
        returndata=await(await session.post(url,data=data['data'],headers=headers)).json()
        await session.close()
        try:
            return Message(returndata,self.token)
        except:
            return Error(returndata)
    async def delete(self):
        headers={
                    "Authorization": "Bot "+self.token
                }
        url=f"https://discord.com/api/v9/channels/{self.channelid}"
        session=aiohttp.ClientSession()
        response=await session.delete(url,headers=headers)
        await session.close()
        returndata=await response.json()
        try:   
            return Channel(returndata,self.token)
        except:
            return Error(returndata)
    async def edit(self, role_or_user_id, IsMember=False, BitWisePerms_allow=0,BitWisePerms_disallow=0):
        headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bot "+self.token
                }
        payload = {"id":role_or_user_id,"type":1 if IsMember else 0,"deny":str(BitWisePerms_disallow),"allow":str(BitWisePerms_allow)}
        session=aiohttp.ClientSession()
        response=await session.put(f"https://discord.com/api/v9/channels/{self.channelid}/permissions/{role_or_user_id}",data=json.dumps(payload), headers=headers)
        await session.close()
        if response.status!=204:
            return Error(await response.json())
        return self
class Guild:
    def __init__(self, guildid, token, CurrentGuilds=None):
        self.token=token
        if CurrentGuilds!=None:
            self.guildid=guildid
            for i in copy.deepcopy(CurrentGuilds):
                if i["id"] == guildid:
                    i["channels"]=[Channel(b,token,None) for b in i["channels"]]
                    i["members"]=[Member(b,token) for b in i["members"]]
                    i["roles"]=[Role(b,token) for b in i["roles"]]
                    self.__dict__=Merge(self.__dict__,i)
                    self.__dict__["_rawmessage"]=i
                    break
            else:
                raise Exception("Unknown guild")
        else:
            self.guildid=guildid["id"]
            if "channels" in guildid:
                guildid["channels"]=[Channel(b,token,None) for b in guildid["channels"]]
            else:
                headers={
                    "Authorization": "Bot "+self.token
                }
                data=httpx.get("https://discord.com/api/v9/guilds/"+self.guildid+"/channels", headers=headers).json()
                data2=httpx.get("https://discord.com/api/v9/guilds/"+self.guildid+"/members", headers=headers).json()
                data3=httpx.get("https://discord.com/api/v9/guilds/"+self.guildid+"/roles", headers=headers).json()#problem
                #print(data3)
                guildid["channels"]=[Channel(b,token,None) for b in data]
                guildid['members']=[Member(b,token) for b in data2]
                guildid['roles']=[Role(b,token) for b in data3]
            self.__dict__=Merge(self.__dict__,guildid)
            self.__dict__["_rawmessage"]=guildid
    async def CreateChannel(self,name,channel_type=0,permission_overwrites=[],catagory_id=None):
        headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bot "+self.token
                }
        payload={}
        payload["type"]=channel_type
        payload["name"]=name
        payload["permission_overwrites"]=permission_overwrites
        payload["parent_id"]=catagory_id
        session=aiohttp.ClientSession()
        data=await(await session.post(f"https://discord.com/api/v9/guilds/{self.guildid}/channels",data=json.dumps(payload),headers=headers)).json()
        await session.close()
        try:
            return Channel(data, self.token)
        except:
            return Error(data)
    async def DeleteChannel(self,channel_id):
        session=aiohttp.ClientSession()
        headers={
                    "Authorization": "Bot "+self.token
                }
        session=aiohttp.ClientSession()
        data=await(await session.delete(f"https://discord.com/api/v9/channels/{channel_id}",headers=headers)).json()
        await session.close()
        try:
            return Channel(data, self.token)
        except:
            return Error(data)
    async def Ban(self, user_id, reason='', delete=0):
        session=aiohttp.ClientSession()
        headers={
                    "x-audit-log-reason": reason,
                    "Authorization": "Bot "+self.token
                }
        payload={'delete_message_seconds': delete}
        resp=await session.put(f"https://discord.com/api/v9/guilds/{self.guildid}/bans/{user_id}",data=json.dumps(payload), headers=headers)
        await session.close()
        if resp.status!=204:
            return Error(await resp.json())
    async def UnBan(self, user_id):
        session=aiohttp.ClientSession()
        headers={
                    "Authorization": "Bot "+self.token
                }
        resp=await session.delete(f"https://discord.com/api/v9/guilds/{self.guildid}/bans/{user_id}", headers=headers)
        await session.close()
        if resp.status!=204:
            return Error(await resp.json())
    async def Kick(self, user_id, reason=''):
        session=aiohttp.ClientSession()
        headers={
                    "x-audit-log-reason": reason,
                    "Authorization": "Bot "+self.token
                }
        resp=await session.delete(f"https://discord.com/api/v9/guilds/{self.guildid}/members/{user_id}",headers=headers)
        await session.close()
        if resp.status!=204:
            return Error(await resp.json())
class User:
    def __init__(self, user_info, token):
        self.token=token
        if "id" not in user_info:
            raise Exception("Missing vital user info")
        if "roles" in user_info:
            user_info["roles"]=[Role(b,token) for b in user_info["roles"]]
        self.user_id=user_info["id"]
        self.__dict__=Merge(self.__dict__,copy.deepcopy(user_info))
        self.__dict__["_rawmessage"]=copy.deepcopy(user_info)
    
    async def create_dm(self):
        headers = {'content-type': 'application/json'}
        headers["authorization"]="Bot "+self.token
        payload={"recipients": [self.user_id]}
        session=aiohttp.ClientSession()
        payload=json.dumps(payload)
        returndata=await(await session.post("https://discord.com/api/v9/users/@me/channels",data=payload,headers=headers)).json()
        await session.close()
        if "id" not in returndata:
            raise Exception("Error creating dm")
        return returndata["id"]
class Member:
    def __init__(self,member_data,token):
        member_data['user']=User(member_data['user'],token)
        self.__dict__=member_data
class Attachments:
    def __init__(self):
        self.attachments={}
    def Add(filename, filebytes):
        self.attachments[filename]=filebytes
class Error:
    def __init__(self, err):
        self.__dict__=Merge(self.__dict__,copy.deepcopy(err))
        self.__dict__["_rawmessage"]=copy.deepcopy(err)
class Role:
    def __init__(self,data,token):
        self.token=token
        if "permissions" in data:
            data["permissions"]=Permissions(data["permissions"])
        self.__dict__["_rawmessage"]=data
        self.__dict__=Merge(self.__dict__,data)
class Permissions:
    def __init__(self,permission_value=0):
        permission_value=int(permission_value)
        self._perms={1: 'CREATE_INSTANT_INVITE', 2: 'KICK_MEMBERS', 4: 'BAN_MEMBERS', 8: 'ADMINISTRATOR', 16: 'MANAGE_CHANNELS', 32: 'MANAGE_GUILD', 64: 'ADD_REACTIONS', 128: 'VIEW_AUDIT_LOG', 256: 'PRIORITY_SPEAKER', 512: 'STREAM', 1024: 'VIEW_CHANNEL', 2048: 'SEND_MESSAGES', 4096: 'SEND_TTS_MESSAGES', 8192: 'MANAGE_MESSAGES', 16384: 'EMBED_LINKS', 32768: 'ATTACH_FILES', 65536: 'READ_MESSAGE_HISTORY', 131072: 'MENTION_EVERYONE', 262144: 'USE_EXTERNAL_EMOJIS', 524288: 'VIEW_GUILD_INSIGHTS', 1048576: 'CONNECT', 2097152: 'SPEAK', 4194304: 'MUTE_MEMBERS', 8388608: 'DEAFEN_MEMBERS', 16777216: 'MOVE_MEMBERS', 33554432: 'USE_VAD', 67108864: 'CHANGE_NICKNAME', 134217728: 'MANAGE_NICKNAMES', 268435456: 'MANAGE_ROLES', 536870912: 'MANAGE_WEBHOOKS', 1073741824: 'MANAGE_EMOJIS_AND_STICKERS', 2147483648: 'USE_APPLICATION_COMMANDS', 4294967296: 'REQUEST_TO_SPEAK', 8589934592: 'MANAGE_EVENTS', 17179869184: 'MANAGE_THREADS', 34359738368: 'CREATE_PUBLIC_THREADS', 68719476736: 'CREATE_PRIVATE_THREADS', 137438953472: 'USE_EXTERNAL_STICKERS', 274877906944: 'SEND_MESSAGES_IN_THREADS', 549755813888: 'USE_EMBEDDED_ACTIVITIES', 1099511627776: 'MODERATE_MEMBERS'}
        self.temp={}
        for i in self._perms.keys():
            self.temp[self._perms[i]]=False
            if (permission_value & i)==i:
                self.temp[self._perms[i]]=True
        self.__dict__["_rawmessage"]=permission_value
        self.__dict__["value"]=permission_value
        self.__dict__=Merge(self.__dict__,self.temp)
    def CalculateBitWise(self, perms_dict=None):
        _temp=[]
        if perms_dict==None:
            perms_dict={i:self.__dict__[i] for i in self.__dict__ if i in list(self._perms.values())}
        for i in perms_dict.keys():
            if i not in list(self._perms.values()):
                raise Exception("Unknown Permission: "+ i)
            if perms_dict[i]==True:
                _temp.append(self._GetKeyByValue(self._perms, i))
        if len(_temp)<1:
            return 0
        returnme=_temp[0]
        for i in _temp[1:]:
            returnme=i|returnme
        return returnme
    def _GetKeyByValue(self, _dict,value):
        for i in _dict.keys():
            if _dict[i]==value:
                return i
        else:
            raise Exception("Unknown Value")
class Reaction:
    def __init__(self,data,token):
        self.token=token
        self.emoji_name=data["emoji"]["name"]
        self.emoji_id=data["emoji"]["id"]
        self.user_id=data['user_id']
        self.channel_id=data['channel_id']
        self.message_id=data['message_id']
        if 'member' in data:
            data["member"]=Member(data["member"],self.token)
        data["emoji"]=Emoji(data["emoji"])
        data["message"]=Message(fetch_message_raw(self.token,data["channel_id"],data["message_id"]),self.token)
        self.__dict__=Merge(self.__dict__,data)
    async def Remove(self):
        headers={
                    "Authorization": "Bot "+self.token
                }
        emojidata=None
        if self.emoji_id!=None:
            emojidata=urllib.parse.quote_plus(f"{self.emoji_name}:{self.emoji_id}")
        else:
            emojidata=urllib.parse.quote_plus(self.emoji_name)
        url=f"https://discord.com/api/v9/channels/{self.channel_id}/messages/{self.message_id}/reactions/{emojidata}/{self.user_id}"
        session=aiohttp.ClientSession()
        response=await session.delete(url,headers=headers)
        await session.close()
        if response.status!=204:
            return Error(await response.json())
class Emoji:
    def __init__(self,data):
        self.__dict__=data
class Typing:
    def __init__(self, typing_message, token):
        pass#make it replace channel with channel class and user with user class etc