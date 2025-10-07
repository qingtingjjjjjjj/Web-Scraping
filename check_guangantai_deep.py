import requests
import subprocess
import concurrent.futures
import time
import csv
import os
import random

# ===== 配置 =====
LIVE_FILE = "live.txt"
WHITELIST_FILE = "港澳台_whitelist.txt"
RESULTS_FILE = "港澳台_test_results.csv"
RETRIES = 2
TIMEOUT = 3
CONCURRENT_WORKERS = 50
FFPROBE_STAGE = [
    ("5s", "5000000"),    # 初测 5 秒
    ("10s", "10000000"),  # 重测 10 秒
    ("15s", "15000000")   # 最终重测 15 秒
]
FFPROBE_SHORT_RETRY = "500000"  # 0.5 秒短重试
MAX_LATENCY = 20  # 秒

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

# ===== HTTP + 延迟测试 =====
def test_http_latency(url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url
    }
    for _ in range(RETRIES):
        try:
            start = time.time()
            r = requests.head(url, timeout=TIMEOUT, headers=headers)
            latency = time.time() - start
            if r.status_code == 200:
                return r.status_code, latency
        except:
            try:
                start = time.time()
                r = requests.get(url, stream=True, timeout=TIMEOUT, headers=headers)
                for _ in range(2):  # 前 10 KB ×2 次
                    r.iter_content(5120)
                latency = time.time() - start
                if r.status_code == 200:
                    return r.status_code, latency
            except:
                time.sleep(0.2)
    return None, None

# ===== ffprobe 播放检测 =====
def test_playable(url, analyzeduration):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-probesize", "10000000",
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
    stage_passed = ""
    retry_count = 0

    if status == 200 and latency <= MAX_LATENCY:
        for stage_name, duration in FFPROBE_STAGE:
            retry_count += 1
            playable = test_playable(url, duration)
            if playable:
                stage_passed = stage_name
                break
        # 对仍失败源增加短重试
        if not playable:
            retry_count += 1
            playable = test_playable(url, FFPROBE_SHORT_RETRY)
            if playable:
                stage_passed = "short_retry_0.5s"
            else:
                fail_reason = "ffprobe failed after all stages + short retry"
    else:
        fail_reason = "HTTP failed or latency too high"

    print(f"[{name}] HTTP: {status}, Latency: {round(latency,2) if latency else 'N/A'}s, "
          f"Playable: {playable}, Stage: {stage_passed}, Retries: {retry_count}, Fail: {fail_reason}")

    return {
        "name": name,
        "url": url,
        "http_status": status if status else "Fail",
        "latency": round(latency,2) if latency else None,
        "playable": playable,
        "stage_passed": stage_passed,
        "retry_count": retry_count,
        "fail_reason": fail_reason
    }

# ===== 提取港澳台分组 =====
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
    writer = csv.DictWriter(f, fieldnames=[
        "name","url","http_status","latency","playable",
        "stage_passed","retry_count","fail_reason"])
    writer.writeheader()
    writer.writerows(results)

print(f"✅ 港澳台测速完成，可用源写入 {WHITELIST_FILE}，详细结果写入 {RESULTS_FILE}")
