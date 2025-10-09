from app.menus.package import get_packages_by_family
from app.menus.util import clear_screen, pause, print_header, Style
from app.service.family_bookmark import FamilyBookmarkInstance

def show_family_bookmark_menu():
    in_menu = True
    while in_menu:
        clear_screen()
        print_header("📚 Bookmark Family Code")
        
        bookmarks = FamilyBookmarkInstance.get_bookmarks()
        if not bookmarks:
            print("Tidak ada bookmark family code tersimpan.")
            pause()
            return

        print("Daftar Bookmark Family Code:")
        for idx, bm in enumerate(bookmarks):
            print(f"  {Style.CYAN}[{idx + 1}]{Style.RESET}. {bm['family_name']} ({bm['family_code']})")

        print("\n" + ("-"*55))
        print("  🔢  Pilih nomor untuk melihat daftar paket")
        print(f"  {Style.CYAN}[99]{Style.RESET}. ❌ Hapus Bookmark")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️ Kembali ke Menu Utama")
        print(f"{'-'*55}")
        
        choice = input("Pilihan > ")

        if choice == "00":
            in_menu = False
        elif choice == "99":
            del_choice_str = input("Masukkan nomor bookmark yang ingin dihapus: ")
            if del_choice_str.isdigit() and 1 <= int(del_choice_str) <= len(bookmarks):
                bm_to_delete = bookmarks[int(del_choice_str) - 1]
                if FamilyBookmarkInstance.remove_bookmark(bm_to_delete['family_code']):
                    print(f"Bookmark '{bm_to_delete['family_name']}' berhasil dihapus.")
                else:
                    print("Gagal menghapus bookmark.")
                pause()
            else:
                print("Pilihan tidak valid.")
                pause()
        elif choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            # Panggil fungsi untuk menampilkan paket berdasarkan family code
            get_packages_by_family(selected_bm['family_code'])
            # Setelah kembali dari get_packages_by_family, loop akan berlanjut
            # dan menampilkan menu bookmark lagi.
        else:
            print("Pilihan tidak valid.")
            pause()