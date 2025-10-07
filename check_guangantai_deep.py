import requests
import subprocess
import concurrent.futures
import time
import csv
import os

# ===== 配置 =====
LIVE_FILE = "live.txt"               # 根目录总直播源文件
WHITELIST_FILE = "港澳台_whitelist.txt"
RESULTS_FILE = "港澳台_test_results.csv"
RETRIES = 2
TIMEOUT = 3
CONCURRENT_WORKERS = 50
FFPROBE_ANALYZE = "3000000"  # 微秒级分析，3 秒
MAX_LATENCY = 20             # 最大允许延迟（秒）

# ===== HTTP + 延迟测试 =====
def test_http_latency(url):
    for _ in range(RETRIES):
        try:
            start = time.time()
            # 尝试 HEAD 请求
            r = requests.head(url, timeout=TIMEOUT)
            latency = time.time() - start
            if r.status_code == 200:
                return r.status_code, latency
        except:
            # HEAD 请求失败，尝试 GET 前 1 KB
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

# ===== ffprobe 播放检测（失败重试一次） =====
def test_playable(url):
    for attempt in range(2):
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-analyzeduration", FFPROBE_ANALYZE,
                    "-timeout", str(TIMEOUT*1000000),
                    "-i", url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                return True
        except:
            time.sleep(0.2)
    return False

# ===== 测试单条源 =====
def test_source(line):
    line = line.strip()
    if not line or "," not in line:
        return None
    name, url = line.split(",", 1)
    
    status, latency = test_http_latency(url)
    playable = False
    if status == 200 and latency <= MAX_LATENCY:
        playable = test_playable(url)
    
    return {
        "name": name,
        "url": url,
        "http_status": status if status else "Fail",
        "latency": round(latency, 2) if latency else None,
        "playable": playable
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
    writer = csv.DictWriter(f, fieldnames=["name","url","http_status","latency","playable"])
    writer.writeheader()
    writer.writerows(results)

print(f"✅ 港澳台测速完成，可用源写入 {WHITELIST_FILE}，详细结果写入 {RESULTS_FILE}")
