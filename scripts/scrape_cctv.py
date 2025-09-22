import requests
import json
import argparse
from tqdm import tqdm

# ===== CCTV 和部分卫视 API 映射 =====
CHANNELS_API = {
    # CCTV
    "CCTV-1 综合": "http://api.cntv.cn/live/getCctv?channel=cctv1",
    "CCTV-2 财经": "http://api.cntv.cn/live/getCctv?channel=cctv2",
    "CCTV-3 综艺": "http://api.cntv.cn/live/getCctv?channel=cctv3",
    "CCTV-4 中文国际": "http://api.cntv.cn/live/getCctv?channel=cctv4",
    "CCTV-5 体育": "http://api.cntv.cn/live/getCctv?channel=cctv5",
    "CCTV-6 电影": "http://api.cntv.cn/live/getCctv?channel=cctv6",
    "CCTV-7 国防军事": "http://api.cntv.cn/live/getCctv?channel=cctv7",
    "CCTV-8 电视剧": "http://api.cntv.cn/live/getCctv?channel=cctv8",
    "CCTV-9 纪录": "http://api.cntv.cn/live/getCctv?channel=cctv9",
    "CCTV-10 科教": "http://api.cntv.cn/live/getCctv?channel=cctv10",
    "CCTV-11 戏曲": "http://api.cntv.cn/live/getCctv?channel=cctv11",
    "CCTV-12 社会与法": "http://api.cntv.cn/live/getCctv?channel=cctv12",
    "CCTV-13 新闻": "http://api.cntv.cn/live/getCctv?channel=cctv13",
    "CCTV-14 少儿": "http://api.cntv.cn/live/getCctv?channel=cctv14",
    "CCTV-15 音乐": "http://api.cntv.cn/live/getCctv?channel=cctv15",
    "CCTV-16 奥林匹克": "http://api.cntv.cn/live/getCctv?channel=cctv16",
    "CCTV-17 农业农村": "http://api.cntv.cn/live/getCctv?channel=cctv17",

    # 卫视示例（部分）
    "湖南卫视": "http://api.cntv.cn/live/getCctv?channel=hunan",
    "浙江卫视": "http://api.cntv.cn/live/getCctv?channel=zhejiang",
    "东方卫视": "http://api.cntv.cn/live/getCctv?channel=dongfang",
    "江苏卫视": "http://api.cntv.cn/live/getCctv?channel=jiangsu",
    "北京卫视": "http://api.cntv.cn/live/getCctv?channel=beijing",
    "广东卫视": "http://api.cntv.cn/live/getCctv?channel=guangdong",
}

def get_live_url(api_url):
    """通过 API 获取 m3u8 地址"""
    try:
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # 假设返回 JSON 里有字段 live_url
        if "live_url" in data and data["live_url"]:
            return data["live_url"]
    except Exception as e:
        print(f"[ERR] API 请求失败: {e}")
    return None

def main(output_file="cctv.txt"):
    results = []
    print("开始获取 CCTV + 卫视直播源 ...")
    for name, api in tqdm(CHANNELS_API.items(), desc="channels"):
        url = get_live_url(api)
        if url:
            results.append((name, url))
            print(f"[OK] {name} -> {url}")
        else:
            print(f"[NO] 未找到直播源: {name}")

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        for name, url in results:
            f.write(f"{name}|{url}\n")

    print(f"输出完成: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取 CCTV 和卫视直播源（API 版）")
    parser.add_argument("--output", default="cctv.txt", help="输出文件名 (默认: cctv.txt)")
    args = parser.parse_args()
    main(output_file=args.output)
