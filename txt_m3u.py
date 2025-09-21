def txt_to_m3u(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as fr:
        lines = fr.readlines()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        print("写入文件开始。")
        genre = ''

        for line in lines:
            line = line.strip()
            if "," in line:
                channel_name, channel_url = line.split(',', 1)
                if channel_url == '#genre#':
                    genre = channel_name
                    print(f"当前分组: {genre}")
                else:
                    f.write(f'#EXTINF:-1 group-title="{genre}",{channel_name}\n')
                    f.write(f'{channel_url}\n')

        print("写入文件结束。")

txt_to_m3u('IPTV_UDP.txt', 'IPTV_UDP.m3u')
print("m3u文件创建成功, IPTV_UDP.m3u")
