import chardet


def detect_encoding(content):
    result = chardet.detect(content)
    return result['encoding']
