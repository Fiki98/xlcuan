from app.client.engsel import get_family, get_family_v2
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause, print_header, Style
from app.service.bookmark import BookmarkInstance

def show_bookmark_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        print_header("🔖 Bookmark Paket")
        bookmarks = BookmarkInstance.get_bookmarks()
        if not bookmarks or len(bookmarks) == 0:
            print("Tidak ada bookmark tersimpan.")
            pause()
            return None
        
        print("Daftar Bookmark:")
        for idx, bm in enumerate(bookmarks):
            validity_str = f" ({bm.get('validity', '')})" if bm.get('validity') else ""
            print(f"  {Style.CYAN}[{idx + 1}]{Style.RESET}. {bm['family_name']} - {bm['variant_name']} - {bm['option_name']}{validity_str}")
        
        print("\n" + ("-"*55))
        print("  🔢  Pilih nomor untuk melihat detail paket")
        print(f"  {Style.CYAN}[99]{Style.RESET}. ❌ Hapus Bookmark")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️ Kembali ke Menu Utama")
        print(f"{'-'*55}")
        choice = input("Pilihan > ")
        if choice == "00":
            in_bookmark_menu = False
            return None
        elif choice == "99":
            del_choice = input("Masukan nomor bookmark yang ingin dihapus: ")
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                del_bm = bookmarks[int(del_choice) - 1]
                BookmarkInstance.remove_bookmark(
                    del_bm["family_code"],
                    del_bm.get("validity", ""),
                    del_bm["is_enterprise"],
                    del_bm["variant_name"],
                    del_bm["order"],
                )
            else:
                print("Input tidak valid. Silahkan coba lagi.")
                pause()
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]
            
            family_data = get_family_v2(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print("Gagal mengambil data family.")
                pause()
                continue
            
            package_variants = family_data["package_variants"]
            option_code = None
            for variant in package_variants:
                if variant["name"] == selected_bm["variant_name"]:
                    selected_variant = variant
                    
                    package_options = selected_variant["package_options"]
                    for option in package_options:
                        if option["order"] == selected_bm["order"]:
                            selected_option = option
                            option_code = selected_option["package_option_code"]
                            break
            
            if option_code:
                print(f"{option_code}")
                show_package_details(api_key, tokens, option_code, is_enterprise)            
            
        else:
            print("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue