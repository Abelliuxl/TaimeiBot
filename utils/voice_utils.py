import httpx
import asyncio
import os
from config.member import MONITORED_MEMBERS

async def join_voice_channel(channel_id: str, token: str):
    url = 'https://www.kookapp.cn/api/v3/voice/join'
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel_id": channel_id
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["data"]

async def stream_audio_to_voice(data, audio_file_path="/home/liuxl/TaimeiBot/audio/test.mp3"):
    ip = data["ip"]
    port = data["port"]
    rtcp_mux = data["rtcp_mux"]
    ssrc = data["audio_ssrc"]
    pt = data["audio_pt"]
    rtcp_port = data.get("rtcp_port")

    if rtcp_mux:
        rtp_url = f"rtp://{ip}:{port}"
    else:
        rtp_url = f"rtp://{ip}:{port}?rtcpport={rtcp_port}"

    # 输出路径
    base, _ = os.path.splitext(audio_file_path)
    saved_output_path = base + "_transcoded.opus"

    bitrate = f"{int(data['bitrate']) // 1000}k"

    # ✅ 第一步：保存到文件
    save_cmd = [
        "ffmpeg", "-y", "-i", audio_file_path,
        "-acodec", "libopus", "-ab", bitrate,
        "-ac", "2", "-ar", "48000",
        "-filter:a", "volume=1",
        saved_output_path
    ]
    print("Saving to:", saved_output_path)
    save_proc = await asyncio.create_subprocess_exec(*save_cmd)
    await save_proc.wait()

    # ✅ 第二步：读取转码后的文件推流
    stream_cmd = [
    "ffmpeg", "-re", "-i", saved_output_path,
    "-map", "0:a:0",
    "-acodec", "libopus", "-ab", bitrate,
    "-ac", "2", "-ar", "48000",
    "-filter:a", "volume=1.5",
    "-f", "tee",
    f"[select=a:f=rtp:ssrc={ssrc}:payload_type={pt}]{'rtp://'+ip+':'+str(port)+'?rtcpport='+str(rtcp_port) if not rtcp_mux else 'rtp://'+ip+':'+str(port)}"
    ]

    print("Streaming to:", rtp_url)
    stream_proc = await asyncio.create_subprocess_exec(*stream_cmd)
    await stream_proc.wait()

async def leave_voice_channel(channel_id: str, token: str):
    url = "https://www.kookapp.cn/api/v3/voice/leave"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel_id": channel_id
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


def get_audio_for_user(user_id: str) -> str | None:
    for member in MONITORED_MEMBERS:
        if member["user_id"] == user_id:
            return f"audio/{member['audio_file']}"
    return None
