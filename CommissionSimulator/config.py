"""
config = {
    time: days to simulate
    drop_rate: urgent commissions appear in 1 minute averagely. (0,03 recommended for 2-4, and 0.05 for A3)
    farm_time: how many hours you will farm in 2-4(or A3) per day.
    oil_resume_rate: how muc oil is resumed per minute. (1.6 for full upgraded)
    oil_get_per_week: how muc oil is get per week. (and also count events as spread in this in average, as well as count
    OperationSiren cost such as 10000/week)(12660 for not buying the Opsi action points, add 1400 for monthly pass，add
                                            553.8 for season pass, add 1638 for mail, minus 10000 for Opsi action points)
}
"""

config = {
    'time': 1000,
    'drop_rate': 0.03,
    'farm_time': 12,
    'use_oil_limitation': True,
    'oil_resume_rate': 1.6,
    'oil_get_per_week': 2660,
    'oil_used_per_round': 22,
    'minute_per_round': 3,
    'commission_per_round': 0.1,
    'print_commission_done': False,
    'print_filter': False
}

Value = {
    "Oil" : 1,
    "Chip" : 87.10801394,
    "Coin" : 0.132100396,
    "Cube" : 265.28,
    "Gem" : 100,
    "Book" : 0,
    "Decor_coin" : 0,
    "Retro" : 0,
    "Box" : 0,
    "Drill" : 0,
    "Plate" : 0,
}

if __name__ == '__main__':
    from simulator import CommissionSimulator
    CS = CommissionSimulator()
    CS.run()