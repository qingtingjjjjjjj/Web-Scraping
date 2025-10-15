import requests, re, time, os, aiohttp, asyncio

# GitHub 授权，可自动获取，增加搜索速率限制
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
KEYWORD = "PopC"
OUTPUT_FILE = f"{KEYWORD}.txt"

async def test_url(session, url):
    start = time.time()
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                return url, round(time.time() - start, 2)
    except:
        pass
    return url, None

async def check_urls(urls):
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [test_url(session, u) for u in urls]
        for r in await asyncio.gather(*tasks):
            if r[1] is not None:
                results.append(r)
    return sorted(results, key=lambda x: x[1])

def search_github(keyword):
    print(f"🔍 正在 GitHub 搜索：{keyword}")
    # 搜索 .m3u 与 .txt 文件
    query = f'{keyword} in:file (extension:m3u OR extension:txt)'
    url = f"https://api.github.com/search/code?q={query}&per_page=20"
    res = requests.get(url, headers=HEADERS).json()
    items = res.get("items", [])
    urls = []
    for item in items:
        raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        try:
            text = requests.get(raw_url, timeout=5).text
            found = re.findall(r'(https?://[^\s]+)', text)
            for u in found:
                if keyword.lower() in u.lower():
                    urls.append(u)
        except:
            continue
    return list(set(urls))

def save_results(results):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url, delay in results:
            f.write(f"{KEYWORD},{url}\n")
    print(f"✅ 结果已保存到 {OUTPUT_FILE}，共 {len(results)} 条可用链接")

if __name__ == "__main__":
    urls = search_github(KEYWORD)
    print(f"共找到 {len(urls)} 个候选链接，开始测速...")
    if urls:
        results = asyncio.run(check_urls(urls))
        save_results(results)
    else:
        print("❌ 没找到任何包含 PopC 的直播源。")
