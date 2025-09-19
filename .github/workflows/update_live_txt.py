import requests
import os
import re

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

url = "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"

# ===== 抓取 M3U =====
try:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
except Exception as e:
    print(f"{RED}抓取失败，保留旧的 live.txt 文件: {e}{RESET}")
    exit(0)  # 抓取失败，不覆盖文件

lines = resp.text.splitlines()
yangshi, weishi = [], []
current_group, current_name = None, None

def simplify_name(name):
    match = re.match(r"(CCTV\d+)", name)
    if match:
        return match.group(1)
    return name

for line in lines:
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

# ===== 抓取到源为空时，不覆盖旧文件 =====
if not yangshi and not weishi:
    print(f"{RED}抓取到的直播源为空，保留旧的 live.txt 文件{RESET}")
    exit(0)

live_file = "live.txt"
yangshi_tag = "央视频道,#genre#"
weishi_tag = "卫视频道,#genre#"

new_lines = []
if yangshi:
    new_lines += [yangshi_tag] + yangshi + [""]
if weishi:
    new_lines += [weishi_tag] + weishi + [""]

# ===== 覆盖写入 =====
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))

# ===== 日志输出 =====
def log_channels(name, records, color):
    print(f"{color}新增{name}数量: {len(records)}{RESET}")
    if records:
        for i, rec in enumerate(records, 1):
            channel_name = rec.split(',')[0]
            print(f"{color}{i}. {channel_name}{RESET}")

log_channels("央视频道", yangshi, GREEN)
log_channels("卫视频道", weishi, YELLOW)
print(f"{RED}更新完成，已覆盖旧源（保证抓取成功才覆盖）{RESET}")
