import requests
import os

# 直播源 URL
SOURCE_URL = "https://hk.gh-proxy.com/https://raw.githubusercontent.com/AnonymousOrz/Mytv/refs/heads/master/output/Mytv.txt"

# 输出文件路径
CCTV_FILE = "专区/央视频道.txt"
SAT_FILE = "专区/卫视频道.txt"

# 创建目录
os.makedirs("专区", exist_ok=True)

CCTV_KEYS = ["CCTV"]
SAT_KEYS = ["卫视"]

def fetch_source():
    resp = requests.get(SOURCE_URL, timeout=15)
    resp.raise_for_status()
    resp.encoding = 'utf-8'
    return resp.text

def split_channels(content):
    lines = content.splitlines()
    cctv_list = []
    sat_list = []
    for line in lines:
        if not line.strip():
            continue
        # 跳过运营商标签
        if line.startswith("中国电信") or line.startswith("中国移动") or line.startswith("中国联通"):
            continue
        name = line.split(",")[0]
        if any(k in name for k in CCTV_KEYS):
            cctv_list.append(line)
        elif any(k in name for k in SAT_KEYS):
            sat_list.append(line)
    return cctv_list, sat_list

def save_file(path, lines):
    if lines:  # 只有有内容才写入文件
        with open(path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

def main():
    content = fetch_source()
    cctv_list, sat_list = split_channels(content)
    save_file(CCTV_FILE, cctv_list)
    save_file(SAT_FILE, sat_list)
    print(f"✅ 文件生成完成：{CCTV_FILE}, {SAT_FILE}")
    print(f"📌 仅包含直播源，不生成任何分组标记")

if __name__ == "__main__":
    main()
