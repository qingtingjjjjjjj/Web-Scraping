import requests
import os
import re

# 直播源 URL
SOURCE_URL = "https://ghfast.top/https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"

# 输出文件
OUTPUT_FILE = "专区/央视频道.txt"

# 创建目录
os.makedirs("专区", exist_ok=True)

# 4K 分组关键字
GROUP_4K = ["4K", "Ultra HD", "UHD"]

def fetch_source():
    resp = requests.get(SOURCE_URL, timeout=10)
    resp.encoding = 'utf-8'
    return resp.text

def extract_4k_channels(content):
    """
    提取所有包含4K关键字的频道及其分组和直播源
    """
    lines = content.splitlines()
    result = []
    include_line = False  # 是否写入当前行

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过运营商行
        if line.startswith("中国电信") or line.startswith("中国移动") or line.startswith("中国联通"):
            continue

        # 处理分组行
        if line.startswith("📡") and "#genre#" in line:
            include_line = False  # 默认不写
            if any(k.lower() in line.lower() for k in GROUP_4K):
                include_line = True
            if include_line:
                result.append(line)
            continue

        # 判断EXTINF行是否包含4K
        if line.startswith("#EXTINF"):
            if any(k.lower() in line.lower() for k in GROUP_4K):
                include_line = True
                result.append(line)
            continue

        # URL 行，如果前一行是4K频道则写入
        if include_line and line.startswith("http"):
            result.append(line)

    return result

def save_file(path, lines):
    with open(path, "a", encoding="utf-8-sig") as f:  # 使用追加模式
        for line in lines:
            f.write(line + "\n")

def main():
    content = fetch_source()
    channels_4k = extract_4k_channels(content)
    save_file(OUTPUT_FILE, channels_4k)
    print(f"✅ 已追加 {len([l for l in channels_4k if l.startswith('http')])} 个4K频道到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
