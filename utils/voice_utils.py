import httpx
import asyncio

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

async def stream_audio_to_voice(data, audio_file_path="welcome.mp3"):
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

    cmd = [
    "ffmpeg", "-re", "-i", audio_file_path, "-map", "0:a:0",
    "-acodec", "libopus", "-ab", "48k", "-ac", "2", "-ar", "48000",
    "-filter:a", "volume=0.8", "-f", "tee",
    f"[select=a:f=rtp:ssrc={ssrc}:payload_type={pt}]{rtp_url}"
    ]

    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.wait()

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
