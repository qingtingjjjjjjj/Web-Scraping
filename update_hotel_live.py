import requests
import os

ROOT_DIR = os.getcwd()
SOURCE_URL = "https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"

OUTPUT_DIR = os.path.join(ROOT_DIR, "专区")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "4K.txt")
GROUP_KEYWORD = "🇨🇳 4K"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_source():
    try:
        resp = requests.get(SOURCE_URL, timeout=15)
        resp.encoding = 'utf-8'
        print("✅ 源文件抓取成功, 长度:", len(resp.text))
        return resp.text
    except Exception as e:
        print(f"❌ 获取源失败: {e}")
        return ""

def extract_4k_streams(content):
    lines = content.splitlines()
    result = []
    include_line = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if GROUP_KEYWORD in line and ",#genre#" in line:
            include_line = True
            continue

        if include_line:
            if ",#genre#" in line:  # 遇到下一个分组停止
                break
            parts = line.split(",", 1)
            if len(parts) == 2:
                result.append(f"{parts[0]}: {parts[1]}")

    print(f"抓取到 {len(result)} 个 4K 直播源")
    return result

def save_file(path, lines):
    # 无论是否抓到源，都生成文件
    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 文件已生成: {os.path.abspath(path)}")

def main():
    content = fetch_source()
    streams = extract_4k_streams(content) if content else []
    save_file(OUTPUT_FILE, streams)

if __name__ == "__main__":
    main()
