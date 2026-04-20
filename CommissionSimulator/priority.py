PRIORITY_NONE = -999


def parse_filter(filter_str: str) -> list:
    return filter_str.replace('\n', '').replace(' ', '').replace('DailyEvent', '').split('>')


def assign_priorities(commission_lists: dict, filter_tags: list, total_count: int):
    priority = total_count + 1

    for commission_list in commission_lists.values():
        for c in commission_list:
            c.priority = -priority

    run_shortest = False

    for tag in filter_tags:
        if tag.lower() == 'shortest':
            run_shortest = True
            continue
        priority -= 1
        for ctype, commission_list in commission_lists.items():
            if not _tag_matches(tag, ctype):
                continue
            for c in commission_list:
                if c.tag == tag:
                    c.priority = priority

    return run_shortest


def _tag_matches(filter_tag: str, commission_type: str) -> bool:
    type_keywords = {
        'Daily': 'Daily',
        'Night': 'Night',
        'Major': 'Major',
        'Extra': 'Extra',
    }
    keyword = type_keywords.get(commission_type)
    if keyword and keyword in filter_tag:
        return True
    if commission_type == 'Urgent':
        if 'Urgent' in filter_tag or 'Gem' in filter_tag or 'Ship' in filter_tag:
            return True
    return False