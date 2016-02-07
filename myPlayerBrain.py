import random as rand
import api.units as lib
from api.units import SpecialPowers
from api.units import MapTile

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
        self.stage = 0
        self.created_hotel_this_turn = False

    def Setup(self, map, me, hotelChains, players):
        pass #any setup code...

    def QuerySpecialPowersBeforeTurn(self, map, me, hotelChains, players):
        # Count number of tiles to determine which "stage" of the game we're in.
        count = 0
        for row in map.tiles:
            for t in row:
                if t.type == MapTile.HOTEL or t.type == MapTile.SINGLE:
                    count += 1
        new_stage = 2 if count > 50 else 1
        if self.stage != new_stage:
            print("{0} tiles placed. Stage advanced to stage {1}.".format(count, new_stage))
            print("Cash on hand: {0}. Stocks: {1}.".format(me.cash, me.stock))
            self.stage = new_stage

        # if rand.randint(0, 29) == 1:
        #     return SpecialPowers.DRAW_5_TILES
        # if rand.randint(0, 29) == 1:
        #     return SpecialPowers.PLACE_4_TILES
        return SpecialPowers.NONE

    def get_adj_tiles(self, map, tile):
        tiles = []
        x = tile.x
        y = tile.y
        if (x > 0):
            tiles.append(map.tiles[x - 1][y])
        if (x < map.width - 1):
            tiles.append(map.tiles[x + 1][y])
        if (y > 0):
            tiles.append(map.tiles[x][y - 1])
        if (y < map.height - 1):
            tiles.append(map.tiles[x][y + 1])
        return tiles

    def check_merge(self, map, tile):
        hotels = set()

        for tile in self.get_adj_tiles(map, tile):
            if tile.type == MapTile.HOTEL:
                hotels.add(tile.hotel)

        return hotels

    def choose_most_appropriate_tile(self, map, me, hotelChains, players):
        blacklist = []
        for t in me.tiles:
            # If a placement would cause a merge, see if it's a good idea for us.
            hotels = self.check_merge(map, t)
            if len(hotels) > 0:
                # See whether we own any stock in either of the hotels.
                # If we own stock in the smaller one, we want that shareholder bonus!
                largest = None
                smallest = None
                # TODO: Handle multi-chain merges.
                for h in hotels:
                    if largest == None or h.num_tiles > largest.num_tiles: largest = h
                    if smallest == None or h.num_tiles < smallest.num_tiles: smallest = h
                # If we are the majority shareholder of the smaller chain, do the merge.
                for o in smallest.first_majority_owners + smallest.second_majority_owners:
                    if o.owner == me.guid:
                        return t
                    else:
                        print("Blacklisted tile {0}.".format(t))
                        blacklist.append(t)
                        continue

            # Check around the tile to try to find adjacent singles.
            if [adj for adj in self.get_adj_tiles(map, t) if adj.type == MapTile.SINGLE]:
                # If there are no available hotels to be made, then it is illegal to place this tile.
                inactive_hotel = next((hotel for hotel in hotelChains if not hotel.is_active), None)
                if inactive_hotel is None:
                    blacklist.append(t)
                    continue
                print('Created "two-bomb" (new hotel) at ({0}, {1}).'.format(t.x, t.y))
                self.created_hotel_this_turn = True
                return t

            # If there are two adjacent tiles in our hand, play one of them.
            for o in me.tiles:
                if abs(t.x - o.x) <= 1 and abs(t.y - o.y) <= 1 and o is not t:
                    return t

        acceptable_tiles = [t for t in me.tiles if t not in blacklist]
        if len(acceptable_tiles) > 0:
            return random_element(acceptable_tiles)
        return random_element(me.tiles)

    def QueryTileOnly(self, map, me, hotelChains, players):
        tile = self.choose_most_appropriate_tile(map, me, hotelChains, players)
        createdHotel = next((hotel for hotel in hotelChains if not hotel.is_active), None)
        mergeSurvivor = next((hotel for hotel in hotelChains if hotel.is_active), None)
        return PlayerPlayTile(tile, createdHotel, mergeSurvivor)

    def QueryTileAndPurchase(self, map, me, hotelChains, players):
        tile = self.choose_most_appropriate_tile(map, me, hotelChains, players)
        inactive = None
        if self.created_hotel_this_turn:
            inactive = next((hotel for hotel in hotelChains if not hotel.is_active), None)
            if inactive is None:
                print("ERROR: No inactive hotel chains!")
        turn = PlayerTurn(tile=tile, created_hotel=inactive, merge_survivor=inactive)
        if self.created_hotel_this_turn:
            # If we created a hotel this turn, then we want to buy another stock in it immediately.
            turn.Buy.append(lib.HotelStock(inactive, 1))
            self.created_hotel_this_turn = False
        # turn.Buy.append(lib.HotelStock(random_element(hotelChains), rand.randint(1, 3)))
        # turn.Buy.append(lib.HotelStock(random_element(hotelChains), rand.randint(1, 3)))

        return turn
        # if rand.randint(0, 20) is not 1:
        #     return turn
        # temp_rand = rand.randint(0, 2)
        # if temp_rand is 0:
        #     turn.Card = SpecialPowers.BUY_5_STOCK
        #     turn.Buy.append(lib.HotelStock(random_element(hotelChains), 3))
        #     return turn
        # elif temp_rand is 1:
        #     turn.Card = SpecialPowers.FREE_3_STOCK
        #     return turn
        # else:
        #     if (len(me.stock) > 0):
        #         turn.Card = SpecialPowers.TRADE_2_STOCK
        #         turn.Trade.append(TradeStock(random_element(me.stock).chain, random_element(hotelChains)))
        #         return turn

    def QueryMergeStock(self, map, me, hotelChains, players, survivor, defunct):
        myStock = next((stock for stock in me.stock if stock.chain == defunct.name), None)
        num = myStock.num_shares
        buy = 0
        if self.stage == 1:
            trade = myStock.num_shares / 2
            sell = num - trade
        else:
            # if maj num shares < 13, trade
            # else if can reach min by trading, trade
            # else sell
            if survivor.first_majority_owners[0].num_shares < 13:
                trade = myStock.num_shares / 2
                sell = num - trade
            else:
                second_maj = survivor.second_majority_owners[0].num_shares
                if num + (myStock.num_shares / 2) >= second_maj:
                    trade = myStock.num_shares / 2
                    sell = num - trade
                else:
                    trade = 0
                    sell = num
        return PlayerMerge(sell, buy, trade)

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
