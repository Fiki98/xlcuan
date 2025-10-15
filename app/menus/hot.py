import requests

from app.client.engsel import get_family, get_family_v2, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause, print_header, Style, print_bordered_line
from app.client.ewallet import show_multipayment_v2
from app.client.qris import show_qris_payment_v2
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem

def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        print_header("🔥 Paket Hot Pertama 🔥")
        url = "https://pastebin.com/raw/kH0nKg9Z"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("Gagal mengambil data hot package.")
            pause()
            return None

        hot_packages = response.json()

        width = 55
        border_top = f"{Style.MAGENTA}╔{'═' * (width - 2)}╗{Style.RESET}"
        border_bottom = f"{Style.MAGENTA}╚{'═' * (width - 2)}╝{Style.RESET}"
        line_separator = f"{Style.MAGENTA}╟{'─' * (width - 2)}╢{Style.RESET}"

        for idx, p in enumerate(hot_packages):
            package_name = f"{p.get('family_name')} - {p.get('variant_name')} - {p.get('option_name')}"
            
            print(border_top)
            validity_str = f" ({p.get('validity', '')})" if p.get('validity') else ""
            print_bordered_line(f"{Style.CYAN}[{idx + 1}]{Style.RESET}. {package_name}{validity_str}", width)
            print(line_separator)
            print_bordered_line(f"     {Style.GREEN}Fam:{Style.RESET} {p.get('family_code', 'N/A')}", width)
            print_bordered_line(f"     {Style.YELLOW}Enterprise:{Style.RESET} {Style.BLUE + 'Ya' + Style.RESET if p.get('is_enterprise') else Style.RED + 'Tidak' + Style.RESET}", width)
            print(border_bottom)

        print("\n" + ("-"*55))
        print("  🔢  Pilih nomor untuk melihat detail paket")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke Menu Utama")
        print(f"{'-'*55}")
        choice = input("Pilihan > ")
        if choice == "00":
            in_bookmark_menu = False
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            variant_name = selected_bm["variant_name"]
            order = selected_bm["order"]
            is_enterprise = selected_bm["is_enterprise"]
            
            # Mengambil detail paket untuk menemukan option_code
            package_detail = get_package_details(api_key, tokens, family_code, variant_name, order, is_enterprise)

            if not package_detail:
                print("Gagal mengambil detail paket dari Hot Promo.")
                pause()
                continue

            option_code = package_detail.get("package_option", {}).get("package_option_code")
            
            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise, option_order=order)
            else:
                print("Tidak dapat menemukan kode opsi paket.")
                pause()
            
        else:
            print("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue

def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        print_header("🔥 Paket Hot Kedua 🔥")
        url = "https://pastebin.com/raw/xSSrLBJj"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("Gagal mengambil data hot package.")
            pause()
            return None

        hot_packages = response.json()

        width = 55
        border_top = f"{Style.MAGENTA}╔{'═' * (width - 2)}╗{Style.RESET}"
        border_bottom = f"{Style.MAGENTA}╚{'═' * (width - 2)}╝{Style.RESET}"
        line_separator = f"{Style.MAGENTA}╟{'─' * (width - 2)}╢{Style.RESET}"

        for idx, p in enumerate(hot_packages):
            print(border_top)
            print_bordered_line(f"{Style.CYAN}[{idx + 1}]{Style.RESET}. {p['name']}", width)
            print_bordered_line(f"     {Style.YELLOW}Harga:{Style.RESET} Rp {p['price']}", width)
            packages_in_bundle = p.get("packages", [])
            if packages_in_bundle:
                print(line_separator)
                print_bordered_line(f"     {Style.YELLOW}Isi Paket:{Style.RESET}", width)
                for pkg_item in packages_in_bundle: # type: ignore
                    print_bordered_line(f"       - {Style.GREEN}Fam:{Style.RESET} {pkg_item.get('family_code', 'N/A')}", width)
            print(border_bottom)

        
        print("\n" + ("-"*55))
        print("  🔢  Pilih nomor untuk membeli paket")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke Menu Utama")
        print(f"{'-'*55}")
        choice = input("Pilihan > ")
        if choice == "00":
            in_bookmark_menu = False
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                print("Paket tidak tersedia.")
                pause()
                continue
            
            payment_items = []
            for package in packages:
                package_detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                )
                
                # Force failed when one of the package detail is None
                if not package_detail:
                    print(f"Gagal mengambil detail paket untuk {package['family_code']}.")
                    return None
                
                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )
            
            clear_screen()
            print_header(f"🛒 Konfirmasi Pembelian: {selected_package['name']}")
            print(f"  Harga Total : Rp {selected_package['price']}")
            print(f"  Detail      : {selected_package['detail']}")
            print(f"{'-'*55}")
            
            in_payment_menu = True
            while in_payment_menu:
                print("\nMetode Pembayaran:")
                print(f"  {Style.CYAN}[1]{Style.RESET}. 💳 E-Wallet (DANA, GoPay, OVO, ShopeePay)")
                print(f"  {Style.CYAN}[2]{Style.RESET}. 📱 QRIS")
                print(f"  {Style.CYAN}[3]{Style.RESET}. 💰 Pulsa")
                print(f"  {Style.CYAN}[0]{Style.RESET}. ↩️ Kembali")
                print(f"{'-'*25}")
                
                input_method = input("Pilih metode (nomor): ")
                if input_method == "1":
                    show_multipayment_v2(
                        api_key,
                        tokens,
                        payment_items,
                        "BUY_PACKAGE",
                        True
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False
                    return None
                elif input_method == "2":
                    show_qris_payment_v2(
                        api_key,
                        tokens,
                        payment_items,
                        "BUY_PACKAGE",
                        True
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False
                    return None
                elif input_method == "3":
                    settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "BUY_PACKAGE",
                        True
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False
                    return None
                elif input_method == "0":
                    in_payment_menu = False
                    continue
                else:
                    print("Metode tidak valid. Silahkan coba lagi.")
                    pause()
                    continue       
            
        else:
            print("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue
