import numpy as np
import os
import csv

WON_AUCTION = False
DATA_NAME = 'data.csv'
FILE_NAME = 'submission'

def evaluate(strategy, prices, won_auction = False):
    """
    Inputs:
    -   strategy, a function.
    -   prices, a python list of lists, where each sub-list contains
        the seven prices as well as auction information.
    -   won_auction, a boolean.
    Outputs:
    -   score, a float.
    """
    passed_info = None
    assets = ["S1", "S2", "S3", "ETF", "A", "B", "USD"]
    current_pos = {a: 0 for a in assets}

    # iterate through the data
    for index, time_step in enumerate(prices[:-1]):
        input_tuple = tuple(time_step[:7])
        if won_auction:
            ratio1 = (prices[index + 1][4] / prices[index][4])
            ratio2 = (prices[index + 1][5] / prices[index][5])
            auction_info = determine_auction_info(ratio1, ratio2)
        else:
            auction_info = None
        trades, passed_info = strategy(input_tuple, passed_info, auction_info)

        if enforce_trade_limit(trades, input_tuple):
            change_pos(current_pos, trades, input_tuple)
        enforce_pos_limit(current_pos, input_tuple)

    # convert all assets to USD at the end
    final_step = tuple(prices[-1][:7])
    enforce_pos_limit(current_pos, final_step, True)
    return current_pos["USD"]


def determine_auction_info(ratio1, ratio2):
    """
    Determines auction_info.

    Inputs:
    - ratio1, ratio2 floats that determine the ratio

    Outputs:
    - (v1, v2) a tuple with each value being in {-1, 0, 1}
    """
    if ratio1 >= 1.02:
        v1 = 1
    elif ratio1 <= 0.98:
        v1 = -1
    else:
        v1 = 0

    if ratio2 >= 1.02:
        v2 = 1
    elif ratio2 <= 0.98:
        v2 = -1
    else:
        v2 = 0

    return (v1, v2)


def enforce_trade_limit(trades, vals):
    """
    Checks whether the value of all trades at each time step
    is under 1e6.

    Inputs:
    - trades, a tuple of the trades that the participant wishes to execute.
    - vals, a tuple of the values of the assets at this time step.

    Outputs:
    - boolean, indicating whether it is a valid set of trades.
    """
    trade_val = abs(trades[0] * vals[0] * vals[4]) + \
                abs(trades[1] * vals[1] * vals[5]) + \
                abs(trades[2] * vals[2]) + \
                abs(trades[3] * vals[3]) + \
                abs(trades[4]) + \
                abs(trades[5]) + \
                abs(trades[6] * vals[5])
    return (trade_val <= 1e6)


def change_pos(current_pos, trades, vals):
    """
    Given the current positions and trades, updates the current position
    to reflect those trades.

    Inputs:
    - current_pos, a dictionary containing the positions of each asset.
    - trades, a tuple of the trades that the participant wishes to execute.
    - vals, a tuple of the values of the assets at this time step.

    Outputs:
    - No output. Modifies current_pos dictionary.
    """
    current_pos["S1"] += trades[0]
    current_pos["S2"] += trades[1]
    current_pos["S3"] += trades[2]
    current_pos["ETF"] += trades[3]

    current_pos["USD"] += (-trades[2] * vals[2] - \
                        (trades[3] * vals[3]) - \
                        trades[4] - \
                        trades[5] - \
                        trades[0] * vals[0] * vals[4] - \
                        trades[1] * vals[1] * vals[5])

    current_pos["A"] += ((trades[4] / vals[4]) + (trades[6] / vals[6]))
    current_pos["B"] += ((trades[5] / vals[5]) - (trades[6]))


def enforce_pos_limit(current_pos, vals, end = False):
    """
    Given a dictionary of current positions, and the asset prices,
    ensures that the position of each asset is in the range (-1e7, 1e7).
    Can also be used at the end to turn all assets into USD.

    Inputs:
    - current_pos, a dictionary containing the positions of each asset.
    - vals, a tuple of the values of the assets at this time step.
    - end, a boolean that indicates whether all assets should be converted
        into USD.

    Outputs:
    - No output. Modifies current_pos dictionary.
    """
    s1_usd = current_pos["S1"] * vals[0] * vals[4]
    s2_usd = current_pos["S2"] * vals[1] * vals[5]
    s3_usd = current_pos["S3"] * vals[2]
    etf_usd = current_pos["ETF"] * vals[3]
    a_usd = current_pos["A"] * vals[4]
    b_usd = current_pos["B"] * vals[5]

    usd_pos = np.array([s1_usd, s2_usd, s3_usd, etf_usd, a_usd, b_usd])
    if end: # if end, want no positions except USD
        f = lambda x: 0
    else:
        f = lambda x: min(1e7, max(-1e7, x))
    allowed_usd_pos = np.vectorize(f)(usd_pos)
    delta_pos = usd_pos - allowed_usd_pos

    if end: # liquidation penalty not at the end.
        current_pos["USD"] += sum(delta_pos)
    else:
        for i in range(6):
            if delta_pos[i] > 0:
                coeff = 0.97
            else:
                coeff = 1.03
            current_pos["USD"] += delta_pos[i] * coeff

    current_pos["S1"] = allowed_usd_pos[0] / (vals[0] * vals[4])
    current_pos["S2"] = allowed_usd_pos[1] / (vals[1] * vals[5])
    current_pos["S3"] = allowed_usd_pos[2] / vals[2]
    current_pos["ETF"] = allowed_usd_pos[3] / vals[3]
    current_pos["A"] = allowed_usd_pos[4] / vals[4]
    current_pos["B"] = allowed_usd_pos[5] / vals[5]


if __name__ == "__main__":
    with open(DATA_NAME) as csvfile:
        rows = csv.reader(csvfile)
        res = list(rows)
        prices = [[float(i) for i in r[1:]] for r in res[1:]]

    module = __import__(FILE_NAME)
    score = evaluate(module.strategy, prices, WON_AUCTION)

    print(score)
