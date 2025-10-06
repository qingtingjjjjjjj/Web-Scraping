import requests
import os

# 配置
SOURCE_URL = "https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"
OUTPUT_DIR = "专区"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "央视频道.txt")

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 获取源文件
def fetch_source(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"❌ 获取源失败: {e}")
        return ""

# 提取 4K 分组
def extract_4k_group(content):
    lines = content.splitlines()
    result = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 过滤 4K 分组行
        if line.startswith("4K,#genre#"):
            continue

        # 提取频道名称和 URL
        parts = line.split(",", 1)
        if len(parts) == 2:
            result.append(f"{parts[0]}: {parts[1]}")

    return result

# 保存到文件
def save_file(path, lines):
    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 文件已生成: {path}")

# 主函数
def main():
    content = fetch_source(SOURCE_URL)
    if not content:
        return

    group_lines = extract_4k_group(content)

    if not group_lines:
        print("⚠️ 没有抓取到 4K 分组内容")
        return

    # 保存文件
    save_file(OUTPUT_FILE, group_lines)

if __name__ == "__main__":
    main()
