from datetime import datetime, timezone, timedelta

from app.client.engsel import get_transaction_history, get_payment_status
from app.menus.util import clear_screen, print_header, pause, Style

def show_transaction_history(api_key, tokens):
    """Menampilkan riwayat transaksi pengguna."""
    page = 1
    limit = 30
    while True:
        clear_screen()
        print_header("📜 RIWAYAT TRANSAKSI 📜")
        print(f"Menampilkan Halaman: {page}")
        print("-" * 55)
        
        history = []
        try:
            print("Mengambil riwayat transaksi...", end="\r")
            data = get_transaction_history(api_key, tokens, page, limit)
            if data and data.get("status") == "SUCCESS":
                history = data.get("data", {}).get("list", [])
            else:
                print(f"{Style.RED}Gagal mengambil data: {data.get('message', 'Status bukan SUCCESS')}{Style.RESET}")
                pause()
                break
        except Exception as e:
            print(f"{Style.RED}Terjadi error: {e}{Style.RESET}")
            pause()
            break
        
        if not history:
            print("\nTidak ada riwayat transaksi ditemukan.")
            if page > 1:
                print("Ini adalah halaman terakhir.")
        else:
            for idx, trx in enumerate(history, start=1):
                try:
                    # Timestamp dari API adalah unix timestamp (detik sejak epoch) dalam UTC.
                    timestamp_s = int(trx.get("timestamp", "0"))
                    dt_utc = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
                    dt_object = dt_utc.astimezone(timezone(timedelta(hours=0)))
                    formatted_time = dt_object.strftime("%d %B %Y, %H:%M:%S WIB")
                except (ValueError, TypeError):
                    formatted_time = "Invalid Timestamp"

                print(f"  {Style.CYAN}[{idx}]{Style.RESET}. {Style.BOLD}{trx.get('title', 'N/A')}{Style.RESET}")
                print(f"     - Harga           : {trx.get('price', 'N/A')}")
                print(f"     - Tanggal         : {formatted_time}")
                print(f"     - Metode Pembayaran: {trx.get('payment_method_label', 'N/A')}")
                status_transaksi = trx.get('status', 'N/A')
                status_pembayaran = trx.get('payment_status', 'N/A')
                print(f"     - Status Transaksi : {status_transaksi}")
                print(f"     - Status Pembayaran: {status_pembayaran}")
                print("-" * 55)

        print("\nNavigasi & Opsi:")
        print("  [n] Halaman Berikutnya (Next)")
        if page > 1:
            print("  [p] Halaman Sebelumnya (Previous)")
        print("  [r] Refresh Halaman Ini")
        print("  [99] Kembali")
        choice = input("\nPilihan > ")

        if choice.lower() == 'n':
            page += 1
        elif choice.lower() == 'p' and page > 1:
            page -= 1
        elif choice.lower() == 'r':
            continue
        elif choice == "99":
            break
        else:
            print("Pilihan tidak valid.")
            pause()