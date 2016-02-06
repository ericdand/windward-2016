class GameMap(object):
    def __init__(self, x=0, y=0, element=None, hotelChains=None):
        self.height = y
        self.width = x
        self.tiles = matrix = [[MapTile(MapTile.UNDEVELOPED)] * self.height for i in range(self.width)]
        if element is not None:
            self.fromXml(element, hotelChains)

    def fromXml(self, element, hotelChains=None):
        self.height = int(element.attrib.get('height'))
        self.width = int(element.attrib.get('width'))
        self.tiles = []
        for column in element.iter("column"):
            string = column.text
            self.tiles.append([MapTile(tile.split(":")[0], get_hotel_name(hotelChains, tile.split(":")[1])) for tile in string.split(';') if tile is not ''])



    def is_tile_undeveloped(self, tile):
        return tile.type == MapTile.UNDEVELOPED

    def is_tile_unplayable(self, tile):
        return tile.type is not MapTile.UNDEVELOPED and tile.type is MapTile.UNPLAYABLE_NO_AVAIL_CHAINS

    def __str__(self):
        return "{}*{} map".format(self.width, self.height)

def get_hotel_name(hotelChains, name):
    if hotelChains == None:
        return None
    return next((a for a in hotelChains if a.name == name), None)


class HotelChain(object):
    def __init__(self, element):
        if element is None:
            print "Error, HotelChain element is none"
        self.name = element.get('name')
        self.start_price = int(element.get('start-price'))
        self.num_tiles = int(element.get('num-tiles'))
        self.is_active = bool(element.get('is-active').lower() == "true")
        self.is_safe = bool(element.get('is-safe').lower() == "true")
        if element.find('owners') is not None:
            self.owners = [StockOwner(owner.get('guid'), owner.get('num-shares')) for owner in element.find('owners')]
        if element.find('first-majority') is not None:
            self.first_majority_owners = [StockOwner(owner.get('guid'), owner.get('num-shares')) for owner in
                                          element.find('first-majority')]
        if element.find('second-majority') is not None:
            self.second_majority_owners = [StockOwner(owner.get('guid'), owner.get('num-shares')) for owner in
                                           element.find('second-majority')]
        self.stock_price = int(element.get('stock-price'))
        self.first_majority_bonus = int(element.get('first-majority'))
        self.second_majority_bonus = int(element.get('second-majority'))
        self.num_available_shares = int(element.get('num-avail-shares'))


    def __str__(self):
        return "HotelChain {}".format(self.name)


class HotelStock(object):
    def __init__(self, chain, num_shares):
        self.chain = chain
        self.num_shares = num_shares

    def __str__(self):
        return "Stock for chain {} has {} shares".format(self.chain, self.num_shares)


class MapTile(object):
    UNDEVELOPED = '1'
    HOTEL = '2'
    SINGLE = '3'
    UNPLAYABLE_MERGE_SAFE = '4'
    UNPLAYABLE_NO_AVAIL_CHAINS = '5'

    def __init__(self, type, hotel=None, element=None):
        self.hotel = hotel
        self.type = type
        if type is None and hotel is None:
            self.type = MapTile.UNDEVELOPED

    def __str__(self):
        return "Hotel {}, Tile: {}".format(self.hotel, self.type)


class Player(object):
    def __init__(self, element):
        if element is not None:
            self.cash = int(element.get('cash'))
            self.guid = element.get('guid')
            self.name = element.get('name')
            self.score = int(element.get('score'))
            self.stock = []
            #print ElementTree.tostring(element,encoding='utf8', method='xml')
            if element.find('tiles') is not None:
                self.tiles = [PlayerTile(elementString=tile) for tile in element.find('tiles').text.split(';') if
                              tile is not None and tile is not '']
            if element.find('powers') is not None:
                self.powers = [SpecialPowers(int(power)) for power in element.find('powers').text.split(';') if
                               power is not '']
            if element.find('scoreboard') is not None:
                self.scoreboard = [score for score in element.find('scoreboard').text.split(';')]
            if element.find('stock') is not None:
                for stock in element.find('stock').text.split(';'):
                    if stock is not '':
                        hotel_stock = HotelStock(stock.split(':')[0], int(stock.split(':')[1]))
                        self.stock.append(hotel_stock)
def __str__(self):
    return "Player {}:   Score - {}".format(self.name, self.score)


class PlayerTile(object):
    def __init__(self, x=0, y=0, elementString=None):
        if elementString is None:
            self.x = x
            self.y = y
        else:
            self.x = int(elementString.split(':')[0])
            self.y = int(elementString.split(':')[1])

    def __str__(self):
        return "PlayerTile at ({},{})".format(self.x, self.y)


class SpecialPowers(object):
    FREE_3_STOCK = '1'
    BUY_5_STOCK = '2'
    TRADE_2_STOCK = '3'
    DRAW_5_TILES = '4'
    PLACE_4_TILES = '5'
    NONE = '0'

    def __init__(self, card):
        self.card = card

    def __str__(self):
        return "Power {}".format(self.card)


class StockOwner(object):
    def __init__(self, owner, num_shares) 
        self.num_shares = num_shares
        self.owner = owner

    def __str__(self):
        return "Owner {} has {} shares".format(self.owner, self.num_shares)
		