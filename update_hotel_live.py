import requests
import os

# 正确的直播源 URL
SOURCE_URL = "https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"
OUTPUT_DIR = "专区"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "4K.txt")  # 修改输出文件
GROUP_4K = "🇨🇳 4K"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 获取源文件
def fetch_source():
    resp = requests.get(SOURCE_URL, timeout=10)
    resp.encoding = 'utf-8'
    return resp.text

# 提取 4K 分组及其直播源
def extract_4k_group(content):
    lines = content.splitlines()
    result = []
    include_line = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if GROUP_4K in line:
            include_line = True
            result.append(line)
            continue
        if include_line:
            if ",#genre#" in line and GROUP_4K not in line:
                break
            parts = line.split(",", 1)
            if len(parts) == 2:
                result.append(f"{parts[0]}: {parts[1]}")
    return result

# 保存到文件
def save_file(path, lines):
    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 文件已生成: {os.path.abspath(path)}")

# 主函数
def main():
    content = fetch_source()
    if not content:
        print("❌ 源文件为空")
        return

    group_4k_lines = extract_4k_group(content)
    if not group_4k_lines:
        print("⚠️ 没有抓取到 🇨🇳 4K 分组内容")
        return

    print(f"总计 {len([l for l in group_4k_lines if 'http' in l])} 个 4K 直播源抓取成功。")
    save_file(OUTPUT_FILE, group_4k_lines)

if __name__ == "__main__":
    main()
