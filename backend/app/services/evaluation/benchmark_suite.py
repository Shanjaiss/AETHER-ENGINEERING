from typing import Dict, Any, List

BENCHMARK_TASKS: List[Dict[str, Any]] = [
    # 1. Bug fixing
    {
        "id": "bench-01",
        "name": "FastAPI JWT Expiry Check",
        "category": "Bug Fixing",
        "description": "Inspect auth.py and fix authenticate() so that expired tokens return False.",
        "initial_files": {
            "auth.py": "import time\ndef authenticate(token_exp: int) -> bool:\n    return True\n"
        },
        "test_files": {
            "test_auth.py": "import time\nfrom auth import authenticate\ndef test_authenticate():\n    now = int(time.time())\n    assert authenticate(now + 1000) is True\n    assert authenticate(now - 10) is False\n"
        },
        "expected_files": ["auth.py"],
        "reference_fix": {
            "auth.py": "import time\ndef authenticate(token_exp: int) -> bool:\n    return token_exp > int(time.time())\n"
        }
    },
    {
        "id": "bench-02",
        "name": "Pagination Off-By-One Slice",
        "category": "Bug Fixing",
        "description": "Fix paginate_items in pagination.py so page 1 returns items 0 to limit.",
        "initial_files": {
            "pagination.py": "def paginate(items, page, limit):\n    start = page * limit\n    return items[start:start+limit]\n"
        },
        "test_files": {
            "test_pagination.py": "from pagination import paginate\ndef test_paginate():\n    items = list(range(10))\n    assert paginate(items, 1, 3) == [0, 1, 2]\n    assert paginate(items, 2, 3) == [3, 4, 5]\n"
        },
        "expected_files": ["pagination.py"],
        "reference_fix": {
            "pagination.py": "def paginate(items, page, limit):\n    start = (page - 1) * limit\n    return items[start:start+limit]\n"
        }
    },
    # 2. Unit-test generation
    {
        "id": "bench-03",
        "name": "Slugify Helper Unit Tests",
        "category": "Unit-Test Generation",
        "description": "Implement comprehensive unit tests in test_slugify.py for slugify function.",
        "initial_files": {
            "slug.py": "import re\ndef slugify(text: str) -> str:\n    text = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip().lower())\n    return text.strip('-')\n"
        },
        "test_files": {
            "test_slugify.py": "from slug import slugify\ndef test_slugify_spaces():\n    assert slugify('Hello World') == 'hello-world'\ndef test_slugify_special_chars():\n    assert slugify('Foo & Bar!!') == 'foo-bar'\n"
        },
        "expected_files": ["test_slugify.py"],
        "reference_fix": {
            "test_slugify.py": "from slug import slugify\ndef test_slugify_spaces():\n    assert slugify('Hello World') == 'hello-world'\ndef test_slugify_special_chars():\n    assert slugify('Foo & Bar!!') == 'foo-bar'\n"
        }
    },
    {
        "id": "bench-04",
        "name": "Currency Formatter Tests",
        "category": "Unit-Test Generation",
        "description": "Add test cases for format_currency in test_currency.py handling zero and decimals.",
        "initial_files": {
            "currency.py": "def format_currency(cents: int) -> str:\n    return f'${cents / 100:.2f}'\n"
        },
        "test_files": {
            "test_currency.py": "from currency import format_currency\ndef test_currency():\n    assert format_currency(1234) == '$12.34'\n    assert format_currency(0) == '$0.00'\n"
        },
        "expected_files": ["test_currency.py"],
        "reference_fix": {
            "test_currency.py": "from currency import format_currency\ndef test_currency():\n    assert format_currency(1234) == '$12.34'\n    assert format_currency(0) == '$0.00'\n"
        }
    },
    # 3. API endpoint implementation
    {
        "id": "bench-05",
        "name": "System Health Status Route",
        "category": "Endpoint Implementation",
        "description": "Implement GET /status route returning dict with status and version.",
        "initial_files": {
            "app.py": "def get_status():\n    return {'status': 'down'}\n"
        },
        "test_files": {
            "test_app.py": "from app import get_status\ndef test_status():\n    res = get_status()\n    assert res['status'] == 'healthy'\n    assert 'version' in res\n"
        },
        "expected_files": ["app.py"],
        "reference_fix": {
            "app.py": "def get_status():\n    return {'status': 'healthy', 'version': '1.0.0'}\n"
        }
    },
    {
        "id": "bench-06",
        "name": "User Profile Calculation",
        "category": "Endpoint Implementation",
        "description": "Implement calculate_profile_completion in profile.py.",
        "initial_files": {
            "profile.py": "def calculate_completion(user_dict: dict) -> int:\n    return 0\n"
        },
        "test_files": {
            "test_profile.py": "from profile import calculate_completion\ndef test_profile():\n    assert calculate_completion({'name': 'Alice', 'email': 'a@b.com'}) == 100\n    assert calculate_completion({'name': 'Alice'}) == 50\n"
        },
        "expected_files": ["profile.py"],
        "reference_fix": {
            "profile.py": "def calculate_completion(user_dict: dict) -> int:\n    keys = ['name', 'email']\n    present = sum(1 for k in keys if user_dict.get(k))\n    return int((present / len(keys)) * 100)\n"
        }
    },
    # 4. Refactoring
    {
        "id": "bench-07",
        "name": "Refactor Dict Params to Named Class",
        "category": "Refactoring",
        "description": "Refactor user creation in service.py to accept UserConfig dataclass.",
        "initial_files": {
            "service.py": "class UserConfig:\n    def __init__(self, name: str, role: str):\n        self.name = name\n        self.role = role\ndef create_user(config: UserConfig):\n    return f'{config.name}:{config.role}'\n"
        },
        "test_files": {
            "test_service.py": "from service import UserConfig, create_user\ndef test_create():\n    cfg = UserConfig('Bob', 'admin')\n    assert create_user(cfg) == 'Bob:admin'\n"
        },
        "expected_files": ["service.py"],
        "reference_fix": {
            "service.py": "class UserConfig:\n    def __init__(self, name: str, role: str):\n        self.name = name\n        self.role = role\ndef create_user(config: UserConfig):\n    return f'{config.name}:{config.role}'\n"
        }
    },
    {
        "id": "bench-08",
        "name": "Consolidate String Cleaners",
        "category": "Refactoring",
        "description": "Consolidate clean_text in utils.py to strip whitespace and unprintable chars.",
        "initial_files": {
            "utils.py": "def clean_text(s: str) -> str:\n    return s\n"
        },
        "test_files": {
            "test_utils.py": "from utils import clean_text\ndef test_clean():\n    assert clean_text('  hello\\x00world  ') == 'helloworld'\n"
        },
        "expected_files": ["utils.py"],
        "reference_fix": {
            "utils.py": "def clean_text(s: str) -> str:\n    return s.strip().replace('\\x00', '')\n"
        }
    },
    # 5. TypeScript / Type errors
    {
        "id": "bench-09",
        "name": "TypeScript Discriminated Union Safety",
        "category": "TypeScript Errors",
        "description": "Fix type narrowing in type_guard.py for union types.",
        "initial_files": {
            "type_guard.py": "def handle_event(event: dict) -> str:\n    return event.get('kind', 'unknown')\n"
        },
        "test_files": {
            "test_type_guard.py": "from type_guard import handle_event\ndef test_event():\n    assert handle_event({'kind': 'click', 'x': 10}) == 'click'\n"
        },
        "expected_files": ["type_guard.py"],
        "reference_fix": {
            "type_guard.py": "def handle_event(event: dict) -> str:\n    return event.get('kind', 'unknown')\n"
        }
    },
    {
        "id": "bench-10",
        "name": "Optional Property Null Safety",
        "category": "TypeScript Errors",
        "description": "Fix get_user_display in display.py when user has no nickname.",
        "initial_files": {
            "display.py": "def get_display(user: dict) -> str:\n    return user['nickname']\n"
        },
        "test_files": {
            "test_display.py": "from display import get_display\ndef test_display():\n    assert get_display({'name': 'John'}) == 'John'\n    assert get_display({'name': 'John', 'nickname': 'Johnny'}) == 'Johnny'\n"
        },
        "expected_files": ["display.py"],
        "reference_fix": {
            "display.py": "def get_display(user: dict) -> str:\n    return user.get('nickname') or user.get('name', 'Anonymous')\n"
        }
    },
    # 6. Python exceptions
    {
        "id": "bench-11",
        "name": "ZeroDivisionError Guard",
        "category": "Python Exceptions",
        "description": "Safeguard safe_divide in math_utils.py against zero division.",
        "initial_files": {
            "math_utils.py": "def safe_divide(a, b):\n    return a / b\n"
        },
        "test_files": {
            "test_math.py": "from math_utils import safe_divide\ndef test_divide():\n    assert safe_divide(10, 2) == 5.0\n    assert safe_divide(10, 0) == 0.0\n"
        },
        "expected_files": ["math_utils.py"],
        "reference_fix": {
            "math_utils.py": "def safe_divide(a, b):\n    return 0.0 if b == 0 else a / b\n"
        }
    },
    {
        "id": "bench-12",
        "name": "KeyError Fallback Handling",
        "category": "Python Exceptions",
        "description": "Fix parse_config in config_parser.py to use default timeout when missing.",
        "initial_files": {
            "config_parser.py": "def parse_config(cfg: dict) -> int:\n    return cfg['timeout']\n"
        },
        "test_files": {
            "test_config.py": "from config_parser import parse_config\ndef test_config():\n    assert parse_config({'timeout': 30}) == 30\n    assert parse_config({}) == 60\n"
        },
        "expected_files": ["config_parser.py"],
        "reference_fix": {
            "config_parser.py": "def parse_config(cfg: dict) -> int:\n    return cfg.get('timeout', 60)\n"
        }
    },
    # 7. Validation failures
    {
        "id": "bench-13",
        "name": "Email Format Validation",
        "category": "Validation Failures",
        "description": "Implement is_valid_email in validator.py rejecting invalid email strings.",
        "initial_files": {
            "validator.py": "def is_valid_email(email: str) -> bool:\n    return False\n"
        },
        "test_files": {
            "test_validator.py": "from validator import is_valid_email\ndef test_emails():\n    assert is_valid_email('user@example.com') is True\n    assert is_valid_email('invalid-email') is False\n"
        },
        "expected_files": ["validator.py"],
        "reference_fix": {
            "validator.py": "import re\ndef is_valid_email(email: str) -> bool:\n    return bool(re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$', email))\n"
        }
    },
    {
        "id": "bench-14",
        "name": "Password Strength Verification",
        "category": "Validation Failures",
        "description": "Implement verify_password_strength requiring min length 8 and a digit.",
        "initial_files": {
            "password.py": "def verify_password(pw: str) -> bool:\n    return True\n"
        },
        "test_files": {
            "test_password.py": "from password import verify_password\ndef test_pw():\n    assert verify_password('SecurePass1') is True\n    assert verify_password('short1') is False\n    assert verify_password('NoDigitsHere') is False\n"
        },
        "expected_files": ["password.py"],
        "reference_fix": {
            "password.py": "def verify_password(pw: str) -> bool:\n    return len(pw) >= 8 and any(c.isdigit() for c in pw)\n"
        }
    },
    # 8. Dependency issues
    {
        "id": "bench-15",
        "name": "Timezone-Aware UTC Datetime Migration",
        "category": "Dependency Issues",
        "description": "Replace deprecated utcnow() with datetime.now(timezone.utc) in time_helper.py.",
        "initial_files": {
            "time_helper.py": "import datetime\ndef get_utc_timestamp():\n    return datetime.datetime.now(datetime.timezone.utc)\n"
        },
        "test_files": {
            "test_time.py": "from time_helper import get_utc_timestamp\ndef test_ts():\n    dt = get_utc_timestamp()\n    assert dt.tzinfo is not None\n"
        },
        "expected_files": ["time_helper.py"],
        "reference_fix": {
            "time_helper.py": "import datetime\ndef get_utc_timestamp():\n    return datetime.datetime.now(datetime.timezone.utc)\n"
        }
    },
    {
        "id": "bench-16",
        "name": "JSON Serialization Fallback",
        "category": "Dependency Issues",
        "description": "Implement safe_json_dump in serializer.py converting non-serializable objects to str.",
        "initial_files": {
            "serializer.py": "import json\ndef safe_dump(obj) -> str:\n    return json.dumps(obj, default=str)\n"
        },
        "test_files": {
            "test_serializer.py": "import datetime\nfrom serializer import safe_dump\ndef test_serialize():\n    now = datetime.datetime(2026, 1, 1)\n    res = safe_dump({'date': now})\n    assert '2026-01-01' in res\n"
        },
        "expected_files": ["serializer.py"],
        "reference_fix": {
            "serializer.py": "import json\ndef safe_dump(obj) -> str:\n    return json.dumps(obj, default=str)\n"
        }
    },
    # 9. Authentication defects
    {
        "id": "bench-17",
        "name": "Timing-Safe Secret Comparison",
        "category": "Authentication Defects",
        "description": "Fix compare_api_keys in security.py to use hmac.compare_digest to prevent timing attacks.",
        "initial_files": {
            "security.py": "def compare_keys(a: str, b: str) -> bool:\n    return a == b\n"
        },
        "test_files": {
            "test_security.py": "from security import compare_keys\ndef test_keys():\n    assert compare_keys('key123', 'key123') is True\n    assert compare_keys('key123', 'key456') is False\n"
        },
        "expected_files": ["security.py"],
        "reference_fix": {
            "security.py": "import hmac\ndef compare_keys(a: str, b: str) -> bool:\n    return hmac.compare_digest(a, b)\n"
        }
    },
    {
        "id": "bench-18",
        "name": "Bearer Token Header Extraction",
        "category": "Authentication Defects",
        "description": "Implement extract_bearer_token in header_auth.py stripping 'Bearer ' prefix.",
        "initial_files": {
            "header_auth.py": "def extract_token(header_val: str) -> str:\n    return header_val\n"
        },
        "test_files": {
            "test_header_auth.py": "from header_auth import extract_token\ndef test_extract():\n    assert extract_token('Bearer my_token_123') == 'my_token_123'\n    assert extract_token('invalid') == ''\n"
        },
        "expected_files": ["header_auth.py"],
        "reference_fix": {
            "header_auth.py": "def extract_token(header_val: str) -> str:\n    if header_val.startswith('Bearer '):\n        return header_val[7:].strip()\n    return ''\n"
        }
    },
    # 10. Frontend / State bugs
    {
        "id": "bench-19",
        "name": "Immutable State Reducer Update",
        "category": "Frontend Bugs",
        "description": "Fix counter_reducer in reducer.py ensuring pure immutable updates.",
        "initial_files": {
            "reducer.py": "def counter_reducer(state: dict, action: dict) -> dict:\n    state['count'] += action.get('amount', 1)\n    return state\n"
        },
        "test_files": {
            "test_reducer.py": "from reducer import counter_reducer\ndef test_pure():\n    initial = {'count': 0}\n    next_state = counter_reducer(initial, {'amount': 2})\n    assert next_state['count'] == 2\n    # Test immutability: initial dictionary was not modified\n    assert initial['count'] == 0\n"
        },
        "expected_files": ["reducer.py"],
        "reference_fix": {
            "reducer.py": "def counter_reducer(state: dict, action: dict) -> dict:\n    new_state = state.copy()\n    new_state['count'] += action.get('amount', 1)\n    return new_state\n"
        }
    },
    {
        "id": "bench-20",
        "name": "Query Param Sanitizer",
        "category": "Frontend Bugs",
        "description": "Implement sanitize_query_params in query_cleaner.py removing null and empty values.",
        "initial_files": {
            "query_cleaner.py": "def clean_params(params: dict) -> dict:\n    return params\n"
        },
        "test_files": {
            "test_query_cleaner.py": "from query_cleaner import clean_params\ndef test_clean():\n    res = clean_params({'q': 'search', 'page': None, 'filter': ''})\n    assert res == {'q': 'search'}\n"
        },
        "expected_files": ["query_cleaner.py"],
        "reference_fix": {
            "query_cleaner.py": "def clean_params(params: dict) -> dict:\n    return {k: v for k, v in params.items() if v is not None and v != ''}\n"
        }
    }
]

