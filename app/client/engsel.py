import os, json, uuid, requests, time
from datetime import datetime, timezone, timedelta
import app.config  # Ensure env vars are loaded

from app.client.encrypt import encryptsign_xdata, java_like_timestamp, ts_gmt7_without_colon, ax_api_signature, decrypt_xdata, API_KEY, get_x_signature_payment, build_encrypted_field, load_ax_fp, ax_device_id

BASE_API_URL = os.getenv("BASE_API_URL")
BASE_CIAM_URL = os.getenv("BASE_CIAM_URL")
if not BASE_API_URL or not BASE_CIAM_URL:
    raise ValueError("BASE_API_URL or BASE_CIAM_URL environment variable not set")

GET_OTP_URL = BASE_CIAM_URL + "/realms/xl-ciam/auth/otp"
BASIC_AUTH = os.getenv("BASIC_AUTH")
AX_DEVICE_ID = ax_device_id()
AX_FP = load_ax_fp()
SUBMIT_OTP_URL = BASE_CIAM_URL + "/realms/xl-ciam/protocol/openid-connect/token"
UA = os.getenv("UA")

def validate_contact(contact: str) -> bool:
    if not contact.startswith("628") or len(contact) > 14:
        print("Invalid number")
        return False
    return True

def get_otp(contact: str) -> str:
    # Contact example: "6287896089467"
    if not validate_contact(contact):
        return None
    
    url = GET_OTP_URL

    querystring = {
        "contact": contact,
        "contactType": "SMS",
        "alternateContact": "false"
    }
    
    now = datetime.now(timezone(timedelta(hours=7)))
    ax_request_at = java_like_timestamp(now)  # format: "2023-10-20T12:34:56.78+07:00"
    ax_request_id = str(uuid.uuid4())

    payload = ""
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Authorization": f"Basic {BASIC_AUTH}",
        "Ax-Device-Id": AX_DEVICE_ID,
        "Ax-Fingerprint": AX_FP,
        "Ax-Request-At": ax_request_at,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Request-Id": ax_request_id,
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/json",
        "Host": BASE_CIAM_URL.replace("https://", ""),
        "User-Agent": UA,
    }

    print("Requesting OTP...")
    try:
        response = requests.request("GET", url, data=payload, headers=headers, params=querystring, timeout=30)
        print("response body", response.text)
        json_body = json.loads(response.text)
    
        if "subscriber_id" not in json_body:
            print(json_body.get("error", "No error message in response"))
            raise ValueError("Subscriber ID not found in response")
        
        return json_body["subscriber_id"]
    except Exception as e:
        print(f"Error requesting OTP: {e}")
        return None
    
def submit_otp(api_key: str, contact: str, code: str):
    if not validate_contact(contact):
        print("Invalid number")
        return None
    
    if not code or len(code) != 6:
        print("Invalid OTP code format")
        return None
    
    url = SUBMIT_OTP_URL

    now_gmt7 = datetime.now(timezone(timedelta(hours=7)))
    ts_for_sign = ts_gmt7_without_colon(now_gmt7)
    ts_header = ts_gmt7_without_colon(now_gmt7 - timedelta(minutes=5))
    signature = ax_api_signature(api_key, ts_for_sign, contact, code, "SMS")

    payload = f"contactType=SMS&code={code}&grant_type=password&contact={contact}&scope=openid"

    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Authorization": f"Basic {BASIC_AUTH}",
        "Ax-Api-Signature": signature,
        "Ax-Device-Id": AX_DEVICE_ID,
        "Ax-Fingerprint": AX_FP,
        "Ax-Request-At": ts_header,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Request-Id": str(uuid.uuid4()),
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": UA,
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        json_body = json.loads(response.text)
        
        if "error" in json_body:
            print(f"[Error submit_otp]: {json_body['error_description']}")
            return None
        
        print("Login successful.")
        return json_body
    except requests.RequestException as e:
        print(f"[Error submit_otp]: {e}")
        return None

def get_new_token(refresh_token: str) -> str:
    url = SUBMIT_OTP_URL

    now = datetime.now(timezone(timedelta(hours=7)))  # GMT+7
    ax_request_at = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0700"
    ax_request_id = str(uuid.uuid4())

    headers = {
        "Host": BASE_CIAM_URL.replace("https://", ""),
        "ax-request-at": ax_request_at,
        "ax-device-id": AX_DEVICE_ID,
        "ax-request-id": ax_request_id,
        "ax-request-device": "samsung",
        "ax-request-device-model": "SM-N935F",
        "ax-fingerprint": AX_FP,
        "authorization": f"Basic {BASIC_AUTH}",
        "user-agent": UA,
        "ax-substype": "PREPAID",
        "content-type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    resp = requests.post(url, headers=headers, data=data, timeout=30)
    if resp.status_code == 400:
        if resp.json().get("error_description") == "Session not active":
            print("Refresh token expired. Pleas remove and re-add the account.")
            return None
        
    resp.raise_for_status()

    body = resp.json()
    
    if "id_token" not in body:
        raise ValueError("ID token not found in response")
    if "error" in body:
        raise ValueError(f"Error in response: {body['error']} - {body.get('error_description', '')}")
    
    return body

def send_api_request(
    api_key: str,
    path: str,
    payload_dict: dict,
    id_token: str,
    method: str = "POST",
):
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method=method,
        path=path,
        id_token=id_token,
        payload=payload_dict
    )
    
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    
    now = datetime.now(timezone.utc).astimezone()
    sig_time_sec = (xtime // 1000)

    body = encrypted_payload["encrypted_body"]
    x_sig = encrypted_payload["x_signature"]
    
    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {id_token}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(now),
        "x-version-app": "8.7.0",
    }
    
    

    url = f"{BASE_API_URL}/{path}"
    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
    
    # print(f"Headers: {json.dumps(headers, indent=2)}")

    try:
        # Coba parse response sebagai JSON terlebih dahulu
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        return decrypted_body
    except json.JSONDecodeError:
        # Jika response bukan JSON (misalnya, halaman error HTML dari Cloudflare)
        print(f"[request err] Response is not valid JSON. Server might be down. Response body:\n{resp.text[:500]}...")
        return None
    except Exception as e:
        print("[decrypt err]", e)
        return None

def get_profile(api_key: str, access_token: str, id_token: str) -> dict:
    path = "api/v8/profile"

    raw_payload = {
        "access_token": access_token,
        "app_version": "8.7.0",
        "is_enterprise": False,
        "lang": "en"
    }

    # print("Fetching profile...")
    res = send_api_request(api_key, path, raw_payload, id_token, "POST")

    return res.get("data") if res else None

def get_balance(api_key: str, id_token: str) -> dict:
    path = "api/v8/packages/balance-and-credit"
    
    raw_payload = {
        "is_enterprise": False,
        "lang": "en"
    }
    
    # print("Fetching balance...")
    res = send_api_request(api_key, path, raw_payload, id_token, "POST")
    # print(f"[GB-256]:\n{json.dumps(res, indent=2)}")
    
    if res and "data" in res:
        if "balance" in res["data"]:
            return res["data"]["balance"]
    else:
        print("Error getting balance:", res.get("error", "Unknown error"))
        return None
    
def get_main_quota(api_key: str, id_token: str) -> dict:
    """
    Fetches all data quotas, aggregates them, and returns a dictionary.
    """
    path = "api/v8/packages/quota-summary"
    payload = {
        "is_enterprise": False,
        "lang": "en"
    }

    try:
        res = send_api_request(api_key, path, payload, id_token, "POST")
    except Exception as e:
        print("Error sending API request for quota:", e)
        return None

    if isinstance(res, dict) and "data" in res:
        quota = res["data"].get("quota", {}).get("data")
        if quota:
            return {
                "remaining": quota.get("remaining", 0),
                "total": quota.get("total", 0),
                "has_unlimited": quota.get("has_unlimited", False)
            }
        else:
            # No quota data in a successful response, return 0
            return {"remaining": 0, "total": 0, "has_unlimited": False}
    else:
        print("Error getting quota:", res.get("error", "Unknown error") if isinstance(res, dict) else res)
        return None

def segments(api_key: str, id_token: str, access_token: str, balance: int = 0) -> dict | None:
    """
    Fetches various user segments like loyalty, notifications, and special offers.
    """
    path = "dashboard/api/v8/segments"
    payload = {
        "access_token": access_token,
        "app_version": "8.7.0",
        "current_balance": balance,
        "family_plan_role": "NO_ROLE",
        "is_enterprise": False,
        "lang": "id",
        "manufacturer_name": "samsung",
        "model_name": "SM-N935F"
    }

    try:
        res = send_api_request(api_key, path, payload, id_token, "POST")
    except Exception as e:
        print(f"Error sending API request for segments: {e}")
        return None

    if not (isinstance(res, dict) and "data" in res):
        err = res.get("error", "Unknown error") if isinstance(res, dict) else res
        print("Error getting segments info:", err)
        return None

    data = res["data"]

    loyalty_data = data.get("loyalty", {}).get("data", {})
    loyalty_info = {
        "current_point": loyalty_data.get("current_point", 0),
        "tier_name": loyalty_data.get("detail_tier", {}).get("name", "")
    }

    notifications = data.get("notification", {}).get("data", [])

    sfy_data = data.get("special_for_you", {}).get("data", {})
    sfy_banners = sfy_data.get("banners", [])
    special_packages = []
    for pkg in sfy_banners:
        kuota_total = 0
        for benefit in pkg.get("benefits", []):
            if benefit.get("data_type") == "DATA":
                kuota_total += int(benefit.get("total", 0))

        kuota_gb = kuota_total / (1024 ** 3)  # dari byte → GB

        original_price = pkg.get('original_price', 0)
        discounted_price = pkg.get('discounted_price', 0)
        diskon_percent = int(round((original_price - discounted_price) / original_price * 100, 0)) if original_price else 0

        formatted_pkg = {
            "name": f"{pkg.get('family_name', '')} ({pkg.get('title', '')}) {pkg.get('validity', '')}",
            "kode_paket": pkg.get("action_param", ""),
            "original_price": original_price,
            "diskon_price": discounted_price,
            "diskon_percent": diskon_percent,
            "kuota_gb": kuota_gb
        }
        special_packages.append(formatted_pkg)

    return {
        "loyalty": loyalty_info,
        "notification": notifications,
        "special_packages": special_packages
    }

def get_point_balance(api_key: str, tokens: dict) -> int:
    """
    Fetches the user's point balance from the login info endpoint.
    """
    path = "api/v8/auth/login"
    # Endpoint ini memerlukan access_token untuk mengembalikan data loyalty/poin.
    payload = {
        "access_token": tokens.get("access_token"),
        "is_enterprise": False,
        "lang": "en"
    }
    res = send_api_request(api_key, path, payload, tokens.get("id_token"), "POST")
    
    if res.get("status") != "SUCCESS" or "data" not in res:
        print("Gagal mengambil sisa poin.")
        return 0
        
    # The point balance is nested within the response
    return res.get("data", {}).get("loyalty", {}).get("point_balance", 0)

def get_family(
    api_key: str,
    tokens: dict,
    family_code: str,
    is_enterprise: bool = False,
    migration_type: str = "NONE"
) -> dict:
    print("Fetching package family...")
    path = "api/v8/xl-stores/options/list"
    id_token = tokens.get("id_token")
    payload_dict = {
        "is_show_tagging_tab": True,
        "is_dedicated_event": True,
        "is_transaction_routine": False,
        "migration_type": migration_type,
        "package_family_code": family_code,
        "is_autobuy": False,
        "is_enterprise": is_enterprise,
        "is_pdlp": True,
        "referral_code": "",
        "is_migration": False,
        "lang": "en"
    }
    
    res = send_api_request(api_key, path, payload_dict, id_token, "POST")
    if res.get("status") != "SUCCESS":
        print(f"Failed to get family {family_code}")
        print(json.dumps(res, indent=2))
        input("Press Enter to continue...")
        return None
    # print(json.dumps(res, indent=2))
    return res["data"]

def get_family_v2(
    api_key: str,
    tokens: dict,
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None,
    silent: bool = False
) -> dict:
    if not silent:
        print("Fetching package family...")
    is_enterprise_list = [
        False,
        True
    ]

    migration_type_list = [
        "NONE",
        "PRE_TO_PRIOH",
        "PRIOH_TO_PRIO"
    ]

    if is_enterprise is not None:
        is_enterprise_list = [is_enterprise]

    if migration_type is not None:
        migration_type_list = [migration_type]


    path = "api/v8/xl-stores/options/list"
    id_token = tokens.get("id_token")

    family_data = None

    for mt in migration_type_list:
        if family_data is not None:
            break

        for ie in is_enterprise_list:
            if family_data is not None:
                break
            # if not silent:
            #     print(f"Trying is_enterprise={ie}, migration_type={mt}...")

            payload_dict = {
                "is_show_tagging_tab": True,
                "is_dedicated_event": True,
                "is_transaction_routine": False,
                "migration_type": mt,
                "package_family_code": family_code,
                "is_autobuy": False,
                "is_enterprise": ie,
                "is_pdlp": True,
                "referral_code": "",
                "is_migration": False,
                "lang": "en"
            }
        
            res = send_api_request(api_key, path, payload_dict, id_token, "POST")
            if res.get("status") != "SUCCESS":
                print(f"Failed to get family {family_code}")
                print(json.dumps(res, indent=2))
                return None
            
            family_name = res["data"]["package_family"].get("name", "")
            if family_name != "":
                family_data = res["data"] # type: ignore
                # if not silent:
                #     print(f"Success with is_enterprise={ie}, migration_type={mt}. Family name: {family_name}")


    if family_data is None:
        print(f"Failed to get valid family data for {family_code}")
        return None

    return family_data

def get_families(api_key: str, tokens: dict, package_category_code: str) -> dict:
    print("Fetching families...")
    path = "api/v8/xl-stores/families"
    payload_dict = {
        "migration_type": "",
        "is_enterprise": False,
        "is_shareable": False,
        "package_category_code": package_category_code,
        "with_icon_url": True,
        "is_migration": False,
        "lang": "en"
    }
    
    res = send_api_request(api_key, path, payload_dict, tokens["id_token"], "POST")
    if res.get("status") != "SUCCESS":
        print(f"Failed to get families for category {package_category_code}")
        print(f"Res:{res}")
        # print(json.dumps(res, indent=2))
        input("Press Enter to continue...")
        return None
    return res["data"]

def get_package(
    api_key: str,
    tokens: dict,
    package_option_code: str,
    package_family_code: str = "",
    package_variant_code: str = "",
    silent: bool = False
    ) -> dict:
    path = "api/v8/xl-stores/options/detail"
    raw_payload = { # type: ignore
        "is_transaction_routine": False,
        "migration_type": "NONE",
        "package_family_code": package_family_code,
        "family_role_hub": "",
        "is_autobuy": False,
        "is_enterprise": False,
        "is_shareable": False,
        "is_migration": False,
        "lang": "en",
        "package_option_code": package_option_code,
        "is_upsell_pdp": False,
        "package_variant_code": package_variant_code
    }
    
    if not silent:
        print("Fetching package...")
    # print(f"Payload: {json.dumps(raw_payload, indent=2)}")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    
    if "data" not in res:
        print(json.dumps(res, indent=2))
        print("Error getting package:", res.get("error", "Unknown error"))
        return None
        
    return res["data"]

def get_addons(api_key: str, tokens: dict, package_option_code: str) -> dict:
    path = "api/v8/xl-stores/options/addons-pinky-box"
    
    raw_payload = {
        "is_enterprise": False,
        "lang": "en",
        "package_option_code": package_option_code
    }
    
    print("Fetching addons...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    
    if "data" not in res:
        print("Error getting addons:", res.get("error", "Unknown error"))
        return None
        
    return res["data"]

def intercept_page(
    api_key: str,
    tokens: dict,
    option_code: str,
    is_enterprise: bool = False
):
    path = "misc/api/v8/utility/intercept-page"
    
    raw_payload = {
        "is_enterprise": is_enterprise,
        "lang": "en",
        "package_option_code": option_code
    }
    
    print("Fetching intercept page...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    
    if "status" in res:
        print(f"Intercept status: {res['status']}")
    else:
        print("Intercept error")

def send_payment_request(
    api_key: str,
    payload_dict: dict,
    access_token: str,
    id_token: str,
    token_payment: str,
    ts_to_sign: int,
    payment_for: str = "BUY_PACKAGE"
):
    path = "payments/api/v8/settlement-balance"
    package_code = payload_dict["items"][0]["item_code"]
    
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method="POST",
        path=path,
        id_token=id_token,
        payload=payload_dict
    )
    
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = (xtime // 1000)
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    payload_dict["timestamp"] = ts_to_sign
    
    body = encrypted_payload["encrypted_body"]
    
    x_sig = get_x_signature_payment(
        api_key,
        access_token,
        ts_to_sign,
        package_code,
        token_payment,
        "BALANCE",
        payment_for
    )
    
    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {id_token}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(x_requested_at),
        "x-version-app": "8.7.0",
    }
    
    url = f"{BASE_API_URL}/{path}"
    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
    
    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        return decrypted_body
    except Exception as e:
        print("[decrypt err]", e)
        return resp.text

def purchase_package(
    api_key: str,
    tokens: dict,
    package_option_code:str,
    is_enterprise: bool = False
    ) -> dict:
    package_details_data = get_package(api_key, tokens, package_option_code)
    if not package_details_data:
        print("Failed to get package details for purchase.")
        return None
    
    token_confirmation = package_details_data["token_confirmation"]
    payment_target = package_details_data["package_option"]["package_option_code"]
    
    variant_name = package_details_data["package_detail_variant"].get("name", "")
    option_name = package_details_data["package_option"].get("name", "")
    item_name = f"{variant_name} {option_name}".strip()
    
    activated_autobuy_code = package_details_data["package_option"]["activated_autobuy_code"]
    autobuy_threshold_setting = package_details_data["package_option"]["autobuy_threshold_setting"]
    can_trigger_rating = package_details_data["package_option"]["can_trigger_rating"]
    payment_for = package_details_data["package_family"]["payment_for"]
    
    price = package_details_data["package_option"]["price"]
    amount_str = input(f"Total amount is {price}.\nEnter value if you need to overwrite, press enter to ignore & use default amount: ")
    amount_int = price
    
    # Intercept, IDK for what purpose
    intercept_page(api_key, tokens, package_option_code, is_enterprise)
    
    if amount_str != "":
        try:
            amount_int = int(amount_str)
        except ValueError:
            print("Invalid overwrite input, using original price.")
            return None
    
    payment_path = "payments/api/v8/payment-methods-option"
    payment_payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": is_enterprise,
        "payment_target": payment_target,
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation
    }
    
    print("Initiating payment...")
    payment_res = send_api_request(api_key, payment_path, payment_payload, tokens["id_token"], "POST")
    if payment_res.get("status") != "SUCCESS":
        print("Failed to initiate payment")
        print(json.dumps(payment_res, indent=2))
        input("Press Enter to continue...")
        return None
    
    token_payment = payment_res["data"]["token_payment"]
    ts_to_sign = payment_res["data"]["timestamp"]
    
    # Overwrite, sometimes the payment_for from package details is empty
    if payment_for == "":
        payment_for = "BUY_PACKAGE"
    
    # Settlement request
    settlement_payload = {
        "total_discount": 0,
        "is_enterprise": is_enterprise,
        "payment_token": "",
        "token_payment": token_payment,
        "activated_autobuy_code": activated_autobuy_code,
        "cc_payment_type": "",
        "is_myxl_wallet": False,
        "pin": "",
        "ewallet_promo_id": "",
        "members": [],
        "total_fee": 0,
        "fingerprint": "",
        "autobuy_threshold_setting": autobuy_threshold_setting,
        "is_use_point": False,
        "lang": "en",
        "payment_method": "BALANCE",
        "timestamp": int(time.time()),
        "points_gained": 0,
        "can_trigger_rating": can_trigger_rating,
        "akrab_members": [],
        "akrab_parent_alias": "",
        "referral_unique_code": "",
        "coupon": "",
        "payment_for": payment_for,
        "with_upsell": False,
        "topup_number": "",
        "stage_token": "",
        "authentication_id": "",
        "encrypted_payment_token": build_encrypted_field(urlsafe_b64=True),
        "token": "",
        "token_confirmation": token_confirmation,
        "access_token": tokens["access_token"],
        "wallet_number": "",
        "encrypted_authentication_id": build_encrypted_field(urlsafe_b64=True),
        "additional_data": {
            "original_price": price,
            "is_spend_limit_temporary": False,
            "migration_type": "",
            "akrab_m2m_group_id": "false",
            "spend_limit_amount": 0,
            "is_spend_limit": False,
            "mission_id": "",
            "tax": 0,
            # "benefit_type": "NONE",
            "quota_bonus": 0,
            "cashtag": "",
            "is_family_plan": False,
            "combo_details": [],
            "is_switch_plan": False,
            "discount_recurring": 0,
            "is_akrab_m2m": False,
            "balance_type": "PREPAID_BALANCE",
            "has_bonus": False,
            "discount_promo": 0
            },
        "total_amount": amount_int,
        "is_using_autobuy": False,
        "items": [
            {
                "item_code": payment_target,
                "product_type": "",
                "item_price": price,
                "item_name": item_name,
                "tax": 0
            }
        ]
    }
    
    print("Processing purchase...")
    # print(f"settlement payload:\n{json.dumps(settlement_payload, indent=2)}")
    purchase_result = send_payment_request(api_key, settlement_payload, tokens["access_token"], tokens["id_token"], token_payment, ts_to_sign, payment_for)
    
    print(f"Purchase result:\n{json.dumps(purchase_result, indent=2)}")
    
    input("Press Enter to continue...")

def login_info(
    api_key: str,
    tokens: dict,
    is_enterprise: bool = False
):
    path = "api/v8/auth/login"
    
    raw_payload = {
        "access_token": tokens["access_token"],
        "is_enterprise": is_enterprise,
        "lang": "en"
    }
    
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    
    if "data" not in res:
        print(json.dumps(res, indent=2))
        print("Error getting package:", res.get("error", "Unknown error"))
        return None
        
    return res["data"]

def get_package_details(
    api_key: str,
    tokens: dict,
    family_code: str,
    variant_code: str,
    option_order: int | None = None,
    is_enterprise: bool | None = None,
    migration_type: str | None = None,
    silent: bool = False
) -> dict | None:
    family_data = get_family_v2(api_key, tokens, family_code, is_enterprise, migration_type, silent=silent)
    if not family_data:
        print(f"Gagal mengambil data family untuk {family_code}.")
        return None

    # Jika is_enterprise tidak diberikan, coba ambil dari family_data
    if is_enterprise is None:
        is_enterprise = family_data.get("package_family", {}).get("is_enterprise", False)

    # Jika variant_code tidak ada atau bukan UUID, coba cari berdasarkan variant_name
    is_valid_uuid = isinstance(variant_code, str) and len(variant_code) == 36 and '-' in variant_code
    if not is_valid_uuid:
        variant_name_to_find = variant_code # Asumsikan variant_code berisi variant_name
        # if not silent:
        #     print(f"Mencari variant_code untuk nama: '{variant_name_to_find}'...")
        variant_code_found = None
        for variant in family_data.get("package_variants", []):
            if variant.get("name") == variant_name_to_find:
                variant_code_found = variant.get("package_variant_code")
                # if not silent:
                #     print(f"Ditemukan variant_code: {variant_code_found}")
                break
        if variant_code_found:
            variant_code = variant_code_found
        else:
            print(f"Gagal menemukan variant_code untuk nama: '{variant_name_to_find}'")
            return None

    
    package_variants = family_data["package_variants"]
    option_code = None
    for variant in package_variants:
        if variant["package_variant_code"] == variant_code:
            selected_variant = variant
            package_options = selected_variant.get("package_options", [])
            for opt in package_options:
                if opt.get("order") == option_order:
                    option_code = opt.get("package_option_code")
                    break

    if option_code is None:
        print("Gagal menemukan opsi paket yang sesuai.")
        return None
        
    package_details_data = get_package(api_key, tokens, option_code, silent=silent)
    if not package_details_data:
        print("Gagal mengambil detail paket.")
        return None
    
    return package_details_data

def ewallet_charge(
    api_key: str,
    tokens: dict,
    packages: list,
    amount: int,
    payment_method: str, # e.g., "SHOPEEPAY"
    is_enterprise: bool = False
) -> dict:
    """
    Initiates a bundle purchase using an e-wallet. This is a simplified version
    that doesn't go through the full settlement process, but directly gets a payment URL.
    """
    path = "payments/api/v8/payment-methods-option"
    
    # Menggunakan package_option_code dari item pertama sebagai payment_target
    # Ini adalah asumsi berdasarkan perilaku aplikasi, mungkin perlu penyesuaian
    if not packages:
        print("Daftar paket tidak boleh kosong.")
        return None
    
    print("Mengambil detail untuk setiap paket dalam bundle...")
    items_for_payment = []
    token_confirmations = []

    for pkg in packages:
        # Ambil detail paket untuk mendapatkan package_option_code dan token_confirmation yang valid
        package_detail = get_package_details(
            api_key,
            tokens,
            pkg.get("family_code"),
            pkg.get("variant_code") or pkg.get("variant_name"), # Support variant_code or variant_name
            pkg.get("order"),
            pkg.get("is_enterprise")
        )

        if not package_detail:
            print(f"Gagal mengambil detail untuk paket: {pkg.get('family_name')} - {pkg.get('option_name')}")
            return {"error": "Failed to get package details", "package": pkg}

        option = package_detail.get("package_option", {})
        item_code = option.get("package_option_code")
        item_name = f"{package_detail.get('package_detail_variant', {}).get('name', '')} {option.get('name', '')}".strip()

        items_for_payment.append({
            "item_code": item_code,
            "item_name": item_name,
            "item_price": option.get("price", 0),
            "product_type": "",
            "tax": 0
        })
        token_confirmations.append(package_detail.get("token_confirmation", ""))

    # Menggunakan item_code dari paket pertama sebagai payment_target
    # dan gabungan token_confirmation
    payment_target = items_for_payment[0]["item_code"] if items_for_payment else None
    token_confirmation = ";".join(filter(None, token_confirmations))

    payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": is_enterprise,
        "payment_target": payment_target,
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation,
        "items": items_for_payment,
        "total_amount": amount,
        "payment_method": payment_method,
        "is_myxl_wallet": False,
        "is_use_point": False,
        "total_discount": 0,
        "total_fee": 0,
        "coupon": "",
        "payment_for": "BUY_PACKAGE",
        "additional_data": {
            "is_family_plan": False,
            "is_akrab_m2m": False,
            "balance_type": "PREPAID_BALANCE",
            "has_bonus": False,
        },
        "encrypted_payment_token": build_encrypted_field(urlsafe_b64=True),
        "encrypted_authentication_id": build_encrypted_field(urlsafe_b64=True),
    }

    print("Memulai pembayaran E-Wallet...")
    res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    
    if res.get("status") != "SUCCESS":
        print("Gagal memulai pembayaran E-Wallet.")
        print(json.dumps(res, indent=2))
        return None
        
    return res.get("data")

def get_payment_status(api_key: str, tokens: dict, order_id: str) -> dict:
    """
    Checks the status of a payment transaction.
    """
    path = "payments/api/v8/payment-status"
    payload = {
        "order_id": order_id,
        "lang": "en"
    }
    
    print(f"Mengecek status pembayaran untuk Order ID: {order_id}...")
    res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    
    return res

def get_transaction_history(api_key: str, tokens: dict, page: int = 1, limit: int = 20) -> dict:
    """
    Fetches the user's transaction history.
    """
    path = "payments/api/v8/transaction-history"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "page": page,
        "limit": limit,
        "filter": {
            "status": [],
            "type": []
        }
    }
    res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    return res