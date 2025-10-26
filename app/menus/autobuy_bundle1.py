import json
import base64
import qrcode
import time
from app.client.engsel import get_package_details
from app.client.ewallet import settlement_multipayment_v2
from app.menus.util import clear_screen, print_header, pause, Style
from app.client.qris import settlement_qris_v2, get_qris_code
from app.service.auth import AuthInstance
from app.client.balance import settlement_balance

# Definisi bundle paket
BUNDLES = [
    {
        "menu_title": "Kuota Edukasi +7GB (QRIS)",
        "payment_method": "QRIS",
        "display_price": "Rp. 3500 (Refund)",
        "data": {
            "name": "Add On Youtube 24GB (Gandengan Xtra Combo)",
            "price": "Rp.1000",
            "detail": "Support E-Wallet & QRIS.\\nHanya bisa dibeli kalau punya XCP/XCVP tertentu.\\nTidak akumulasi, beli ulang jika sudah habis.\\nMasa aktif mengikuti paket XCP/XCVP.",
            "packages": [
                {
                    "family_name": "Kuota Bersama",
                    "family_code": "d018a3ad-172f-433c-b291-f574f4b6fbad",
                    "is_enterprise": None,
                    "variant_name": "Kuota Bersama",
                    "option_name": "Kuota HP Sekeluarga 50GB",
                    "order": 3
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 5GB",
                    "order": 5
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 2GB",
                    "order": 6
                }
            ]
        }
    },
    {
        "menu_title": "Kuota Edukasi +7GB (ShopeePay)",
        "payment_method": "SHOPEEPAY",
        "display_price": "Rp. 3500 (Refund)",
        "data": {
            "name": "Add On Youtube 24GB (Gandengan Xtra Combo)",
            "price": "Rp.1000",
            "detail": "Support E-Wallet & QRIS.\\nHanya bisa dibeli kalau punya XCP/XCVP tertentu.\\nTidak akumulasi, beli ulang jika sudah habis.\\nMasa aktif mengikuti paket XCP/XCVP.",
            "packages": [
                {
                    "family_name": "Kuota Bersama",
                    "family_code": "d018a3ad-172f-433c-b291-f574f4b6fbad",
                    "is_enterprise": None,
                    "variant_name": "Kuota Bersama",
                    "option_name": "Kuota HP Sekeluarga 50GB",
                    "order": 3
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 5GB",
                    "order": 5
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 2GB",
                    "order": 6
                }
            ]
        }
    },
    {
        "menu_title": "Conference +5Gb (QRIS)",
        "payment_method": "QRIS",
        "display_price": "Rp. 4000 (Refund)",
        "data": {
            "name": "Conference +5Gb (QRIS)",
            "price": "Rp.4000",
            "detail": "Support E-Wallet & QRIS.",
            "packages": [
                {
                    "family_name": "Kuota Bersama",
                    "family_code": "d018a3ad-172f-433c-b291-f574f4b6fbad",
                    "is_enterprise": None,
                    "variant_name": "Kuota Bersama",
                    "option_name": "Kuota HP Sekeluarga 50GB",
                    "order": 3
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Conference 5GB",
                    "order": 2
                }
            ]
        }
    },
    {
        "menu_title": "Conference +5Gb (ShopeePay)",
        "payment_method": "SHOPEEPAY",
        "display_price": "Rp. 4000 (Refund)",
        "data": {
            "name": "Conference +5Gb (ShopeePay)",
            "price": "Rp.4000",
            "detail": "Support E-Wallet & QRIS.",
            "packages": [
                {
                    "family_name": "Kuota Bersama",
                    "family_code": "d018a3ad-172f-433c-b291-f574f4b6fbad",
                    "is_enterprise": None,
                    "variant_name": "Kuota Bersama",
                    "option_name": "Kuota HP Sekeluarga 50GB",
                    "order": 3
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Conference 5GB",
                    "order": 2
                }
            ]
        }
    },
]

def execute_autobuy(bundle_data, payment_method):
    """Mengeksekusi pembelian bundle dan menampilkan link pembayaran."""
    active_user = AuthInstance.get_active_user()
    if not active_user:
        print("Silakan login terlebih dahulu.")
        pause()
        return

    # 1. Ambil detail setiap paket untuk membuat payment_items
    payment_items = []
    total_bundle_price = 0
    for package in bundle_data["packages"]:
        package_detail = get_package_details(
            AuthInstance.api_key,
            active_user["tokens"],
            package.get("family_code"),
            package.get("variant_code") or package.get("variant_name"),
            package.get("order"),
            package.get("is_enterprise"),
            silent=False
        )
        if not package_detail:
            print(f"\n{Style.RED}Gagal mengambil detail untuk paket: {package.get('option_name')}{Style.RESET}")
            pause()
            return

        item_price = package_detail["package_option"]["price"]
        total_bundle_price += item_price
        payment_items.append({
            "item_code": package_detail["package_option"]["package_option_code"],
            "product_type": "",
            "item_price": item_price,
            "item_name": f"{package_detail.get('package_detail_variant', {}).get('name', '')} {package_detail['package_option']['name']}".strip(),
            "tax": 0,
            "token_confirmation": package_detail["token_confirmation"],
        })

    # 2. Lakukan settlement berdasarkan metode pembayaran
    if payment_method == "QRIS":
        print("Memproses pembayaran dengan QRIS...")
        transaction_id = settlement_qris_v2(
            AuthInstance.api_key,
            active_user["tokens"],
            payment_items,
            "BUY_PACKAGE",
            ask_overwrite=False,
            amount_overwrite=total_bundle_price
        )

        if not transaction_id:
            print(f"\n{Style.RED}Gagal membuat transaksi QRIS.{Style.RESET}")
        else:
            print("Mengambil kode QRIS...")
            qris_data = get_qris_code(AuthInstance.api_key, active_user["tokens"], transaction_id)
            if qris_data:
                print(f"\n{Style.GREEN}Kode QRIS berhasil dibuat! Silakan scan.{Style.RESET}")
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=1, border=1)
                qr.add_data(qris_data)
                qr.make(fit=True)
                qr.print_ascii(invert=True)
                qris_b64 = base64.urlsafe_b64encode(qris_data.encode()).decode()
                print(f"\nAtau buka link berikut untuk melihat QRIS:\nhttps://ki-ar-kod.netlify.app/?data={qris_b64}")
            else:
                print(f"\n{Style.RED}Gagal mengambil data QRIS setelah transaksi dibuat.{Style.RESET}")

    elif payment_method == "SHOPEEPAY":
        print("Memproses pembayaran dengan ShopeePay...")
        settlement_response = settlement_multipayment_v2(
            AuthInstance.api_key, active_user["tokens"], payment_items, "", "SHOPEEPAY", "BUY_PACKAGE", 
            ask_overwrite=False, amount_overwrite=total_bundle_price
        )
        
        if not settlement_response or settlement_response.get("status") != "SUCCESS":
            print(f"\n{Style.RED}Gagal membuat transaksi ShopeePay.{Style.RESET}")
            print(f"Error: {settlement_response}")
        else:
            deeplink = settlement_response["data"].get("deeplink", "")
            if deeplink:
                print(f"\n{Style.GREEN}Silakan selesaikan pembayaran melalui link berikut:{Style.RESET}\n{deeplink}")
            else:
                print(f"\n{Style.RED}Gagal mendapatkan link pembayaran ShopeePay.{Style.RESET}")
    else:
        print(f"\n{Style.RED}Metode pembayaran '{payment_method}' tidak didukung.{Style.RESET}")

    pause()

def execute_unlimited_vidio_autobuy():
    """Mengeksekusi pembelian Unlimited Vidio Auto pilot Buy (Qris)."""
    active_user = AuthInstance.get_active_user()
    if not active_user:
        print("Silakan login terlebih dahulu.")
        pause()
        return

    # 1. Cek validity harga pada beberapa paket
    print("Memeriksa harga paket, mohon tunggu...")
    packages_to_check = [
        { "order": 1, "expected_price": 99000, "variant_name": "For Xtra Combo", "option_name": "Premium" },
        { "order": 2, "expected_price": 75000, "variant_name": "For Xtra Combo", "option_name": "VIP" },
        { "order": 3, "expected_price": 51000, "variant_name": "For Xtra Combo", "option_name": "Plus" },
        { "order": 4, "expected_price": 33000, "variant_name": "For Xtra Combo", "option_name": "Basic" },
    ]

    package_details_list = []
    prices_match_count = 0

    for pkg_info in packages_to_check:
        detail = get_package_details(
            AuthInstance.api_key,
            active_user["tokens"],
            "08a3b1e6-8e78-4e45-a540-b40f06871cfe",
            pkg_info["variant_name"],
            pkg_info["order"],
            None, # is_enterprise
            silent=True
        )
        if not detail:
            print(f"\n{Style.RED}Gagal mengambil detail untuk paket order: {pkg_info['order']}{Style.RESET}")
            pause()
            return
        
        # Tambahkan 'order' ke dalam detail paket untuk referensi nanti
        detail['order_from_request'] = pkg_info['order']
        package_details_list.append(detail)
        actual_price = detail["package_option"]["price"]
        if actual_price == pkg_info["expected_price"]:
            prices_match_count += 1

    # 2. Jika tidak ada harga yang sesuai
    if prices_match_count == 0:
        print(f"\n{Style.RED}> ⚠️ Harga paket tidak sesuai dengan ketentuan pembelian. ⚠️\n🚫 Ulangi besok hari atau buang kartumu GANTI DENGAN YANG BARU 🔥😎{Style.RESET}")
        pause()
        return

    # 3. Jika sebagian harga sesuai, langsung ke step 6
    elif 0 < prices_match_count < len(packages_to_check):
        print("Beberapa harga sesuai, langsung ke proses payment Unlimited Tiktok...")
        # Langsung ke step 6 (pembelian paket Tiktok)

    # 4. Jika semua harga sesuai, lanjutkan dengan pembelian pulsa dan timer
    else: # prices_match_count == len(packages_to_check)
        print("Semua harga sesuai, melanjutkan proses payment...")
        
        # Ambil detail paket Basic (order 4) dari list yang sudah di-fetch
        package_detail_basic = next((d for d in package_details_list if d.get('order_from_request') == 4), None)

        if not package_detail_basic:
            print(f"\n{Style.RED}Gagal menemukan detail paket Basic (order 4) yang sudah di-fetch.{Style.RESET}")
            pause()
            return

        price_basic = package_detail_basic["package_option"]["price"]

        payment_items_1 = [{
            "item_code": package_detail_basic["package_option"]["package_option_code"],
            "product_type": "",
            "item_price": price_basic,
            "item_name": f"{package_detail_basic.get('package_detail_variant', {}).get('name', '')} {package_detail_basic['package_option']['name']}".strip(),
            "tax": 0,
            "token_confirmation": package_detail_basic["token_confirmation"],
        }]
        
        settlement_response = settlement_balance(
            AuthInstance.api_key,
            active_user["tokens"],
            payment_items_1,
            "BUY_PACKAGE",
            ask_overwrite=False, # Jangan tanya overwrite
            amount_used="first"
        )

        if not settlement_response or settlement_response.get("status") != "SUCCESS":
            print(f"\n{Style.RED}Gagal melakukan pembayaran dengan pulsa.{Style.RESET}")
            print(f"Error: {settlement_response}")
            pause()
            return

        # 5. Timer 10 menit
        print("\nTunggu waktu 2 Menit, jangan tutup Script/Termux")
        try:
            for i in range(120, 0, -1):
                print(f"\r{Style.YELLOW}Waktu tersisa: {i//60:02d}:{i%60:02d}{Style.RESET}", end="")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nProses dibatalkan oleh pengguna.")
            return
            
        print("\n")

        # Refresh token
        print("Refreshing token...")
        if not AuthInstance.renew_active_user_token():
            print(f"\n{Style.RED}Gagal merefresh token.{Style.RESET}")
            pause()
            return
        print("- Active user token renewed successfully - fetching package")
        active_user = AuthInstance.get_active_user() # get updated tokens

    # 6. Lanjut cek paket Tiktok
    print("Mengambil detail paket Vidio...")
    package_tiktok_info = {
        "family_name": "Unlimited Turbo",
        "family_code": "08a3b1e6-8e78-4e45-a540-b40f06871cfe",
        "is_enterprise": None,
        "variant_name": "For Xtra Combo",
        "option_name": "Netflix",
        "order": 5
    }

    package_detail_tiktok = get_package_details(
        AuthInstance.api_key,
        active_user["tokens"],
        package_tiktok_info.get("family_code"),
        package_tiktok_info.get("variant_name"),
        package_tiktok_info.get("order"),
        package_tiktok_info.get("is_enterprise"),
        silent=False
    )

    if not package_detail_tiktok:
        print(f"\n{Style.RED}Gagal mengambil detail untuk paket: {package_tiktok_info.get('option_name')}{Style.RESET}")
        pause()
        return

    # 7. Lanjut payment dengan metode Qris
    payment_items_2 = [{
        "item_code": package_detail_tiktok["package_option"]["package_option_code"],
        "product_type": "",
        "item_price": package_detail_tiktok["package_option"]["price"],
        "item_name": f"{package_detail_tiktok.get('package_detail_variant', {}).get('name', '')} {package_detail_tiktok['package_option']['name']}".strip(),
        "tax": 0,
        "token_confirmation": package_detail_tiktok["token_confirmation"],
    }]

    # 8. Qris muncul
    print("Memproses pembayaran dengan QRIS...")
    transaction_id = settlement_qris_v2(
        AuthInstance.api_key,
        active_user["tokens"],
        payment_items_2,
        "BUY_PACKAGE",
        ask_overwrite=False,
        amount_overwrite=30000
    )

    if not transaction_id:
        print(f"\n{Style.RED}Gagal membuat transaksi QRIS.{Style.RESET}")
    else:
        print("Mengambil kode QRIS...")
        qris_data = get_qris_code(AuthInstance.api_key, active_user["tokens"], transaction_id)
        if qris_data:
            print(f"\n{Style.GREEN}Kode QRIS berhasil dibuat! Silakan scan.{Style.RESET}")
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=1, border=1)
            qr.add_data(qris_data)
            qr.make(fit=True)
            qr.print_ascii(invert=True)
            qris_b64 = base64.urlsafe_b64encode(qris_data.encode()).decode()
            print(f"\nAtau buka link berikut untuk melihat QRIS:\nhttps://ki-ar-kod.netlify.app/?data={qris_b64}")
        else:
            print(f"\n{Style.RED}Gagal mengambil data QRIS setelah transaksi dibuat.{Style.RESET}")
    
    pause()

def show_autobuy_bundle_menu():
    """Menampilkan menu untuk auto-buy bundle."""
    clear_screen()
    print_header("✨ AUTOBUY BUNDLE (HIDDEN) ✨")
    for i, bundle in enumerate(BUNDLES, 1):
        print(f"  [{i}] {bundle['menu_title']}. || {bundle['display_price']}")
    print("  [5] Unlimited Tiktok Auto pilot Buy (Qris) || Rp. 30000")
    print("\n  [99] Kembali ke Menu Utama")
    print(f"{'-'*55}")
    choice = input("Pilihan > ")

    if choice.isdigit() and 1 <= int(choice) <= len(BUNDLES):
        selected_bundle = BUNDLES[int(choice) - 1]
        execute_autobuy(selected_bundle["data"], selected_bundle["payment_method"])
    elif choice == "5":
        execute_unlimited_vidio_autobuy()
    elif choice == "99":
        return
    else:
        print("Pilihan tidak valid.")
        pause()
