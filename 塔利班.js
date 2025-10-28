/*!
 * @name AllMusicSource
 * @description 聚合音乐源：网易/酷我/酷狗/咪咕/企鹅
 * @version 1.0.0
 */

const { EVENT_NAMES, on, send, request, env, version } = globalThis.lx;

// -------------------- 工具函数 --------------------
const httpFetch = (url, options = { method: 'GET' }) =>
  new Promise((resolve, reject) => {
    console.log('request url: ' + url);
    request(url, options, (err, resp) => {
      if (err) return reject(err);
      resolve(resp);
    });
  });

// -------------------- 酷我音乐 --------------------
const Kuwo = {
  name: '酷我音乐',
  qualityMap: {
    '128k': '128kmp3',
    '320k': '320kmp3',
    flac: '2000kflac',
    flac24bit: '4000kflac',
    hires: '4000kflac',
  },
  async musicUrl({ songmid }, quality) {
    const url = `https://mobi.kuwo.cn/mobi.s?f=web&rid=${songmid}&source=jiakong&type=convert_url_with_sign&surl=1${this.qualityMap[quality]}`;
    const { body } = await httpFetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': env ? `lx-music-${env}/${version}` : `LXMusic/${version}`,
      },
      follow_max: 5,
    });
    if (!body || isNaN(Number(body.code))) throw new Error('未知错误');
    if (body.code === 200) return body.data.surl;
    throw new Error('获取失败');
  },
};

// -------------------- 网易音乐 --------------------
const Wy = {
  name: '网易音乐',
  async musicUrl({ songmid }, quality = '128k') {
    const wy_token = null; // 如果你有网易 token，可填入
    const wy_cookie = wy_token ? `MUSIC_U=${wy_token}; os=pc` : 'os=pc';
    const br = { '128k': 128000, '320k': 320000, flac: 999000 }[quality];
    const target_url = 'https://interface3.music.163.com/eapi/song/enhance/player/url';
    const eapiUrl = '/api/song/enhance/player/url';
    const message = JSON.stringify({ ids: `[${songmid}]`, br });
    const data = { params: message }; // 简化 AES 加密逻辑
    const { body } = await httpFetch(target_url, { method: 'POST', form: data, headers: { cookie: wy_cookie } });
    if (!body || !body.data?.[0]?.url) throw new Error('获取失败');
    return body.data[0].url;
  },
};

// -------------------- 酷狗音乐 --------------------
const Kg = {
  name: '酷狗音乐',
  async musicUrl({ hash, albumId }) {
    const url = `https://wwwapi.kugou.com/yy/index.php?r=play/getdata&hash=${hash}&platid=4&album_id=${albumId}&mid=00000000000000000000000000000000`;
    const { body } = await httpFetch(url);
    if (body.status !== 1 || body.data.privilege > 9) throw new Error('获取失败');
    return body.data.play_backup_url;
  },
};

// -------------------- 企鹅音乐 --------------------
const Tx = {
  name: '企鹅音乐',
  fileConfig: { '128k': { s: 'M500', e: '.mp3' }, '320k': { s: 'M800', e: '.mp3' } },
  async musicUrl({ songmid, strMediaMid }, quality = '128k') {
    const cfg = this.fileConfig[quality];
    const file = `${cfg.s}${strMediaMid}${cfg.e}`;
    const guid = '10000', uin = '0';
    const data = {
      req_0: { module: 'vkey.GetVkeyServer', method: 'CgiGetVkey', param: { filename: [file], guid, songmid: [songmid], songtype: [0], uin, loginflag: 1, platform: '20' } },
      loginUin: uin,
      comm: { uin, format: 'json', ct: 24, cv: 0 },
    };
    const { body } = await httpFetch(`https://u.y.qq.com/cgi-bin/musicu.fcg?format=json&data=${JSON.stringify(data)}`);
    const purl = body.req_0.data.midurlinfo[0].purl;
    if (!purl) throw new Error('获取失败');
    return body.req_0.data.sip[0] + purl;
  },
};

// -------------------- 咪咕音乐 --------------------
const Mg = {
  name: '咪咕音乐',
  async musicUrl({ songmid }, quality = '128k') {
    const url = `https://app.c.nf.migu.cn/MIGUM2.0/strategy/listen-url/v2.2?netType=01&resourceType=E&songId=${songmid}&toneFlag=${quality}`;
    const { body } = await httpFetch(url);
    if (!body?.data?.url) throw new Error('获取失败');
    return body.data.url.replace(/\+/g, '%2B').split('?')[0];
  },
};

// -------------------- 聚合到 LX Music --------------------
const sources = { kuwo: Kuwo, wy: Wy, kg: Kg, tx: Tx, mg: Mg };
const musicSources = {};
Object.keys(sources).forEach((name) => {
  musicSources[name] = { name, type: 'music', actions: ['musicUrl'], qualitys: Object.keys(sources[name].qualityMap || { '128k': 1 }) };
});

on(EVENT_NAMES.request, async ({ action, source, info }) => {
  if (action !== 'musicUrl') return Promise.reject('action not support');
  try {
    return await sources[source].musicUrl(info.musicInfo, info.type);
  } catch (err) {
    return Promise.reject(err);
  }
});

send(EVENT_NAMES.inited, { status: true, openDevTools: false, sources: musicSources });
