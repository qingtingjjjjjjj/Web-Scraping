import requests
from bs4 import BeautifulSoup
import os
import argparse
from tqdm import tqdm

# ===== 频道列表（央视 + 卫视）=====
CHANNELS = [
    # ===== CCTV =====
    ("CCTV-1 综合", "http://tv.cctv.com/live/cctv1"),
    ("CCTV-2 财经", "http://tv.cctv.com/live/cctv2"),
    ("CCTV-3 综艺", "http://tv.cctv.com/live/cctv3"),
    ("CCTV-4 中文国际", "http://tv.cctv.com/live/cctv4"),
    ("CCTV-5 体育", "http://tv.cctv.com/live/cctv5"),
    ("CCTV-6 电影", "http://tv.cctv.com/live/cctv6"),
    ("CCTV-7 国防军事", "http://tv.cctv.com/live/cctv7"),
    ("CCTV-8 电视剧", "http://tv.cctv.com/live/cctv8"),
    ("CCTV-9 纪录", "http://tv.cctv.com/live/cctv9"),
    ("CCTV-10 科教", "http://tv.cctv.com/live/cctv10"),
    ("CCTV-11 戏曲", "http://tv.cctv.com/live/cctv11"),
    ("CCTV-12 社会与法", "http://tv.cctv.com/live/cctv12"),
    ("CCTV-13 新闻", "http://tv.cctv.com/live/cctv13"),
    ("CCTV-14 少儿", "http://tv.cctv.com/live/cctv14"),
    ("CCTV-15 音乐", "http://tv.cctv.com/live/cctv15"),
    ("CCTV-16 奥林匹克", "http://tv.cctv.com/live/cctv16"),
    ("CCTV-17 农业农村", "http://tv.cctv.com/live/cctv17"),

    # ===== 卫视频道 =====
    ("湖南卫视", "http://tv.cctv.com/live/hunan"),
    ("浙江卫视", "http://tv.cctv.com/live/zhejiang"),
    ("东方卫视", "http://tv.cctv.com/live/dongfang"),
    ("江苏卫视", "http://tv.cctv.com/live/jiangsu"),
    ("北京卫视", "http://tv.cctv.com/live/beijing"),
    ("广东卫视", "http://tv.cctv.com/live/guangdong"),
    ("深圳卫视", "http://tv.cctv.com/live/shenzhen"),
    ("安徽卫视", "http://tv.cctv.com/live/anhui"),
    ("山东卫视", "http://tv.cctv.com/live/shandong"),
    ("天津卫视", "http://tv.cctv.com/live/tianjin"),
    ("重庆卫视", "http://tv.cctv.com/live/chongqing"),
    ("湖北卫视", "http://tv.cctv.com/live/hubei"),
    ("江西卫视", "http://tv.cctv.com/live/jiangxi"),
    ("河北卫视", "http://tv.cctv.com/live/hebei"),
    ("辽宁卫视", "http://tv.cctv.com/live/liaoning"),
    ("东南卫视", "http://tv.cctv.com/live/dongnan"),
    ("黑龙江卫视", "http://tv.cctv.com/live/heilongjiang"),
    ("贵州卫视", "http://tv.cctv.com/live/guizhou"),
    ("云南卫视", "http://tv.cctv.com/live/yunnan"),
    ("广西卫视", "http://tv.cctv.com/live/guangxi"),
    ("宁夏卫视", "http://tv.cctv.com/live/ningxia"),
    ("青海卫视", "http://tv.cctv.com/live/qinghai"),
    ("海南卫视", "http://tv.cctv.com/live/hainan"),
    ("新疆卫视", "http://tv.cctv.com/live/xinjiang"),
    ("西藏卫视", "http://tv.cctv.com/live/xizang"),
    ("甘肃卫视", "http://tv.cctv.com/live/gansu"),
    ("内蒙古卫视", "http://tv.cctv.com/live/neimenggu"),
    ("陕西卫视", "http://tv.cctv.com/live/shanxi"),
    ("山西卫视", "http://tv.cctv.com/live/shanxi2"),
    ("吉林卫视", "http://tv.cctv.com/live/jilin"),
]

def scrape_channel(channel, timeout=8):
    """爬取单个频道的直播源地址"""
    name, url = channel
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # CCTV 网页里可能有 .m3u8 链接
        m3u8_links = [s for s in soup.get_text().split('"') if ".m3u8" in s]

        if m3u8_links:
            return [(name, m3u8_links[0])]
    except Exception as e:
        print(f"[ERR] {name} 爬取失败: {e}")
    return None


def main(output_file="cctv.txt", timeout=8):
    results = []
    print("开始爬取 CCTV + 卫视频道 直播源 ...")
    for entry in tqdm(CHANNELS, desc="channels"):
        found = scrape_channel(entry, timeout=timeout)
        if found:
            results.append(found[0])
            print(f"[OK] {found[0][0]} -> {found[0][1]}")
        else:
            print(f"[NO] 未找到可用地址: {entry[0]} ({entry[1]})")

    # 写入 cctv.txt
    with open(output_file, "w", encoding="utf-8") as f:
        for name, url in results:
            f.write(f"{name}|{url}\n")

    print(f"输出完成: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="爬取央视网及卫视频道直播源")
    parser.add_argument("--output", default="cctv.txt", help="输出文件名 (默认: cctv.txt)")
    parser.add_argument("--timeout", type=int, default=8, help="请求超时时间 (秒)")
    args = parser.parse_args()

    main(output_file=args.output, timeout=args.timeout)
