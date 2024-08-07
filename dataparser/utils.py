from collections import defaultdict

import chardet
from bs4 import BeautifulSoup


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read(100)
        result = chardet.detect(raw_data)
        return result['encoding']


def get_th_tags_data(soup, field_name):
    tag = soup.find('th', text=f'{field_name}:')
    if tag:
        sibling = tag.find_next_sibling('th')
        if sibling:
            b_tag = sibling.find('b')
            if b_tag:
                return b_tag.text


def get_td_tags_data(soup, field_name):
    tag = soup.find('td', text=f'{field_name}:')
    if tag:
        sibling = tag.find_next_sibling('td')
        if sibling:
            b_tag = sibling.find('b')
            if b_tag:
                return b_tag.text


def get_total_net_profit(soup):
    return float(get_td_tags_data(soup, 'Total Net Profit'))


def get_commissions_total_deals_table(soup):
    rows = soup.find_all('tr', align="right")

    for row in rows:
        td_elements = row.find_all('td')

        if len(td_elements) == 7:
            return float(td_elements[1].get_text(strip=True))


def count_commissions(soup):
    positive_count = 0
    negative_count = 0
    header_row = soup.find('th', text="Positions").find_parent('tr')
    column_headers_row = header_row.find_next_sibling('tr')
    headers = column_headers_row.find_all('td')
    commission_index = None

    for index, td in enumerate(headers):
        if td.get_text(strip=True) == "Commission":
            commission_index = index + 1
            break

    if commission_index is None:
        raise ValueError("Commission header not found")

    current_row = column_headers_row.find_next_sibling('tr')

    while current_row:
        if current_row.find('th', text="Orders"):
            break

        cells = current_row.find_all('td')
        if len(cells) > commission_index:
            commission_value = float(cells[commission_index].get_text(strip=True))
            if commission_value > 0:
                positive_count += 1
            if commission_value < 0:
                negative_count += 1

        current_row = current_row.find_next_sibling('tr')

    return {'positive_count': positive_count, 'negative_count': negative_count}


def extract_positions_by_date(soup):
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

            row_data = {header_indices[index]: cells[index] if index < len(cells) else '' for index in range(len(headers))}

            data_by_date[row_data['Time']] = row_data

        current_row = current_row.find_next_sibling('tr')

    organized_data = defaultdict(lambda: defaultdict(list))

    for timestamp, fields in data_by_date.items():
        date, _ = timestamp.split(' ', 1)
        for key, value in fields.items():
            organized_data[date][key].append(value)

    organized_data = {date: dict(fields) for date, fields in organized_data.items()}

    return organized_data


def extract_data_from_html_file(report_file):
    response = {}
    encoding = detect_encoding(report_file)
    with open(report_file, 'r', encoding=encoding) as file:
        file_content = file.read()
        soup = BeautifulSoup(file_content, 'html.parser')

        th_fields = ['Name', 'Account', 'Company', 'Date']
        for field in th_fields:
            value = get_th_tags_data(soup, field)
            if value:
                response[field.lower()] = value

        td_fields = [
            'Balance', 'Credit Facility', 'Floating P/L', 'Equity',
            'Free Margin', 'Margin', 'Margin Level',
            'Total Net Profit', 'Profit Factor', 'Recovery Factor',
            'Gross Profit', 'Expected Payoff', 'Sharpe Ratio', 'Gross Loss',
            'Balance Drawdown', 'Balance Drawdown Absolute', 'Balance Drawdown Maximal', 'Balance Drawdown Relative',
            'Total Trades', 'Short Trades (won %)', 'Long Trades (won %)', 'Profit Trades (% of total)',
            'Loss Trades (% of total)', 'Largest profit trade', 'Largest loss trade', 'Average profit trade',
            'Average loss trade', 'Maximum consecutive wins ($)', 'Maximum consecutive losses ($)',
            'Maximal consecutive profit (count)', 'Maximal consecutive loss (count)', 'Average consecutive wins',
            'Average consecutive losses',
        ]
        for field in td_fields:
            value = get_td_tags_data(soup, field)
            if value:
                response[field.lower()] = value

        response['negative_commissions_count'] = count_commissions(soup)['negative_count']
        response['positive_commissions_count'] = count_commissions(soup)['positive_count']

        response['p_and_l'] = get_total_net_profit(soup) - get_commissions_total_deals_table(soup)

        response['position_table_data'] = extract_positions_by_date(soup)

    return response
