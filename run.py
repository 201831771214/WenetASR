from model_classes.model_loader import ModelLoader
import sounddevice as sd
from model_utils.query_dev_infos import get_dev_info
import numpy as np
from funasr import AutoModel
from model_utils.inireader import IniReader
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("run.log", mode="w", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

ini_reader = IniReader("./configs/cfg.ini")
cfg = ini_reader.GetConfig()

units_path = "./models/ASR/WeNet-U2pp_Conformer-16K/units.txt"
model_path = "./models/ASR/WeNet-U2pp_Conformer-16K/"

vad_model_path = "./models/VAD/fsmn-vad/"

# Dev Params
chunk_size = 2048
chunk_slider = 50
sample_rate = 48000

# VAD Params
# 新增全局状态变量
active_segments = []     # 存储有效语音段[[start1,end1],...]
current_start = -1       # 当前语音段起始时间
last_vad_time = 0        # 最后一次检测到语音的时间
VAD_THRESHOLD_MS = 800
chunk_size = 200
chunk_stride = int(chunk_size * 16000 / 1000)

decibel_thres=cfg["decibel_thres"]
speech_noise_thres=cfg["speech_noise_thres"]
max_end_silence_time=cfg["max_end_silence_time"]
max_start_silence_time=cfg["max_start_silence_time"]
speech_2_noise_ratio=cfg["speech_2_noise_ratio"]
speech_noise_thresh_low=cfg["speech_noise_thresh_low"]
speech_noise_thresh_high=cfg["speech_noise_thresh_high"]

def update_vad_segments(vad_result, timestamp):
    global current_start, last_vad_time, active_segments
    if vad_result:
        for seg in vad_result:
            seg_start, seg_end = seg
            # 处理起始标记
            if seg_start != -1 and current_start == -1:
                current_start = seg_start
            # 处理结束标记
            if seg_end != -1 and current_start != -1:
                active_segments.append([current_start, seg_end])
                current_start = -1
                last_vad_time = seg_end
    else:
        # 超时判定（VAD_THRESHOLD_MS=800ms）, 当前时间戳-最后一次检测到语音的时间>800ms且当前语音段起始时间不为-1
        if timestamp - last_vad_time > VAD_THRESHOLD_MS and current_start != -1:
            active_segments.append([current_start, timestamp])
            current_start = -1

if __name__ == "__main__":
    get_dev_info()

    input_stream = sd.InputStream(
        samplerate=sample_rate,
        blocksize=chunk_size*chunk_slider,
        device=8,
        channels=1,
        dtype=np.float32
    )

    model_loader = ModelLoader(model_path, units_path, language="ch", device="cpu", beam_size=5)

    vad_model = AutoModel(
        model=vad_model_path,
        model_revision="v2.0.4",
        disable_update=True,
        decibel_thres=decibel_thres,
        speech_noise_thres=speech_noise_thres,
        max_end_silence_time=max_end_silence_time,
        max_start_silence_time=max_start_silence_time,
        speech_2_noise_ratio=speech_2_noise_ratio,
        speech_noise_thresh_low=speech_noise_thresh_low,
        speech_noise_thresh_high=speech_noise_thresh_high,
        device="cpu",
        disable_pbar=True,
        disable_log=True
    )

    audio_buffer = np.array([], dtype=np.float32)
    vad_cache = {}
    
    logger.info(f"▶开始语音检测...")
    input_stream.start()
    try:
        while True:
            audio_data = input_stream.read(chunk_size*chunk_slider)

            if sample_rate != 16000:
                audio_data = np.squeeze(audio_data[0].astype(np.float32))
                audio_data = model_loader.resample_audio(audio_data, sample_rate, 16000)

            audio_buffer = np.concatenate([audio_buffer, audio_data])


            if len(audio_buffer) >= 16000*3:
                total_chunk_num = int(len((audio_buffer)-1)/chunk_stride+1)
                for i in range(total_chunk_num):
                    speech_chunk = audio_buffer[i*chunk_stride:(i+1)*chunk_stride]
                    is_final = i == total_chunk_num - 1
                    vad_res = vad_model.generate(
                        input=speech_chunk, 
                        cache=vad_cache, 
                        is_final=is_final, 
                        chunk_size=chunk_size)

                    current_time = time.time() * 1000  # 当前时间戳(ms)
                    # update_vad_segments(vad_res[0]['value'], current_time, current_start, last_vad_time, active_segments, VAD_THRESHOLD_MS)
                    update_vad_segments(vad_res[0]['value'], current_time)

                    if active_segments:
                        for seg in active_segments.copy():
                            start_ms, end_ms = seg
                            # 转换为采样点索引
                            start_idx = int(start_ms * 16000 / 1000)
                            end_idx = int(end_ms * 16000 / 1000)
                            
                            # 提取有效音频段
                            valid_audio = audio_buffer[start_idx:end_idx]

                            res = model_loader.ExecInfer_with_audio(valid_audio, 16000)

                            if res != "":
                                logger.info(f"ASR Result: {res}")
                        
                        active_segments.remove(seg)
                audio_buffer = np.array([], dtype=np.float32)
    except Exception as e:
        logger.error(f"❌程序异常: {e}")
    except KeyboardInterrupt:
        logger.info(f"🛑语音检测结束...")
        input_stream.stop()
        input_stream.close()
        logger.info(f"🛑程序结束...")