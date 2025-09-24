import requests
from pathlib import Path

# 直播源 TXT 地址
HOTEL_TXT_URL = "https://raw.githubusercontent.com/lalifeier/IPTV/main/txt/hotel/全国.txt"

# 输出文件
OUTPUT_FILE = "live.txt"

# CCTV 频道列表
CCTV_CHANNELS = [f"CCTV{i}" for i in range(1, 16)] + ["CCTV5+", "CCTV16奥运匹克", "CCTV17", "CCTV赛事"]

def fetch_hotel_txt(url):
    resp = requests.get(url, timeout=15)
    resp.encoding = resp.apparent_encoding
    return resp.text.splitlines()

def process_lines(lines):
    cctv_group = []
    sat_group = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("中国电信") or line.startswith("#genre#"):
            continue
        if "," not in line:
            continue
        name, url = line.split(",", 1)
        if name in CCTV_CHANNELS:
            cctv_group.append(f"{name},{url}")
        else:
            sat_group.append(f"{name},{url}")
    return cctv_group, sat_group

def update_live_file(cctv, sat):
    content = ["#央视频道"] + cctv + ["", "#卫视频道"] + sat
    Path(OUTPUT_FILE).write_text("\n".join(content), encoding="utf-8")
    print(f"✅ 已更新 {OUTPUT_FILE}，共 {len(cctv)} 个央视，{len(sat)} 个卫视")

if __name__ == "__main__":
    lines = fetch_hotel_txt(HOTEL_TXT_URL)
    cctv_group, sat_group = process_lines(lines)
    update_live_file(cctv_group, sat_group)
