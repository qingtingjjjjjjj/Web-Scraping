import requests
import os
import re

# 抓取 M3U
url = "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"
resp = requests.get(url)
resp.raise_for_status()
lines = resp.text.splitlines()

# 分组
yangshi, weishi = [], []
yangshi_names, weishi_names = [], []
current_group = None
current_name = None

# CCTV 统一简化规则
def simplify_name(name):
    match = re.match(r"(CCTV\d+)", name)
    if match:
        return match.group(1)
    return name

for line in lines:
    if line.startswith("#EXTINF"):
        current_name = line.split(",")[-1].strip()
        current_name = simplify_name(current_name)  # 名称处理
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
            yangshi_names.append(current_name)
        elif current_group == "weishi":
            weishi.append(record)
            weishi_names.append(current_name)

# 日志输出
print(f"新抓取央视频道数量: {len(yangshi)}")
print(f"新抓取卫视频道数量: {len(weishi)}")
print("新增央视频道频道列表:", yangshi_names)
print("新增卫视频道频道列表:", weishi_names)

# live.txt 文件路径
live_file = "live.txt"
if os.path.exists(live_file):
    with open(live_file, "r", encoding="utf-8") as f:
        old_lines = f.read().splitlines()
else:
    old_lines = []

# 定义分组标签
yangshi_tag = "央视频道,#genre#"
weishi_tag = "卫视频道,#genre#"

# 找到分组起始位置
def insert_group(existing_lines, tag, new_records):
    if tag in existing_lines:
        idx = existing_lines.index(tag) + 1
        # 插入到分组最前面
        return existing_lines[:idx] + new_records + existing_lines[idx:]
    else:
        # 分组不存在，创建新分组放在文件最前面
        return [tag] + new_records + [""] + existing_lines

# 插入央视频道和卫视频道
lines_after_yangshi = insert_group(old_lines, yangshi_tag, yangshi)
lines_after_weishi = insert_group(lines_after_yangshi, weishi_tag, weishi)

# 写回 live.txt
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_after_weishi))

print("更新完成，已插入到对应分组最前面，CCTV频道名称已简化。")
