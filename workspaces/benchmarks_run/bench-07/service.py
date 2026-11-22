class UserConfig:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
def create_user(config: UserConfig):
    return f'{config.name}:{config.role}'
