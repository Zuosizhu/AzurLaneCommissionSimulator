"""
Battle-based Commission Simulator Configuration

Parameters:
    TIME: Days to simulate
    OIL_RESUME_RATE: Oil resumed per minute (1.6 for full upgraded)
    OIL_GET_PER_WEEK: Oil received per week
    OIL_OTHER_PER_DAY: Oil used for other activities per day (e.g., hard mode)
    EVENT_PAUSE_INTERVAL: Days between each event pause
    EVENT_PAUSE_DURATION: Days each event pause lasts
    ELITE_COUNT: Number of elite enemies (1-3 typical)
    BATTLE_COUNT: Total battles in one map run (6-12 typical)
    BOSS_COUNT: Number of boss battles (1 typical)
    BATTLE_TIME: Time per battle in minutes (3 typical)
    MAP_COST_OIL: Oil cost to enter a map (10 typical)
    BATTLE_COST_OIL: Oil cost per battle (3 typical)
    BOSS_COST_OIL: Oil cost per boss battle (5 typical)
    MAP_DROP_RATE: Drop rate when entering map (0.005 main, 0.0025 event)
    ELITE_DROP_RATE: Drop rate for elite battles (0.03-0.08)
    NORMAL_DROP_RATE: Drop rate for normal battles (0.03-0.075)
    BOSS_DROP_RATE: Drop rate for boss battles (0.075)
"""

config = {
    'TIME': 3650,
    'OIL_RESUME_RATE': 1.6,
    'OIL_GET_PER_WEEK': 2660,
    'OIL_OTHER_PER_DAY': 200,
    'EVENT_PAUSE_INTERVAL': 60,
    'EVENT_PAUSE_DURATION': 8,
    'ELITE_COUNT': 0,
    'BATTLE_COUNT': 5,
    'BOSS_COUNT': 1,
    'BATTLE_TIME': 0.02,
    'MAP_COST_OIL': 10,
    'BATTLE_COST_OIL': 3,
    'BOSS_COST_OIL': 3,
    'ELITE_DROP_RATE': 0.05,
    'NORMAL_DROP_RATE': 0.05,
    'BOSS_DROP_RATE': 0.075,
    'MAP_DROP_RATE': 0.005,
    'PRINT_COMMISSION_DONE': False,
    'PRINT_FILTER': False,
}

"""
Resource Value Configuration
Balanced settings for resource valuation
"""

Value = {
    "Oil": 1,
    "Chip": 87.10801394,
    "Coin": 0.132100396,
    "Cube": 265.28,
    "Gem": 100,
    "Book": 0,
    "Decor_coin": 0,
    "Retro": 0,
    "Box": 0,
    "Drill": 0,
    "Plate": 0,
}

# Yes, you can run simulator here in IDE, as it seems ridiculous in a config file. BUT I LOVE IT!!!
if __name__ == '__main__':
    from simulator import CommissionSimulator

    CS = CommissionSimulator()
    CS.run()