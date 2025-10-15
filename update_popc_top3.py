import aiohttp
import asyncio
import datetime
import os
import requests
from collections import defaultdict

LIVE_KEYWORD = "PopC"
OUTPUT_FILE = "PopC_live_top3.txt"
GITHUB_TOKEN = ""  # 可选，增加 API 限额
PER_PAGE = 30       # 每页搜索数量
MAX_PAGES = 3       # 最多抓取页数

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# 1️⃣ GitHub 搜索多页
def fetch_github_search():
    files = []
    for page in range(1, MAX_PAGES + 1):
        url = f"https://api.github.com/search/code?q={LIVE_KEYWORD}+in:file&per_page={PER_PAGE}&page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            for item in items:
                raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                files.append(raw_url)
        except Exception as e:
            print(f"❌ GitHub 搜索失败: {e}")
            continue
    return files

# 2️⃣ 异步抓取文件内容
async def fetch_file(session, url):
    try:
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            text = await resp.text()
            return [line for line in text.splitlines() if LIVE_KEYWORD in line]
    except:
        return []

async def fetch_all_files(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_file(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        lines = [line for sublist in results for line in sublist]
        return lines

# 3️⃣ 异步测速单个 URL
async def test_url(session, name, url):
    try:
        start = asyncio.get_event_loop().time()
        async with session.get(url, timeout=5) as resp:
            await resp.read()
            latency = asyncio.get_event_loop().time() - start
            return (name, url, latency)
    except:
        return (name, url, float("inf"))

# 4️⃣ 异步测速所有 PopC
async def test_popc_live(lines):
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for line in lines:
            if "," in line:
                name, url = line.split(",", 1)
                tasks.append(test_url(session, name, url))
        results = await asyncio.gather(*tasks)
    # 按节目分组，取 Top3 最快
    grouped = defaultdict(list)
    for name, url, latency in results:
        grouped[name].append((url, latency))
    top3_results = []
    for name, urls in grouped.items():
        urls.sort(key=lambda x: x[1])
        for url, latency in urls[:3]:
            top3_results.append((name, url, latency))
    # 全部按延迟排序
    top3_results.sort(key=lambda x: x[2])
    return top3_results

# 5️⃣ 保存文件
def save_file(results):
    if not os.path.exists(os.path.dirname(OUTPUT_FILE)) and os.path.dirname(OUTPUT_FILE):
        os.makedirs(os.path.dirname(OUTPUT_FILE))
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for name, url, latency in results:
            latency_str = "timeout" if latency == float("inf") else f"{latency:.2f}s"
            f.write(f"{name},{url},延迟:{latency_str}\n")
        f.write(f"# 更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"✅ 文件已生成: {OUTPUT_FILE}")

# 6️⃣ 主函数
async def main():
    urls = fetch_github_search()
    print(f"🔍 共找到 {len(urls)} 个 GitHub 文件")
    lines = await fetch_all_files(urls)
    print(f"📄 共抓取 {len(lines)} 条 PopC 直播源")
    results = await test_popc_live(lines)
    save_file(results)

if __name__ == "__main__":
    asyncio.run(main())
