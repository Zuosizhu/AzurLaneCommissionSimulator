import os

source = open(file='data.csv', mode='r', encoding='utf-8')
source.readline()
if os.path.exists('data.py'):
    os.remove('data.py')
py = open(file='data.py', mode='x', encoding='utf-8')
py.write('''"""
This file is created by data_extractor.py. Manually editing this file is not recommended.
"""\n''')


py.write("""

daily_commissions = []
extra_commissions = []
major_commissions = []
urgent_commissions = []
night_commissions = []


""")


daily_commission = []
extra_commission = []
major_commission = []
urgent_commission = []
night_commission = []

while True:
    line = source.readline()
    dataline = line.split(',')
    if line == '':
        break
    for _ in range(18):
        if dataline[_] == '' or dataline[_] == '\n':
            dataline[_] = 0
    (num, code, name, time, oil_consumed, oil_gain, chip, coin, cube, gem, book, decor_coin, retro, box, drill, plate,
     rate, time_limit) = dataline
    time = round(float(time) * 6)*10
    rate = float(rate)
    time_limit = round(float(time_limit) * 6)*10
    output_suffix = '}]\n'
    output_data = \
        f"""
    'num': {num},
    'code': '{code}',
    'name': '{name}',
    'time': {time},
    'time_limit': {time_limit},
    'oil': {-float(oil_consumed) + float(oil_gain)},
    'chip': {float(chip)},
    'coin': {float(coin)},
    'cube': {float(cube)},
    'gem': {float(gem)},
    'book': {float(book)},
    'decor_coin': {float(decor_coin)},
    'retro': {float(retro)},
    'box': {float(box)},
    'drill': {float(drill)},
    'plate': {float(plate)},
    'rate': {rate},
"""
    output_prefix = ''
    if 'Daily' in code:
        daily_commission += [num]
        output_prefix = 'daily_commissions += [{'
        output_data += "    'type': 'Daily',\n"
    if 'Extra' in code:
        extra_commission += [num]
        output_prefix = 'extra_commissions += [{'
        output_data += "    'type': 'Extra',\n"
    if 'Major' in code:
        major_commission += [num]
        output_prefix = 'major_commissions += [{'
        output_data += "    'type': 'Major',\n"
    if 'Urgent' in code or 'Gem' in code or 'Ship' in code:
        urgent_commission += [num]
        output_prefix = 'urgent_commissions += [{'
        output_data += "    'type': 'Urgent',\n"
    if 'Night' in code:
        night_commission += [num]
        output_prefix = 'night_commissions += [{'
        output_data += "    'type': 'Night',\n"
    output = output_prefix + output_data + output_suffix
    py.write(output)
py.write(f"""daily_commission_count = {len(daily_commission)}
extra_commission_count = {len(extra_commission)}
major_commission_count = {len(major_commission)}
urgent_commission_count = {len(urgent_commission)}
night_commission_count = {len(night_commission)}
""")
py.close()
source.close()
