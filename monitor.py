import subprocess
from datetime import datetime
import time
import re
import os


PING_DELAY_THRESHOLD = 1000
LOG_FILE = "ping.log"
TRACEROUTE_COOLDOWN_SECONDS = 60

TARGETS = {
    "router": os.environ.get("ROUTER_IP"),
    "google_dns": "8.8.8.8",
    "cloudflare_dns": "1.1.1.1",
}

def main():
    packet_lost = {name: False for name in TARGETS}
    traceroute_permission = {name: False for name in TARGETS}
    traceroute_time = {name: 0 for name in TARGETS}

    while True:
        for name, ip in TARGETS.items():

            result_ping = run_ping(ip)

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #正規表現
            #\d → 数字
            #. → 小数点も許可
            #+ → 1文字以上続く
            match = re.search(r"time=([\d.]+)", result_ping.stdout)

            ping_time = None

            # match.group(1)で取得した文字列をfloatに変換
            if match:
                ping_time = float(match.group(1))
                
            #result_ping.returncode 0 応答あり, 1 応答なし
            if result_ping.returncode != 0:
                if not packet_lost[name]:
                    with open(LOG_FILE, "a") as f:
                        f.write(f"{now}\n")
                        f.write(f"{name}:packet loss\n")
                        f.write("パケットロス検知\n")
                        f.write("\n")

                packet_lost[name] = True
            else:
                if packet_lost[name]:
                    with open(LOG_FILE, "a") as f:
                        f.write(f"{now}\n")
                        f.write(f"{name}:recovered\n")
                        f.write("パケットロス回復\n")
                        f.write("\n")

                if ping_time is not None and ping_time > PING_DELAY_THRESHOLD:
                    if not traceroute_permission[name]:
                        try:
                            result_traceroute = run_traceroute(ip)

                            with open(LOG_FILE, "a") as f:
                                f.write(f"{now}\n")
                                f.write(f"traceroute:{name}\n")
                                f.write(f"{result_traceroute.stdout}\n")
                                f.write("\n")

                        except subprocess.TimeoutExpired:
                            with open(LOG_FILE, "a") as f:
                                f.write(f"{now}\n")
                                f.write(f"traceroute:{name}:timeout\n\n")
                        
                        traceroute_time[name] = time.monotonic()
                        traceroute_permission[name] = True
                else:
                    if time.monotonic() - traceroute_time[name] >= TRACEROUTE_COOLDOWN_SECONDS:
                        traceroute_permission[name] = False

                    with open(LOG_FILE, "a") as f:
                        f.write(f"{now}\n")
                        f.write(f"{result_ping.stdout}\n")
                        f.write("\n")

                packet_lost[name] = False

            time.sleep(1)

def run_ping(ip):
    result = subprocess.run(
        ["ping", "-c", "1", ip],
        capture_output=True, #コマンドの出力をPython側で受け取るための指定
        text=True #受け取った出力を文字列（str）として扱う指定
    )
    return result

def run_traceroute(host):
    result = subprocess.run(
        ["traceroute", host],
        capture_output=True,
        text=True,
        timeout=15
    )
    return result

if __name__ == "__main__":
    main()