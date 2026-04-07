#!/usr/bin/env python3
# divellaeasy_auto_login.py - Versione con 22 chiavi funzionanti

import os
import time
import requests
import numpy as np
import cv2
import faiss
import json
import gc
import threading
from datetime import datetime
from datasets import load_dataset
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================ CHIAVI BROWSERLESS FUNZIONANTI (22 chiavi) ====================
BROWSERLESS_KEYS = [
    "2UG2N7qWFYK8FpG61e2f9913ec3368d2f02f87839db356dcc",
    "2UG2Ovzb5pkwkdua0d400b43082a6ad138fc947b98ad962ba",
    "2UG2QjLUmcxfw9Kfc631f82350b42772cfe9291bfbaf2ed27",
    "2UG2RgbTdpVTYBOf5942d35cd9f3da7b52af0bd115b1b3bdf",
    "2UG2TlpDxsQJn2Wd1f204756127d4ac2136b41bd01baaa0ca",
    "2UGdbQnmFCJwS9Vd714eb85438cf63d00a8f878a898cfe865",
    "2UGdcalCbtmQNCt0c0a65e134b1833ed5d77b0c27fec4df7a",
    "2UGdeyvPnuYf2tm78f5d97e862f004feef3a8e41dfd58b3ef",
    "2UGdfrLYfztPfpy65ea1648786cdfe855a89073f49a24fa15",
    "2UGdh0XeC72wcccb12714bdae43194a6a8647ce9a836d9cf9",
    "2UGdiXdiszEa5rw5c83ff671b0f30e6b45cb159d1b7a8f221",
    "2UH1q8Mnj1ERdcZf243e8d19a8e05da8998570d64e212cc3a",
    "2UH1rvpwwnyIqKYf3d2b847c23f1bf100eb78217b4abe399e",
    "2UH1tCPjVWSuutr98a6d9529fb8c03b457496afe6466ebac0",
    "2UH1uDTJQKxWMi750e2ad5d114a378275b4f4963b81476824",
    "2UH1xtruDYkpN6qafcf735210a0d390f38b7934fee7020509",
    "2UH1yEsOSdMyVgBb79e5d9f7283da3ab24b099772a221c0c1",
    "2UH200RyjgTPJAyd69e6979481a42076d9715120add383b2f",
    "2UH21NyLelnPOXN89ef213e06c030d3a20fe91f74ed023cd6",
    "2UH23g4Tjer24qYda1b38b3bf4995babae59f6ade1b5d80d5",
    "2UH24rd152tYgA9bfd616f9e0a1eee38c91957e77f7388367",
    "2UH26buZuikxxt088fe658690e962e79f00f03bae1c9c23d3",
]

BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"

# Account EasyHits4U
EASYHITS_EMAIL = "sandrominori50+Uinrzrgtlqe@gmail.com"
EASYHITS_PASSWORD = "DDnmVV45!!"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"

# ================ CONFIGURAZIONE ====================
DIM = 64
REQUEST_TIMEOUT = 15
ERRORI_DIR = "errori"
HEALTH_CHECK_PORT = int(os.environ.get('PORT', 10000))

current_key_index = 0
server_ready = False

dataset = None
classes_fast = None
faiss_index = None
vector_dim = 33

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_next_key():
    global current_key_index
    key = BROWSERLESS_KEYS[current_key_index % len(BROWSERLESS_KEYS)]
    current_key_index += 1
    log(f"   🔑 Usando chiave {current_key_index}/{len(BROWSERLESS_KEYS)}: {key[:10]}...")
    return key

def do_login():
    log("🔐 Esecuzione login via Browserless...")
    
    for attempt in range(len(BROWSERLESS_KEYS)):
        api_key = get_next_key()
        
        query = f"""
mutation {{
  goto(url: "https://www.easyhits4u.com/logon/", waitUntil: networkIdle, timeout: 60000) {{
    status
  }}
  solve(type: cloudflare, timeout: 60000) {{
    solved
    token
    time
  }}
  typeUsername: type(selector: "input[name='username']", text: "{EASYHITS_EMAIL}") {{
    time
  }}
  typePassword: type(selector: "input[name='password']", text: "{EASYHITS_PASSWORD}") {{
    time
  }}
  clickSubmit: click(selector: "button[type='submit'], input[type='submit']", timeout: 60000) {{
    time
  }}
  waitForNavigation(timeout: 60000) {{
    url
    status
  }}
}}
"""
        
        url = f"{BROWSERLESS_URL}?token={api_key}"
        
        try:
            log(f"   📡 Invio richiesta...")
            response = requests.post(url, json={"query": query}, timeout=120)
            log(f"   📡 Status: {response.status_code}")
            
            if response.status_code != 200:
                if response.status_code == 401:
                    log(f"   ⚠️ Chiave scaduta, passo alla prossima")
                continue
            
            data = response.json()
            if "errors" in data:
                log(f"   ❌ BQL error: {data['errors']}")
                continue
            
            solve_info = data.get("data", {}).get("solve", {})
            log(f"   🛡️ Turnstile solved: {solve_info.get('solved')}")
            
            if not solve_info.get("solved"):
                log(f"   ❌ Turnstile non risolto")
                continue
            
            nav_info = data.get("data", {}).get("waitForNavigation", {})
            log(f"   🧭 Navigazione: status={nav_info.get('status')}")
            
            cookies = response.cookies.get_dict()
            log(f"   🍪 Cookie ricevuti: {list(cookies.keys())}")
            
            if 'user_id' in cookies:
                log(f"   ✅ Login OK! user_id={cookies['user_id']}")
                return cookies
            else:
                log(f"   ❌ user_id non trovato")
                
        except Exception as e:
            log(f"   ❌ Errore: {e}")
            continue
    
    log("❌ Login fallito dopo tutti i tentativi")
    return None

# ================ HEALTH CHECK =====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
    def log_message(self, format, *args):
        pass

def run_health_server():
    global server_ready
    try:
        server = HTTPServer(('0.0.0.0', HEALTH_CHECK_PORT), HealthHandler)
        server_ready = True
        log(f"🏥 Health check server avviato sulla porta {HEALTH_CHECK_PORT}")
        server.serve_forever()
    except Exception as e:
        log(f"❌ ERRORE health check: {e}")
        server_ready = False

health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()
timeout = 10
while not server_ready and timeout > 0:
    time.sleep(0.5)
    timeout -= 0.5

# ================ DATASET =====================
def load_dataset_hf():
    global dataset, classes_fast, faiss_index
    log("📥 Caricamento dataset...")
    try:
        dataset = load_dataset("zenadazurli/easyhits4u-dataset", split="train", token=None)
        log(f"✅ Dataset caricato: {len(dataset)} vettori")
        class_names = dataset.features['y'].names
        classes_fast = {i: name for i, name in enumerate(class_names)}
        
        X_list = []
        batch_size = 500
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i+batch_size]
            X_list.append(np.array(batch['X'], dtype=np.float32))
        
        X_all = np.vstack(X_list)
        nlist = 100
        m = 3
        d = vector_dim
        quantizer = faiss.IndexFlatL2(d)
        index = faiss.IndexIVFPQ(quantizer, d, nlist, m, 8)
        index.train(X_all)
        index.add(X_all)
        faiss_index = index
        del X_list, X_all
        gc.collect()
        return True
    except Exception as e:
        log(f"❌ Errore dataset: {e}")
        return False

# ================ FUNZIONI PER IL SURF =====================
def centra_figura(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return cv2.resize(image, (DIM, DIM))
    cnt = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(cnt)
    crop = image[y:y+h, x:x+w]
    return cv2.resize(crop, (DIM, DIM))

def estrai_descrittori(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    circularity = aspect_ratio = 0.0
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        peri = cv2.arcLength(cnt, True)
        area = cv2.contourArea(cnt)
        if peri != 0:
            circularity = 4.0 * np.pi * area / (peri * peri)
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w)/h if h != 0 else 0.0
    moments = cv2.moments(thresh)
    hu = cv2.HuMoments(moments).flatten().tolist()
    h, w = img.shape[:2]
    cx, cy = w//2, h//2
    raggi = [int(min(h,w)*r) for r in (0.2, 0.4, 0.6, 0.8)]
    radiale = []
    for r in raggi:
        mask = np.zeros((h,w), np.uint8)
        cv2.circle(mask, (cx,cy), r, 255, -1)
        mean = cv2.mean(img, mask=mask)[:3]
        radiale.extend([m/255.0 for m in mean])
    spaziale = []
    quadranti = [(0,0,cx,cy), (cx,0,w,cy), (0,cy,cx,h), (cx,cy,w,h)]
    for (x1,y1,x2,y2) in quadranti:
        roi = img[y1:y2, x1:x2]
        if roi.size > 0:
            mean = cv2.mean(roi)[:3]
            spaziale.extend([m/255.0 for m in mean])
    vettore = radiale + spaziale + [circularity, aspect_ratio] + hu
    return np.array(vettore, dtype=float)

def get_features(img):
    img_centrata = centra_figura(img)
    return estrai_descrittori(img_centrata)

def predict(img_crop):
    if img_crop is None or img_crop.size == 0:
        return None
    features = get_features(img_crop).astype(np.float32).reshape(1, -1)
    distances, indices = faiss_index.search(features, 1)
    best_idx = indices[0][0]
    true_label_idx = dataset['y'][best_idx]
    return classes_fast.get(int(true_label_idx), "errore")

def crop_safe(img, coords):
    try:
        x1, y1, x2, y2 = map(int, coords.split(","))
    except:
        return None
    h, w = img.shape[:2]
    x1 = max(0, min(w-1, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h-1, y1))
    y2 = max(0, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return img[y1:y2, x1:x2]

def salva_errore(qpic, img, picmap, labels, chosen_idx, motivo, urlid=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(ERRORI_DIR, f"{timestamp}_{qpic}")
    os.makedirs(folder, exist_ok=True)
    full_path = os.path.join(folder, "full.jpg")
    cv2.imwrite(full_path, img)
    for i, p in enumerate(picmap):
        crop = crop_safe(img, p.get("coords", ""))
        if crop is not None and crop.size > 0:
            crop_path = os.path.join(folder, f"crop_{i+1}.jpg")
            cv2.imwrite(crop_path, crop)
    metadata = {"timestamp": timestamp, "qpic": qpic, "urlid": urlid, "motivo": motivo}
    with open(os.path.join(folder, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    log(f"📁 Errore salvato in {folder}")

def main():
    log("=" * 50)
    log("🚀 Avvio DivellaEasy - Auto Refresh (22 chiavi funzionanti)")
    
    if not load_dataset_hf():
        return
    
    while True:
        cookies = do_login()
        if not cookies:
            log("❌ Login fallito, riprovo tra 60 secondi...")
            time.sleep(60)
            continue
        
        COOKIE_STRING = f"sesids={cookies.get('sesids', '')}; user_id={cookies.get('user_id', '')}"
        log(f"🍪 Cookie: {COOKIE_STRING}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": COOKIE_STRING
        }
        session = requests.Session()
        captcha_counter = 0
        
        while True:
            try:
                r = session.post(
                    "https://www.easyhits4u.com/surf/?ajax=1&try=1",
                    headers=headers, verify=False, timeout=REQUEST_TIMEOUT
                )
                
                if r.status_code != 200:
                    log(f"❌ Status {r.status_code} - Cookie scaduti?")
                    break
                
                data = r.json()
                urlid = data.get("surfses", {}).get("urlid")
                qpic = data.get("surfses", {}).get("qpic")
                seconds = int(data.get("surfses", {}).get("seconds", 20))
                picmap = data.get("picmap", [])
                
                if not urlid or not qpic or not picmap or len(picmap) < 5:
                    log(f"❌ Dati incompleti - Cookie scaduti?")
                    break
                
                img_data = session.get(f"https://www.easyhits4u.com/simg/{qpic}.jpg", verify=False).content
                img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                crops = [crop_safe(img, p.get("coords", "")) for p in picmap]
                labels = [predict(c) for c in crops]
                log(f"Labels: {labels}")
                
                seen = {}
                chosen_idx = None
                for i, label in enumerate(labels):
                    if label and label != "errore":
                        if label in seen:
                            chosen_idx = seen[label]
                            break
                        seen[label] = i
                
                if chosen_idx is None:
                    log("❌ Nessun duplicato")
                    salva_errore(qpic, img, picmap, labels, None, "nessun_duplicato", urlid)
                    break
                
                time.sleep(seconds)
                word = picmap[chosen_idx]["value"]
                resp = session.get(
                    f"https://www.easyhits4u.com/surf/?f=surf&urlid={urlid}&surftype=2"
                    f"&ajax=1&word={word}&screen_width=1024&screen_height=768",
                    headers=headers, verify=False
                )
                
                if resp.json().get("warning") == "wrong_choice":
                    log("❌ Wrong choice")
                    salva_errore(qpic, img, picmap, labels, chosen_idx, "wrong_choice", urlid)
                    break
                
                captcha_counter += 1
                log(f"✅ OK - indice {chosen_idx} - Totale: {captcha_counter}")
                
                if captcha_counter % 10 == 0:
                    gc.collect()
                
                time.sleep(2)
                
            except Exception as e:
                log(f"❌ Errore: {e}")
                break
        
        log("🔄 Rinnovo sessione...")
        time.sleep(5)

if __name__ == "__main__":
    main()