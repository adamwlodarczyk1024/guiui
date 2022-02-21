# This Python file uses the following encoding: utf-8
#GUI
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
#NETWORK

import socket
import threading


# Setup

SERVER_IP = "192.168.100.208"
MANAGER_PORT = 25500
INFO_PORT = 25501

# ----- NET PROTOCOL -----

# Manager packets
LOGIN_PACKET = b'\x01'
CREATE_CHANNEL_PACKET = b'\x02'

# Info packets
LIST_CHANNELS_PACKET = b'\x01'
LIST_MEMBERS_ON_CHANNEL_PACKET = b'\x00'

# Channel packets
JOIN_CHANNEL_PACKET = b'\x01'
LEAVE_CHANNEL_PACKET = b'\x00'











# ----- NET PROTOCOL FUNCTIONS -----

def login_user(ipserv, user_name, manager_port):
        manager_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        manager_socket.connect((ipserv, int(manager_port)))
        manager_socket.send(LOGIN_PACKET)
        manager_socket.send(user_name.encode('utf-8'))

        return manager_socket

def join_channel(user_name, channel):
    join_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    join_socket.connect((SERVER_IP, channel['join_port']))
    join_socket.send(JOIN_CHANNEL_PACKET)
    join_socket.send(user_name.encode('utf-8'))
    join_socket.close()


def leave_channel(user_name, channel):
    leave_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    leave_socket.connect((SERVER_IP, channel['join_port']))
    leave_socket.send(LEAVE_CHANNEL_PACKET)
    leave_socket.send(user_name.encode('utf-8'))
    leave_socket.close()


def create_channel(creator_name, channel_name):
    manager_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    manager_socket.connect((SERVER_IP, MANAGER_PORT))
    manager_socket.send(CREATE_CHANNEL_PACKET)
    creator_name = bytes(creator_name, 'utf-8')

    for i in range(0, 32 - len(creator_name)):
        creator_name += b'\x00'

    manager_socket.send(creator_name + channel_name.encode('utf-8'))
    curr_channel_join_port = manager_socket.recv(4)

    if curr_channel_join_port == b'\x00':
        print("Failed to create channel on server")

    manager_socket.close()

    join_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    join_socket.connect((SERVER_IP, int.from_bytes(curr_channel_join_port, byteorder='little')))
    join_socket.send(JOIN_CHANNEL_PACKET)

    join_socket.send(creator_name)

    join_socket.close()


def get_channels():
    info_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    info_socket.connect((SERVER_IP, INFO_PORT))

    info_socket.send(LIST_CHANNELS_PACKET)

    number_of_channels = info_socket.recv(4)

    number_of_channels = int.from_bytes(number_of_channels, byteorder='little')

    channels_list = []
    for i in range(number_of_channels):
        channel_info = info_socket.recv(40)
        chat_port = int.from_bytes(channel_info[0:4], byteorder='little')
        join_port = int.from_bytes(channel_info[4:8], byteorder='little')
        channel_name = channel_info[8:40].split(b'\x00')
        channel_name = channel_name[0].decode('utf-8')
        channels_list.append({'chat_port': chat_port, 'join_port': join_port, 'channel_name': channel_name})

    info_socket.close()

    return channels_list


def get_channel_members(channel):
    info_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    info_socket.connect((SERVER_IP, INFO_PORT))

    info_socket.send(LIST_MEMBERS_ON_CHANNEL_PACKET)

    info_socket.send(channel["channel_name"].encode("utf-8"))

    number_of_channels = info_socket.recv(4)
    number_of_channels = int.from_bytes(number_of_channels, byteorder='little')

    members_on_channel = []
    for i in range(number_of_channels):
        member = info_socket.recv(32)
        member = member.split(b'\x00')
        member = member[0].decode('utf-8')
        members_on_channel.append(member)

    info_socket.close()

    return members_on_channel


def send_message(channel, message, creator_name):
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_socket.connect((SERVER_IP, channel['chat_port']))

    creator_name = bytes(creator_name, 'utf-8')

    for i in range(0, 32 - len(creator_name)):
        creator_name += b'\x00'

    message = bytes(message, 'utf-8')

    for i in range(0, 160 - len(message)):
        message += b'\x00'

    send_socket.send(creator_name + message)

    send_socket.close()


def get_message(channel_conn_socket):
    received_message = channel_conn_socket.recv(224)

    author = received_message[0:32].split(b'\x00')
    author = author[0].decode('utf-8')

    channel = received_message[32:64].split(b'\x00')
    channel = channel[0].decode('utf-8')

    message = received_message[64:224].split(b'\x00')
    message = message[0].decode('utf-8')

    return {'author': author, 'channel': channel, 'message': message}


# recive messages

print_sync_lock = threading.Lock()
receiver_thread_kill_signal = False


def chat_listener(messages_conn_socket):
    while True:
        rec_message = get_message(messages_conn_socket)
        if rec_message == b'':
            continue
        if receiver_thread_kill_signal:
            return
        print_sync_lock.acquire()
        widget.conversation.append(str(rec_message['author']) + ' : ' + str(rec_message['message']))
        print_sync_lock.release()









def clickchannel(item):
    #print(item.text())
    item.setBackground( QColor('#7fc97f'))



    tmp_channels = get_channels()
    ch_name = item.text()

    req_channel = None
    for ch in tmp_channels:
        if item.text() == ch['channel_name']:
            req_channel = ch
            break


    join_channel(widget.user_name, req_channel)
    leave_channel(widget.user_name, widget.curr_channel)
    widget.curr_channel = req_channel
    widget.conversation.append("Joined channel " +  item.text())



class Widget(QWidget):
    def __init__(self):
        super(Widget, self).__init__()
        loadUi('form.ui',self)
        #self.load_ui()
        self.logged = 0 
        self.curr_channel = get_channels()[0]
        self.main_channel = get_channels()[0]

        self.setWindowTitle('IRC')



        self.user_name = ""
        self.manager_port = self.port_manage_input.text()
        self.ipserv = self.ip_input.text()  
        self.user_name = self.user_input.text()

        timer = QTimer(self)
        timer.timeout.connect(self.channellistrefresh)
        timer.start(1000)


        self.connect_button.clicked.connect(self.onconnectbutton)
        self.send_button.clicked.connect(self.onsendbutton)
        self.channel_create_button.clicked.connect(self.onchannelcreatebutton)

        self.channel_list.itemActivated.connect(clickchannel)




    def onconnectbutton(self):
        widget.user_name = self.user_input.text()
        widget.manager_port = self.port_manage_input.text()
        widget.ipserv = self.ip_input.text()  
        

        messages_socket = login_user(self.ipserv,self.user_name,self.manager_port)
        self.conversation.append("Logged in " + self.ipserv + " as " + self.user_name)

        receiver_thread = threading.Thread(target=chat_listener, args=(messages_socket, ))
        receiver_thread.start()



        join_channel(self.user_name, self.curr_channel)
        self.logged = 1

    def onsendbutton(self):
        mts = self.text_input.text().split(' ')

        message_to_send = ''
        for part in mts:
            message_to_send += part + ' '

        send_message(self.curr_channel, message_to_send, self.user_name)
        self.text_input.clear()

    def channellistrefresh(self):
        #jeśli już zalogowano
        if self.logged == 1:
            
            self.channel_list.clear()
            tmp_channels = get_channels()

            for ch in tmp_channels:
                self.channel_list.addItem(str(ch['channel_name']))

            self.channel_list.repaint()

            






    def onchannelcreatebutton(self):
        ch_name = self.channel_input.text()
        

        create_channel(widget.user_name, ch_name)
        

        tmp_channels = get_channels()
        req_channel = None
        for ch in tmp_channels:
            if ch_name == ch['channel_name']:
                req_channel = ch
                break
        #join_channel(self.user_name, req_channel)
        leave_channel(widget.user_name, widget.curr_channel)
        self.curr_channel = req_channel
        
        widget.conversation.append("Created channel " + str(ch_name))
        widget.conversation.append("Joined channel " +  str(ch_name))
        


if __name__ == "__main__":

    app = QApplication([])
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())
