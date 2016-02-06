import random as rand
import api.units as lib
from api.units import SpecialPowers

NAME = "Wintermute"
SCHOOL = "University of Victoria"


def random_element(list):
    if len(list) < 1:
        print "random element from empty list? returning None..."
        return None
    return list[rand.randint(0, len(list) - 1)]


class MyPlayerBrain(object):
    """The Python AI class."""

    def __init__(self):
        self.name = NAME
        self.school = SCHOOL
        #The player's avatar (looks in the same directory that this module is in).
        #Must be a 32 x 32 PNG file.
        try:
            avatar = open("MyAvatar.png", "rb")
            avatar_str = b''
            for line in avatar:
                avatar_str += line
            avatar = avatar_str
        except IOError:
            avatar = None # avatar is optional
        self.avatar = avatar

    def Setup(self, map, me, hotelChains, players):
        pass #any setup code...

    def QuerySpecialPowersBeforeTurn(self, map, me, hotelChains, players):
        # if rand.randint(0, 29) == 1:
        #     return SpecialPowers.DRAW_5_TILES
        # if rand.randint(0, 29) == 1:
        #     return SpecialPowers.PLACE_4_TILES
        return SpecialPowers.NONE

    def choose_most_appropriate_tile(self, map, me, hotelChains, players):
        tile = None
        for t in me.tiles:
            # If a placement would cause a merge, see if it's a good idea for us.

            # Check around the tile to try to find adjacent singles.
            if ((t.x > 0 and map.tiles[t.x - 1][t.y].type == MapTile.SINGLE)
            or (t.x < map.width - 1 and map.tiles[t.x + 1][t.y].type == MapTile.SINGLE)
            or (t.y > 0 and map.tiles[t.x][t.y - 1].type == MapTile.SINGLE)
            or (t.y < map.height - 1 and map.tiles[t.x][t.y + 1].type == MapTile.SINGLE)):
                tile = t
                break

        if tile is None:
            tile = random_element(me.tiles)
        return tile

    def QueryTileOnly(self, map, me, hotelChains, players):
        tile = choose_most_appropriate_tile(map, me, hotelChains, players)
        createdHotel = next((hotel for hotel in hotelChains if not hotel.is_active), None)
        mergeSurvivor = next((hotel for hotel in hotelChains if hotel.is_active), None)
        return PlayerPlayTile(tile, createdHotel, mergeSurvivor)

    def QueryTileAndPurchase(self, map, me, hotelChains, players):
        tile = choose_most_appropriate_tile(map, me, hotelChains, players)
        inactive = next((hotel for hotel in hotelChains if not hotel.is_active), None)
        turn = PlayerTurn(tile=tile, created_hotel=inactive, merge_survivor=inactive)
        turn.Buy.append(lib.HotelStock(random_element(hotelChains), rand.randint(1, 3)))
        turn.Buy.append(lib.HotelStock(random_element(hotelChains), rand.randint(1, 3)))

        if rand.randint(0, 20) is not 1:
            return turn
        temp_rand = rand.randint(0, 2)
        if temp_rand is 0:
            turn.Card = SpecialPowers.BUY_5_STOCK
            turn.Buy.append(lib.HotelStock(random_element(hotelChains), 3))
            return turn
        elif temp_rand is 1:
            turn.Card = SpecialPowers.FREE_3_STOCK
            return turn
        else:
            if (len(me.stock) > 0):
                turn.Card = SpecialPowers.TRADE_2_STOCK
                turn.Trade.append(TradeStock(random_element(me.stock).chain, random_element(hotelChains)))
                return turn

    def QueryMergeStock(self, map, me, hotelChains, players, survivor, defunct):
        myStock = next((stock for stock in me.stock if stock.chain == defunct.name), None)
        return PlayerMerge(myStock.num_shares / 3, myStock.num_shares / 3, (myStock.num_shares + 2) / 3)

class PlayerMerge(object):
    def __init__(self, sell, keep, trade):
        self.Sell = sell
        self.Keep = keep
        self.Trade = trade

class PlayerPlayTile(object):
    def __init__(self, tile, created_hotel, merge_survivor):
        self.Tile = tile
        self.CreatedHotel = created_hotel
        self.MergeSurvivor = merge_survivor

class PlayerTurn(PlayerPlayTile):
    def __init__(self, tile, created_hotel, merge_survivor):
        super(PlayerTurn, self).__init__(tile, created_hotel, merge_survivor)
        self.Card = lib.SpecialPowers.NONE
        self.Buy = []   # hotel stock list
        self.Trade = []    # trade stock list

class TradeStock(object):
    def __init__(self, trade_in, get):
        self.Trade = trade_in
        self.Get = get
