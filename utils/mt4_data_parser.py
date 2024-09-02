from collections import defaultdict

import requests
from bs4 import BeautifulSoup

from utils.validators import detect_encoding


def mt4_get_td_tags_data(soup, field):
    tag = soup.find('b', text=lambda text: text and text.startswith(field))
    if tag:
        return tag.text.split(f"{field}:")[1].strip()
    return None


def mt4_get_date(soup):
    date_tag = soup.find('td', align='right')
    if date_tag:
        return date_tag.text.strip()
    return None


def mt4_extract_summary_data(soup, field):
    tag = soup.find('b', text=lambda text: text and text.startswith(field))
    if tag:
        value_tag = tag.find_parent('td').find_next_sibling('td').find('b')
        if value_tag:
            return value_tag.text.strip()
    return None


def mt4_extract_closed_transactions(soup):
    trades = []

    header_row = soup.find('tr', bgcolor="#C0C0C0")
    current_row = header_row.find_next_sibling('tr')

    while current_row and "Open Trades:" not in current_row.get_text():
        cells = current_row.find_all('td')

        if len(cells) == 5 and 'colspan' in cells[3].attrs:
            trade_details = {
                "ticket": cells[0].get_text(strip=True),
                "open_time": cells[1].get_text(strip=True),
                "type": cells[2].get_text(strip=True),
                "comment": cells[3].get_text(strip=True),
                "profit": cells[4].get_text(strip=True)
            }
            trades.append(trade_details)

        if len(cells) == 14:
            trade_details = {
                "ticket": cells[0].get_text(strip=True),
                "open_time": cells[1].get_text(strip=True),
                "type": cells[2].get_text(strip=True),
                "size": cells[3].get_text(strip=True),
                "item": cells[4].get_text(strip=True),
                "price_open": cells[5].get_text(strip=True),
                "s_l": cells[6].get_text(strip=True),
                "t_p": cells[7].get_text(strip=True),
                "close_time": cells[8].get_text(strip=True),
                "price_close": cells[9].get_text(strip=True),
                "commission": cells[10].get_text(strip=True),
                "taxes": cells[11].get_text(strip=True),
                "swap": cells[12].get_text(strip=True),
                "profit": cells[13].get_text(strip=True),
            }

            trades.append(trade_details)

        current_row = current_row.find_next_sibling('tr')

    return trades


def mt4_count_profit_types(trades):
    positive_count = 0
    negative_count = 0

    for trade in trades:
        profit = float(trade.get('profit', 0))
        if profit > 0:
            positive_count += 1
        elif profit < 0:
            negative_count += 1

    return {'positive_count': positive_count, 'negative_count': negative_count}


def mt4_calculate_daily_profits(trades):
    daily_stats = defaultdict(lambda: {"win_count": 0, "loss_count": 0})

    for trade in trades:
        date_str = trade['open_time'].split()[0]
        profit = float(trade['profit'])

        if profit > 0:
            daily_stats[date_str]['win_count'] += 1
        elif profit < 0:
            daily_stats[date_str]['loss_count'] += 1

    daily_profits = [{"date": date, "win_count": stats["win_count"], "loss_count": stats["loss_count"]}
                     for date, stats in sorted(daily_stats.items())]

    return daily_profits


def mt4_extract_data_from_html_file(url):
    response = {}
    response_content = requests.get(url).content
    encoding = detect_encoding(response_content)
    html_content = response_content.decode(encoding)

    soup = BeautifulSoup(html_content, 'html.parser')

    td_fields = ['Account', 'Name', 'Currency']

    for field in td_fields:
        value = mt4_get_td_tags_data(soup, field)
        if value:
            response[field.lower().replace(' ', '_')] = value

    date_value = mt4_get_date(soup)
    if date_value:
        response['date'] = date_value

    summary_fields = [
        'Deposit/Withdrawal', 'Credit Facility', 'Closed Trade P/L',
        'Floating P/L', 'Margin', 'Balance', 'Equity', 'Free Margin'
    ]
    for field in summary_fields:
        value = mt4_extract_summary_data(soup, field)
        if value:
            response[field.lower().replace(' ', '_').replace('/', '_')] = value

    response['closed_transactions'] = mt4_extract_closed_transactions(soup)

    response['total_win_count'] = mt4_count_profit_types(response['closed_transactions'])['positive_count']
    response['total_loss_count'] = mt4_count_profit_types(response['closed_transactions'])['negative_count']

    response['daily_profits'] = mt4_calculate_daily_profits(response['closed_transactions'])

    return response
