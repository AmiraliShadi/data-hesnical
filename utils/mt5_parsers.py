def mt5_parse_maximum_consecutive_value(value):
    open_paren_index = value.find('(')
    close_paren_index = value.find(')')

    if open_paren_index != -1 and close_paren_index != -1:
        count = value[:open_paren_index].strip()
        dollar_amount = value[open_paren_index + 1:close_paren_index].strip()
        return count, dollar_amount

    return None, None


def mt5_parse_maximal_consecutive_value(value):
    open_paren_index = value.find('(')
    close_paren_index = value.find(')')

    if open_paren_index != -1 and close_paren_index != -1:
        dollar_amount = value[:open_paren_index].strip()
        count = value[open_paren_index + 1:close_paren_index].strip()
        return dollar_amount, count

    return None, None


def mt5_parse_trades_value(value):
    open_paren_index = value.find('(')
    close_paren_index = value.find(')')

    if open_paren_index != -1 and close_paren_index != -1:
        count = value[:open_paren_index].strip()
        percent = value[open_paren_index + 1:close_paren_index].strip('%').strip()
        return count, percent

    return None, None


def mt5_parse_profit_loss_value(value):
    open_paren_index = value.find('(')
    close_paren_index = value.find(')')

    if open_paren_index != -1 and close_paren_index != -1:
        count = value[:open_paren_index].strip()
        percent = value[open_paren_index + 1:close_paren_index].strip('%').strip()
        return count, percent

    return None, None


def mt5_parse_balance_drawdown_value(value):
    open_paren_index = value.find('(')
    close_paren_index = value.find(')')

    if open_paren_index != -1 and close_paren_index != -1:
        dollar_amount = value[:open_paren_index].strip()
        percent = value[open_paren_index + 1:close_paren_index].strip('%').strip()
        return dollar_amount, percent

    return None, None


def mt5_parse_balance_drawdown_relative_value(value):
    open_paren_index = value.find('(')
    close_paren_index = value.find(')')

    if open_paren_index != -1 and close_paren_index != -1:
        percent = value[:open_paren_index].strip().rstrip('%')
        dollar_amount = value[open_paren_index + 1:close_paren_index].strip()
        return percent, dollar_amount

    return None, None


def mt5_parse_margin_level_value(value):
    percent = value.strip().rstrip('%')
    return percent
