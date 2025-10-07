import requests
import subprocess
import concurrent.futures
import time
import os

# ===== 配置 =====
LIVE_FILE = "live.txt"             # 原始直播源列表
OUTPUT_FILE = "live_checked.txt"   # 测试通过后的输出文件
RETRIES = 2                        # 请求重试次数
TIMEOUT = 3                        # 请求超时时间（秒）
MAX_LATENCY = 10                   # 最大允许延迟（秒）
CONCURRENT_WORKERS = 25            # 并发线程数

# ===== 测试 HTTP 是否可访问 =====
def test_http(url):
    for _ in range(RETRIES):
        try:
            r = requests.head(url, timeout=TIMEOUT)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            time.sleep(0.5)
    return False

# ===== 测试 m3u8 是否可播放 =====
def test_playable(url):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-analyzeduration", "2000000",          # 分析时长约 2 秒
                "-timeout", str(TIMEOUT * 1000000),    # 微秒单位
                "-i", url
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception:
        return False

# ===== 测试延迟 =====
def measure_latency(url):
    try:
        start = time.time()
        requests.head(url, timeout=TIMEOUT)
        return time.time() - start
    except:
        return float('inf')

# ===== 测试单条直播源 =====
def test_source(line):
    line = line.strip()
    if not line or "," not in line:
        return None
    name, url = line.split(",", 1)

    # HTTP 请求检查
    if not test_http(url):
        return None

    # 延迟过滤
    latency = measure_latency(url)
    if latency > MAX_LATENCY:
        return None

    # ffprobe 播放检测
    if not test_playable(url):
        return None

    return f"{name},{url}"

# ===== 读取直播源 =====
with open(LIVE_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# ===== 并发测速 =====
checked_sources = []
with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
    results = executor.map(test_source, lines)
    for r in results:
        if r:
            checked_sources.append(r)

# ===== 写入输出文件 =====
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(checked_sources))

print(f"✅ 测试完成，共 {len(checked_sources)} 个直播源可用，已写入 {OUTPUT_FILE}")
