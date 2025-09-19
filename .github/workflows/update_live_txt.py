import requests
import os

# 抓取 M3U
url = "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"
resp = requests.get(url)
resp.raise_for_status()
lines = resp.text.splitlines()

# 分组
yangshi, weishi = [], []
yangshi_names, weishi_names = [], []  # 用于日志输出频道名字
current_group = None
current_name = None

for line in lines:
    if line.startswith("#EXTINF"):
        current_name = line.split(",")[-1].strip()
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
print(f"总共新插入 {len(yangshi)+len(weishi)} 条记录到 live.txt\n")

print("新增央视频道频道列表:")
for name in yangshi_names:
    print(f"- {name}")

print("\n新增卫视频道频道列表:")
for name in weishi_names:
    print(f"- {name}")

# 读取原有 live.txt
live_file = "live.txt"
if os.path.exists(live_file):
    with open(live_file, "r", encoding="utf-8") as f:
        old_content = f.read()
else:
    old_content = ""

# 新内容 = 央视频道 + 卫视频道 + 原内容
new_content = "\n".join(yangshi + weishi) + ("\n" + old_content if old_content else "")

# 写回 live.txt
with open(live_file, "w", encoding="utf-8") as f:
    f.write(new_content)
