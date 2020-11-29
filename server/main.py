from aiohttp import web
import aiohttp
import json
import base64
import math


# def base64_to_wav(string, file_name):
#     wav_file = open(file_name, "wb")
#     decode_string = base64.b64decode(string)
#     wav_file.write(decode_string)
#
#
# def wav_to_base64(file_name):
#     wav_file = open(file_name, "wb")
#     encode_string = base64.b64encode(wav_file)
#     wav_file.close()
#     return encode_string

class ExtensionUser:

    def __init__(self, ws, pos_i, pos_j):
        self.ws = ws
        self.pos_i = pos_i
        self.pos_j = pos_j



class WebSocketRequestHandler:

    def __init__(self):
        self.ws = None
        self.connections = set()

    def send_matrix(self, ext_user):
        st = ''
        for i in range(8):
            for j in range(7):
                st += str(i) + '' + str(j)
                b = False
                for user in self.connections:
                    if user.pos_i == i and user.pos_j == j:
                        if user == ext_user:
                            st += str(2)
                        else:
                            st += str(1)
                        b = True
                        break
                if b == False:
                    st += '0'
                st += ';'
        st = '1' + st
        #print("Our matrix:\n" + st)
        return st


    async def handle(self, request):

        #session = await
        ws = web.WebSocketResponse()
        #self.connections.add(ws)
        self.ws = ws

        await ws.prepare(request)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':

                    for user in self.connections:
                        if user.ws == ws:
                            self.connections.remove(user)

                    await ws.close()
                    print('Closed')
                else:

                    print(self.connections)
                    data = msg.data
                    print('Received' + msg.data)
                    json_data = json.loads(msg.data)
                    print(f'Type {json_data["type"]}')

                    if json_data['type'] == 'set_place':
                        i = int(json_data['i'])
                        j = int(json_data['j'])
                        #get user check if exists
                        b = False
                        for user in self.connections:
                            if user.ws == ws:
                                b = True
                                break
                        #check overlap
                        for user in self.connections:
                            if user.pos_i == i and user.pos_j == j:
                                b = True
                                break
                        if b == False:
                            new_user = ExtensionUser(ws, i, j)
                            self.connections.add(new_user)
                            await new_user.ws.send_str("sit");

                            for user in self.connections:
                                await user.ws.send_str(self.send_matrix(user))

                    if json_data['type'] == 'send_sound':
                        #get current user
                        main_user = None
                        for user in self.connections:
                            if user.ws == ws:
                                main_user = user
                                break
                        if main_user == None:
                            return

                        for user in self.connections:
                            if user.ws != ws:
                                sound = json_data['sound']
                                dist_i = user.pos_i - main_user.pos_i
                                dist_j = user.pos_j - main_user.pos_j
                                volume = round(10 - math.sqrt((dist_i*dist_i)+(dist_j*dist_j)));
                                #print("I: " + str(dist_i) + ", J: " + str(dist_j) + ", Vol: " + str(volume));
                                await user.ws.send_str("2" + str(volume) + sound);

                    if json_data['type'] == 'get_matrix':
                        await ws.send_str(self.send_matrix(None))

        for user in self.connections:
            if user.ws == ws:
                self.connections.remove(user)

        print('Closed')
        return ws


app = web.Application()
handler = WebSocketRequestHandler()
app.add_routes([web.get('/', handler.handle)])
web.run_app(app)

#print(wav_to_base64('temp.wav'))
