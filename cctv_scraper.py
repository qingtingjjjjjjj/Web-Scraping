import asyncio
from playwright.async_api import async_playwright

channels = {
    "CCTV-1 综合": "cctv1",
    "CCTV-2 财经": "cctv2",
    "CCTV-3 综艺": "cctv3",
    "CCTV-4 中文国际": "cctv4",
    "CCTV-5 体育": "cctv5",
    "CCTV-5+ 体育赛事": "cctv5plus",
    "CCTV-6 电影": "cctv6",
    "CCTV-7 国防军事": "cctv7",
    "CCTV-8 电视剧": "cctv8",
    "CCTV-9 纪录": "cctv9",
    "CCTV-10 科教": "cctv10",
    "CCTV-11 戏曲": "cctv11",
    "CCTV-12 社会与法": "cctv12",
    "CCTV-13 新闻": "cctv13",
    "CCTV-14 少儿": "cctv14",
    "CCTV-15 音乐": "cctv15",
    "CCTV-16 奥林匹克": "cctv16",
    "CCTV-17 农业农村": "cctv17"
}

async def fetch_m3u8(channel_code, channel_name, page):
    url = f"https://tv.cctv.com/live/{channel_code}"
    m3u8_url = None

    def handle_request(request):
        nonlocal m3u8_url
        if ".m3u8" in request.url:
            m3u8_url = request.url

    page.on("request", handle_request)
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(8000)  # 等待页面加载
    return channel_name, m3u8_url

async def main():
    playlist = ["#EXTM3U\n"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for name, code in channels.items():
            print(f"正在抓取 {name} ...")
            ch_name, m3u8 = await fetch_m3u8(code, name, page)
            if m3u8:
                playlist.append(f'#EXTINF:-1 tvg-name="{ch_name}",{ch_name}\n{m3u8}\n')
                print(f"✅ {ch_name}: {m3u8}")
            else:
                print(f"❌ {ch_name} 抓取失败")

        await browser.close()

    with open("cctv.m3u", "w", encoding="utf-8") as f:
        f.writelines(playlist)

    print("\n🎉 已生成 cctv.m3u")

if __name__ == "__main__":
    asyncio.run(main())
