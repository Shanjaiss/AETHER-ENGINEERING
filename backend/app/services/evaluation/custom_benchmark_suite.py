"""
AETHER ENGINEER - Custom Software Engineering Benchmark Suite
50 Controlled Software Engineering Tasks across 5 core categories (10 tasks each).
Includes held-out evaluation fixtures to prevent overfitting and guarantee objective scoring.
"""

from typing import List, Dict, Any

CUSTOM_BENCHMARK_TASKS: List[Dict[str, Any]] = [
    # =========================================================================
    # CATEGORY 1: PYTHON (10 Tasks: py-01 to py-10)
    # =========================================================================
    {
        "id": "py-01",
        "name": "Tiered Pricing Discount Calculation",
        "language": "python",
        "difficulty": "EASY",
        "category": "Python",
        "subcategory": "Incorrect business logic",
        "description": "In pricing.py, calculate_discount() calculates wrong tiers for orders above 100 items. Correct tier boundary logic.",
        "initial_files": {
            "pricing.py": "def calculate_discount(quantity: int, unit_price: float) -> float:\n    # Bug: quantity > 100 gets 0% discount\n    if quantity > 50:\n        return quantity * unit_price * 0.10\n    elif quantity > 10:\n        return quantity * unit_price * 0.05\n    return 0.0\n"
        },
        "baseline_passing_tests": {
            "test_baseline_pricing.py": "from pricing import calculate_discount\ndef test_small_orders():\n    assert calculate_discount(5, 10.0) == 0.0\n    assert calculate_discount(20, 10.0) == 10.0\n"
        },
        "test_files": {
            "test_acceptance_pricing.py": "from pricing import calculate_discount\ndef test_tiered_pricing():\n    assert calculate_discount(150, 10.0) == 300.0  # 20% discount for > 100\n    assert calculate_discount(75, 10.0) == 75.0    # 10% discount for > 50\n    assert calculate_discount(20, 10.0) == 10.0    # 5% discount for > 10\n    assert calculate_discount(5, 10.0) == 0.0\n"
        },
        "expected_files": ["pricing.py"],
        "reference_fix": {
            "pricing.py": "def calculate_discount(quantity: int, unit_price: float) -> float:\n    if quantity > 100:\n        return quantity * unit_price * 0.20\n    elif quantity > 50:\n        return quantity * unit_price * 0.10\n    elif quantity > 10:\n        return quantity * unit_price * 0.05\n    return 0.0\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-02",
        "name": "Safe JSON File Loader Exception Fallback",
        "language": "python",
        "difficulty": "EASY",
        "category": "Python",
        "subcategory": "Exception handling",
        "description": "In json_loader.py, load_config() crashes on missing file or malformed JSON instead of returning default_fallback.",
        "initial_files": {
            "json_loader.py": "import json\nfrom pathlib import Path\ndef load_config(file_path: str, default_fallback: dict) -> dict:\n    with open(file_path, 'r') as f:\n        return json.load(f)\n"
        },
        "test_files": {
            "test_json_loader.py": "import tempfile\nfrom pathlib import Path\nfrom json_loader import load_config\ndef test_missing_and_corrupt():\n    fallback = {'status': 'default'}\n    assert load_config('/non/existent/path.json', fallback) == fallback\n    with tempfile.NamedTemporaryFile('w', delete=False) as tf:\n        tf.write('{invalid json')\n        tf_name = tf.name\n    assert load_config(tf_name, fallback) == fallback\n"
        },
        "expected_files": ["json_loader.py"],
        "reference_fix": {
            "json_loader.py": "import json\nfrom pathlib import Path\ndef load_config(file_path: str, default_fallback: dict) -> dict:\n    try:\n        with open(file_path, 'r') as f:\n            return json.load(f)\n    except (FileNotFoundError, json.JSONDecodeError, OSError):\n        return default_fallback\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-03",
        "name": "User Registration Input Validator",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Python",
        "subcategory": "Input validation",
        "description": "In validator.py, validate_registration() must validate email format, password length >= 8 with digit, and username alphanumeric.",
        "initial_files": {
            "validator.py": "def validate_registration(data: dict) -> tuple[bool, str]:\n    # Incomplete validator\n    return True, ''\n"
        },
        "test_files": {
            "test_validator.py": "from validator import validate_registration\ndef test_validation_rules():\n    ok, _ = validate_registration({'username': 'alice1', 'email': 'a@b.com', 'password': 'Pass1234'})\n    assert ok is True\n    ok2, err2 = validate_registration({'username': 'al!ce', 'email': 'a@b.com', 'password': 'Pass1234'})\n    assert ok2 is False and 'username' in err2.lower()\n    ok3, err3 = validate_registration({'username': 'alice1', 'email': 'invalid', 'password': 'Pass1234'})\n    assert ok3 is False and 'email' in err3.lower()\n    ok4, err4 = validate_registration({'username': 'alice1', 'email': 'a@b.com', 'password': 'short'})\n    assert ok4 is False and 'password' in err4.lower()\n"
        },
        "expected_files": ["validator.py"],
        "reference_fix": {
            "validator.py": "import re\ndef validate_registration(data: dict) -> tuple[bool, str]:\n    u = data.get('username', '')\n    if not u.isalnum():\n        return False, 'Invalid username: must be alphanumeric'\n    e = data.get('email', '')\n    if not re.match(r'^[^@]+@[^@]+\\.[^@]+$', e):\n        return False, 'Invalid email address'\n    p = data.get('password', '')\n    if len(p) < 8 or not any(c.isdigit() for c in p):\n        return False, 'Invalid password: must be at least 8 chars and contain a digit'\n    return True, ''\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-04",
        "name": "Nested Dictionary Flattener",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Python",
        "subcategory": "Data processing",
        "description": "In flattener.py, flatten_dict() should recursively flatten nested dicts using a custom delimiter like 'a.b.c'.",
        "initial_files": {
            "flattener.py": "def flatten_dict(d: dict, delimiter: str = '.') -> dict:\n    # Unimplemented\n    return d\n"
        },
        "test_files": {
            "test_flattener.py": "from flattener import flatten_dict\ndef test_flatten_nested():\n    inp = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}\n    exp = {'a': 1, 'b.c': 2, 'b.d.e': 3}\n    assert flatten_dict(inp) == exp\n    assert flatten_dict({'x': {'y': 10}}, delimiter='/') == {'x/y': 10}\n"
        },
        "expected_files": ["flattener.py"],
        "reference_fix": {
            "flattener.py": "def flatten_dict(d: dict, delimiter: str = '.') -> dict:\n    out = {}\n    def _walk(sub, prefix):\n        for k, v in sub.items():\n            new_key = f'{prefix}{delimiter}{k}' if prefix else k\n            if isinstance(v, dict) and v:\n                _walk(v, new_key)\n            else:\n                out[new_key] = v\n    _walk(d, '')\n    return out\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-05",
        "name": "Imperative Loop to Functional Pipeline Refactoring",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Python",
        "subcategory": "Function refactoring",
        "description": "In pipeline.py, extract_active_user_emails() must filter active users, normalize emails to lowercase, deduplicate, and sort alphabetically.",
        "initial_files": {
            "pipeline.py": "def extract_active_user_emails(users: list[dict]) -> list[str]:\n    # Buggy imperative implementation misses deduplication and sorting\n    res = []\n    for u in users:\n        if u.get('is_active'):\n            res.append(u.get('email', ''))\n    return res\n"
        },
        "test_files": {
            "test_pipeline.py": "from pipeline import extract_active_user_emails\ndef test_pipeline():\n    users = [\n        {'email': 'Bob@example.com', 'is_active': True},\n        {'email': 'alice@example.com', 'is_active': True},\n        {'email': 'charlie@example.com', 'is_active': False},\n        {'email': 'bob@example.com', 'is_active': True},\n    ]\n    assert extract_active_user_emails(users) == ['alice@example.com', 'bob@example.com']\n"
        },
        "expected_files": ["pipeline.py"],
        "reference_fix": {
            "pipeline.py": "def extract_active_user_emails(users: list[dict]) -> list[str]:\n    return sorted(list({u['email'].strip().lower() for u in users if u.get('is_active') and u.get('email')}))\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-06",
        "name": "LRU Cache Data Structure",
        "language": "python",
        "difficulty": "HARD",
        "category": "Python",
        "subcategory": "Class implementation",
        "description": "In cache.py, implement LRUCache class with get(key) and put(key, val) evicting least recently used items at capacity.",
        "initial_files": {
            "cache.py": "class LRUCache:\n    def __init__(self, capacity: int):\n        self.capacity = capacity\n    def get(self, key: str):\n        return None\n    def put(self, key: str, value: any) -> None:\n        pass\n"
        },
        "test_files": {
            "test_cache.py": "from cache import LRUCache\ndef test_lru_cache():\n    c = LRUCache(2)\n    c.put('a', 1)\n    c.put('b', 2)\n    assert c.get('a') == 1\n    c.put('c', 3)  # evicts 'b'\n    assert c.get('b') is None\n    assert c.get('a') == 1\n    assert c.get('c') == 3\n"
        },
        "expected_files": ["cache.py"],
        "reference_fix": {
            "cache.py": "from collections import OrderedDict\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.capacity = capacity\n        self.cache = OrderedDict()\n    def get(self, key: str):\n        if key not in self.cache:\n            return None\n        self.cache.move_to_end(key)\n        return self.cache[key]\n    def put(self, key: str, value: any) -> None:\n        if key in self.cache:\n            self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.capacity:\n            self.cache.popitem(last=False)\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-07",
        "name": "Safe Deep Attribute Path Accessor",
        "language": "python",
        "difficulty": "EASY",
        "category": "Python",
        "subcategory": "Type errors",
        "description": "In safe_accessor.py, safe_get() raises TypeError when encountering None intermediate values. Fix to return default gracefully.",
        "initial_files": {
            "safe_accessor.py": "def safe_get(obj: dict, path: list[str], default=None):\n    curr = obj\n    for p in path:\n        curr = curr[p]  # Crashes if curr is None\n    return curr\n"
        },
        "test_files": {
            "test_safe_accessor.py": "from safe_accessor import safe_get\ndef test_safe_get():\n    data = {'user': {'profile': None}}\n    assert safe_get(data, ['user', 'profile', 'bio'], 'N/A') == 'N/A'\n    assert safe_get(data, ['user', 'nonexistent'], 'missing') == 'missing'\n    data2 = {'user': {'profile': {'bio': 'Developer'}}}\n    assert safe_get(data2, ['user', 'profile', 'bio'], 'N/A') == 'Developer'\n"
        },
        "expected_files": ["safe_accessor.py"],
        "reference_fix": {
            "safe_accessor.py": "def safe_get(obj: dict, path: list[str], default=None):\n    curr = obj\n    for p in path:\n        if not isinstance(curr, dict) or p not in curr:\n            return default\n        curr = curr[p]\n    return curr if curr is not None else default\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-08",
        "name": "Binary Search Boundary and Empty Slice Handling",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Python",
        "subcategory": "Boundary conditions",
        "description": "In search.py, binary_search() has an infinite loop on missing elements and off-by-one errors on boundary targets.",
        "initial_files": {
            "search.py": "def binary_search(arr: list[int], target: int) -> int:\n    low = 0\n    high = len(arr)\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid\n        else:\n            high = mid\n    return -1\n"
        },
        "test_files": {
            "test_search.py": "from search import binary_search\ndef test_binary_search():\n    assert binary_search([], 5) == -1\n    assert binary_search([1, 3, 5, 7, 9], 1) == 0\n    assert binary_search([1, 3, 5, 7, 9], 9) == 4\n    assert binary_search([1, 3, 5, 7, 9], 5) == 2\n    assert binary_search([1, 3, 5, 7, 9], 4) == -1\n"
        },
        "expected_files": ["search.py"],
        "reference_fix": {
            "search.py": "def binary_search(arr: list[int], target: int) -> int:\n    low = 0\n    high = len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n"
        },
        "is_held_out": False
    },
    {
        "id": "py-09",
        "name": "ISO Timestamp Normalizer and UTC Conversion",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Python",
        "subcategory": "Regression defects",
        "description": "In date_utils.py, normalize_to_utc() fails on timezone offsets like +02:00 or trailing 'Z'. Normalize output to UTC ISO format.",
        "initial_files": {
            "date_utils.py": "from datetime import datetime\ndef normalize_to_utc(iso_str: str) -> str:\n    # naive implementation\n    return iso_str\n"
        },
        "test_files": {
            "test_date_utils.py": "from date_utils import normalize_to_utc\ndef test_utc_normalization():\n    res1 = normalize_to_utc('2026-11-21T15:00:00Z')\n    assert res1.startswith('2026-11-21T15:00:00')\n    res2 = normalize_to_utc('2026-11-21T17:00:00+02:00')\n    assert '15:00:00' in res2\n"
        },
        "expected_files": ["date_utils.py"],
        "reference_fix": {
            "date_utils.py": "from datetime import datetime, timezone\ndef normalize_to_utc(iso_str: str) -> str:\n    dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))\n    utc_dt = dt.astimezone(timezone.utc)\n    return utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')\n"
        },
        "is_held_out": True
    },
    {
        "id": "py-10",
        "name": "Dynamic Settings Hierarchy and Env Override",
        "language": "python",
        "difficulty": "HARD",
        "category": "Python",
        "subcategory": "Multi-module bugs",
        "description": "In config_loader.py, load_merged_settings() must merge default_dict with env_overrides and convert numeric values.",
        "initial_files": {
            "config_loader.py": "def load_merged_settings(defaults: dict, overrides: dict) -> dict:\n    # Buggy shallow copy without type conversion\n    out = defaults.copy()\n    out.update(overrides)\n    return out\n"
        },
        "test_files": {
            "test_config_loader.py": "from config_loader import load_merged_settings\ndef test_merged_settings():\n    defs = {'HOST': 'localhost', 'PORT': 8000, 'DEBUG': False}\n    envs = {'PORT': '9000', 'DEBUG': 'true'}\n    merged = load_merged_settings(defs, envs)\n    assert merged['HOST'] == 'localhost'\n    assert merged['PORT'] == 9000\n    assert merged['DEBUG'] is True\n"
        },
        "expected_files": ["config_loader.py"],
        "reference_fix": {
            "config_loader.py": "def load_merged_settings(defaults: dict, overrides: dict) -> dict:\n    out = defaults.copy()\n    for k, v in overrides.items():\n        if k in defaults:\n            orig_t = type(defaults[k])\n            if orig_t is bool:\n                out[k] = str(v).lower() in ('true', '1', 'yes')\n            elif orig_t is int:\n                out[k] = int(v)\n            else:\n                out[k] = v\n        else:\n            out[k] = v\n    return out\n"
        },
        "is_held_out": True
    },

    # =========================================================================
    # CATEGORY 2: JAVASCRIPT & TYPESCRIPT (10 Tasks: js-01 to ts-10)
    # =========================================================================
    {
        "id": "js-01",
        "name": "Async Sequence Order Checkout Race Condition",
        "language": "javascript",
        "difficulty": "MEDIUM",
        "category": "JavaScript and TypeScript",
        "subcategory": "Incorrect asynchronous behavior",
        "description": "In checkout.js, processSteps() executes steps in parallel with forEach instead of sequentially awaiting each step.",
        "initial_files": {
            "checkout.js": "async function processSteps(steps, context) {\n    const logs = [];\n    // Bug: forEach does not await async callback\n    steps.forEach(async (step) => {\n        const res = await step(context);\n        logs.push(res);\n    });\n    return logs;\n}\nmodule.exports = { processSteps };\n"
        },
        "test_files": {
            "test_checkout.py": "import subprocess, json\ndef test_checkout():\n    node_code = '''\n    const { processSteps } = require('./checkout.js');\n    async function run() {\n        const step1 = async () => { await new Promise(r => setTimeout(r, 10)); return 'A'; };\n        const step2 = async () => { return 'B'; };\n        const res = await processSteps([step1, step2], {});\n        console.log(JSON.stringify(res));\n    }\n    run();\n    '''\n    out = subprocess.check_output(['node', '-e', node_code]).decode().strip()\n    assert json.loads(out) == ['A', 'B']\n"
        },
        "expected_files": ["checkout.js"],
        "reference_fix": {
            "checkout.js": "async function processSteps(steps, context) {\n    const logs = [];\n    for (const step of steps) {\n        const res = await step(context);\n        logs.push(res);\n    }\n    return logs;\n}\nmodule.exports = { processSteps };\n"
        },
        "is_held_out": False
    },
    {
        "id": "js-02",
        "name": "Promise Settlement Error Containment",
        "language": "javascript",
        "difficulty": "MEDIUM",
        "category": "JavaScript and TypeScript",
        "subcategory": "Promise handling",
        "description": "In batch_runner.js, runBatch() must resolve all promises and return { success: [], errors: [] } without unhandled rejections.",
        "initial_files": {
            "batch_runner.js": "async function runBatch(tasks) {\n    // Bug: Promise.all rejects immediately on first error\n    const results = await Promise.all(tasks.map(t => t()));\n    return { success: results, errors: [] };\n}\nmodule.exports = { runBatch };\n"
        },
        "test_files": {
            "test_batch_runner.py": "import subprocess, json\ndef test_batch():\n    code = '''\n    const { runBatch } = require('./batch_runner.js');\n    async function test() {\n        const t1 = async () => 'OK1';\n        const t2 = async () => { throw new Error('ERR2'); };\n        const t3 = async () => 'OK3';\n        const res = await runBatch([t1, t2, t3]);\n        console.log(JSON.stringify(res));\n    }\n    test();\n    '''\n    out = subprocess.check_output(['node', '-e', code]).decode().strip()\n    data = json.loads(out)\n    assert data['success'] == ['OK1', 'OK3']\n    assert len(data['errors']) == 1\n"
        },
        "expected_files": ["batch_runner.js"],
        "reference_fix": {
            "batch_runner.js": "async function runBatch(tasks) {\n    const settled = await Promise.allSettled(tasks.map(t => t()));\n    const success = [];\n    const errors = [];\n    settled.forEach(r => {\n        if (r.status === 'fulfilled') success.push(r.value);\n        else errors.push(r.reason?.message || String(r.reason));\n    });\n    return { success, errors };\n}\nmodule.exports = { runBatch };\n"
        },
        "is_held_out": False
    },
    {
        "id": "ts-03",
        "name": "Discriminated Union Payment Handler",
        "language": "typescript",
        "difficulty": "MEDIUM",
        "category": "JavaScript and TypeScript",
        "subcategory": "TypeScript errors",
        "description": "In payment.ts, handlePayment() has missing exhaustive check and type errors for 'crypto' payment type.",
        "initial_files": {
            "payment.ts": "type Payment = \n  | { type: 'credit_card'; cardNumber: string; amount: number }\n  | { type: 'paypal'; email: string; amount: number }\n  | { type: 'crypto'; walletAddress: string; amount: number };\n\nexport function handlePayment(p: Payment): string {\n  if (p.type === 'credit_card') return `Card:${p.cardNumber}:${p.amount}`;\n  if (p.type === 'paypal') return `PayPal:${p.email}:${p.amount}`;\n  return '';\n}\n"
        },
        "test_files": {
            "test_payment.py": "import subprocess\ndef test_payment():\n    code = '''\n    const { handlePayment } = require('./payment.js');\n    const res = handlePayment({ type: 'crypto', walletAddress: '0xABC', amount: 50 });\n    if (res !== 'Crypto:0xABC:50') process.exit(1);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["payment.ts"],
        "reference_fix": {
            "payment.ts": "type Payment = \n  | { type: 'credit_card'; cardNumber: string; amount: number }\n  | { type: 'paypal'; email: string; amount: number }\n  | { type: 'crypto'; walletAddress: string; amount: number };\n\nexport function handlePayment(p: Payment): string {\n  switch (p.type) {\n    case 'credit_card': return `Card:${p.cardNumber}:${p.amount}`;\n    case 'paypal': return `PayPal:${p.email}:${p.amount}`;\n    case 'crypto': return `Crypto:${p.walletAddress}:${p.amount}`;\n  }\n}\n"
        },
        "is_held_out": False
    },
    {
        "id": "js-04",
        "name": "Deep Group-By and Aggregator Utility",
        "language": "javascript",
        "difficulty": "EASY",
        "category": "JavaScript and TypeScript",
        "subcategory": "Array transformations",
        "description": "In group_by.js, groupBy() must group objects by a key or key accessor function into a plain JavaScript object.",
        "initial_files": {
            "group_by.js": "function groupBy(items, keySelector) {\n    // Bug: returns empty\n    return {};\n}\nmodule.exports = { groupBy };\n"
        },
        "test_files": {
            "test_group_by.py": "import subprocess, json\ndef test_group():\n    code = '''\n    const { groupBy } = require('./group_by.js');\n    const data = [{ tag: 'A', v: 1 }, { tag: 'B', v: 2 }, { tag: 'A', v: 3 }];\n    const res = groupBy(data, x => x.tag);\n    console.log(JSON.stringify(res));\n    '''\n    out = subprocess.check_output(['node', '-e', code]).decode().strip()\n    obj = json.loads(out)\n    assert len(obj['A']) == 2\n    assert len(obj['B']) == 1\n"
        },
        "expected_files": ["group_by.js"],
        "reference_fix": {
            "group_by.js": "function groupBy(items, keySelector) {\n    const fn = typeof keySelector === 'function' ? keySelector : (x => x[keySelector]);\n    const res = {};\n    for (const item of items) {\n        const k = String(fn(item));\n        if (!res[k]) res[k] = [];\n        res[k].push(item);\n    }\n    return res;\n}\nmodule.exports = { groupBy };\n"
        },
        "is_held_out": False
    },
    {
        "id": "ts-05",
        "name": "Immutable Nested Cart State Updater",
        "language": "typescript",
        "difficulty": "MEDIUM",
        "category": "JavaScript and TypeScript",
        "subcategory": "State-management bugs",
        "description": "In cart_state.ts, updateQuantity() mutates the existing state array in place. Fix to return a new immutable copy.",
        "initial_files": {
            "cart_state.ts": "export interface CartItem { id: string; qty: number; }\nexport interface CartState { items: CartItem[]; updatedAt: number; }\nexport function updateQuantity(state: CartState, id: string, qty: number): CartState {\n    const it = state.items.find(x => x.id === id);\n    if (it) it.qty = qty; // Mutation bug!\n    return state;\n}\n"
        },
        "test_files": {
            "test_cart_state.py": "import subprocess\ndef test_cart_immutability():\n    code = '''\n    const { updateQuantity } = require('./cart_state.js');\n    const initial = { items: [{ id: '1', qty: 2 }], updatedAt: 100 };\n    const updated = updateQuantity(initial, '1', 5);\n    if (initial === updated) process.exit(1); // must be new reference\n    if (initial.items[0].qty !== 2) process.exit(2); // must not mutate original\n    if (updated.items[0].qty !== 5) process.exit(3);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["cart_state.ts"],
        "reference_fix": {
            "cart_state.ts": "export interface CartItem { id: string; qty: number; }\nexport interface CartState { items: CartItem[]; updatedAt: number; }\nexport function updateQuantity(state: CartState, id: string, qty: number): CartState {\n    return {\n        ...state,\n        updatedAt: Date.now(),\n        items: state.items.map(it => it.id === id ? { ...it, qty } : it)\n    };\n}\n"
        },
        "is_held_out": False
    },
    {
        "id": "js-06",
        "name": "Custom AppError Subclass Prototype Preservation",
        "language": "javascript",
        "difficulty": "EASY",
        "category": "JavaScript and TypeScript",
        "subcategory": "Error handling",
        "description": "In errors.js, AppError does not set prototype correctly, failing instanceof checks and missing statusCode.",
        "initial_files": {
            "errors.js": "function AppError(message, statusCode) {\n    this.message = message;\n    this.statusCode = statusCode;\n}\nmodule.exports = { AppError };\n"
        },
        "test_files": {
            "test_errors.py": "import subprocess\ndef test_app_error():\n    code = '''\n    const { AppError } = require('./errors.js');\n    const err = new AppError('Forbidden', 403);\n    if (!(err instanceof Error)) process.exit(1);\n    if (err.statusCode !== 403) process.exit(2);\n    if (err.name !== 'AppError') process.exit(3);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["errors.js"],
        "reference_fix": {
            "errors.js": "class AppError extends Error {\n    constructor(message, statusCode = 500) {\n        super(message);\n        this.name = 'AppError';\n        this.statusCode = statusCode;\n        if (Error.captureStackTrace) Error.captureStackTrace(this, AppError);\n    }\n}\nmodule.exports = { AppError };\n"
        },
        "is_held_out": False
    },
    {
        "id": "ts-07",
        "name": "Debounce Utility with Immediate Execution and Cancel",
        "language": "typescript",
        "difficulty": "MEDIUM",
        "category": "JavaScript and TypeScript",
        "subcategory": "Function implementation",
        "description": "In debounce.ts, debounce() must delay invocation, support immediate=true flag, and expose a .cancel() method.",
        "initial_files": {
            "debounce.ts": "export function debounce(fn: Function, wait: number, immediate: boolean = false) {\n    let timer: any = null;\n    const debounced = function(...args: any[]) {\n        clearTimeout(timer);\n        timer = setTimeout(() => fn(...args), wait);\n    };\n    debounced.cancel = () => clearTimeout(timer);\n    return debounced;\n}\n"
        },
        "test_files": {
            "test_debounce.py": "import subprocess\ndef test_debounce():\n    code = '''\n    const { debounce } = require('./debounce.js');\n    let calls = 0;\n    const fn = debounce(() => { calls++; }, 50, true);\n    fn();\n    fn();\n    if (calls !== 1) process.exit(1); // immediate flag invoked once\n    fn.cancel();\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["debounce.ts"],
        "reference_fix": {
            "debounce.ts": "export function debounce(fn: Function, wait: number, immediate: boolean = false) {\n    let timer: any = null;\n    const debounced: any = function(...args: any[]) {\n        const callNow = immediate && !timer;\n        clearTimeout(timer);\n        timer = setTimeout(() => {\n            timer = null;\n            if (!immediate) fn(...args);\n        }, wait);\n        if (callNow) fn(...args);\n    };\n    debounced.cancel = () => {\n        clearTimeout(timer);\n        timer = null;\n    };\n    return debounced;\n}\n"
        },
        "is_held_out": False
    },
    {
        "id": "js-08",
        "name": "Circular Module Export Resolution via Late Getter",
        "language": "javascript",
        "difficulty": "HARD",
        "category": "JavaScript and TypeScript",
        "subcategory": "Dependency issues",
        "description": "In service_b.js, cyclical require('./service_a') causes undefined reference during module evaluation.",
        "initial_files": {
            "service_a.js": "const b = require('./service_b');\nfunction a() { return 'A' + b.getB(); }\nmodule.exports = { a, getA: () => 'A' };\n",
            "service_b.js": "const a = require('./service_a');\nfunction b() { return 'B' + a.getA(); }\nmodule.exports = { b, getB: () => 'B' };\n"
        },
        "test_files": {
            "test_circular.py": "import subprocess\ndef test_circular_resolution():\n    code = '''\n    const sa = require('./service_a.js');\n    const sb = require('./service_b.js');\n    if (sa.a() !== 'AB') process.exit(1);\n    if (sb.b() !== 'BA') process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["service_b.js"],
        "reference_fix": {
            "service_b.js": "module.exports = {\n    b: () => 'B' + require('./service_a').getA(),\n    getB: () => 'B'\n};\n"
        },
        "is_held_out": False
    },
    {
        "id": "ts-09",
        "name": "Logger Adapter Pattern Interface Implementation",
        "language": "typescript",
        "difficulty": "EASY",
        "category": "JavaScript and TypeScript",
        "subcategory": "Module integration",
        "description": "In logger_adapter.ts, ConsoleLoggerAdapter must filter log messages below the minimum LogLevel.",
        "initial_files": {
            "logger_adapter.ts": "export enum LogLevel { DEBUG = 0, INFO = 1, WARN = 2, ERROR = 3 }\nexport class ConsoleLoggerAdapter {\n    constructor(private minLevel: LogLevel = LogLevel.INFO) {}\n    log(level: LogLevel, msg: string): boolean {\n        // Bug: logs everything\n        return true;\n    }\n}\n"
        },
        "test_files": {
            "test_logger_adapter.py": "import subprocess\ndef test_logger():\n    code = '''\n    const { ConsoleLoggerAdapter, LogLevel } = require('./logger_adapter.js');\n    const logger = new ConsoleLoggerAdapter(LogLevel.WARN);\n    if (logger.log(LogLevel.INFO, 'test') !== false) process.exit(1);\n    if (logger.log(LogLevel.ERROR, 'test') !== true) process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["logger_adapter.ts"],
        "reference_fix": {
            "logger_adapter.ts": "export enum LogLevel { DEBUG = 0, INFO = 1, WARN = 2, ERROR = 3 }\nexport class ConsoleLoggerAdapter {\n    constructor(private minLevel: LogLevel = LogLevel.INFO) {}\n    log(level: LogLevel, msg: string): boolean {\n        if (level < this.minLevel) return false;\n        return true;\n    }\n}\n"
        },
        "is_held_out": True
    },
    {
        "id": "ts-10",
        "name": "Client Server DTO Mismatch Schema Transformer",
        "language": "typescript",
        "difficulty": "MEDIUM",
        "category": "JavaScript and TypeScript",
        "subcategory": "Multi-file defects",
        "description": "In user_mapper.ts, transformServerUserToClient() must map snake_case created_at to camelCase createdAt and format roles.",
        "initial_files": {
            "user_mapper.ts": "export function transformServerUserToClient(s: any): any {\n    return s;\n}\n"
        },
        "test_files": {
            "test_user_mapper.py": "import subprocess, json\ndef test_mapper():\n    code = '''\n    const { transformServerUserToClient } = require('./user_mapper.js');\n    const server = { id: 'u1', first_name: 'John', created_at: 12345, roles: ['admin'] };\n    const client = transformServerUserToClient(server);\n    if (client.firstName !== 'John' || client.createdAt !== 12345) process.exit(1);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["user_mapper.ts"],
        "reference_fix": {
            "user_mapper.ts": "export function transformServerUserToClient(s: any): any {\n    return {\n        id: s.id,\n        firstName: s.first_name,\n        createdAt: s.created_at,\n        roles: Array.isArray(s.roles) ? [...s.roles] : []\n    };\n}\n"
        },
        "is_held_out": True
    },

    # =========================================================================
    # CATEGORY 3: BACKEND & API ENGINEERING (10 Tasks: api-01 to api-10)
    # =========================================================================
    {
        "id": "api-01",
        "name": "Standardized Error Response Envelope and HTTP Status",
        "language": "python",
        "difficulty": "EASY",
        "category": "Backend and API Engineering",
        "subcategory": "Incorrect API responses",
        "description": "In response_builder.py, build_error_response() returns 200 with error text. Update to return specified HTTP status code and standard JSON envelope.",
        "initial_files": {
            "response_builder.py": "def build_error_response(message: str, code: int = 400) -> tuple[dict, int]:\n    # Bug: returns HTTP 200\n    return {'error': message}, 200\n"
        },
        "test_files": {
            "test_response_builder.py": "from response_builder import build_error_response\ndef test_error_response():\n    body, status = build_error_response('Validation failed', 422)\n    assert status == 422\n    assert body == {'success': False, 'error': {'message': 'Validation failed', 'code': 422}}\n"
        },
        "expected_files": ["response_builder.py"],
        "reference_fix": {
            "response_builder.py": "def build_error_response(message: str, code: int = 400) -> tuple[dict, int]:\n    return {'success': False, 'error': {'message': message, 'code': code}}, code\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-02",
        "name": "Pagination Limit Bounds and Page Sanitization",
        "language": "python",
        "difficulty": "EASY",
        "category": "Backend and API Engineering",
        "subcategory": "Request validation",
        "description": "In request_params.py, sanitize_pagination() must ensure page >= 1, and limit is clamped between 1 and 100 with default 20.",
        "initial_files": {
            "request_params.py": "def sanitize_pagination(page: any, limit: any) -> tuple[int, int]:\n    # Unsanitized\n    return int(page), int(limit)\n"
        },
        "test_files": {
            "test_request_params.py": "from request_params import sanitize_pagination\ndef test_sanitization():\n    assert sanitize_pagination(-5, 500) == (1, 100)\n    assert sanitize_pagination('2', '15') == (2, 15)\n    assert sanitize_pagination(None, None) == (1, 20)\n"
        },
        "expected_files": ["request_params.py"],
        "reference_fix": {
            "request_params.py": "def sanitize_pagination(page: any, limit: any) -> tuple[int, int]:\n    try:\n        p = max(1, int(page))\n    except (TypeError, ValueError):\n        p = 1\n    try:\n        l = min(100, max(1, int(limit)))\n    except (TypeError, ValueError):\n        l = 20\n    return p, l\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-03",
        "name": "JWT Algorithm None Security Vulnerability Fix",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Backend and API Engineering",
        "subcategory": "Authentication logic",
        "description": "In auth_validator.py, verify_token_header() allows alg: 'none' or missing secret. Reject tokens without allowed HMAC-SHA256 signature.",
        "initial_files": {
            "auth_validator.py": "def verify_token_header(header: dict, secret: str) -> bool:\n    # Insecure: permits alg: none\n    if header.get('alg') == 'none':\n        return True\n    return bool(secret and header.get('alg') == 'HS256')\n"
        },
        "test_files": {
            "test_auth_validator.py": "from auth_validator import verify_token_header\ndef test_token_auth():\n    assert verify_token_header({'alg': 'none'}, 'secret') is False\n    assert verify_token_header({'alg': 'HS256'}, '') is False\n    assert verify_token_header({'alg': 'HS256'}, 'valid-secret') is True\n"
        },
        "expected_files": ["auth_validator.py"],
        "reference_fix": {
            "auth_validator.py": "def verify_token_header(header: dict, secret: str) -> bool:\n    if header.get('alg') != 'HS256':\n        return False\n    return bool(secret and len(secret) >= 8)\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-04",
        "name": "RBAC Multi-Tenant Tenant Isolation Checker",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Backend and API Engineering",
        "subcategory": "Authorization defects",
        "description": "In rbac.py, can_access_resource() checks user role but forgets to check matching tenant_id. Enforce strict tenant isolation.",
        "initial_files": {
            "rbac.py": "def can_access_resource(user: dict, resource: dict) -> bool:\n    # Bug: forgets tenant isolation\n    return 'ADMIN' in user.get('roles', [])\n"
        },
        "test_files": {
            "test_rbac.py": "from rbac import can_access_resource\ndef test_rbac():\n    admin_t1 = {'id': 'u1', 'tenant_id': 't1', 'roles': ['ADMIN']}\n    res_t1 = {'id': 'r1', 'tenant_id': 't1'}\n    res_t2 = {'id': 'r2', 'tenant_id': 't2'}\n    assert can_access_resource(admin_t1, res_t1) is True\n    assert can_access_resource(admin_t1, res_t2) is False  # Must not cross tenant boundary\n"
        },
        "expected_files": ["rbac.py"],
        "reference_fix": {
            "rbac.py": "def can_access_resource(user: dict, resource: dict) -> bool:\n    if user.get('tenant_id') != resource.get('tenant_id'):\n        return False\n    return 'ADMIN' in user.get('roles', [])\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-05",
        "name": "SQL Injection Prevention via Parameterized Queries",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Backend and API Engineering",
        "subcategory": "Database-query errors",
        "description": "In query_builder.py, build_user_query() string-interpolates raw user inputs. Convert to parameterized query tuple (sql, params).",
        "initial_files": {
            "query_builder.py": "def build_user_query(email: str, status: str) -> tuple[str, dict]:\n    # Vulnerable string concatenation\n    sql = f'SELECT * FROM users WHERE email = \\'{email}\\' AND status = \\'{status}\\''\n    return sql, {}\n"
        },
        "test_files": {
            "test_query_builder.py": "from query_builder import build_user_query\ndef test_parameterized():\n    sql, params = build_user_query(\"admin' OR 1=1;--\", 'active')\n    assert \"'\" not in sql\n    assert ':email' in sql and ':status' in sql\n    assert params['email'] == \"admin' OR 1=1;--\"\n    assert params['status'] == 'active'\n"
        },
        "expected_files": ["query_builder.py"],
        "reference_fix": {
            "query_builder.py": "def build_user_query(email: str, status: str) -> tuple[str, dict]:\n    sql = 'SELECT * FROM users WHERE email = :email AND status = :status'\n    return sql, {'email': email, 'status': status}\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-06",
        "name": "Cursor Pagination Boundary Deduplication",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Backend and API Engineering",
        "subcategory": "Pagination defects",
        "description": "In cursor_page.py, paginate_by_cursor() includes the cursor item twice. Exclusive boundary > instead of >=.",
        "initial_files": {
            "cursor_page.py": "def paginate_by_cursor(items: list[dict], cursor_id: int | None, limit: int) -> tuple[list[dict], int | None]:\n    # Bug: >= includes cursor itself\n    filtered = [x for x in items if cursor_id is None or x['id'] >= cursor_id]\n    res = filtered[:limit]\n    next_cursor = res[-1]['id'] if len(res) == limit else None\n    return res, next_cursor\n"
        },
        "test_files": {
            "test_cursor_page.py": "from cursor_page import paginate_by_cursor\ndef test_cursor():\n    items = [{'id': i} for i in range(1, 10)]\n    p1, c1 = paginate_by_cursor(items, None, 3)\n    assert [x['id'] for x in p1] == [1, 2, 3]\n    assert c1 == 3\n    p2, c2 = paginate_by_cursor(items, c1, 3)\n    assert [x['id'] for x in p2] == [4, 5, 6]\n"
        },
        "expected_files": ["cursor_page.py"],
        "reference_fix": {
            "cursor_page.py": "def paginate_by_cursor(items: list[dict], cursor_id: int | None, limit: int) -> tuple[list[dict], int | None]:\n    filtered = [x for x in items if cursor_id is None or x['id'] > cursor_id]\n    res = filtered[:limit]\n    next_cursor = res[-1]['id'] if len(res) == limit and len(filtered) > limit else None\n    return res, next_cursor\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-07",
        "name": "RFC 7807 Problem Details Error Formatter",
        "language": "python",
        "difficulty": "EASY",
        "category": "Backend and API Engineering",
        "subcategory": "Error-response handling",
        "description": "In problem_details.py, format_problem() must format standard RFC 7807 problem details dictionary.",
        "initial_files": {
            "problem_details.py": "def format_problem(status: int, title: str, detail: str, instance: str) -> dict:\n    return {'error': title}\n"
        },
        "test_files": {
            "test_problem_details.py": "from problem_details import format_problem\ndef test_rfc_7807():\n    res = format_problem(404, 'Not Found', 'User 123 not found', '/users/123')\n    assert res['status'] == 404\n    assert res['title'] == 'Not Found'\n    assert res['detail'] == 'User 123 not found'\n    assert res['instance'] == '/users/123'\n    assert res['type'] == 'about:blank'\n"
        },
        "expected_files": ["problem_details.py"],
        "reference_fix": {
            "problem_details.py": "def format_problem(status: int, title: str, detail: str, instance: str) -> dict:\n    return {\n        'type': 'about:blank',\n        'status': status,\n        'title': title,\n        'detail': detail,\n        'instance': instance\n    }\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-08",
        "name": "HTTP Client Retry Policy with Exponential Backoff",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Backend and API Engineering",
        "subcategory": "Service integration",
        "description": "In retry_policy.py, calculate_backoff() must compute base * (2 ** attempt) clamped to max_backoff.",
        "initial_files": {
            "retry_policy.py": "def calculate_backoff(attempt: int, base: float = 0.5, max_backoff: float = 10.0) -> float:\n    # Bug: linear backoff without max clamp\n    return attempt * base\n"
        },
        "test_files": {
            "test_retry_policy.py": "from retry_policy import calculate_backoff\ndef test_backoff():\n    assert calculate_backoff(0, 1.0, 10.0) == 1.0\n    assert calculate_backoff(1, 1.0, 10.0) == 2.0\n    assert calculate_backoff(2, 1.0, 10.0) == 4.0\n    assert calculate_backoff(10, 1.0, 10.0) == 10.0  # Clamped to max\n"
        },
        "expected_files": ["retry_policy.py"],
        "reference_fix": {
            "retry_policy.py": "def calculate_backoff(attempt: int, base: float = 0.5, max_backoff: float = 10.0) -> float:\n    raw = base * (2 ** attempt)\n    return min(raw, max_backoff)\n"
        },
        "is_held_out": False
    },
    {
        "id": "api-09",
        "name": "Cascade Delete and Foreign Key Reference Constraint",
        "language": "python",
        "difficulty": "HARD",
        "category": "Backend and API Engineering",
        "subcategory": "Data-model validation",
        "description": "In db_relations.py, delete_parent() must check for dependent children and raise DependencyError unless cascade=True.",
        "initial_files": {
            "db_relations.py": "class DependencyError(Exception): pass\ndef delete_parent(parent_id: str, children_table: list[dict], cascade: bool = False) -> list[dict]:\n    # Bug: deletes parent and leaves orphaned children without error\n    return children_table\n"
        },
        "test_files": {
            "test_db_relations.py": "import pytest\nfrom db_relations import delete_parent, DependencyError\ndef test_cascade_delete():\n    kids = [{'id': 'c1', 'parent_id': 'p1'}, {'id': 'c2', 'parent_id': 'p2'}]\n    with pytest.raises(DependencyError):\n        delete_parent('p1', kids, cascade=False)\n    remaining = delete_parent('p1', kids, cascade=True)\n    assert len(remaining) == 1 and remaining[0]['id'] == 'c2'\n"
        },
        "expected_files": ["db_relations.py"],
        "reference_fix": {
            "db_relations.py": "class DependencyError(Exception): pass\ndef delete_parent(parent_id: str, children_table: list[dict], cascade: bool = False) -> list[dict]:\n    has_children = any(c['parent_id'] == parent_id for c in children_table)\n    if has_children and not cascade:\n        raise DependencyError(f'Cannot delete parent {parent_id} with existing children')\n    return [c for c in children_table if c['parent_id'] != parent_id]\n"
        },
        "is_held_out": True
    },
    {
        "id": "api-10",
        "name": "API Route Backward Compatibility Serializer",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Backend and API Engineering",
        "subcategory": "API regression testing",
        "description": "In route_serializer.py, serialize_response() must include deprecated 'name' alias when requested by V1 client.",
        "initial_files": {
            "route_serializer.py": "def serialize_response(data: dict, api_version: int = 2) -> dict:\n    # Only returns v2 format\n    return {'first_name': data.get('first_name'), 'last_name': data.get('last_name')}\n"
        },
        "test_files": {
            "test_route_serializer.py": "from route_serializer import serialize_response\ndef test_v1_compatibility():\n    user = {'first_name': 'Jane', 'last_name': 'Doe'}\n    v2 = serialize_response(user, api_version=2)\n    assert 'name' not in v2\n    v1 = serialize_response(user, api_version=1)\n    assert v1['name'] == 'Jane Doe'\n    assert v1['first_name'] == 'Jane'\n"
        },
        "expected_files": ["route_serializer.py"],
        "reference_fix": {
            "route_serializer.py": "def serialize_response(data: dict, api_version: int = 2) -> dict:\n    res = {'first_name': data.get('first_name'), 'last_name': data.get('last_name')}\n    if api_version == 1:\n        res['name'] = f\"{data.get('first_name', '')} {data.get('last_name', '')}\".strip()\n    return res\n"
        },
        "is_held_out": True
    },

    # =========================================================================
    # CATEGORY 4: FRONTEND ENGINEERING (10 Tasks: fe-01 to fe-10)
    # =========================================================================
    {
        "id": "fe-01",
        "name": "React useEffect Stale Closure Timer Fix",
        "language": "javascript",
        "difficulty": "MEDIUM",
        "category": "Frontend Engineering",
        "subcategory": "React state issues",
        "description": "In timer_hook.js, useTimerCount() retains stale count in setInterval closure. Use functional state updater.",
        "initial_files": {
            "timer_hook.js": "function createTimerState(initialCount) {\n    let count = initialCount;\n    const listeners = [];\n    function setCount(updater) {\n        count = typeof updater === 'function' ? updater(count) : updater;\n        listeners.forEach(l => l(count));\n    }\n    function tickStale() {\n        // Bug: uses captured count instead of functional updater\n        setCount(count + 1);\n    }\n    return { getCount: () => count, tickStale, setCount };\n}\nmodule.exports = { createTimerState };\n"
        },
        "test_files": {
            "test_timer_hook.py": "import subprocess\ndef test_timer_closure():\n    code = '''\n    const { createTimerState } = require('./timer_hook.js');\n    const s = createTimerState(0);\n    s.tickStale();\n    s.tickStale();\n    if (s.getCount() !== 2) process.exit(1);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["timer_hook.js"],
        "reference_fix": {
            "timer_hook.js": "function createTimerState(initialCount) {\n    let count = initialCount;\n    const listeners = [];\n    function setCount(updater) {\n        count = typeof updater === 'function' ? updater(count) : updater;\n        listeners.forEach(l => l(count));\n    }\n    function tickStale() {\n        setCount(prev => prev + 1);\n    }\n    return { getCount: () => count, tickStale, setCount };\n}\nmodule.exports = { createTimerState };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-02",
        "name": "Component Rendering Null Pointer Avatar Guard",
        "language": "javascript",
        "difficulty": "EASY",
        "category": "Frontend Engineering",
        "subcategory": "Component rendering",
        "description": "In render_card.js, renderUserCard() crashes on undefined avatar or user object. Provide safe fallback image.",
        "initial_files": {
            "render_card.js": "function renderUserCard(user) {\n    // Bug: throws TypeError if user.profile is null\n    return `<div class=\"card\"><img src=\"${user.profile.avatar.url}\"/><h3>${user.name}</h3></div>`;\n}\nmodule.exports = { renderUserCard };\n"
        },
        "test_files": {
            "test_render_card.py": "import subprocess\ndef test_card_guard():\n    code = '''\n    const { renderUserCard } = require('./render_card.js');\n    const out1 = renderUserCard({ name: 'Alice', profile: null });\n    if (!out1.includes('placeholder.png')) process.exit(1);\n    const out2 = renderUserCard({ name: 'Bob', profile: { avatar: { url: 'bob.jpg' } } });\n    if (!out2.includes('bob.jpg')) process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["render_card.js"],
        "reference_fix": {
            "render_card.js": "function renderUserCard(user) {\n    const name = user?.name || 'Anonymous';\n    const avatar = user?.profile?.avatar?.url || '/images/placeholder.png';\n    return `<div class=\"card\"><img src=\"${avatar}\"/><h3>${name}</h3></div>`;\n}\nmodule.exports = { renderUserCard };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-03",
        "name": "Reactive Form Validator State Feedback",
        "language": "javascript",
        "difficulty": "MEDIUM",
        "category": "Frontend Engineering",
        "subcategory": "Form validation",
        "description": "In form_state.js, validateForm() must return isValid boolean and map of errors for touched fields.",
        "initial_files": {
            "form_state.js": "function validateForm(values) {\n    return { isValid: true, errors: {} };\n}\nmodule.exports = { validateForm };\n"
        },
        "test_files": {
            "test_form_state.py": "import subprocess, json\ndef test_form_val():\n    code = '''\n    const { validateForm } = require('./form_state.js');\n    const res = validateForm({ email: 'bad', age: 15 });\n    console.log(JSON.stringify(res));\n    '''\n    out = subprocess.check_output(['node', '-e', code]).decode().strip()\n    data = json.loads(out)\n    assert data['isValid'] is False\n    assert 'email' in data['errors'] and 'age' in data['errors']\n"
        },
        "expected_files": ["form_state.js"],
        "reference_fix": {
            "form_state.js": "function validateForm(values) {\n    const errors = {};\n    if (!values?.email || !values.email.includes('@')) errors.email = 'Valid email required';\n    if (!values?.age || values.age < 18) errors.age = 'Must be at least 18';\n    return { isValid: Object.keys(errors).length === 0, errors };\n}\nmodule.exports = { validateForm };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-04",
        "name": "AbortController Cleanup on Component Unmount",
        "language": "javascript",
        "difficulty": "MEDIUM",
        "category": "Frontend Engineering",
        "subcategory": "API integration",
        "description": "In fetch_manager.js, createFetchSession() must return an abort() function and flag cancelled requests as aborted.",
        "initial_files": {
            "fetch_manager.js": "function createFetchSession() {\n    return { abort: () => {}, isAborted: () => false };\n}\nmodule.exports = { createFetchSession };\n"
        },
        "test_files": {
            "test_fetch_manager.py": "import subprocess\ndef test_abort():\n    code = '''\n    const { createFetchSession } = require('./fetch_manager.js');\n    const session = createFetchSession();\n    if (session.isAborted()) process.exit(1);\n    session.abort();\n    if (!session.isAborted()) process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["fetch_manager.js"],
        "reference_fix": {
            "fetch_manager.js": "function createFetchSession() {\n    let aborted = false;\n    return {\n        abort: () => { aborted = true; },\n        isAborted: () => aborted\n    };\n}\nmodule.exports = { createFetchSession };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-05",
        "name": "Skeleton Loader Flicker Threshold Delay",
        "language": "javascript",
        "difficulty": "EASY",
        "category": "Frontend Engineering",
        "subcategory": "Loading states",
        "description": "In loading_helper.js, shouldShowSkeleton() prevents flash of loading skeleton if response completes under minDelayMs.",
        "initial_files": {
            "loading_helper.js": "function shouldShowSkeleton(elapsedMs, minDelayMs = 200) {\n    return true;\n}\nmodule.exports = { shouldShowSkeleton };\n"
        },
        "test_files": {
            "test_loading_helper.py": "import subprocess\ndef test_skeleton():\n    code = '''\n    const { shouldShowSkeleton } = require('./loading_helper.js');\n    if (shouldShowSkeleton(50, 200) !== false) process.exit(1);\n    if (shouldShowSkeleton(250, 200) !== true) process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["loading_helper.js"],
        "reference_fix": {
            "loading_helper.js": "function shouldShowSkeleton(elapsedMs, minDelayMs = 200) {\n    return elapsedMs >= minDelayMs;\n}\nmodule.exports = { shouldShowSkeleton };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-06",
        "name": "Error Boundary Fallback State Reset",
        "language": "javascript",
        "difficulty": "MEDIUM",
        "category": "Frontend Engineering",
        "subcategory": "Error states",
        "description": "In error_boundary_state.js, createBoundary() must catch error and allow resetError() to restore normal state.",
        "initial_files": {
            "error_boundary_state.js": "function createBoundary() {\n    let hasError = false;\n    return { hasError: () => hasError };\n}\nmodule.exports = { createBoundary };\n"
        },
        "test_files": {
            "test_error_boundary.py": "import subprocess\ndef test_boundary():\n    code = '''\n    const { createBoundary } = require('./error_boundary_state.js');\n    const b = createBoundary();\n    b.catchError(new Error('Crash'));\n    if (!b.hasError()) process.exit(1);\n    b.resetError();\n    if (b.hasError()) process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["error_boundary_state.js"],
        "reference_fix": {
            "error_boundary_state.js": "function createBoundary() {\n    let error = null;\n    return {\n        hasError: () => error !== null,\n        catchError: (err) => { error = err; },\n        resetError: () => { error = null; }\n    };\n}\nmodule.exports = { createBoundary };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-07",
        "name": "Viewport Resize Listener Registration Cleanup",
        "language": "javascript",
        "difficulty": "EASY",
        "category": "Frontend Engineering",
        "subcategory": "Responsive behavior",
        "description": "In resize_tracker.js, subscribeResize() must return an unsubscribe cleanup function to prevent memory leaks.",
        "initial_files": {
            "resize_tracker.js": "function createResizeTracker() {\n    const listeners = [];\n    function subscribe(cb) { listeners.push(cb); }\n    return { subscribe, getListenerCount: () => listeners.length };\n}\nmodule.exports = { createResizeTracker };\n"
        },
        "test_files": {
            "test_resize_tracker.py": "import subprocess\ndef test_resize_cleanup():\n    code = '''\n    const { createResizeTracker } = require('./resize_tracker.js');\n    const tracker = createResizeTracker();\n    const unsub = tracker.subscribe(() => {});\n    if (tracker.getListenerCount() !== 1) process.exit(1);\n    unsub();\n    if (tracker.getListenerCount() !== 0) process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["resize_tracker.js"],
        "reference_fix": {
            "resize_tracker.js": "function createResizeTracker() {\n    let listeners = [];\n    function subscribe(cb) {\n        listeners.push(cb);\n        return () => {\n            listeners = listeners.filter(l => l !== cb);\n        };\n    }\n    return { subscribe, getListenerCount: () => listeners.length };\n}\nmodule.exports = { createResizeTracker };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-08",
        "name": "Modal Overlay Synthetic Event Propagation Guard",
        "language": "javascript",
        "difficulty": "EASY",
        "category": "Frontend Engineering",
        "subcategory": "Event handling",
        "description": "In modal_events.js, handleModalClick() must invoke stopPropagation() when clicking modal content.",
        "initial_files": {
            "modal_events.js": "function handleModalClick(event, isContentClick) {\n    // Bug: does not stop propagation\n}\nmodule.exports = { handleModalClick };\n"
        },
        "test_files": {
            "test_modal_events.py": "import subprocess\ndef test_modal():\n    code = '''\n    const { handleModalClick } = require('./modal_events.js');\n    let stopped = false;\n    const mockEvent = { stopPropagation: () => { stopped = true; } };\n    handleModalClick(mockEvent, true);\n    if (!stopped) process.exit(1);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["modal_events.js"],
        "reference_fix": {
            "modal_events.js": "function handleModalClick(event, isContentClick) {\n    if (isContentClick && event?.stopPropagation) {\n        event.stopPropagation();\n    }\n}\nmodule.exports = { handleModalClick };\n"
        },
        "is_held_out": False
    },
    {
        "id": "fe-09",
        "name": "Generic Component Table Key Inference",
        "language": "typescript",
        "difficulty": "MEDIUM",
        "category": "Frontend Engineering",
        "subcategory": "TypeScript component errors",
        "description": "In table_keys.ts, extractRowKey() must safely extract key field from generic row object or fallback to index.",
        "initial_files": {
            "table_keys.ts": "export function extractRowKey<T>(row: T, keyField: keyof T, index: number): string {\n    return '';\n}\n"
        },
        "test_files": {
            "test_table_keys.py": "import subprocess\ndef test_keys():\n    code = '''\n    const { extractRowKey } = require('./table_keys.js');\n    const row = { id: 42, name: 'Test' };\n    if (extractRowKey(row, 'id', 0) !== '42') process.exit(1);\n    if (extractRowKey(row, 'missing', 5) !== 'row-5') process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["table_keys.ts"],
        "reference_fix": {
            "table_keys.ts": "export function extractRowKey<T>(row: T, keyField: keyof T, index: number): string {\n    if (row && (row as any)[keyField] !== undefined) {\n        return String((row as any)[keyField]);\n    }\n    return `row-${index}`;\n}\n"
        },
        "is_held_out": True
    },
    {
        "id": "fe-10",
        "name": "Accordion Accessible Keyboard Navigation and ARIA",
        "language": "javascript",
        "difficulty": "EASY",
        "category": "Frontend Engineering",
        "subcategory": "Accessibility defects",
        "description": "In accordion_a11y.js, getAccordionProps() must return aria-expanded boolean and handle Enter or Space keypress.",
        "initial_files": {
            "accordion_a11y.js": "function getAccordionProps(isOpen) {\n    return {};\n}\nmodule.exports = { getAccordionProps };\n"
        },
        "test_files": {
            "test_accordion_a11y.py": "import subprocess, json\ndef test_a11y():\n    code = '''\n    const { getAccordionProps } = require('./accordion_a11y.js');\n    const props = getAccordionProps(true);\n    if (props['aria-expanded'] !== true) process.exit(1);\n    if (props['role'] !== 'button') process.exit(2);\n    '''\n    subprocess.check_call(['node', '-e', code])\n"
        },
        "expected_files": ["accordion_a11y.js"],
        "reference_fix": {
            "accordion_a11y.js": "function getAccordionProps(isOpen) {\n    return {\n        'role': 'button',\n        'aria-expanded': Boolean(isOpen),\n        'tabIndex': 0\n    };\n}\nmodule.exports = { getAccordionProps };\n"
        },
        "is_held_out": True
    },

    # =========================================================================
    # CATEGORY 5: ADVANCED SOFTWARE ENGINEERING (10 Tasks: adv-01 to adv-10)
    # =========================================================================
    {
        "id": "adv-01",
        "name": "Decouple Storage Repository Interface from Filesystem",
        "language": "python",
        "difficulty": "HARD",
        "category": "Advanced Software Engineering",
        "subcategory": "Multi-file refactoring",
        "description": "Refactor storage.py and repository.py so Repository depends on abstract IStorage interface rather than hardcoded disk file calls.",
        "initial_files": {
            "storage_interface.py": "from abc import ABC, abstractmethod\nclass IStorage(ABC):\n    @abstractmethod\n    def read(self, key: str) -> str: pass\n    @abstractmethod\n    def write(self, key: str, val: str) -> None: pass\n",
            "memory_storage.py": "from storage_interface import IStorage\nclass MemoryStorage(IStorage):\n    def __init__(self):\n        self.store = {}\n    def read(self, key: str) -> str:\n        return self.store.get(key, '')\n    def write(self, key: str, val: str) -> None:\n        self.store[key] = val\n",
            "repository.py": "class ItemRepository:\n    def __init__(self):\n        # Bug: hardcoded to dict instead of IStorage\n        self.data = {}\n    def save_item(self, item_id: str, payload: str):\n        self.data[item_id] = payload\n    def get_item(self, item_id: str) -> str:\n        return self.data.get(item_id, '')\n"
        },
        "test_files": {
            "test_storage_refactor.py": "from repository import ItemRepository\nfrom memory_storage import MemoryStorage\ndef test_repository_with_storage():\n    storage = MemoryStorage()\n    repo = ItemRepository(storage)\n    repo.save_item('k1', 'val1')\n    assert repo.get_item('k1') == 'val1'\n    assert storage.read('k1') == 'val1'\n"
        },
        "expected_files": ["repository.py"],
        "reference_fix": {
            "repository.py": "from storage_interface import IStorage\nclass ItemRepository:\n    def __init__(self, storage: IStorage):\n        self.storage = storage\n    def save_item(self, item_id: str, payload: str):\n        self.storage.write(item_id, payload)\n    def get_item(self, item_id: str) -> str:\n        return self.storage.read(item_id)\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-02",
        "name": "Dependency Injection Container Lazy Resolver",
        "language": "python",
        "difficulty": "HARD",
        "category": "Advanced Software Engineering",
        "subcategory": "Cross-module dependencies",
        "description": "In di_container.py, DIContainer.register() and resolve() must support lazy singleton instantiation and detect unresolvable dependencies.",
        "initial_files": {
            "di_container.py": "class DIContainer:\n    def __init__(self):\n        self.registry = {}\n    def register(self, key: str, factory_fn, singleton: bool = False):\n        pass\n    def resolve(self, key: str):\n        return None\n"
        },
        "test_files": {
            "test_di_container.py": "from di_container import DIContainer\ndef test_container():\n    c = DIContainer()\n    calls = 0\n    def make_db():\n        nonlocal calls\n        calls += 1\n        return {'conn': 'active'}\n    c.register('db', make_db, singleton=True)\n    inst1 = c.resolve('db')\n    inst2 = c.resolve('db')\n    assert inst1 is inst2\n    assert calls == 1\n"
        },
        "expected_files": ["di_container.py"],
        "reference_fix": {
            "di_container.py": "class DIContainer:\n    def __init__(self):\n        self._factories = {}\n        self._singletons = {}\n        self._instances = {}\n    def register(self, key: str, factory_fn, singleton: bool = False):\n        self._factories[key] = factory_fn\n        self._singletons[key] = singleton\n    def resolve(self, key: str):\n        if key not in self._factories:\n            raise KeyError(f'Service {key} not registered')\n        if self._singletons.get(key):\n            if key not in self._instances:\n                self._instances[key] = self._factories[key]()\n            return self._instances[key]\n        return self._factories[key]()\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-03",
        "name": "Distributed Idempotency Key Lock Deduplicator",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Advanced Software Engineering",
        "subcategory": "Regression prevention",
        "description": "In idempotency.py, process_idempotent() must return cached result if idempotency_key was already processed.",
        "initial_files": {
            "idempotency.py": "def process_idempotent(key: str, action_fn, cache: dict) -> any:\n    # Bug: always executes action_fn\n    return action_fn()\n"
        },
        "test_files": {
            "test_idempotency.py": "from idempotency import process_idempotent\ndef test_dedup():\n    cache = {}\n    count = 0\n    def charge():\n        nonlocal count\n        count += 1\n        return {'charged': 50}\n    res1 = process_idempotent('tx-123', charge, cache)\n    res2 = process_idempotent('tx-123', charge, cache)\n    assert res1 == res2 == {'charged': 50}\n    assert count == 1  # Only charged once\n"
        },
        "expected_files": ["idempotency.py"],
        "reference_fix": {
            "idempotency.py": "def process_idempotent(key: str, action_fn, cache: dict) -> any:\n    if key in cache:\n        return cache[key]\n    result = action_fn()\n    cache[key] = result\n    return result\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-04",
        "name": "O(N^2) Nested Lookup Optimization to O(1) Hash Map",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Advanced Software Engineering",
        "subcategory": "Performance defects",
        "description": "In matcher.py, match_user_orders() has O(N * M) nested loop performance. Optimize using index dictionary mapping.",
        "initial_files": {
            "matcher.py": "def match_user_orders(users: list[dict], orders: list[dict]) -> dict:\n    # O(N*M) nested lookup\n    res = {}\n    for u in users:\n        u_orders = []\n        for o in orders:\n            if o['user_id'] == u['id']:\n                u_orders.append(o['order_id'])\n        res[u['id']] = u_orders\n    return res\n"
        },
        "test_files": {
            "test_matcher.py": "from matcher import match_user_orders\ndef test_matching():\n    users = [{'id': f'u{i}'} for i in range(100)]\n    orders = [{'order_id': f'o{i}', 'user_id': f'u{i % 10}'} for i in range(500)]\n    res = match_user_orders(users, orders)\n    assert len(res['u0']) == 50\n    assert len(res['u99']) == 0\n"
        },
        "expected_files": ["matcher.py"],
        "reference_fix": {
            "matcher.py": "def match_user_orders(users: list[dict], orders: list[dict]) -> dict:\n    from collections import defaultdict\n    order_map = defaultdict(list)\n    for o in orders:\n        order_map[o['user_id']].append(o['order_id'])\n    return {u['id']: order_map[u['id']] for u in users}\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-05",
        "name": "Configuration Hierarchy Cascade Precedence",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Advanced Software Engineering",
        "subcategory": "Configuration problems",
        "description": "In config_cascade.py, resolve_config() must enforce priority: cli_args > env_vars > config_file > defaults.",
        "initial_files": {
            "config_cascade.py": "def resolve_config(defaults: dict, file_cfg: dict, env_vars: dict, cli_args: dict) -> dict:\n    # Wrong precedence\n    return {**cli_args, **defaults}\n"
        },
        "test_files": {
            "test_config_cascade.py": "from config_cascade import resolve_config\ndef test_cascade_precedence():\n    d = {'port': 80, 'env': 'dev', 'host': '0.0.0.0'}\n    f = {'port': 8080, 'env': 'stage'}\n    e = {'env': 'prod'}\n    c = {'port': 9000}\n    final = resolve_config(d, f, e, c)\n    assert final['port'] == 9000     # from CLI\n    assert final['env'] == 'prod'    # from ENV\n    assert final['host'] == '0.0.0.0'# from default\n"
        },
        "expected_files": ["config_cascade.py"],
        "reference_fix": {
            "config_cascade.py": "def resolve_config(defaults: dict, file_cfg: dict, env_vars: dict, cli_args: dict) -> dict:\n    res = defaults.copy()\n    res.update({k: v for k, v in file_cfg.items() if v is not None})\n    res.update({k: v for k, v in env_vars.items() if v is not None})\n    res.update({k: v for k, v in cli_args.items() if v is not None})\n    return res\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-06",
        "name": "Deep Recursive Hierarchy Stack Overflow Guard",
        "language": "python",
        "difficulty": "HARD",
        "category": "Advanced Software Engineering",
        "subcategory": "Complex debugging",
        "description": "In tree_flattener.py, collect_all_nodes() overflows call stack on deep trees (10,000 depth). Convert recursion to iterative stack.",
        "initial_files": {
            "tree_flattener.py": "def collect_all_nodes(node: dict) -> list[str]:\n    # Recursive - stack overflows on depth > 1000\n    res = [node['id']]\n    for child in node.get('children', []):\n        res.extend(collect_all_nodes(child))\n    return res\n"
        },
        "test_files": {
            "test_tree_flattener.py": "from tree_flattener import collect_all_nodes\ndef test_deep_tree():\n    curr = {'id': 'root', 'children': []}\n    deepest = curr\n    for i in range(1500):\n        child = {'id': f'node_{i}', 'children': []}\n        deepest['children'].append(child)\n        deepest = child\n    nodes = collect_all_nodes(curr)\n    assert len(nodes) == 1501\n"
        },
        "expected_files": ["tree_flattener.py"],
        "reference_fix": {
            "tree_flattener.py": "def collect_all_nodes(node: dict) -> list[str]:\n    res = []\n    stack = [node]\n    while stack:\n        curr = stack.pop()\n        if curr and 'id' in curr:\n            res.append(curr['id'])\n            children = curr.get('children', [])\n            for child in reversed(children):\n                stack.append(child)\n    return res\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-07",
        "name": "Deterministic Clock Mocking for Flaky Timing Tests",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Advanced Software Engineering",
        "subcategory": "Test-suite improvements",
        "description": "In rate_limiter.py, RateLimiter depends on real wall-clock time causing flaky tests. Inject a clock callable provider.",
        "initial_files": {
            "rate_limiter.py": "import time\nclass RateLimiter:\n    def __init__(self, limit: int, window_seconds: float):\n        self.limit = limit\n        self.window = window_seconds\n        self.calls = []\n    def is_allowed(self) -> bool:\n        now = time.time()\n        self.calls = [t for t in self.calls if now - t < self.window]\n        if len(self.calls) < self.limit:\n            self.calls.append(now)\n            return True\n        return False\n"
        },
        "test_files": {
            "test_rate_limiter.py": "from rate_limiter import RateLimiter\ndef test_deterministic_rate_limiter():\n    mock_time = 1000.0\n    def clock(): return mock_time\n    limiter = RateLimiter(limit=2, window_seconds=10.0, time_provider=clock)\n    assert limiter.is_allowed() is True\n    assert limiter.is_allowed() is True\n    assert limiter.is_allowed() is False\n    mock_time += 11.0\n    assert limiter.is_allowed() is True\n"
        },
        "expected_files": ["rate_limiter.py"],
        "reference_fix": {
            "rate_limiter.py": "import time\nclass RateLimiter:\n    def __init__(self, limit: int, window_seconds: float, time_provider=None):\n        self.limit = limit\n        self.window = window_seconds\n        self.clock = time_provider or time.time\n        self.calls = []\n    def is_allowed(self) -> bool:\n        now = self.clock()\n        self.calls = [t for t in self.calls if now - t < self.window]\n        if len(self.calls) < self.limit:\n            self.calls.append(now)\n            return True\n        return False\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-08",
        "name": "Domain Event Bus Subscriber Decoupling",
        "language": "python",
        "difficulty": "MEDIUM",
        "category": "Advanced Software Engineering",
        "subcategory": "Architectural consistency",
        "description": "In event_bus.py, EventBus.publish() fails if any handler raises an exception, aborting remaining handlers. Add error isolation.",
        "initial_files": {
            "event_bus.py": "class EventBus:\n    def __init__(self):\n        self.subscribers = {}\n    def subscribe(self, event_name: str, handler):\n        self.subscribers.setdefault(event_name, []).append(handler)\n    def publish(self, event_name: str, payload: dict):\n        for h in self.subscribers.get(event_name, []):\n            h(payload)\n"
        },
        "test_files": {
            "test_event_bus.py": "from event_bus import EventBus\ndef test_event_isolation():\n    bus = EventBus()\n    called = []\n    def faulty(p): raise RuntimeError('Boom')\n    def healthy(p): called.append(p['id'])\n    bus.subscribe('user_created', faulty)\n    bus.subscribe('user_created', healthy)\n    bus.publish('user_created', {'id': 'u1'})\n    assert called == ['u1']  # Healthy handler was still called\n"
        },
        "expected_files": ["event_bus.py"],
        "reference_fix": {
            "event_bus.py": "class EventBus:\n    def __init__(self):\n        self.subscribers = {}\n    def subscribe(self, event_name: str, handler):\n        self.subscribers.setdefault(event_name, []).append(handler)\n    def publish(self, event_name: str, payload: dict):\n        for h in self.subscribers.get(event_name, []):\n            try:\n                h(payload)\n            except Exception:\n                pass\n"
        },
        "is_held_out": False
    },
    {
        "id": "adv-09",
        "name": "Path Traversal and Safe Basename Resolution",
        "language": "python",
        "difficulty": "HARD",
        "category": "Advanced Software Engineering",
        "subcategory": "Security-related defects",
        "description": "In safe_reader.py, read_workspace_file() vulnerable to directory traversal via '../'. Restrict reads to base_dir.",
        "initial_files": {
            "safe_reader.py": "import os\ndef read_workspace_file(base_dir: str, rel_path: str) -> str:\n    # Insecure path join\n    target = os.path.join(base_dir, rel_path)\n    with open(target, 'r') as f:\n        return f.read()\n"
        },
        "test_files": {
            "test_safe_reader.py": "import os, tempfile, pytest\nfrom safe_reader import read_workspace_file\ndef test_safe_reader():\n    with tempfile.TemporaryDirectory() as base:\n        secret_path = os.path.join(os.path.dirname(base), 'secret.txt')\n        with open(secret_path, 'w') as sf: sf.write('TOP_SECRET')\n        valid_file = os.path.join(base, 'hello.txt')\n        with open(valid_file, 'w') as vf: vf.write('HELLO')\n        assert read_workspace_file(base, 'hello.txt') == 'HELLO'\n        with pytest.raises(PermissionError):\n            read_workspace_file(base, '../secret.txt')\n        if os.path.exists(secret_path): os.remove(secret_path)\n"
        },
        "expected_files": ["safe_reader.py"],
        "reference_fix": {
            "safe_reader.py": "from pathlib import Path\ndef read_workspace_file(base_dir: str, rel_path: str) -> str:\n    base = Path(base_dir).resolve()\n    target = (base / rel_path).resolve()\n    try:\n        target.relative_to(base)\n    except ValueError:\n        raise PermissionError(f'Access denied: {rel_path} escapes workspace')\n    with open(target, 'r') as f:\n        return f.read()\n"
        },
        "is_held_out": True
    },
    {
        "id": "adv-10",
        "name": "Two-Phase Commit Transactional Batch Processor with Rollback",
        "language": "python",
        "difficulty": "HARD",
        "category": "Advanced Software Engineering",
        "subcategory": "Multi-step feature implementation",
        "description": "In txn_manager.py, TransactionManager.execute_batch() must prepare each step, execute commit, and call rollback() on all completed steps if any step fails.",
        "initial_files": {
            "txn_manager.py": "class TransactionManager:\n    def execute_batch(self, operations: list) -> bool:\n        # Bug: fails to rollback previous steps when an operation fails\n        for op in operations:\n            op.execute()\n        return True\n"
        },
        "test_files": {
            "test_txn_manager.py": "from txn_manager import TransactionManager\ndef test_batch_rollback():\n    log = []\n    class Op1:\n        def execute(self): log.append('op1_exec')\n        def rollback(self): log.append('op1_rollback')\n    class Op2:\n        def execute(self): raise RuntimeError('Op2 Fail')\n        def rollback(self): log.append('op2_rollback')\n    tm = TransactionManager()\n    ok = tm.execute_batch([Op1(), Op2()])\n    assert ok is False\n    assert log == ['op1_exec', 'op1_rollback']\n"
        },
        "expected_files": ["txn_manager.py"],
        "reference_fix": {
            "txn_manager.py": "class TransactionManager:\n    def execute_batch(self, operations: list) -> bool:\n        executed = []\n        try:\n            for op in operations:\n                op.execute()\n                executed.append(op)\n            return True\n        except Exception:\n            for op in reversed(executed):\n                if hasattr(op, 'rollback'):\n                    try:\n                        op.rollback()\n                    except Exception:\n                        pass\n            return False\n"
        },
        "is_held_out": True
    }
]

