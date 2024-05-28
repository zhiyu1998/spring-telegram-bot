import re
import asyncio
import time

import httpx
import os

from commands import command_handler, regex_handler
from event import Event
from log import logger
from utils import EnvConfig

from .bili23_utils import getDownloadUrl, downloadBFile, mergeFileToMp4, get_dynamic
from .common_utils import delete_boring_characters, download_video
from .constants import URL_TYPE_CODE_DICT, BILI_VIDEO_INFO, DOUYIN_VIDEO, TIKTOK_VIDEO, GENERAL_REQ_LINK, XHS_REQ_LINK

PROXY = EnvConfig.get_env().get("PROXY")
BOT_NAME = EnvConfig.get_env().get("BOT_NAME")


@command_handler('start')
async def start(e: Event):
    await e.send_message(
        f"{e.user_name} 你好，我是 @RrOrangeAndFriends 最好的朋友，可以帮助你下载哔哩哔哩视频、YouTube视频、小红书图片和视频等")


@regex_handler('bilibili.com')
async def bilibili(e: Event):
    header = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'referer': 'https://www.bilibili.com',
    }
    # 消息
    url: str = str(e.text).strip()
    # 正则匹配
    url_reg = "(http:|https:)\/\/www.bilibili.com\/[A-Za-z\d._?%&+\-=\/#]*"
    b_short_rex = "(http:|https:)\/\/b23.tv\/[A-Za-z\d._?%&+\-=\/#]*"
    # 处理短号问题
    if 'b23.tv' in url:
        b_short_url = re.search(b_short_rex, url)[0]
        resp = httpx.get(b_short_url, headers=header, follow_redirects=True)
        url: str = str(resp.url)
    else:
        url: str = re.search(url_reg, url)[0]
    # 发现解析的是动态，转移一下
    if 't.bilibili.com' in url:
        # 去除多余的参数
        if '?' in url:
            url = url[:url.index('?')]
        dynamic_id = re.search(r'[^/]+(?!.*/)', url)[0]
        dynamic_desc, dynamic_src = get_dynamic(dynamic_id)
        if len(dynamic_src) > 0:
            await e.send_message(f"{BOT_NAME}识别：B站动态，{dynamic_desc}")
            paths = await asyncio.gather(*dynamic_src)
            await asyncio.gather(*[e.send_image(open(path, "rb")) for path in paths])
            # 刪除文件
            for temp in paths:
                # logger.info(f'{temp}')
                os.unlink(temp)
        # 跳出函数
        return

    # 获取视频信息
    # logger.error(url)
    video_id = re.search(r"video\/[^\?\/ ]+", url)[0].split('/')[1]
    # logger.error(video_id)
    video_info = httpx.get(
        f"{BILI_VIDEO_INFO}?bvid={video_id}" if video_id.startswith(
            "BV") else f"{BILI_VIDEO_INFO}?aid={video_id}", headers=header)
    # logger.info(video_title)
    video_info = video_info.json()['data']
    if video_info is None:
        await e.send_message(f"{BOT_NAME}识别：B站，出错，无法获取数据！")
        return
    video_title, video_cover = video_info['title'], video_info['pic']
    # video_title = delete_boring_characters(video_title)
    # video_title = re.sub(r'[\\/:*?"<>|]', "", video_title)
    await e.send_message(f"\n{BOT_NAME}识别：B站，{video_title}")
    # 获取下载链接
    video_url, audio_url = getDownloadUrl(url)
    # 下载视频和音频
    cur_time = str(int(time.time()))
    path = os.getcwd() + "\\" + cur_time
    await asyncio.gather(
        downloadBFile(video_url, f"{path}-video.m4s", logger.info),
        downloadBFile(audio_url, f"{path}-audio.m4s", logger.info))
    mergeFileToMp4(f"{path}-video.m4s", f"{path}-audio.m4s", f"{path}-res.mp4")
    # logger.info(os.getcwd())
    # 发送出去
    # logger.info(path)
    # await bili23.send(Message(MessageSegment.video(f"{path}-res.mp4")))
    logger.info(f"{path}-res.mp4")
    await e.send_video(video=open(f"{path}-res.mp4", "rb"))
    # logger.info(f'{path}-res.mp4')
    # 清理文件
    os.unlink(f"{path}-res.mp4")
    if os.path.exists(f"{path}-res.mp4.jpg"):
        os.unlink(f"{path}-res.mp4.jpg")


@regex_handler("youtube.com")
async def youtube(e: Event):
    msg_url = re.search(
        r"(?:https?:\/\/)?(www\.)?youtube\.com\/[A-Za-z\d._?%&+\-=\/#]*|(?:https?:\/\/)?youtu\.be\/[A-Za-z\d._?%&+\-=\/#]*",
        str(e.text).strip())[0]

    form_data = {
        "link": msg_url,
        "from": "videodownloaded"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        "origin": "https://www.ytbsaver.com"
    }
    # Configure proxy if needed
    client_args = {
        'headers': headers,
        'timeout': httpx.Timeout(60, connect=5.0),
    }
    if PROXY != '' or PROXY is not None:
        client_args['proxy'] = 'http://127.0.0.1:7890'

    # Create an HTTP client instance
    async with httpx.AsyncClient(**client_args) as client:
        # Perform the POST request
        response = await client.post("https://api.ytbvideoly.com/api/thirdvideo/parse",
                                     data=form_data)
        response_data = response.json()

        # Process response data
        video_data = response_data['data']
        title = video_data['title']
        duration = video_data['duration']
        formats = video_data['formats']

        await e.send_message(f"{BOT_NAME}识别：油管，{title}\n时长：{duration} 秒")

        # Handle video formats and download video
        if formats:
            video_url = formats[-1]['url']  # Assuming last format is the preferred one
            logger.info(video_url)
            video_path = await download_video(video_url, proxy='http://127.0.0.1:7890')
            await e.send_video(open(video_path, 'rb'))
            os.unlink(video_path)