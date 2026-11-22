def prepare_method(method):
    if isinstance(method, bytes):
        return method.decode('utf-8')
    return str(method)
