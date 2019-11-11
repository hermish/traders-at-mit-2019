def strategy(prices, my_info, auction_info = None):
    """
    Determines the trades you want to execute at a particular time step
    and keeps track of any additional information.

    Inputs:
    - prices, a tuple of prices of products in their respective currencies
    at this timestep.
    - my_info, information you would like to save and pass at each timestep.
    This can have any reasonable format you want. At time 0, it is None.
    - auction_info, a tuple indicating direction of currency move. If
    you do not win the auction, it is None.

    Outputs:
    - quantities, a tuple of length 7 indicating the quantity of each
    product you would like to trade in the format given in the PDF.
    - save_info, information you pass to the next time step.
    """
    # Unpack Prices & Information
    p1, p2, p3, pE, A_USD, B_USD, A_B = prices
    
    if my_info is None:
        positions = {'s1': 0, 's2': 0, 's3':0, 'E':0, 'A':0, 'B':0}
        other = None # UPDATE
    else:
        positions, other = my_info

    # Choose Trades
    q1, q2, q3, qE, qA, qB, qA_B = 0, 0, 0, 0, 0, 0, 0

    ## Arbitrage
    DOLLARS_A = 100000
    if A_USD  < A_B * B_USD:
        qA += DOLLARS_A
        qB -= (DOLLARS_A / A_USD) * A_B * B_USD
        qA_B -= (DOLLARS_A / A_USD) * A_B
    if  A_USD  > A_B * B_USD:
        qA -= DOLLARS_A
        qB += (DOLLARS_A / A_USD) * A_B * B_USD
        qA_B += (DOLLARS_A / A_USD) * A_B

    #fin
    numE = 0
    E = 0.20894491*p1*A_USD + 2.38349261*p2*B_USD +  1.31707919*p3
    if E - pE > 5:
        qE+=numE
    if E - pE < -5 :
        qE-=numE


        
    # Assert Limits
    dollars_traded = abs(q1 * p1 * A_USD) + \
                     abs(q2 * p2 * B_USD) + \
                     abs(q3 * p3) + \
                     abs(qE * pE) + \
                     abs(qA) + \
                     abs(qB) + \
                     abs(qA_B * B_USD)
    while dollars_traded
    if dollars_traded > 1e6:
        pass
    assert dollars_traded <= 1e6


    # Pack Information
    quantities = q1, q2, q3, qE, qA, qB, qA_B
    positions['s1'] += quantities[0]
    positions['s2'] += quantities[1]
    positions['s3'] += quantities[2]
    positions['E'] += quantities[3]
    positions['A'] += ((quantities[4] / A_USD) + (quantities[6] / A_B))
    positions['B'] += ((quantities[5] / B_USD) - (quantities[6]))
    
    other = None # UPDATE
    save_info = positions, other
    return quantities, save_info
