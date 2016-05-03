# Faucet used for the registration of the bot's account on the blockchain
faucet = "https://bitshares.openledger.info/"

# Referrer used for the faucet registration
referrer = "bitshares-munich"


# Xeroc's bot config
# Wallet RPC connection details
wallet_host = "cli-wallet"
wallet_port = 8092
wallet_user = ""
wallet_password = "reallyhardpasswordbecuasemultipleenglishwordbutnotspelcorrectlyevenbetterer"

# Your account that executes the trades
account = "liquidity-bot-mauritso"  # prefix liquidity-bot-

# Websocket URL
witness_url = "wss://bitshares.openledger.info/ws"

# Set of ALL markets that you inted to serve
watch_markets = [
    "EUR : BTS",
    "CAD : BTS",
    "SILVER : BTS"
]
market_separator = " : "  # separator between assets


# If this flag is set to True, nothing will be done really
safe_mode = False


# Load the strategies
from strategies.liquidity_wall import LiquiditySellBuyWalls
from strategies.maintain_collateral_ratio import MaintainCollateralRatio
# Each bot has its individual name and carries the strategy and settings
bots = {}

bots["LiquidityWall"] = {
    "symmetric_sides" : False,
    "bot": LiquiditySellBuyWalls,
    "markets": [
        "EUR : BTS",
        "CAD : BTS",
        "SILVER : BTS"
    ],
    "borrow_percentages": {
        "EUR": 12,
        "CAD": 2,
        "SILVER": 12,
        "BTS": 74
    },
    "minimum_amounts": {
        "EUR": 0.20,
        "CAD": 0.30,
        "SILVER": 0.02,
    },
    "target_price": "feed",
    "target_price_offset_percentage": 0,
    "spread_percentage": 2,
    "allowed_spread_percentage": 1,
    "volume_percentage": 70,
    "expiration": 60 * 60 * 3,
    "skip_blocks": 5,
    "ratio": 2.5,
    "minimum_change_percentage": 10,
    # Total bts calculation, only bts or the total worth of the account in bts ("bts" or "worth")
    "calculate_bts_total": "bts",
}

bots["Collateral"] = {
    "bot" : MaintainCollateralRatio,
    "markets" : ["EUR : BTS", "SILVER : BTS", "CAD : BTS"],
    "target_ratio" : 2.5,
    "lower_threshold" : 2.3,
    "upper_threshold" : 2.7,
    "skip_blocks" : 1,
}
