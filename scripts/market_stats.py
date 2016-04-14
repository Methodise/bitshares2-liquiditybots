from grapheneapi import GrapheneAPI, GrapheneWebsocketRPC
from functools import reduce
from grapheneexchange import GrapheneExchange
import numpy as np
import json
import track_bot
import time
import graphing
import collections


dump_to_json = False
rpc = GrapheneWebsocketRPC("wss://bitshares.openledger.info/ws", "", "")
bots = [bot for bot in track_bot.bots]
markets = [
    ("CAD", "BTS"),
    ("EUR", "BTS"),
    ("SILVER", "BTS"),
]


get_asset_symbol = lambda asset_data: asset_data['symbol']
get_asset_id = lambda asset_data: asset_data['id']
get_all_of_op = lambda account_history, op: [operation['op'][1] for operation in account_history if operation['op'][0] == op]
        
   
def get_volume_at_spread_percentage(order_book, asset_data, bot_ids, percentage):
    settlement_price = get_exchange_rate(asset_data[0])
    bids = [order for order in order_book if order['sell_price']['base']['asset_id'] == '1.3.0']
    asks = [order for order in order_book if order['sell_price']['quote']['asset_id'] == '1.3.0']
    
    for order in bids:
        bts_amount = order['sell_price']['base']['amount']
        other_amount = order['sell_price']['quote']['amount']
        order['price'] = calculate_price(asset_data, bts_amount, other_amount)
        
    for order in asks:
        bts_amount = order['sell_price']['quote']['amount']
        other_amount = order['sell_price']['base']['amount']
        order['price'] = calculate_price(asset_data, bts_amount, other_amount)
        
    bids_at_percentage = [bid for bid in bids if (float(bid['price'])/settlement_price)*100 >= 100 - percentage]
    asks_at_percentage = [ask for ask in asks if (float(ask['price'])/settlement_price)*100 <= 100 + percentage]
    
    bids_volume_list = [float(bid['sell_price']['base']['amount']) / 10 ** 5 for bid in bids_at_percentage]
    asks_volume_list = [float(ask['sell_price']['quote']['amount']) / 10 ** 5 for ask in asks_at_percentage]
    bots_bids_volume_list = [float(bid['sell_price']['base']['amount']) / 10 ** 5 for bid in bids_at_percentage if bid['seller'] in bot_ids]
    bots_asks_volume_list = [float(ask['sell_price']['quote']['amount']) / 10 ** 5 for ask in asks_at_percentage if ask['seller'] in bot_ids]
    
    return (get_total_volume(bids_volume_list), get_total_volume(asks_volume_list), get_total_volume(bots_bids_volume_list), get_total_volume(bots_asks_volume_list))


def get_spread_percentages(order_book, asset_data):
    settlement_price = get_exchange_rate(asset_data[0])
    bids = [order for order in order_book if order['sell_price']['base']['asset_id'] == '1.3.0']
    asks = [order for order in order_book if order['sell_price']['quote']['asset_id'] == '1.3.0']
    
    for order in bids:
        bts_amount = order['sell_price']['base']['amount']
        other_amount = order['sell_price']['quote']['amount']
        order['price'] = calculate_price(asset_data, bts_amount, other_amount)
        order['spread'] = (float(order['price'])/settlement_price)*100  - 100
        order['volume'] = float(order['sell_price']['base']['amount']) / 10 ** 5
        
    for order in asks:
        bts_amount = order['sell_price']['quote']['amount']
        other_amount = order['sell_price']['base']['amount']
        order['price'] = calculate_price(asset_data, bts_amount, other_amount)
        order['spread'] = (float(order['price'])/settlement_price)*100 - 100
        order['volume'] = float(order['sell_price']['quote']['amount']) / 10 ** 5
        
    return(bids, asks)

    
def get_total_volume(volume_list):
    total_volume = reduce(lambda a,b: a + b, volume_list) if len(volume_list) != 0 else 0
    return total_volume
    
    
def calculate_price(asset_data, bts_amount, other_amount):
    other = float(other_amount) / 10 ** asset_data[0]['precision']
    bts = float(bts_amount) / 10 ** asset_data[1]['precision']
    return bts / other
    
    
def get_exchange_rate(asset_data, in_asset=False, rpc=rpc):
    bitasset_data = rpc.get_objects([asset_data['bitasset_data_id']])
    base = bitasset_data[0]['current_feed']['settlement_price']['base']['amount'] / 10 ** asset_data['precision']
    quote = bitasset_data[0]['current_feed']['settlement_price']['quote']['amount'] / 10 ** 5 # assuming BTS
    price = base / quote if in_asset else quote / base
    return price


def orders_to_graph_data(orders):
    bot, other  = collections.OrderedDict(), collections.OrderedDict()
    order_data = collections.OrderedDict()
    for list_position, order in enumerate(orders):
        volume_list_bot = [order['volume'] for order in orders[0:list_position+1] if order['seller'] in bot_ids]
        volume_list_other = [order['volume'] for order in orders[0:list_position+1]]
        if order['seller'] in bot_ids:
            bot[order['spread']] = reduce(lambda a,b: a + b, volume_list_bot, 0)
        other[order['spread']] = reduce(lambda a,b: a + b, volume_list_other, 0)
        bot_total = reduce(lambda a,b: a + b, [bot[e] for e in bot], 0)
        other_total = reduce(lambda a,b: a + b, [other[e] for e in other], 0)
        order_data[order['spread']] = (other_total, bot_total)
    return order_data    
    
    
def print_volume_data(volume_data):
    for market, market_volume_data in volume_data.items():
        print("")
        print("%s : %s" % (market[0], market[1]))
        for volume_percentage, volume in market_volume_data.items(): 
            print(volume_percentage, 
                "|",
                ("Bids: %.2f" % volume[0]).ljust(15), 
                ("/ Bots: %.2f" % volume[2]).ljust(15),
                ("/ %%: %.2f" % (0 if volume[2] == 0 else 100 * volume[2]/volume[0])).ljust(10),
                ("| Asks: %.2f" % volume[1]).ljust(17),
                ("/ Bots: %.2f" % volume[3]).ljust(15),
                ("/ %%: %.2f" % (0 if volume[3] == 0 else 100 * volume[3]/volume[1])).ljust(10),
            )
     
        
if __name__ == "__main__":
    bot_ids = []
    for bot in bots:
        bot_ids.append(rpc.get_account(bot)['id'])

    for market in markets:
        asset_data = (rpc.get_asset(market[0]), rpc.get_asset(market[1]))
        order_book = rpc.get_limit_orders(asset_data[0]['id'], asset_data[1]['id'], 150)
        bids, asks = get_spread_percentages(order_book, asset_data)
        bids_s = sorted(bids, key=lambda k: k['spread'], reverse=True)
        asks_s = sorted(asks, key=lambda k: k['spread'])
        
        graph_data = {}
        graph_data['bids'] = orders_to_graph_data(bids_s)
        graph_data['asks'] = orders_to_graph_data(asks_s)
        graphing.graph_market_stats_v2(graph_data, market, './graphing/market_graph_%s_%s_%s' % (market[0], market[1], time.strftime("%Y-%m-%d_%H-%M-%S")))


    if dump_to_json:
        with open('./json/market_stats_%s.json' % time.strftime("%Y-%m-%d_%H-%M-%S"), 'w') as outfile:
            volume_data_json = {}
            for market in volume_data:
                volume_data_json[market[0] + " - " + market[1]] = volume_data[market]
            json.dump(volume_data_json, outfile)
