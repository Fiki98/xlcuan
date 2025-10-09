import time
import json
import requests
from app.service.auth import AuthInstance
from app.client.engsel import *
from app.client.encrypt import *
from app.menus.util import clear_screen

SERVER_URL = "https://flask-poin.onrender.com/get-signature-point"

def get_x_signature_exchange_poin(
    package_code: str,
    token_confirmation: str,
    path: str,
    method: str,
    timestamp: int,
) -> str:
    payload = {
        "package_code": package_code,
        "token_confirmation": token_confirmation,
        "path": path,
        "method": method,
        "timestamp": timestamp,
    }
    response = requests.post(SERVER_URL, json=payload)
    response.raise_for_status()

    data = response.json()
    if "signature" not in data:
        raise ValueError(f"Invalid response: {data}")
    return data["signature"]
    
def fetch_catalog(api_key, id_token):
    path = "gamification/api/v8/loyalties/tiering/rewards-catalog"
    payload = {"is_enterprise": False, "lang": "id"}
    res = send_api_request(api_key, path, payload, id_token)

    if res.get("status") != "SUCCESS":
        print("Gagal ambil katalog:", res)
        return []

    catalog = []
    points = res["data"]["tiers"][0]["points"]

    for i, item in enumerate(points, start=1):
        print(f"{i}. {item['title']} - {item['price']} Poin")
        catalog.append({
            "code": item["code"], 
            "title": item["title"],  
            "price": item["price"], 
            "benefit_code": item.get("benefit_code", ""),
            "validity": item.get("validity", ""),
            "expiration_date": item.get("expiration_date", 0)
        })

    return catalog


def fetch_detail(api_key, id_token, package_code):
    clear_screen()
    path = "api/v8/xl-stores/options/detail"
    payload = {
        "is_enterprise": False,
        "lang": "id",
        "package_option_code": package_code
    }
    res = send_api_request(api_key, path, payload, id_token)
    if res.get("status") != "SUCCESS":
        print("Gagal ambil detail:", res)
        return None
    option = res["data"]["package_option"]
    print("\n=== Detail Paket ===")
    print(f"Nama : {option['name']}")
    print(f"Harga: {option['price']} Poin")
    print(f"Masa Aktif: {option['validity']}")
    print("Benefits:")
    for b in option.get("benefits", []):
        print(f"- {b['name']}")
    print("S&K:")
    print(option["tnc"])
    return res["data"]


def settlement_exchange_poin(
    api_key: str,
    tokens: dict,
    token_confirmation: str,
    ts_to_sign: int,
    package_code: str,
    price: int,
):
    # Settlement request
    path = "gamification/api/v8/loyalties/tiering/exchange"
    settlement_payload = {
        "amount": "0",
        "is_enterprise": False,
        "item_code": package_code,
        "item_name": "",
        "lang": "id",
        "partner": "",
        "points": price,
        "timestamp": ts_to_sign,
        "token_confirmation": token_confirmation
    }
        
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method="POST",
        path=path,
        id_token=tokens["id_token"],
        payload=settlement_payload
    )
    
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = (xtime // 1000)
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    settlement_payload["timestamp"] = ts_to_sign
    
    body = encrypted_payload["encrypted_body"]
        
    x_sig = get_x_signature_exchange_poin(
        timestamp=ts_to_sign,
        package_code=package_code,
        token_confirmation=token_confirmation,
        path=path,
        method="POST"
    )
    
    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(x_requested_at),
        "x-version-app": "8.7.0",
    }
    
    url = f"{BASE_API_URL}/{path}"
    print("Sending bounty request...")
    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
    
    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        if decrypted_body["status"] != "SUCCESS":
            print("Failed to claim")
            print(f"Error: {decrypted_body}")
            return None
        
        print(decrypted_body)
        
        return decrypted_body
    except Exception as e:
        print("[decrypt err]", e)
        return resp.text

def run_point_exchange(tokens: dict):
    id_token = tokens.get("id_token")
    api_key = AuthInstance.api_key
    
    clear_screen()
    catalog = fetch_catalog(api_key, tokens.get("id_token"))
    if not catalog:
        return

    choice = input("\nPilih nomor paket untuk tukar poin (atau 99 untuk batal): ")
    if choice == "99":
        return

    try:
        item = catalog[int(choice) - 1]
    except Exception:
        print("Pilihan tidak valid.")
        return

    detail = fetch_detail(api_key, tokens.get("id_token"), item["code"])
    if not detail:
        return

    confirm = input("\nTukar poin sekarang? (y/n): ")
    if confirm.lower() == "y":
        settlement_exchange_poin(
            api_key=api_key,
            tokens=tokens,
            package_code=item["code"],
            price=detail["package_option"]["price"],
            token_confirmation=detail["token_confirmation"],
            ts_to_sign=detail["timestamp"]
        )
        input("Tekan Enter untuk Kembali ke Menu")
