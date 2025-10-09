import json
from app.client.engsel import segments
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause


def fetch_special_for_you(id_token: str, access_token: str) -> list:

    try:
        seg_data = segments(id_token, access_token)
        if not seg_data:
            return []

        packages = seg_data.get("special_for_you", [])
        special_packages = []

        for pkg in packages:
            try:
                name = pkg.get("name", "Unknown Package")
                kode_paket = pkg.get("action_param", "-")

                # harga
                original_price = int(pkg.get("price", 0))
                diskon_price = int(pkg.get("discount_price", original_price))

                # hitung diskon persen
                diskon_percent = 0
                if original_price > 0 and diskon_price < original_price:
                    diskon_percent = int(
                        round((original_price - diskon_price) / original_price * 100)
                    )

                special_packages.append(
                    {
                        "name": name,
                        "kode_paket": kode_paket,
                        "original_price": f"Rp {original_price:,}".replace(",", "."),
                        "diskon_price": f"Rp {diskon_price:,}".replace(",", "."),
                        "diskon_percent": diskon_percent,
                    }
                )
            except Exception as e:
                print(f"Gagal parse paket: {e}")
                continue

        # urutkan berdasarkan diskon tertinggi
        special_packages.sort(key=lambda x: x["diskon_percent"], reverse=True)
        return special_packages

    except Exception as e:
        print(f"Error fetch_special_for_you: {e}")
        return []


def show_special_for_you_menu(tokens, special_packages):
    clear_screen()
    print("-------------------------------------------------------")
    print("🔥 Daftar Paket Special Diskon Untukmu 🔥")
    print("-------------------------------------------------------")

    for idx, pkg in enumerate(special_packages, 1):
        print(f"{idx}. {pkg['name']}")
        print(f"   Kode Paket: {pkg['kode_paket']}")
        print(f"   Diskon: {pkg['diskon_percent']}%")
        print(f"   Harga Normal: ~~{pkg['original_price']}~~")
        print(f"   Harga Diskon: {pkg['diskon_price']}")
        print("-------------------------------------------------------")

    choice = input("Pilih nomor paket untuk lihat detail (atau '99' untuk batal): ").strip()

    if choice == "99":
        return

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(special_packages):
            selected_pkg = special_packages[choice_idx]
            print(f"Kamu memilih paket: {selected_pkg['name']}")
            pause()
            # panggil show_package_details dengan is_enterprise=False
            api_key = AuthInstance.api_key
            show_package_details(api_key, tokens, selected_pkg["kode_paket"], False)
        else:
            print("Pilihan tidak valid.")
            pause()
    except ValueError:
        print("Input tidak valid.")
        pause()
