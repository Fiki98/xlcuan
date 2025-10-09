import json
from app.client.balance import settlement_balance
from app.client.engsel import get_family_v2, get_package, get_package_details
from app.client.ewallet import show_multipayment_v2
from app.client.qris import show_qris_payment_v2
from app.menus.package import get_packages_by_family
from app.menus.util import clear_screen, pause, print_header, Style
from app.service.auth import AuthInstance
from app.service.bookmark import BookmarkInstance
from app.service.family_bookmark import FamilyBookmarkInstance
from app.type_dict import PaymentItem

def get_package_from_bookmark():
    """
    Menampilkan daftar bookmark dan mengembalikan detail paket yang dipilih.
    Mengembalikan tuple (package_detail, display_name).
    """
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    clear_screen()
    print_header("➕ Tambah Paket dari Bookmark")
    bookmarks = BookmarkInstance.get_bookmarks()
    if not bookmarks:
        print("Tidak ada bookmark tersimpan.")
        pause()
        return None, None

    for idx, bm in enumerate(bookmarks):
        validity_str = f" ({bm.get('validity', '')})" if bm.get('validity') else ""
        print(f"  {Style.CYAN}[{idx + 1}]{Style.RESET}. {bm['family_name']} - {bm['variant_name']} - {bm['option_name']}{validity_str}")
    
    print("\n" + ("-"*55))
    print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali")
    print(f"{'-'*55}")
    choice = input("Pilih nomor paket yang ingin ditambahkan > ")

    if choice == "00":
        return None, None

    if choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
        selected_bm = bookmarks[int(choice) - 1]
        
        # Ambil data family terlebih dahulu untuk menemukan variant_code
        family_data = get_family_v2(api_key, tokens, selected_bm['family_code'], selected_bm['is_enterprise'])
        if not family_data:
            print("Gagal mengambil data family untuk bookmark.")
            pause()
            return None, None

        # Cari variant_code berdasarkan variant_name dari bookmark
        variant_code = None
        for variant in family_data.get("package_variants", []):
            if variant.get("name") == selected_bm['variant_name']:
                variant_code = variant.get("package_variant_code")
                break

        print("Mengambil detail paket...")
        package_detail = get_package_details(
            api_key, tokens, 
            selected_bm['family_code'], 
            variant_code, # Gunakan variant_code yang sudah ditemukan
            selected_bm['order'], 
            selected_bm['is_enterprise']
        )
        
        if package_detail:
            display_name = f"{selected_bm['family_name']} - {selected_bm['variant_name']} - {selected_bm['option_name']}"
            return package_detail, display_name
        else:
            print("Gagal mengambil detail paket dari bookmark.")
            pause()
            return None, None
    else:
        print("Pilihan tidak valid.")
        pause()
        return None, None

def get_package_from_family_bookmark():
    """
    Menampilkan daftar bookmark family code dan mengembalikan detail paket yang dipilih.
    Mengembalikan tuple (package_detail, display_name).
    """
    clear_screen()
    print_header("➕ Tambah Paket dari Bookmark Family Code")
    
    bookmarks = FamilyBookmarkInstance.get_bookmarks()
    if not bookmarks:
        print("Tidak ada bookmark family code tersimpan.")
        pause()
        return None, None

    print("Daftar Bookmark Family Code:")
    for idx, bm in enumerate(bookmarks):
        print(f"  {Style.CYAN}[{idx + 1}]{Style.RESET}. {bm['family_name']} ({bm['family_code']})")

    print("\n" + ("-"*55))
    print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali")
    print(f"{'-'*55}")
    choice = input("Pilih nomor family code > ")

    if choice == "00":
        return None, None

    if choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
        selected_bm = bookmarks[int(choice) - 1]
        # Panggil get_packages_by_family untuk memilih paket dari family tersebut
        return get_packages_by_family(selected_bm['family_code'], return_package_detail=True)
    else:
        print("Pilihan tidak valid.")
        pause()
        return None, None

def show_bundle_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    cart_items: list[PaymentItem] = []
    display_cart = []
    total_price = 0

    in_bundle_menu = True
    while in_bundle_menu:
        clear_screen()
        print_header("🛒 Keranjang Paket Bundle")

        if not cart_items:
            print("Keranjang Anda masih kosong.")
        else:
            print("Isi Keranjang:")
            for i, item in enumerate(display_cart):
                print(f"  {Style.CYAN}[{i+1}]{Style.RESET}. {item['name']} - Rp {item['price']}")
            print(f"{'-'*55}")
            print(f"  Total Harga: Rp {total_price}")

        print("\n" + ("-"*55))
        print(f"  {Style.CYAN}[1]{Style.RESET}. ➕ Tambah Paket dari Bookmark")
        print(f"  {Style.CYAN}[2]{Style.RESET}. ➕ Tambah Paket dari Bookmark Family Code")
        print(f"  {Style.CYAN}[3]{Style.RESET}. ➕ Tambah Paket dari Family Code (Manual)")
        print(f"  {Style.CYAN}[4]{Style.RESET}. 🗑️ Hapus item dari keranjang")
        if cart_items:
            print(f"  {Style.CYAN}[5]{Style.RESET}. 💳 Lanjutkan ke Pembayaran")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️ Kembali ke Menu Utama")
        print(f"{'-'*55}")
        
        choice = input("Pilihan > ")

        if choice == '1':
            package_detail, display_name = get_package_from_bookmark()
            if package_detail:
                option = package_detail['package_option']
                cart_items.append(PaymentItem(
                    item_code=option['package_option_code'],
                    product_type="", item_price=option['price'],
                    item_name=option['name'], tax=0,
                    token_confirmation=package_detail['token_confirmation']
                ))
                display_cart.append({'name': display_name, 'price': option['price']})
                total_price += option['price']
                print(f"✅ Paket '{display_name}' berhasil ditambahkan ke keranjang.")
                pause()

        elif choice == '2':
            package_detail, display_name = get_package_from_family_bookmark()
            if package_detail:
                option = package_detail['package_option']
                cart_items.append(PaymentItem(
                    item_code=option['package_option_code'],
                    product_type="", item_price=option['price'],
                    item_name=option['name'], tax=0,
                    token_confirmation=package_detail['token_confirmation']
                ))
                display_cart.append({'name': display_name, 'price': option['price']})
                total_price += option['price']
                print(f"✅ Paket '{display_name}' berhasil ditambahkan ke keranjang.")
                pause()


        elif choice == '3':
            family_code = input("Masukkan Family Code: ")
            # Fungsi ini akan menampilkan daftar paket dan mengembalikan detail paket yg dipilih
            result = get_packages_by_family(family_code, return_package_detail=True)
            if not result:
                # get_packages_by_family sudah menangani pesan error, jadi kita hanya perlu lanjut.
                continue
            
            package_detail, display_name = result
            if package_detail:
                option = package_detail['package_option']
                cart_items.append(PaymentItem(
                    item_code=option['package_option_code'],
                    product_type="", item_price=option['price'],
                    item_name=option['name'], tax=0,
                    token_confirmation=package_detail['token_confirmation']
                ))
                display_cart.append({'name': display_name, 'price': option['price']})
                total_price += option['price']
                print(f"✅ Paket '{display_name}' berhasil ditambahkan ke keranjang.")
                pause()

        elif choice == '4' and cart_items:
            del_choice = input("Masukkan nomor item yang ingin dihapus: ")
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(cart_items):
                idx_to_del = int(del_choice) - 1
                removed_item = display_cart.pop(idx_to_del)
                cart_items.pop(idx_to_del)
                total_price -= removed_item['price']
                print(f"Item '{removed_item['name']}' telah dihapus.")
                pause()
            else:
                print("Nomor item tidak valid.")
                pause()

        elif choice == '5' and cart_items:
            clear_screen()
            print_header("💳 Konfirmasi Pembayaran Bundle")
            for i, item in enumerate(display_cart):
                print(f"  {i+1}. {item['name']} - Rp {item['price']}")
            print(f"{'-'*55}")
            print(f"  Total Pembayaran: Rp {total_price}")
            print(f"{'-'*55}")

            print("\nMetode Pembayaran:")
            print(f"  {Style.CYAN}[1]{Style.RESET}. 💳 E-Wallet (DANA, GoPay, OVO)")
            print(f"  {Style.CYAN}[2]{Style.RESET}. 💳 ShopeePay")
            print(f"  {Style.CYAN}[3]{Style.RESET}. 📱 QRIS")
            print(f"  {Style.CYAN}[4]{Style.RESET}. 💰 Pulsa")
            print(f"  {Style.CYAN}[0]{Style.RESET}. ↩️ Batal")
            print(f"{'-'*25}")
            
            method_choice = input("Pilih metode pembayaran > ")
            payment_for = "BUY_PACKAGE" # Asumsi

            if method_choice == '1':
                show_multipayment_v2(api_key, tokens, cart_items, payment_for, True, exclude_shopeepay=True)
            elif method_choice == '2':
                show_multipayment_v2(api_key, tokens, cart_items, payment_for, True, force_payment_method="SHOPEEPAY")
            elif method_choice == '3':
                show_qris_payment_v2(api_key, tokens, cart_items, payment_for, True)
            elif method_choice == '4':
                settlement_balance(api_key, tokens, cart_items, payment_for, True)
            else:
                continue
            
            input("\nTekan Enter untuk kembali ke menu utama...")
            in_bundle_menu = False

        elif choice == '00':
            in_bundle_menu = False

        else:
            print("Pilihan tidak valid.")
            pause()