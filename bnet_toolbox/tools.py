import httpx
import typer

from rich import print

USER_AGENT = "phoenix-agent/1.0"
HEADERS = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}

PATCH_URL = "http://us.patch.battle.net:1119"
AGENT_URL = "http://127.0.0.1:1120"

client = httpx.Client(base_url=AGENT_URL)
app = typer.Typer(name="bnet")

GAME_DATA_CACHE = {}


def is_authenticated() -> bool:
    return "Authorization" in HEADERS


def auth():
    if is_authenticated():
        return

    print("Authenticating...")
    res = client.get("/agent")
    res.raise_for_status()
    print("Authenticated!")

    data = res.json()
    HEADERS["Authorization"] = data["authorization"]


def requires_auth(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            auth()
        return func(*args, **kwargs)

    return wrapper


@requires_auth
def is_game_initialized(product: str):
    res = client.get(f"/game/{product}", headers=HEADERS)
    if res.status_code == 200:
        GAME_DATA_CACHE[product] = res.json()
        return True

    return False


@requires_auth
def get_game_data(product: str):
    if product in GAME_DATA_CACHE:
        return GAME_DATA_CACHE[product]

    game_res = client.get(f"/game/{product}", headers=HEADERS)
    game_res.raise_for_status()
    game_data = game_res.json()
    GAME_DATA_CACHE[product] = game_data
    return game_data


@requires_auth
def game_has_pending_update(product: str):
    data = get_game_data(product)
    return data["installed"] == True and not data["download_complete"]


@requires_auth
def get_install_summary():
    summary_res = client.get("/game", headers=HEADERS)
    summary_res.raise_for_status()
    return summary_res.json()


@requires_auth
def get_install_dir():
    summary = get_install_summary()

    installed_game_name = None
    for name in summary:
        if "wow" in name:
            installed_game_name = name
            break

    if installed_game_name is None:
        print("Unable to find World of Warcraft install path")
        exit(1)

    game_data = get_game_data(installed_game_name)
    return game_data["install_dir"]


@requires_auth
def is_game_installed(product: str):
    game_data = get_game_data(product)
    return game_data["installed"]


@requires_auth
def initialize_product(product: str):
    if is_game_initialized(product):
        print(f"'{product}' is already initialized")
        return

    data = {
        "instructions_dataset": ["torrent", "win", product, "enUS"],
        "instructions_patch_url": f"{PATCH_URL}/{product}",
        "instructions_product": "NGDP",
        "monitor_pid": 0,
        "priority": {"insert_at_head": True, "value": 900},
        "uid": product,
    }

    print(f"Initializing {product}...")
    res = client.post("/install", json=data, headers=HEADERS)
    res.raise_for_status()


@requires_auth
def queue_product_install(product: str):
    if is_game_installed(product):
        if game_has_pending_update(product):
            print(f"'{product}' is already installed and has an update pending")
        else:
            print(f"'{product}' is already installed")
        return

    game_dir = get_install_dir()
    data = {
        "account_country": "USA",
        "finalized": True,
        "game_dir": game_dir,
        "geo_ip_country": "US",
        "language": ["enUS"],
        "selected_asset_locale": "enUS",
        "selected_locale": "enUS",
        "shortcut": "all",
        "tome_torrent": "",
    }

    print(f"Queueing {product} for install...")
    res = client.post(f"/install/{product}", json=data, headers=HEADERS)
    res.raise_for_status()


@requires_auth
def update_product(product: str):
    data = {"priority": {"insert_at_head": True, "value": 999}, "uid": product}
    print(f"Queueing update for {product}...")
    res = client.post(f"/update/{product}", json=data, headers=HEADERS)
    res.raise_for_status()


@requires_auth
def remove_product(product: str, run_compaction: bool = True):
    if not is_game_installed(product):
        print(f"Product '{product}' is not installed.")
        return

    data = {"run_compaction": run_compaction, "uid": product}

    print(f"Starting uninstall for {product}...")
    res = client.post(f"/uninstall", json=data, headers=HEADERS)
    res.raise_for_status()


@requires_auth
def get_game_sessions():
    res = client.get("/gamesession", headers=HEADERS)
    res.raise_for_status()
    return res.json()


@app.command(name="install", help="Initializes and installs a new product")
def cmd_init_and_queue_product_install(product: str):
    if product == "wow":
        product = "wow_enus"

    initialize_product(product)
    queue_product_install(product)
    exit(0)


@app.command(name="uninstall", help="Uninstalls a product")
def cmd_uninstall_product(product: str):
    if product == "wow":
        product = "wow_enus"

    remove_product(product)
    exit(0)


@app.command(name="sessions", help="Lists active game sessions")
def cmd_list_sessions():
    sessions = get_game_sessions()
    print(sessions)


@app.command(name="products", help="Lists currently installed products")
def cmd_list_products():
    summary = get_install_summary()
    print(summary)


@app.command(name="update", help="Updates an installed product")
def cmd_update_product(product: str):
    if not is_game_installed(product):
        print(f"Product '{product}' is not installed.")
        exit(1)

    update_product(product)


def handle_cli():
    app()
