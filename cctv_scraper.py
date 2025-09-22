import requests

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

def get_m3u8(channel_code):
    api_url = f"https://vdn.apps.cntv.cn/api2/live.do?channel={channel_code}&client=html5"
    try:
        resp = requests.get(api_url, timeout=10)
        data = resp.json()
        if "hls_url" in data:
            return data["hls_url"]
    except Exception as e:
        print(f"❌ {channel_code} 获取失败: {e}")
    return None

def main():
    playlist = ["#EXTM3U\n"]
    for name, code in channels.items():
        print(f"正在获取 {name} ...")
        m3u8 = get_m3u8(code)
        if m3u8:
            playlist.append(f'#EXTINF:-1 tvg-name="{name}",{name}\n{m3u8}\n')
            print(f"✅ {name}: {m3u8}")
        else:
            print(f"❌ {name} 获取失败")
    
    with open("cctv.m3u", "w", encoding="utf-8") as f:
        f.writelines(playlist)
    print("\n🎉 已生成 cctv.m3u")

if __name__ == "__main__":
    main()
