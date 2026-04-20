import re
from commission import RESOURCE_TAGS, HOUR
from config import Value
from data import daily_commissions, extra_commissions, major_commissions, urgent_commissions, night_commissions


CONFIG_OUTPUT_KEYS = [
    'TIME', 'OIL_RESUME_RATE', 'OIL_GET_PER_WEEK', 'OIL_OTHER_PER_DAY',
    'EVENT_PAUSE_DAYS', 'ELITE_COUNT', 'BATTLE_COUNT', 'BOSS_COUNT',
    'BATTLE_TIME', 'MAP_COST_OIL', 'BATTLE_COST_OIL', 'BOSS_COST_OIL',
    'MAP_DROP_RATE', 'ELITE_DROP_RATE', 'NORMAL_DROP_RATE', 'BOSS_DROP_RATE',
]

REQUIRED_CONFIG_KEYS = [
    'TIME', 'OIL_RESUME_RATE', 'OIL_GET_PER_WEEK', 'OIL_OTHER_PER_DAY',
    'EVENT_PAUSE_DAYS', 'BATTLE_COUNT', 'BATTLE_TIME', 'MAP_COST_OIL',
    'BATTLE_COST_OIL', 'BOSS_COST_OIL', 'ELITE_DROP_RATE',
    'NORMAL_DROP_RATE', 'BOSS_DROP_RATE', 'MAP_DROP_RATE',
]


class Reporter:
    def __init__(self, config: dict, filter_tags: list):
        self.config = config
        self.filter_tags = filter_tags

    def validate_config(self):
        for param in REQUIRED_CONFIG_KEYS:
            if param not in self.config:
                exit(f'Missing config parameter: {param}')

    def print_config(self):
        for key in CONFIG_OUTPUT_KEYS:
            print(f"{key:<20}: {self.config[key]}")

    def print_filter(self):
        if not self.config.get('PRINT_FILTER', False):
            return
        print('\nFilter:')
        tags = [t for t in self.filter_tags if t]
        item_in_one_line = 1
        print('DailyEvent >')
        for i, tag in enumerate(tags):
            if i == len(tags) - 1:
                if item_in_one_line == 1:
                    print(tag)
                else:
                    print('\n' + tag)
                break
            if item_in_one_line < 5:
                print(tag + ' > ', end='')
                item_in_one_line += 1
            else:
                print(tag + ' >')
                item_in_one_line = 1

    def print_results(self, sim):
        max_len_total = len('%.4f' % round(sim.total_income['oil'], 4))
        all_commissions = daily_commissions + extra_commissions + major_commissions + urgent_commissions + night_commissions

        if self.config.get('PRINT_COMMISSION_DONE', False):
            print('\nCommissions done:')
            for i in range(len(all_commissions)):
                if sim.commissions_done[i + 1] == 0:
                    continue
                name = all_commissions[i]['name']
                print('  ' + name + (20 - len(name) - len(re.sub(r'[a-zA-Z,-]', '', name)) // 2) * ' '
                      + ': ', sim.commissions_done[i + 1])
            max_len_done = len(str(sim.urgent_done_count + sim.daily_done_count + sim.night_done_count + sim.major_done_count))
            total_done = sim.urgent_done_count + sim.daily_done_count + sim.night_done_count + sim.major_done_count
            print(f'Total  done: {total_done}')
            print(f'Daily  done: {(max_len_done - len(str(sim.daily_done_count))) * " "}{sim.daily_done_count}')
            print(f'Night  done: {(max_len_done - len(str(sim.night_done_count))) * " "}{sim.night_done_count}')
            print(f'Urgent done: {(max_len_done - len(str(sim.urgent_done_count))) * " "}{sim.urgent_done_count}')
            if sim.major_done_count:
                print(f'Major done:{sim.major_done_count}')

        if len(sim.refresh_times):
            print(f"\nAverage pool refresh time (Hours): {'%.4f' % round(sum(sim.refresh_times) / len(sim.refresh_times), 4)}")
        if len(sim.last_gem_run_times):
            gem_times = [t for t in sim.last_gem_run_times if t != 0]
            if gem_times:
                print(f"Average gem run out time  (Hours):  {'%.4f' % round(sum(gem_times) / len(gem_times) / HOUR, 4)}")
        if hasattr(sim, 'battle_run_count'):
            print(f"\nBattles count      : {sim.battle_run_count}")
            print(f"Avg battles per day: {'%.2f' % round(sim.battle_run_count / self.config['TIME'], 2)}")

        total_value = 0
        print('Income:')
        for k in RESOURCE_TAGS:
            v = sim.total_income[k]
            k_cap = k.capitalize()
            total_value += v * Value[k_cap]
            t = '%.3f' % round(v, 3)
            v_day = '%.4f' % round(v / self.config['TIME'], 4)
            print('  ' + k_cap + (10 - len(k_cap)) * ' ' + ': ' + ((12 - len(v_day)) * ' ') + v_day + '/Day' + '     Total:' +
                  (max_len_total + 1 - len(t)) * ' ' + t)
        k = "Total value"
        t = '%.3f' % round(total_value, 3)
        v_day = '%.4f' % round(total_value / self.config['TIME'], 4)
        print(k + (12 - len(k)) * ' ' + ': ' + ((12 - len(v_day)) * ' ') + v_day + '/Day' + '     Total:' +
              (max_len_total + 1 - len(t)) * ' ' + t)