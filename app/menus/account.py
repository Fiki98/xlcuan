from app.client.engsel import get_otp, submit_otp
from app.menus.util import clear_screen, pause, print_header, Style
from app.service.auth import AuthInstance
    
def login_prompt(api_key: str):
    clear_screen()
    print_header(
        "🔐 Login Akun MyXL"
    )
    print("Masukan nomor XL Prabayar (Contoh 6281234567890):")
    phone_number = input("Nomor: ")

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print("Nomor tidak valid. Pastikan nomor diawali dengan '628' dan memiliki panjang yang benar.")
        return None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            return None
        print_header("OTP Berhasil dikirim ke nomor Anda.")
        
        otp = input("Masukkan OTP yang telah dikirim: ")
        if not otp.isdigit() or len(otp) != 6:
            print("OTP tidak valid. Pastikan OTP terdiri dari 6 digit angka.")
            pause()
            return None
        
        tokens = submit_otp(api_key, phone_number, otp)
        if not tokens:
            print("Gagal login. Periksa OTP dan coba lagi.")
            pause()
            return None
        
        print("Berhasil login!")
        
        return phone_number, tokens["refresh_token"]
    except Exception as e:
        return None, None

def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()
    
    # print(f"users: {users}")
    
    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()
        if AuthInstance.get_active_user() is None or add_user:
            # Jika tidak ada user atau sedang dalam mode tambah user,
            # langsung tampilkan prompt login.
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print("Gagal menambah akun. Silahkan coba lagi.")
                pause()
                continue
            
            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            
            
            if add_user:
                add_user = False
            continue
        
        print_header(
            "👤 Manajemen Akun"
        )
        print("Daftar Akun Tersimpan:")
        if not users or len(users) == 0:
            print("Tidak ada akun tersimpan.")

        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            active_marker = " 🟢 (Aktif)" if is_active else ""
            print(f"  {Style.CYAN}[{idx + 1}]{Style.RESET}. {user['number']}{active_marker}")
        
        print("\n" + ("-"*55))
        print("  🔢  Pilih nomor untuk ganti akun")
        print(f"  {Style.CYAN}[0]{Style.RESET}. ➕ Tambah Akun Baru")
        print(f"  {Style.CYAN}[99]{Style.RESET}. ❌ Hapus Akun (yang aktif)")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️ Kembali ke Menu Utama")
        print(f"{'-'*55}")
        input_str = input("Pilihan > ")
        if input_str == "00":
            in_account_menu = False
        elif input_str == "0":
            add_user = True
            continue
        elif input_str == "99":
            if not active_user:
                print("Tidak ada akun aktif untuk dihapus.")
                pause()
                continue
            confirm = input(f"Yakin ingin menghapus akun {active_user['number']}? (y/n): ")
            if confirm.lower() == 'y':
                AuthInstance.remove_refresh_token(active_user["number"])
                # AuthInstance.load_tokens()
                users = AuthInstance.refresh_tokens
                active_user = AuthInstance.get_active_user()
                print("Akun berhasil dihapus.")
                pause()
            else:
                print("Penghapusan akun dibatalkan.")
                pause()
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            AuthInstance.set_active_user(selected_user['number'])
            return
        else:
            print("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue
