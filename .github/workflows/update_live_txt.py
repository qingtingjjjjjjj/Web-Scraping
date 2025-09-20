import requests
import os
import re

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

live_file = "live.txt"

# 两个接口
sources = {
    "M3U": "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt",
    "TXT": "https://raw.githubusercontent.com/lucheng7996/TE/refs/heads/main/outfiles/beijing_cucc.txt"
}

# 存放不同组
yangshi, weishi = [], []

def simplify_name(name: str) -> str:
    """简化频道名，例如 CCTV1HD -> CCTV1"""
    match = re.match(r"(CCTV\d+)", name)
    if match:
        return match.group(1)
    return name.strip()

def fetch_source(name, url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        print(f"{GREEN}[{name}] 抓取成功，共 {len(resp.text.splitlines())} 行{RESET}")
        return resp.text.splitlines()
    except Exception as e:
        print(f"{RED}[{name}] 抓取失败: {e}{RESET}")
        return []

# 抓取两个接口
lines_m3u = fetch_source("M3U", sources["M3U"])
lines_txt = fetch_source("TXT", sources["TXT"])

# 解析 M3U
current_group, current_name = None, None
for line in lines_m3u:
    if line.startswith("#EXTINF"):
        current_name = line.split(",")[-1].strip()
        current_name = simplify_name(current_name)
        if "央视" in line:
            current_group = "yangshi"
        elif "卫视" in line:
            current_group = "weishi"
        else:
            current_group = None
    elif line.startswith("http") and current_group and current_name:
        record = f"{current_name},{line.strip()}"
        if current_group == "yangshi":
            yangshi.append(record)
        elif current_group == "weishi":
            weishi.append(record)

# 解析 TXT (假设格式: 频道名,URL)
for line in lines_txt:
    if "," in line:
        name, url = line.split(",", 1)
        name = simplify_name(name)
        if "CCTV" in name:
            yangshi.append(f"{name},{url.strip()}")
        elif "卫视" in name:
            weishi.append(f"{name},{url.strip()}")

if not yangshi and not weishi:
    print(f"{RED}抓取到的直播源为空，保留旧的 live.txt 文件{RESET}")
    exit(0)

# ===== 读取原有 live.txt =====
if os.path.exists(live_file):
    with open(live_file, "r", encoding="utf-8") as f:
        old_lines = f.read().splitlines()
else:
    old_lines = []

# 分组标签
yangshi_tag = "央视频道,#genre#"
weishi_tag = "卫视频道,#genre#"

def update_group(existing_lines, tag, new_records):
    """在分组最前面插入新抓取源，按频道名覆盖上一次抓取的源"""
    if tag not in existing_lines:
        return existing_lines + ["", tag] + new_records + [""]

    idx = existing_lines.index(tag) + 1
    end_idx = idx
    while end_idx < len(existing_lines) and existing_lines[end_idx].strip() != "" and not existing_lines[end_idx].endswith(",#genre#"):
        end_idx += 1

    group_lines = existing_lines[idx:end_idx]

    new_names = {rec.split(",")[0] for rec in new_records}
    filtered_group = [line for line in group_lines if line.split(",")[0] not in new_names]

    updated_group = new_records + filtered_group

    return existing_lines[:idx] + updated_group + existing_lines[end_idx:]

# ===== 更新两个分组 =====
lines_after_yangshi = update_group(old_lines, yangshi_tag, yangshi)
lines_after_weishi = update_group(lines_after_yangshi, weishi_tag, weishi)

# ===== 写回 live.txt =====
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_after_weishi))

# ===== 日志输出 =====
def log_channels(source_name, name, records, color):
    print(f"{color}[{source_name}] {name}: 新增 {len(records)} 条{RESET}")
    for i, rec in enumerate(records, 1):
        channel, url = rec.split(",", 1)
        print(f"{color}{i}. {channel} -> {url}{RESET}")

log_channels("M3U+TXT", "央视频道", yangshi, GREEN)
log_channels("M3U+TXT", "卫视频道", weishi, YELLOW)
print(f"{RED}更新完成，已覆盖上一次抓取的源，保留组内其他直播源和其他分组。{RESET}")
