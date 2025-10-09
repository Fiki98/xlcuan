import sys
import concurrent.futures
import app.config  # Load environment variables first
from app.util import format_quota
from app.config import HIDDEN_MENU_PIN
from app.menus.util import clear_screen, pause, print_header, Style, ascii_art
from app.client.engsel import *
from app.service.auth import AuthInstance
from app.menus.payment import show_transaction_history
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.family_bookmark import show_family_bookmark_menu
from app.menus.special import show_special_for_you_menu
from app.menus.bundle import show_bundle_menu
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.menus.autobuy_bundle import show_autobuy_bundle_menu
from app.menus.points import run_point_exchange
from app.service.sentry import enter_sentry_mode

def show_main_menu(number, balance, balance_expired_at, quota_info, profile_info, segments_data):
    clear_screen()
    expired_at_dt = datetime.fromtimestamp(balance_expired_at).strftime("%Y-%m-%d %H:%M:%S")

    quota_remaining_str = "N/A"
    if quota_info:
        remaining = quota_info.get("remaining", 0)
        total = quota_info.get("total", 0)
        remaining_formatted = format_quota(remaining)
        total_formatted = format_quota(total)
        quota_remaining_str = f"{remaining_formatted} / {total_formatted}"
        if quota_info.get("has_unlimited"):
            quota_remaining_str += " (Unlimited)"

    profile_name = profile_info.get("profile", {}).get("full_name", "Pengguna")
    tiers = segments_data.get("loyalty", {})
    notifications = segments_data.get("notification")
    special_packages = segments_data.get("special_packages")

    print_header("✨ MENU UTAMA ✨") 
    print(f"  {Style.GREEN}👤 Akun       : {profile_name} ({number}){Style.RESET}")
    print(f"{'-'*55}")
    print(f"  {Style.YELLOW}💰 Sisa Pulsa : Rp {balance}{Style.RESET}")
    print(f"  {Style.MAGENTA}📊 Sisa Kuota : {quota_remaining_str}{Style.RESET}")
    print(f"  {Style.BLUE}⏳ Masa Aktif : {expired_at_dt}{Style.RESET}")
    print(f"  {Style.GREEN}⭐ Tier       : {tiers.get('tier_name', '-')} ({tiers.get('current_point', 0)} poin){Style.RESET}")
    print(f"{'-'*55}")

    print(f"  {Style.BOLD}📢 Notifikasi:{Style.RESET}")
    if notifications:
        notif = notifications[0]
        print(f"  - {notif.get('title', '')}: {notif.get('body', '')}")
    
    print(f"  {Style.CYAN}[T]{Style.YELLOW} 🔥Unlimited Turbo Tiktok New Method | {Style.GREEN}💰Rp.30000{Style.RESET}")
    print(f"{'-'*55}")

    if special_packages:
        def score(pkg):
            return pkg.get("diskon_percent", 0) * pkg.get("kuota_gb", 0)

        special_packages_sorted = sorted(special_packages, key=score, reverse=True)
        best = special_packages_sorted[0]

        print(f"  {Style.BOLD}🔥 Paket Special Untukmu!{Style.RESET}")
        print(f"  {best['name']}")
        print(f"  Diskon {best['diskon_percent']}% | {Style.RED}~~Rp {best['original_price']:,}~~{Style.RESET} -> {Style.GREEN}Rp {best['diskon_price']:,}{Style.RESET}")
        print(f"  {Style.YELLOW}Pilih [s] untuk lihat semua paket spesial{Style.RESET}")
        print(f"{'-'*55}")

    print(f"{'-'*55}")
    print(f"  {Style.BOLD}Pilih Menu:{Style.RESET}")
    print(f"  {Style.CYAN}[1]{Style.RESET}. 👤 Login / Ganti Akun")
    print(f"  {Style.CYAN}[2]{Style.RESET}. 📦 Lihat Paket Saya")
    print(f"  {Style.CYAN}[3]{Style.RESET}. 📜 Riwayat Transaksi")
    print(f"  {Style.CYAN}[4]{Style.RESET}. 🔥 Beli Paket Hot Promo")
    print(f"  {Style.CYAN}[5]{Style.RESET}. 🔥 Beli Paket Hot Promo 2 (Bundling)")
    print(f"  {Style.CYAN}[6]{Style.RESET}. 🔍 Beli Paket Berdasarkan Family Code")
    print(f"  {Style.CYAN}[7]{Style.RESET}. 🛒 Beli Paket Bundle (Multi)")
    print(f"  {Style.CYAN}[8]{Style.RESET}. 🔖 Bookmark Paket")
    print(f"  {Style.CYAN}[9]{Style.RESET}. 📚 Bookmark Family Code")
    print(f"  {Style.CYAN}[0]{Style.RESET}. 🎁 Tukar Poin")
    print(f"  {Style.CYAN}[88]{Style.RESET}. 🕵️ Hidden Menu")
    print(f"  {Style.CYAN}[99]{Style.RESET}. 🚪 Keluar Aplikasi")
    print(f"{'-'*55}")

show_menu = True
def main():
    
    if ascii_art:
        ascii_art.to_terminal(columns=55)

    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            print("Memuat data, mohon tunggu...", end="\r")
            try:
                # Jalankan semua permintaan data secara bersamaan untuk mengurangi waktu tunggu
                balance = None
                segments_data = None
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    balance_future = executor.submit(get_balance, AuthInstance.api_key, active_user["tokens"]["id_token"])
                    quota_future = executor.submit(get_main_quota, AuthInstance.api_key, active_user["tokens"]["id_token"])
                    profile_future = executor.submit(login_info, AuthInstance.api_key, active_user["tokens"])

                    balance = balance_future.result()
                    balance_remaining = balance.get("remaining", 0) if balance else 0

                    segments_future = executor.submit(segments, AuthInstance.api_key, active_user["tokens"]["id_token"], active_user["tokens"]["access_token"], balance_remaining)

                    quota_info = quota_future.result()
                    profile_info = profile_future.result()
                    segments_data = segments_future.result()

                if quota_info is None:
                    print("Gagal mengambil data kuota.")
                    # Set default value to avoid crash
                    quota_info = {"remaining": 0, "total": 0, "has_unlimited": False}

                if profile_info is None:
                    print("Gagal mengambil data profil.")
                    profile_info = {}

                if segments_data is None:
                    print("Gagal mengambil data segmen.")
                    segments_data = {}

                balance_remaining = balance.get("remaining", 0) if balance else 0
                balance_expired_at = balance.get("expired_at", 0) if balance else 0

            except (Exception, concurrent.futures.CancelledError, concurrent.futures.TimeoutError) as e:
                print(f"Gagal memuat data: {e}")
                AuthInstance.set_active_user(None) # Logout on critical data fetch failure
                pause()
                continue
            
            show_main_menu(active_user["number"], balance_remaining, balance_expired_at, quota_info, profile_info, segments_data)

            choice = input("Pilihan > ")
            if choice == "1":
                show_account_menu()
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "4":
                show_hot_menu()
            elif choice == "5":
                show_hot_menu2()
            elif choice == "6":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            elif choice == "7":
                show_bundle_menu()
            elif choice == "8":
                show_bookmark_menu()
            elif choice == "9":
                show_family_bookmark_menu()
            elif choice == "0":
                run_point_exchange(active_user["tokens"])
            elif choice == "88":
                pin_input = input("Masukkan PIN untuk mengakses menu tersembunyi: ")
                if pin_input == HIDDEN_MENU_PIN:
                    show_autobuy_bundle_menu()
                else:
                    print(f"\n{Style.RED}PIN salah. Akses ditolak.{Style.RESET}")
                    pause()
                continue
            elif choice == "99":
                print("Exiting the application.")
                sys.exit(0)
            elif choice.lower() == "t":
                from app.menus.autobuy_bundle import execute_unlimited_tiktok_autobuy
                execute_unlimited_tiktok_autobuy()
            elif choice.lower() == "s":
                special_packages = segments_data.get("special_packages")
                if special_packages:
                    show_special_for_you_menu(active_user["tokens"], special_packages)
                else:
                    print("Tidak ada paket Special For You yang tersedia saat ini.")
                    pause()
            else:
                print("Invalid choice. Please try again.")
                pause()
        else:
            # Not logged in
            show_account_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting the application.")
    # except Exception as e:
    #     print(f"An error occurred: {e}")
