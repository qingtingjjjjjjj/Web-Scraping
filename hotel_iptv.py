import asyncio
import os

try:
    import opencc
except ModuleNotFoundError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencc-python-reimplemented"])
    import opencc

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Hotel:
    def __init__(self):
        self.converter = opencc.OpenCC('t2s')

    async def sniff_ip(self):
        print("开始抓取酒店 IPTV IP ...")
        await asyncio.sleep(1)  # 模拟抓取
        ips = ["192.168.0.101", "192.168.0.102"]  # 示例
        with open(os.path.join(OUTPUT_DIR, "hotel_ip.txt"), "w", encoding="utf-8") as f:
            for ip in ips:
                f.write(ip + "\n")
        print("抓取完成，已保存 hotel_ip.txt")

    async def generate_playlist(self):
        print("生成播放列表 ...")
        await asyncio.sleep(1)  # 模拟生成
        channels = ["频道1", "频道2", "频道3"]
        with open(os.path.join(OUTPUT_DIR, "hotel_playlist.txt"), "w", encoding="utf-8") as f:
            for ch in channels:
                f.write(self.converter.convert(ch) + "\n")
        print("播放列表生成完成，已保存 hotel_playlist.txt")

async def main(type_: str = "hotel", mode: str = None):
    hotel = Hotel()
    if mode == "ip":
        await hotel.sniff_ip()
    elif mode == "playlist":
        await hotel.generate_playlist()
    else:
        await hotel.sniff_ip()
        await hotel.generate_playlist()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="hotel")
    parser.add_argument("--ip", action="store_true")
    parser.add_argument("--playlist", action="store_true")
    args = parser.parse_args()

    mode = None
    if args.ip:
        mode = "ip"
    elif args.playlist:
        mode = "playlist"

    asyncio.run(main(args.type, mode))
