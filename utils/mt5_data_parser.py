from collections import defaultdict

import requests
from bs4 import BeautifulSoup

from utils.mt5_parsers import mt5_parse_maximum_consecutive_value, mt5_parse_maximal_consecutive_value, \
    mt5_parse_trades_value, mt5_parse_profit_loss_value, mt5_parse_balance_drawdown_value, \
    mt5_parse_balance_drawdown_relative_value, mt5_parse_margin_level_value
from utils.validators import detect_encoding


def mt5_get_th_tags_data(soup, field_name):
    tag = soup.find('th', text=f'{field_name}:')
    if tag:
        sibling = tag.find_next_sibling('th')
        if sibling:
            b_tag = sibling.find('b')
            if b_tag:
                return b_tag.text


def mt5_get_td_tags_data(soup, field_name):
    tag = soup.find('td', text=f'{field_name}:')
    if tag:
        sibling = tag.find_next_sibling('td')
        if sibling:
            b_tag = sibling.find('b')
            if b_tag:
                return b_tag.text


def mt5_get_total_net_profit(soup):
    return float(mt5_get_td_tags_data(soup, 'Total Net Profit'))


def mt5_get_commissions_total_deals_table(soup):
    rows = soup.find_all('tr', align="right")

    for row in rows:
        td_elements = row.find_all('td')

        if len(td_elements) == 7:
            return float(td_elements[1].get_text(strip=True))


def mt5_count_daily_profits(soup):
    daily_profits = defaultdict(lambda: {'win_count': 0, 'loss_count': 0})

    header_row = soup.find('th', text="Positions").find_parent('tr')
    column_headers_row = header_row.find_next_sibling('tr')
    headers = column_headers_row.find_all('td')
    profit_index = None

    for index, td in enumerate(headers):
        if td.get_text(strip=True) == "Profit":
            profit_index = index + 1
            break

    if profit_index is None:
        raise ValueError("Profit header not found")

    current_row = column_headers_row.find_next_sibling('tr')

    while current_row:
        if current_row.find('th', text="Orders"):
            break

        cells = current_row.find_all('td')

        if len(cells) <= profit_index:
            current_row = current_row.find_next_sibling('tr')
            continue

        date_str = cells[0].get_text(strip=True)
        profit_str = cells[profit_index].get_text(strip=True)

        try:
            profit = float(profit_str)
        except ValueError:
            current_row = current_row.find_next_sibling('tr')
            continue

        date = date_str.split(' ')[0]

        if profit > 0:
            daily_profits[date]['win_count'] += 1
        elif profit < 0:
            daily_profits[date]['loss_count'] += 1

        current_row = current_row.find_next_sibling('tr')

    daily_profits_list = [
        {"date": date, **stats}
        for date, stats in daily_profits.items()
    ]

    return daily_profits_list


def mt5_extract_trade_details(soup):
    trades = []

    header_row = soup.find('th', text="Positions").find_parent('tr')
    column_headers_row = header_row.find_next_sibling('tr')
    headers = column_headers_row.find_all('td')
    profit_index = None

    for index, td in enumerate(headers):
        if td.get_text(strip=True) == "Profit":
            profit_index = index + 1
            break

    if profit_index is None:
        raise ValueError("Profit header not found")

    current_row = column_headers_row.find_next_sibling('tr')

    while current_row:
        if current_row.find('th', text="Orders"):
            break

        cells = current_row.find_all('td')

        if len(cells) <= profit_index:
            current_row = current_row.find_next_sibling('tr')
            continue

        trade_details = {
            "time": cells[0].get_text(strip=True),
            "position": cells[1].get_text(strip=True),
            "symbol": cells[2].get_text(strip=True),
            "type": cells[3].get_text(strip=True),
            "volume": cells[5].get_text(strip=True) if cells[5].get_text(strip=True) else None,
            "price": cells[6].get_text(strip=True) if cells[6].get_text(strip=True) else None,
            "s/l": cells[7].get_text(strip=True),
            "t/p": cells[8].get_text(strip=True),
            "time_2": cells[9].get_text(strip=True),
            "price_2": cells[10].get_text(strip=True) if cells[10].get_text(strip=True) else None,
            "commission": cells[11].get_text(strip=True) if cells[11].get_text(strip=True) else None,
            "swap": cells[12].get_text(strip=True) if cells[12].get_text(strip=True) else None,
            "profit": cells[profit_index].get_text(strip=True)
        }

        trades.append(trade_details)

        current_row = current_row.find_next_sibling('tr')

    return trades


def mt5_count_profits(soup):
    positive_count = 0
    negative_count = 0
    header_row = soup.find('th', text="Positions").find_parent('tr')
    column_headers_row = header_row.find_next_sibling('tr')
    headers = column_headers_row.find_all('td')
    profit_index = None

    for index, td in enumerate(headers):
        if td.get_text(strip=True) == "Profit":
            profit_index = index + 1
            break

    if profit_index is None:
        raise ValueError("Profit header not found")

    current_row = column_headers_row.find_next_sibling('tr')

    while current_row:
        if current_row.find('th', text="Orders"):
            break

        cells = current_row.find_all('td')
        if len(cells) > profit_index:
            commission_value = float(cells[profit_index].get_text(strip=True))
            if commission_value > 0:
                positive_count += 1
            if commission_value < 0:
                negative_count += 1

        current_row = current_row.find_next_sibling('tr')

    return {'positive_count': positive_count, 'negative_count': negative_count}


def mt5_extract_positions_by_date(soup):
    header_row = soup.find('th', text="Positions").find_parent('tr')

    column_headers_row = header_row.find_next_sibling('tr')
    header_cells = column_headers_row.find_all('td')

    headers = [td.text for td in header_cells]
    header_indices = {}
    for index, header in enumerate(headers):
        header_indices[index] = header

    data_by_date = {}

    current_row = column_headers_row.find_next_sibling('tr')

    while current_row:
        if current_row.find('th', text="Orders"):
            break

        if len(current_row.find_all('td')) == 14:

            cells = []
            for td in current_row.find_all('td'):
                if td.has_attr('class'):
                    if 'hidden' in td['class']:
                        continue
                cells.append(td.text)

            row_data = {header_indices[index]: cells[index] if index < len(cells) else '' for index in
                        range(len(headers))}

            data_by_date[row_data['Time']] = row_data

        current_row = current_row.find_next_sibling('tr')

    organized_data = defaultdict(lambda: defaultdict(list))

    for timestamp, fields in data_by_date.items():
        date, _ = timestamp.split(' ', 1)
        for key, value in fields.items():
            organized_data[date][key].append(value)

    organized_data = {date: dict(fields) for date, fields in organized_data.items()}

    return organized_data


def mt5_extract_data_from_html_file(url):
    response = {}
    response_content = requests.get(url).content
    encoding = detect_encoding(response_content)
    html_content = response_content.decode(encoding)

    soup = BeautifulSoup(html_content, 'html.parser')

    th_fields = ['Name', 'Account', 'Company', 'Date']
    for field in th_fields:
        value = mt5_get_th_tags_data(soup, field)
        if value:
            response[field.lower().replace(' ', '_')] = value

    td_fields = [
        'Balance', 'Credit Facility', 'Floating P/L', 'Equity', 'Free Margin', 'Margin',
        'Total Net Profit', 'Profit Factor', 'Recovery Factor', 'Gross Profit', 'Expected Payoff', 'Sharpe Ratio',
        'Gross Loss', 'Balance Drawdown', 'Balance Drawdown Absolute', 'Total Trades', 'Largest profit trade',
        'Largest loss trade', 'Average profit trade', 'Average loss trade', 'Average consecutive wins',
        'Average consecutive losses',
    ]
    for field in td_fields:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            response[field.lower().replace(' ', '_')] = value.replace(' ', '')

    maximum_consecutive_td_fields = ['Maximum consecutive wins ($)', 'Maximum consecutive losses ($)']
    for field in maximum_consecutive_td_fields:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            field_base = field.lower().replace(' ', '_').replace('($)', '')
            count, dollar_amount = mt5_parse_maximum_consecutive_value(value)
            if count is not None and dollar_amount is not None:
                response[f"{field_base}count"] = count
                response[f"{field_base}dollar"] = dollar_amount

    maximal_consecutive_td_fields = ['Maximal consecutive profit (count)', 'Maximal consecutive loss (count)']
    for field in maximal_consecutive_td_fields:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            field_base = field.lower().replace(' ', '_').replace('(count)', '')
            dollar_amount, count = mt5_parse_maximal_consecutive_value(value)
            if dollar_amount is not None and count is not None:
                response[f"{field_base}dollar"] = dollar_amount
                response[f"{field_base}count"] = count

    trades_td_fields = ['Short Trades (won %)', 'Long Trades (won %)']
    for field in trades_td_fields:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            field_base = field.lower().replace(' ', '_').replace('(won_%', '').replace(')', '')
            count, percent = mt5_parse_trades_value(value)
            if count is not None and percent is not None:
                response[f"{field_base}count"] = count
                response[f"{field_base}percent"] = percent

    profit_loss_td_fields = ['Profit Trades (% of total)', 'Loss Trades (% of total)']
    for field in profit_loss_td_fields:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            field_base = field.lower().replace(' ', '_').replace('(%_of_total)', '')
            count, percent = mt5_parse_profit_loss_value(value)
            if count is not None and percent is not None:
                response[f"{field_base}count"] = count
                response[f"{field_base}percent"] = percent

    balance_drawdown_maximal_td_fields = ['Balance Drawdown Maximal']
    for field in balance_drawdown_maximal_td_fields:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            field_base = field.lower().replace(' ', '_')
            dollar_amount, percent = mt5_parse_balance_drawdown_value(value)
            if dollar_amount is not None and percent is not None:
                response[f"{field_base}_dollar"] = dollar_amount
                response[f"{field_base}_percent"] = percent

    balance_drawdown_relative_td_fields = ['Balance Drawdown Relative']
    for field in balance_drawdown_relative_td_fields:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            field_base = field.lower().replace(' ', '_')
            percent, dollar_amount = mt5_parse_balance_drawdown_relative_value(value)
            if percent is not None and dollar_amount is not None:
                response[f"{field_base}_percent"] = percent
                response[f"{field_base}_dollar"] = dollar_amount

    margin_level_td_field = ['Margin Level']
    for field in margin_level_td_field:
        value = mt5_get_td_tags_data(soup, field)
        if value:
            field_base = field.lower().replace(' ', '_')
            percent = mt5_parse_margin_level_value(value)
            response[f"{field_base}_percent"] = percent

    response['total_win_count'] = mt5_count_profits(soup)['positive_count']
    response['total_loss_count'] = mt5_count_profits(soup)['negative_count']

    response['daily_profits'] = mt5_count_daily_profits(soup)

    response['p_and_l'] = mt5_get_total_net_profit(soup) - mt5_get_commissions_total_deals_table(soup)

    response['position_table_data'] = mt5_extract_trade_details(soup)

    return response
