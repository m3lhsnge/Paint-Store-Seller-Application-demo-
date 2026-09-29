import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000/api"

def make_request(method, url, data=None, headers=None):
    if headers is None:
        headers = {}
    if data is not None:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))
    except Exception as e:
        return 500, {"error": str(e)}

def print_result(step, status, data):
    if status >= 400:
        print(f"[FAIL] {step} BAŞARISIZ! Status: {status}")
        print(data)
        sys.exit(1)
    else:
        print(f"[OK] {step} BAŞARILI!")
        return data

print("--- DEMO BOYA APP TEST BAŞLIYOR ---")

# 1. Login
status, data = make_request("POST", f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123"})
data = print_result("Login (admin)", status, data)
token = data["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Get User Info
status, data = make_request("GET", f"{BASE_URL}/auth/me", headers=headers)
me = print_result("Kullanıcı Bilgisi Çekme", status, data)
print(f"   Aktif Kullanıcı: {me['username']} (Rol: {me['role']}, Şube: {me['branch_name']})")

# 3. List Categories & Materials
status, data = make_request("GET", f"{BASE_URL}/materials/categories", headers=headers)
cats = print_result("Kategorileri Listeleme", status, data)

status, data = make_request("GET", f"{BASE_URL}/materials", headers=headers)
mats = print_result("Hammaddeleri Listeleme", status, data)
if len(mats) == 0:
    print("[FAIL] Hammadde bulunamadı, test devam edemez!")
    sys.exit(1)

# 4. Create Customer
cust_payload = {"company_name": "Test Otomotiv A.Ş.", "contact_info": "test@oto.com"}
status, data = make_request("POST", f"{BASE_URL}/customers", data=cust_payload, headers=headers)
cust = print_result("Yeni Firma Ekleme", status, data)

# 5. Simulate Recipe
sim_payload = {
    "items": [
        {"raw_material_id": mats[0]["id"], "weight_gr": 150},
        {"raw_material_id": mats[1]["id"], "weight_gr": 50}
    ]
}
status, data = make_request("POST", f"{BASE_URL}/recipes/simulate", data=sim_payload, headers=headers)
sim = print_result("Reçete Simülasyonu", status, data)
print(f"   Simülasyon Sonucu: Toplam Maliyet {sim['total_cost']} TL, Renk: {sim['mixed_hex_code']}")

# 6. Create Recipe
recipe_payload = {
    "customer_id": cust["id"],
    "custom_paint_code": "TEST-001",
    "notes": "Otomasyon testi ile oluşturuldu",
    "margin_percentage": 25.0,
    "items": [
        {"raw_material_id": mats[0]["id"], "weight_gr": 150},
        {"raw_material_id": mats[1]["id"], "weight_gr": 50}
    ]
}
status, data = make_request("POST", f"{BASE_URL}/recipes", data=recipe_payload, headers=headers)
recipe = print_result("Reçete Kaydetme", status, data)
print(f"   Yeni Reçete ID: {recipe['id']}, Satış Fiyatı: {recipe['final_selling_price']} TL")

# 7. Create Recipe without Customer (opsiyonel firma kontrolü)
recipe_no_cust_payload = {
    "custom_paint_code": "TEST-002-NOCUST",
    "margin_percentage": 10.0,
    "items": [
        {"raw_material_id": mats[0]["id"], "weight_gr": 100}
    ]
}
status, data = make_request("POST", f"{BASE_URL}/recipes", data=recipe_no_cust_payload, headers=headers)
recipe2 = print_result("Firma Seçmeden Reçete Kaydetme (Opsiyonel testi)", status, data)

# 8. List Recipes
status, data = make_request("GET", f"{BASE_URL}/recipes", headers=headers)
recipes = print_result("Reçeteleri Listeleme", status, data)
print(f"   Şubedeki toplam reçete sayısı: {len(recipes)}")

# 9. Switch Branch (Admin)
status, data = make_request("POST", f"{BASE_URL}/auth/switch-branch", data={"branch_name": "Şube B"}, headers=headers)
switch = print_result("Şube Değiştirme (Şube B'ye geçiş)", status, data)
new_token = switch["access_token"]
headers2 = {"Authorization": f"Bearer {new_token}"}

# 10. List Recipes in New Branch (should be different)
status, data = make_request("GET", f"{BASE_URL}/recipes", headers=headers2)
recipes2 = print_result("Yeni Şubedeki Reçeteleri Listeleme", status, data)
print(f"   Şube B'deki toplam reçete sayısı: {len(recipes2)}")

print("\n[DONE] TÜM TESTLER BAŞARIYLA TAMAMLANDI!")
