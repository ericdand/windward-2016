#!/usr/bin/env python
"""
  ----------------------------------------------------------------------------
  "THE BEER-WARE LICENSE"
  As long as you retain this notice you can do whatever you want with this
  stuff. If you meet an employee from Windward some day, and you think this
  stuff is worth it, you can buy them a beer in return. Windward Studios
  ----------------------------------------------------------------------------
"""

## first_or_default = next((x for x in lst if ...), None)

import sys
import base64
import traceback
import threading
import time
from xml.etree import ElementTree as ET

import api.units as lib
import tcpClient
import myPlayerBrain
from debug import printrap

#local machine
DEFAULT_ADDRESS = "134.87.173.83"


class Framework(object):
    def __init__(self, args):
        if len(args) >= 2:
            self.brain = myPlayerBrain.MyPlayerBrain(args[1])
        else:
            self.brain = myPlayerBrain.MyPlayerBrain()
        self.ipAddress = args[0] if len(args) >= 1 else DEFAULT_ADDRESS
        self.guid = None

        # this is used to make sure we don't have multiple threads updating the
        # Player/Passenger lists, sending back multiple orders, etc.
        self.lock = threading.Lock()

        print("Connecting to server '%s' for user: %r, school: %r" %
              (self.ipAddress, self.brain.name, myPlayerBrain.SCHOOL))

    def _run(self):
        print("starting...")

        self.client = tcpClient.TcpClient(self.ipAddress, self)
        self.client.start()
        self._connectToServer()

        #It's all messages to us now.
        print('enter "exit" to exit program')
        try:
            while True:
                line = input()
                if line == 'exit':
                    break
        except EOFError:
            self.client.close() # exit on EOF
        finally:
            self.client.close()

    def statusMessage(self, message):
        print(message)

    def send_xml(self, message):
        #print ET.tostring(message) # uncomment to see all sent messages
        self.client.sendMessage(ET.tostring(message))

    def incomingMessage(self, message):
        try:
            startTime = time.clock()
            # get the XML - we assume we always get a valid message from the server.
            #print ET.tostring(xml,encoding='utf8', method='xml')

            xml = ET.XML(message)
            name = xml.tag
            printrap("Received message of type: " + name)
            self.guid = xml.get('my-guid')
            map = lib.GameMap(element=xml.find('map')) # need to handle the actual column/rows
            players = [lib.Player(player) for player in xml.find('players')]
            hotels = [lib.HotelChain(hotel) for hotel in xml.find('hotels')]
            #fix stock pointers to right place...

            #pdb.set_trace()
            me = None
            msgid = xml.get('msg-id')
            reply = None
            for player in players:
                if player.guid == self.guid:
                    me = player
                    print "found matching guid..."
                elif player.name == self.brain.name:
                    me = player
                    print "no matching guid, but found matching name... "

            if name == 'query-card':
                move = self.brain.QuerySpecialPowersBeforeTurn(map, me, hotels, players)
                reply = ET.Element('reply', {'cmd': name, 'msg-id': msgid, 'card': move})

            elif name == 'query-tile-purchase':
                move = self.brain.QueryTileAndPurchase(map, me, hotels, players)
                reply = ET.Element('reply', {'cmd': name, 'msg-id': msgid})
                if move is not None:
                    if move.Tile is not None:
                        reply.set("tile-x", str(move.Tile.x))
                        reply.set("tile-y", str(move.Tile.y))
                    if move.CreatedHotel is not None:
                        reply.set("created-hotel",move.CreatedHotel.name)
                    if move.MergeSurvivor is not None:
                        reply.set("merge-survivor", move.MergeSurvivor.name)

                    trade_string = ''.join(["{}:{};".format(stock.Trade, stock.Get) for stock in move.Trade])
                    if len(trade_string) > 0:
                        reply.set("trade", trade_string)

                    buy_string = ''.join(["{}:{};".format(stock.chain.name, stock.num_shares) for stock in move.Buy])
                    if len(buy_string) > 0:
                        reply.set("buy", buy_string)

            elif name == 'query-tile':
                move = self.brain.QueryTileOnly(map, me, hotels, players)
                reply = ET.Element('reply', {'cmd': name, 'msg-id': msgid})
                if move is not None:
                    if move.Tile is not None:
                        reply.set("tile-x", str(move.Tile.x))
                        reply.set("tile-y", str(move.Tile.y))
                    if move.CreatedHotel is not None:
                        reply.set("created-hotel",move.CreatedHotel.name)
                    if move.MergeSurvivor is not None:
                        reply.set("merge-survivor", move.MergeSurvivor.name)

            elif name == 'query-merge':
                defunct_name = xml.get('defunct')
                survivor_name = xml.get('survivor')
                defunct = next((hotel for hotel in hotels if hotel.name == defunct_name),None)
                survivor = next((hotel for hotel in hotels if hotel.name == survivor_name),None)
                move = self.brain.QueryMergeStock(map, me, hotels, players, survivor, defunct)
                reply = ET.Element('reply', {'cmd': name, 'msg-id': msgid})

                if move is not None:
                    reply.set( "keep",  str(move.Keep))
                    reply.set( "sell",  str(move.Sell))
                    reply.set( "trade", str(move.Trade))

            elif name == 'setup':
                self.brain.Setup(map, me, hotels, players)
                reply = ET.Element('ready')

            elif name == 'exit':
                print("Received exit message")
                sys.exit(0)
            else:
                printrap("ERROR: bad message (XML) from server - root node %r" % name)
            self.send_xml(reply)
            turnTime = time.clock() - startTime
            prefix = '' if turnTime < 0.8 else "WARNING - "
            print(prefix + "turn took %r seconds" % turnTime)#Enable this to see turn speed
        except Exception as e:
            traceback.print_exc()
            printrap("Error on incoming message.  Exception: %r" % e)

    def connectionLost(self, exception):
        print("Lost our connection! Exception: %r" % exception)
        client = self.client

        delay = .5
        while True:
            try:
                if client is not None:
                    client.close()
                client = self.client = tcpClient.TcpClient(self.ipAddress, self)
                client.start()

                self._connectToServer()
                print("Re-connected")
                return
            except Exception as e:
                print("Re-connection failed! Exception: %r" % e) # fix this
                time.sleep(delay)
                delay += .5

    def _connectToServer(self):
        root = ET.Element('join', {'name': self.brain.name,
                                   'school': myPlayerBrain.SCHOOL,
                                   'language': "Python"})
        avatar = self.brain.avatar
        if avatar is not None:
            av_el = ET.Element('avatar')
            av_el.text = base64.b64encode(avatar)
            root.append(av_el)
        self.client.sendMessage(ET.tostring(root))


if __name__ == '__main__':
    printrap(sys.argv[0], breakOn=not sys.argv[0].endswith("framework.py"))
    framework = Framework(sys.argv[1:])
    framework._run()
