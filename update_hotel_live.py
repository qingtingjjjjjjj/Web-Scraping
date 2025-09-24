import requests

# 直播源 URL
SOURCE_URL = "https://raw.githubusercontent.com/lalifeier/IPTV/main/txt/hotel/全国.txt"

# 输出文件
RAW_FILE = "hotel.txt"
GROUPED_FILE = "hotel_grouped.txt"

# 央视频道关键字
CCTV_KEYS = ["CCTV"]
# 卫视频道关键字
SAT_KEYS = ["卫视"]

def fetch_source():
    resp = requests.get(SOURCE_URL)
    resp.encoding = 'utf-8'
    return resp.text

def save_raw(content):
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def generate_grouped(content):
    lines = content.splitlines()
    grouped = {"央视频道": [], "卫视频道": [], "其他频道": []}
    for line in lines:
        if not line.strip() or line.startswith("中国电信") or line.startswith("中国移动") or line.startswith("中国联通"):
            # 分组标题保留原样
            grouped["其他频道"].append(line)
            continue
        name = line.split(",")[0]
        if any(k in name for k in CCTV_KEYS):
            grouped["央视频道"].append(line)
        elif any(k in name for k in SAT_KEYS):
            grouped["卫视频道"].append(line)
        else:
            grouped["其他频道"].append(line)

    with open(GROUPED_FILE, "w", encoding="utf-8") as f:
        for group_name, items in grouped.items():
            f.write(f"=== {group_name} ===\n")
            for item in items:
                f.write(item + "\n")
            f.write("\n")

def main():
    content = fetch_source()
    save_raw(content)
    generate_grouped(content)
    print("✅ 文件生成完成：", RAW_FILE, GROUPED_FILE)

if __name__ == "__main__":
    main()
