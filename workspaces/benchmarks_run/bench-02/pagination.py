def paginate(items, page, limit):
    start = (page - 1) * limit
    return items[start:start+limit]
