from urllib.parse import urlencode


def build_querystring(querydict, **updates):
    params = {}
    for key, value in querydict.items():
        if value not in (None, ""):
            params[key] = value
    for key, value in updates.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    return urlencode(params)
