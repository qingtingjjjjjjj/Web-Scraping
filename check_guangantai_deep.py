import requests
import subprocess
import concurrent.futures
import time
import csv
import os

# ===== 配置 =====
LIVE_FILE = "live.txt"
WHITELIST_FILE = "港澳台_whitelist.txt"
RESULTS_FILE = "港澳台_test_results.csv"
RETRIES = 2
TIMEOUT = 3
CONCURRENT_WORKERS = 50
FFPROBE_INITIAL = "3000000"  # 初测 3 秒
FFPROBE_RETRY = "5000000"    # 重测 5 秒
MAX_LATENCY = 20             # 最大允许延迟（秒）

# ===== HTTP + 延迟测试 =====
def test_http_latency(url):
    for _ in range(RETRIES):
        try:
            start = time.time()
            r = requests.head(url, timeout=TIMEOUT)
            latency = time.time() - start
            if r.status_code == 200:
                return r.status_code, latency
        except:
            try:
                start = time.time()
                r = requests.get(url, stream=True, timeout=TIMEOUT)
                r.iter_content(1024)
                latency = time.time() - start
                if r.status_code == 200:
                    return r.status_code, latency
            except:
                time.sleep(0.2)
    return None, None

# ===== ffprobe 播放检测（初测/重测） =====
def test_playable(url, analyzeduration):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-analyzeduration", analyzeduration,
                "-timeout", str(TIMEOUT*1000000),
                "-i", url
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except:
        return False

# ===== 测试单条源 =====
def test_source(line):
    line = line.strip()
    if not line or "," not in line:
        return None
    name, url = line.split(",", 1)
    
    status, latency = test_http_latency(url)
    playable = False
    fail_reason = ""
    if status == 200 and latency <= MAX_LATENCY:
        # 初测 3 秒
        playable = test_playable(url, FFPROBE_INITIAL)
        if not playable:
            # 初测失败，重测 5 秒
            playable = test_playable(url, FFPROBE_RETRY)
            if not playable:
                fail_reason = "ffprobe failed"
    else:
        fail_reason = "HTTP failed or latency too high"

    return {
        "name": name,
        "url": url,
        "http_status": status if status else "Fail",
        "latency": round(latency, 2) if latency else None,
        "playable": playable,
        "fail_reason": fail_reason
    }

# ===== 从 live.txt 中提取港澳台分组 =====
def extract_guangantai(lines):
    group = []
    in_group = False
    for line in lines:
        line = line.strip()
        if line.startswith("港澳台,#genre#"):
            in_group = True
            continue
        if in_group:
            if line.endswith("#genre#") or line == "" or line.startswith("🇨🇳"):
                break
            group.append(line)
    return group

# ===== 读取 live.txt =====
with open(LIVE_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

guangantai_lines = extract_guangantai(lines)

# ===== 并发测速 =====
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
    for res in executor.map(test_source, guangantai_lines):
        if res:
            results.append(res)

# ===== 写入 whitelist.txt =====
with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
    for r in results:
        if r["http_status"] == 200 and r["playable"]:
            f.write(f"{r['name']},{r['url']}\n")

# ===== 写入 test_results.csv =====
with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name","url","http_status","latency","playable","fail_reason"])
    writer.writeheader()
    writer.writerows(results)

print(f"✅ 港澳台测速完成，可用源写入 {WHITELIST_FILE}，详细结果写入 {RESULTS_FILE}")
