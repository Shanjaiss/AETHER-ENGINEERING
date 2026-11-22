def calculate_completion(user_dict: dict) -> int:
    keys = ['name', 'email']
    present = sum(1 for k in keys if user_dict.get(k))
    return int((present / len(keys)) * 100)
