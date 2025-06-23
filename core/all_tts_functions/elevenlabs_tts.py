from pathlib import Path
import requests
import json
import os, sys
from time import sleep
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key

BASE_URL = "https://api.elevenlabs.io/v2/text-to-speech"

def elevenlabs_tts(text, save_path):
    API_KEY = load_key("elevenlabs.api_key")
    voice_id = load_key("elevenlabs.voice_id")
    model_id = load_key("elevenlabs.model_id", default="eleven_multilingual_v2")
    
    # 从配置中加载语音设置，如果没有则使用默认值
    voice_settings = load_key("elevenlabs.voice_settings", default={
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True,
        "speaking_rate": 1.0,
        "pitch": 1.0
    })
    
    # 加载高级参数设置
    advanced_settings = load_key("elevenlabs.advanced_settings", default={
        "optimize_streaming_latency": 0,  # 0-4，数值越高延迟越低但质量可能下降
        "pronunciation_dictionary": {},  # 自定义发音字典，如 {"word": "pronunciation"}
        "text_processing": {  # 文本处理选项
            "chunk_length": 250,  # 文本分段长度
            "max_chunks": 10  # 最大分段数
        }
    })
    
    headers = {
        "Accept": "audio/wav",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings,
        "output_format": "wav",
        "optimize_streaming_latency": advanced_settings["optimize_streaming_latency"],
        "pronunciation_dictionary": advanced_settings["pronunciation_dictionary"],
        "return_timestamps": True
    }
    
    # 如果文本过长，进行分段处理
    if len(text) > advanced_settings["text_processing"]["chunk_length"]:
        chunks = [text[i:i + advanced_settings["text_processing"]["chunk_length"]] 
                 for i in range(0, len(text), advanced_settings["text_processing"]["chunk_length"])]
        chunks = chunks[:advanced_settings["text_processing"]["max_chunks"]]
        
        # 创建临时文件存储每个分段的音频
        temp_files = []
        for i, chunk in enumerate(chunks):
            temp_file = f"{save_path}.part{i}"
            payload["text"] = chunk
            if process_chunk(payload, headers, temp_file):
                temp_files.append(temp_file)
            else:
                # 清理临时文件
                for f in temp_files:
                    if os.path.exists(f):
                        os.remove(f)
                return False
        
        # 合并所有音频片段
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for temp_file in temp_files:
            segment = AudioSegment.from_wav(temp_file)
            combined += segment
            os.remove(temp_file)  # 删除临时文件
        
        speech_file_path = Path(save_path)
        speech_file_path.parent.mkdir(parents=True, exist_ok=True)
        combined.export(speech_file_path, format="wav")
        print(f"✅ Combined audio saved to {speech_file_path}")
        return True
    else:
        return process_chunk(payload, headers, save_path)

def process_chunk(payload, headers, save_path):
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{BASE_URL}/{voice_id}",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Audio chunk saved to {save_path}")
                
                # 如果返回了时间戳信息，保存到同名的JSON文件中
                if response.headers.get('Content-Type') == 'application/json':
                    timestamp_file = Path(save_path).with_suffix('.json')
                    with open(timestamp_file, 'w', encoding='utf-8') as f:
                        json.dump(response.json(), f, ensure_ascii=False, indent=2)
                    print(f"✅ Timestamps saved to {timestamp_file}")
                return True
            elif response.status_code == 429:  # Rate limit
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"⚠️ Rate limit reached. Waiting {wait_time} seconds...")
                    sleep(wait_time)
                    continue
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying... (Attempt {attempt + 1}/{max_retries})")
                sleep(retry_delay)
                continue
            raise
    
    return False

if __name__ == "__main__":
    elevenlabs_tts("Hi! Welcome to VideoLingo!", "test.wav")