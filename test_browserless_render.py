#!/usr/bin/env python3
# test_browserless_render.py - Test chiavi Browserless su Render

import requests
import time
import os
from datetime import datetime

# ================ CHIAVI FUNZIONANTI (testate in locale) ====================
BROWSERLESS_KEYS = [
    "2UG2N7qWFYK8FpG61e2f9913ec3368d2f02f87839db356dcc",
    "2UG2Ovzb5pkwkdua0d400b43082a6ad138fc947b98ad962ba",
    "2UG2QjLUmcxfw9Kfc631f82350b42772cfe9291bfbaf2ed27",
    "2UG2RgbTdpVTYBOf5942d35cd9f3da7b52af0bd115b1b3bdf",
    "2UG2TlpDxsQJn2Wd1f204756127d4ac2136b41bd01baaa0ca",
    "2UG2VwLUuefvx2T691bc9e7bd958eaebca5928b349ccdb6b0",
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
HEALTH_CHECK_PORT = int(os.environ.get('PORT', 10000))

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def test_key(api_key):
    """Testa una singola chiave con una query minimale"""
    query = """
mutation {
  goto(url: "https://www.easyhits4u.com/logon/", waitUntil: networkIdle, timeout: 30000) {
    status
  }
}
"""
    url = f"{BROWSERLESS_URL}?token={api_key}"
    
    try:
        start = time.time()
        response = requests.post(url, json={"query": query}, timeout=45)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            return "✅ FUNZIONA", elapsed
        elif response.status_code == 401:
            return "❌ SCADUTA", elapsed
        elif response.status_code == 408:
            return "⏰ TIMEOUT", elapsed
        else:
            return f"⚠️ HTTP {response.status_code}", elapsed
    except requests.exceptions.Timeout:
        return "⏰ TIMEOUT", 45
    except Exception as e:
        return f"❌ ERRORE: {str(e)[:30]}", 0

def main():
    print("=" * 60)
    print("🧪 TEST CHIAVI BROWSERLESS SU RENDER")
    print(f"📊 Totale chiavi: {len(BROWSERLESS_KEYS)}")
    print(f"🏥 Health check porta: {HEALTH_CHECK_PORT}")
    print("=" * 60)
    
    risultati = {"✅ FUNZIONA": [], "❌ SCADUTA": [], "⏰ TIMEOUT": [], "⚠️ ALTRO": []}
    
    for i, key in enumerate(BROWSERLESS_KEYS):
        status, elapsed = test_key(key)
        risultati[status if status in risultati else "⚠️ ALTRO"].append(key)
        print(f"   [{i+1:3d}/{len(BROWSERLESS_KEYS)}] {key[:10]}... → {status} ({elapsed:.1f}s)")
        time.sleep(0.5)  # Piccola pausa tra le richieste
    
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO")
    print("=" * 60)
    print(f"✅ FUNZIONA: {len(risultati['✅ FUNZIONA'])}")
    print(f"❌ SCADUTA: {len(risultati['❌ SCADUTA'])}")
    print(f"⏰ TIMEOUT: {len(risultati['⏰ TIMEOUT'])}")
    
    if risultati["✅ FUNZIONA"]:
        print(f"\n🔑 Chiavi funzionanti su Render ({len(risultati['✅ FUNZIONA'])}):")
        for key in risultati["✅ FUNZIONA"]:
            print(f"   {key}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()