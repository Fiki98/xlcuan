import json
import sys
from datetime import datetime
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_family_v2, get_package, get_addons, get_package_details, purchase_package, send_api_request
from app.service.bookmark import BookmarkInstance
from app.client.purchase import show_qris_payment, settlement_bounty
from app.client.ewallet import show_multipayment
from app.menus.util import clear_screen, pause, display_html, print_header, Style
from app.client.qris import show_qris_payment_v2
from app.client.ewallet import show_multipayment_v2
from app.client.balance import settlement_balance
from app.service.family_bookmark import FamilyBookmarkInstance
from app.util import format_quota
from app.type_dict import PaymentItem


def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    package = get_package(api_key, tokens, package_option_code)
    # print(f"[SPD-202]:\n{json.dumps(package, indent=1)}")
    if not package:
        print("Failed to load package details.")
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name","") #Vidio
    family_name = package.get("package_family", {}).get("name","") #Unlimited Turbo
    variant_name = package.get("package_detail_variant", "").get("name","") #For Xtra Combo
    option_name = package.get("package_option", {}).get("name","") #Vidio
    
    title = f"{family_name} - {variant_name} - {option_name}".strip()

    clear_screen()
    print_header(f"📦 Detail Paket: {title}")
    
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    
    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]
    
    print(f"  Harga       : Rp {price}")
    print(f"  Masa Aktif  : {validity}")
    print(f"  Tipe        : {package['package_family']['plan_type']}")
    print(f"  Payment For : {payment_for}")
    print(f"  Point       : {package['package_option']['point']}")
    print(f"{'-'*55}")
    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        print("Benefit Paket:")
        for benefit in benefits:
            print(f" Name: {benefit['name']}")
            print(f"  Item id: {benefit['item_id']}")
            data_type = benefit['data_type']
            if data_type == "VOICE" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']/60} menit")
            elif data_type == "TEXT" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']} SMS")
            elif data_type == "DATA" and benefit['total'] > 0:
                if benefit['total'] > 0:
                    quota = int(benefit['total'])
                    # It is in byte, make it in GB
                    if quota >= 1_000_000_000:
                        quota_gb = quota / (1024 ** 3)
                        print(f"  Quota: {quota_gb:.2f} GB")
                    elif quota >= 1_000_000:
                        quota_mb = quota / (1024 ** 2)
                        print(f"  Quota: {quota_mb:.2f} MB")
                    elif quota >= 1_000:
                        quota_kb = quota / 1024
                        print(f"  Quota: {quota_kb:.2f} KB")
                    else:
                        print(f"  Total: {quota}")
            elif data_type not in ["DATA", "VOICE", "TEXT"]:
                print(f"  Total: {benefit['total']} ({data_type})")
            
            if benefit["is_unlimited"]:
                print("  Unlimited: Yes")
            print(f"{'-'*55}")
    addons = get_addons(api_key, tokens, package_option_code)
    

    bonuses = addons.get("bonuses", [])
    
    # Pick 1st bonus if available, need more testing
    # if len(bonuses) > 0:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonuses[0]["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonuses[0]["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )
    
    # Pick all bonuses, need more testing
    # for bonus in bonuses:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonus["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonus["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )

    print(f"Addons:\n{json.dumps(addons, indent=2)}")
    print(f"{'-'*55}")
    print(f"SnK MyXL:\n{detail}")
    print(f"{'-'*55}")
    
    in_package_detail_menu = True
    while in_package_detail_menu:
        print("\nOpsi Pembelian:")
        print(f"  {Style.CYAN}[1]{Style.RESET}. 💰 Pulsa")
        print(f"  {Style.CYAN}[2]{Style.RESET}. 💳 ShopeePay")
        print(f"  {Style.CYAN}[3]{Style.RESET}. 💳 E-Wallet (Lainnya)")
        print(f"  {Style.CYAN}[4]{Style.RESET}. 📱 QRIS")
        
        # Sometimes payment_for is empty, so we set default to BUY_PACKAGE
        if payment_for == "":
            payment_for = "BUY_PACKAGE"
        
        if payment_for == "REDEEM_VOUCHER":
            print(f"  {Style.CYAN}[4]{Style.RESET}. 🎁 Ambil sebagai bonus (jika tersedia)")

        if option_order != -1:
            print(f"  {Style.CYAN}[0]{Style.RESET}. 🔖 Tambah ke Bookmark")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke daftar paket")
        print(f"{'-'*25}")

        choice = input("Pilihan > ")
        if choice == "00":
            return False
        if choice == "0" and option_order != -1:
            # Add to bookmark
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                print("Paket berhasil ditambahkan ke bookmark.")
            else:
                print("Paket sudah ada di bookmark.")
            pause()
            continue
        
        if choice == '1':
            # purchase_package(api_key, tokens, package_option_code, is_enterprise)
            settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used="first"
            )
            input("Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '2':
            show_multipayment_v2(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used="first",
                force_payment_method="SHOPEEPAY"
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '3':
            show_multipayment_v2(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used="first",
                exclude_shopeepay=True
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '4':
            show_qris_payment_v2(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used="first",
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '9':
            # Decoy
            pd = get_package_details(
                api_key,
                tokens,
                "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                6,
                False,
                "NONE",
            )
            
            payment_items.append(
                PaymentItem(
                    item_code=pd["package_option"]["package_option_code"],
                    product_type="",
                    item_price=pd["package_option"]["price"],
                    item_name=pd["package_option"]["name"],
                    tax=0,
                    token_confirmation=pd["token_confirmation"],
                )
            )

            show_qris_payment_v2(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used=""
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '5' and payment_for == "REDEEM_VOUCHER":
            settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
        else:
            print("Purchase cancelled.")
            return False
    pause()
    sys.exit(0)

def handle_bundle_purchase(primary_package, is_enterprise_primary):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return

    # Details for the "Work & School" package to be bundled
    ws_family_code = "5d63dddd-4f90-4f4c-8438-2f005c20151f"
    ws_variant_name = "Work & School"
    ws_order = 6
    ws_is_enterprise = False

    print("Mengambil detail paket untuk bundling...")

    # 1. Get details for the primary package
    primary_package_detail = get_package(api_key, tokens, primary_package["code"])
    if not primary_package_detail:
        print("Gagal mengambil detail paket utama.")
        pause()
        return

    # 2. Get details for the Work & School package
    ws_package_detail = get_package_details(api_key, tokens, ws_family_code, ws_variant_name, ws_order, ws_is_enterprise)
    if not ws_package_detail:
        print("Gagal mengambil detail paket Work & School.")
        pause()
        return

    payment_items = [
        {
            "item_code": primary_package_detail["package_option"]["package_option_code"],
            "product_type": "",
            "item_price": primary_package_detail["package_option"]["price"],
            "item_name": f'{primary_package["variant_name"]} {primary_package["option_name"]}'.strip(),
            "tax": 0,
            "token_confirmation": primary_package_detail["token_confirmation"],
        },
        {
            "item_code": ws_package_detail["package_option"]["package_option_code"],
            "product_type": "",
            "item_price": ws_package_detail["package_option"]["price"],
            "item_name": f'{ws_package_detail["package_family"]["name"]} {ws_package_detail["package_option"]["name"]}'.strip(),
            "tax": 0,
            "token_confirmation": ws_package_detail["token_confirmation"],
        }
    ]

    total_price = sum(item['item_price'] for item in payment_items)

    clear_screen()
    print_header("🛒 Konfirmasi Pembelian Bundling")
    print("Anda akan membeli paket berikut:")
    for item in payment_items:
        print(f"  - {item['item_name']} (Rp {item['item_price']})")
    print(f"{'-'*55}")
    print(f"  Harga Total: Rp {total_price}")
    print(f"{'-'*55}")

    in_payment_menu = True
    while in_payment_menu:
        print("\nMetode Pembayaran:")
        print(f"  {Style.CYAN}[1]{Style.RESET}. 💳 E-Wallet (DANA, GoPay, OVO, ShopeePay)")
        print(f"  {Style.CYAN}[2]{Style.RESET}. 📱 QRIS")
        print(f"  {Style.CYAN}[3]{Style.RESET}. 💰 Pulsa")
        print(f"  {Style.CYAN}[0]{Style.RESET}. ↩️ Batal")
        print(f"{'-'*25}")
        
        input_method = input("Pilih metode (nomor): ")
        if input_method == "1":
            show_multipayment_v2(api_key, tokens, payment_items, "BUY_PACKAGE", True)
            input("Tekan enter untuk kembali...")
            in_payment_menu = False
        elif input_method == "2":
            show_qris_payment_v2(api_key, tokens, payment_items, "BUY_PACKAGE", True)
            input("Tekan enter untuk kembali...")
            in_payment_menu = False
        elif input_method == "3":
            settlement_balance(api_key, tokens, payment_items, "BUY_PACKAGE", True)
            input("Tekan enter untuk kembali...")
            in_payment_menu = False
        elif input_method == "0":
            print("Pembelian dibatalkan.")
            pause()
            in_payment_menu = False
        else:
            print("Metode tidak valid. Silahkan coba lagi.")
            pause()

    return


def get_packages_by_family(

    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None,
    return_package_detail: bool = False
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None
    
    packages = []
    
    # data = get_family(api_key, tokens, family_code, is_enterprise, migration_type)
    data = get_family_v2(
        api_key,
        tokens,
        family_code,
        is_enterprise,
        migration_type
    )
    if not data:
        print("Failed to load family data.")
        return None    
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        print_header(f"🛍️ Daftar Paket: {data['package_family']['name']}")
        print(f"  Family Code: {family_code}")
        print(f"  Tipe       : {data['package_family']['package_family_type']}")
        print(f"{'-'*55}")
        package_variants = data["package_variants"]
        
        option_number = 1
        variant_number = 1
        
        for variant in package_variants:
            variant_name = variant["name"]
            variant_code = variant["package_variant_code"]
            print(f"💠 Variant {variant_number}: {variant_name}")
            # print(f" Code: {variant_code}")
            for option in variant["package_options"]:
                option_name = option["name"]
                validity = option.get("validity", "")
                
                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": option["price"],
                    "validity": validity,
                    "code": option["package_option_code"],
                    "option_order": option["order"]
                })
                
                # print(json.dumps(option, indent=2))
                
                print(f"  {Style.CYAN}[{option_number:2d}]{Style.RESET}. {Style.YELLOW}{option_name}{Style.RESET} - {Style.GREEN}Rp {option['price']}{Style.RESET} ({Style.BLUE}{validity}{Style.RESET})")
                
                option_number += 1
            
            if variant_number < len(package_variants):
                print(f"{'-'*55}")
            variant_number += 1
        print(f"{'-'*55}")
        print("  🔢  Pilih nomor untuk melihat detail paket")
        print(f"  {Style.CYAN}[s]{Style.RESET}. 💾 Simpan Family Code ini")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke Menu Utama")
        print(f"{'-'*55}")
        pkg_choice = input("Pilihan > ")
        if pkg_choice == "00":
            in_package_menu = False
            return None
        elif pkg_choice.lower() == 's':
            family_name = data.get('package_family', {}).get('name', 'Unknown Family')
            if FamilyBookmarkInstance.add_bookmark(family_code, family_name):
                print(f"✅ Family Code '{family_name}' berhasil disimpan.")
            else:
                print(f"ℹ️ Family Code '{family_name}' sudah ada di bookmark.")
            pause()
            continue

        try:
            choice_num = int(pkg_choice)
            selected_pkg = next((p for p in packages if p["number"] == choice_num), None)
        except ValueError:
            print("Input tidak valid. Harap masukkan nomor.")
            pause()
            continue
        
        if not selected_pkg:
            print("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
            pause()
            continue

        if return_package_detail:
            print("Mengambil detail paket...")
            package_detail = get_package(api_key, tokens, selected_pkg["code"])
            if package_detail:
                display_name = f"{data['package_family']['name']} - {selected_pkg['variant_name']} - {selected_pkg['option_name']}"
                return package_detail, display_name
            else:
                print("Gagal mengambil detail paket.")
                pause()
                return None, None
        else:
            while True:
                print("\nPilih metode pembayaran:")
                print(f"  {Style.CYAN}[1]{Style.RESET}. Pembayaran Normal")
                print(f"  {Style.CYAN}[2]{Style.RESET}. Pembayaran Bundling (Work & School)")
                print(f"  {Style.CYAN}[00]{Style.RESET}. Kembali")
                payment_choice = input("Pilihan > ")

                if payment_choice == "1":
                    is_done = show_package_details(api_key, tokens, selected_pkg["code"], is_enterprise, option_order=selected_pkg["option_order"])
                    if is_done:
                        in_package_menu = False
                    break 
                elif payment_choice == "2":
                    handle_bundle_purchase(selected_pkg, is_enterprise)
                    in_package_menu = False
                    break
                elif payment_choice == "00":
                    break
                else:
                    print("Pilihan tidak valid.")
                    pause()
            continue
        
    return packages

def fetch_my_packages():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None
    
    id_token = tokens.get("id_token")
    
    path = "api/v8/packages/quota-details"
    
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }
    
    print("Fetching my packages...")
    res = send_api_request(api_key, path, payload, id_token, "POST")
    if res.get("status") != "SUCCESS":
        print("Failed to fetch packages")
        print("Response:", res)
        pause()
        return None
    
    quotas = res["data"]["quotas"]
    
    clear_screen()
    print_header("📦 Paket Saya")
    my_packages =[]
    num = 1
    for quota in quotas:
        quota_code = quota["quota_code"] # Can be used as option_code
        group_code = quota["group_code"]
        initial_name = quota["name"]
        # Ambil data kuota dari sumber utama (daftar paket)
        initial_remaining = quota.get("remaining", 0)
        initial_total = quota.get("total", 0)
        initial_is_unlimited = quota.get("is_unlimited", False)

        expired_at_timestamp_from_quota = quota.get("expired_at")
        
        print(f"fetching package no. {num} details...")
        package_details = get_package(api_key, tokens, quota_code)
        
        validity = "N/A"
        expired_at_str = "N/A"
        print(f"{'-'*55}")
        print(f"{Style.CYAN}Paket #{num}{Style.RESET}")
        
        if package_details:
            # Ambil data yang lebih akurat dari detail paket
            package_option = package_details.get("package_option", {})
            
            # Ambil data kuota dari detail paket sebagai sumber kedua
            detail_remaining = package_option.get("remaining", 0)
            detail_total = package_option.get("total", 0)
            detail_is_unlimited = package_option.get("is_unlimited", False)

            name = package_option.get("name", initial_name)
            validity = package_option.get("validity", "N/A")
            
            # Prioritaskan expired_at dari detail, fallback ke list quota awal
            expired_at_timestamp = package_option.get("expired_at") or expired_at_timestamp_from_quota
            if expired_at_timestamp:
                expired_at_str = datetime.fromtimestamp(expired_at_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  {Style.GREEN}Nama       : {name}{Style.RESET}")
            family_code = package_details.get("package_family", {}).get("package_family_code", "N/A")
            print(f"  {Style.GREEN}Family Code: {Style.YELLOW}{family_code}{Style.RESET}")
        else:
            # Fallback jika detail paket gagal diambil
            print(f"  {Style.GREEN}Nama       : {initial_name}{Style.RESET}")
        
        print(f"  {Style.GREEN}Quota Code : {quota_code}{Style.RESET}")
        print(f"  {Style.GREEN}Masa Aktif : {validity}{Style.RESET}")
        print(f"  {Style.GREEN}Exp. Date  : {expired_at_str}{Style.RESET}")
        print(f"  {Style.GREEN}Group Code : {group_code}{Style.RESET}")

        # --- PENAMBAHAN KODE UNTUK MENAMPILKAN BENEFITS ---
        benefits = quota.get("benefits", [])
        if benefits:
            print(f"  {Style.YELLOW}Benefits   :{Style.RESET}")
            for benefit in benefits:
                benefit_id = benefit.get("id", "")
                name = benefit.get("name", "")
                data_type = benefit.get("data_type", "N/A")
                
                print("  -----------------------------------------------------")
                print(f"    ID    : {benefit_id}")
                print(f"    Name  : {name}")
                print(f"    Type  : {data_type}")

                remaining = benefit.get("remaining", 0)
                total = benefit.get("total", 0)
                kuota_str = ""

                if data_type == "DATA":
                    remaining_val, remaining_unit = format_quota(remaining, True)
                    total_val, total_unit = format_quota(total, True)
                    
                    if total > 0:
                        kuota_str = f"{Style.RED}{remaining_val}{Style.RESET} {remaining_unit} / {Style.BLUE}{total_val}{Style.RESET} {total_unit}"
                    else:
                        kuota_str = f"{Style.RED}{remaining_val}{Style.RESET} {remaining_unit}"
                elif data_type == "VOICE":
                    if total > 0:
                        kuota_str = f"{remaining/60:.2f} / {total/60:.2f} menit"
                    else:
                        kuota_str = f"{remaining/60:.2f} menit"
                elif data_type == "TEXT":
                    if total > 0:
                        kuota_str = f"{remaining} / {total} SMS"
                    else:
                        kuota_str = f"{remaining} SMS"
                else:
                    if total > 0:
                        kuota_str = f"{remaining} / {total}"
                    else:
                        kuota_str = str(remaining)
                
                print(f"    Kuota : {kuota_str}")
            print("  -----------------------------------------------------")
        
        my_packages.append({
            "number": num,
            "quota_code": quota_code,
        })
        
        num += 1
    
    print(f"{'-'*55}")
    print("  🔢  Pilih nomor untuk membeli ulang (Rebuy)")
    print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke Menu Utama")
    print(f"{'-'*55}")
    choice = input("Pilihan > ")
    if choice == "00":
        return None
    selected_pkg = next((pkg for pkg in my_packages if str(pkg["number"]) == choice), None)
    
    if not selected_pkg:
        print("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
        return None
    
    is_done = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)
    if is_done:
        return None
        
    pause()
