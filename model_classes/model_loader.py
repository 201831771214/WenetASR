# -*- coding: utf-8 -*-

import wenet.wenet as wenet
import soundfile as sf
import torch
import numpy as np
import sounddevice as sd
import librosa

from wenet.wenet.transformer.search import ctc_prefix_beam_search, attention_beam_search, attention_rescoring
from wenet.wenet.utils.file_utils import read_symbol_table

class ModelLoader:
    def __init__(self, model_path, units_path, language:str = "ch", device:str = "cpu", beam_size:int = 5):
        """
        初始化模型加载器
        :param model_path: 模型路径
        :param units_path: 单位路径
        :param language: 语言 可选值为 "ch" 和 "en"
        :param device: 设备
        :param beam_size: 束搜索大小
        """

        self.model_path = model_path
        self.units_path = units_path
        self.language = language
        self.device = device

        self.model_executor = None
        self.model = None

        self.symbol_table = None
        self.char_dict = None
        self.beam_size = beam_size

        self.__InitModelParams()

    # 初始化模型参数
    def __InitModelParams(self):
        self.model_executor = wenet.load_model(language=self.language, model_dir=self.model_path, device=self.device)
        self.model = self.model_executor.model
        self.symbol_table = read_symbol_table(self.units_path)
        self.char_dict = {v: k for k, v in self.symbol_table.items()}

    def resample_audio(self, audio, ori_sr, tar_sr):
        re_audio = librosa.resample(
            audio,
            orig_sr=ori_sr,
            target_sr=tar_sr,
            res_type="kaiser_fast"
        )
        return re_audio

    def __Preprocess_audio_data(self, audio, sr):
        if isinstance(audio, tuple):
            audio = audio[0].astype(np.float32)
        elif isinstance(audio, np.ndarray):
            audio = audio.astype(np.float32)
        else:
            raise ValueError(f"audio type error: {type(audio)}")
        
        audio = np.squeeze(audio)
        re_audio = audio if sr == 16000 else self.resample_audio(audio, sr, 16000) # 重采样适配模型输入

        return re_audio

    # 实现audio数据推理
    def ExecInfer_with_audio(self, audio, sr) -> dict:
        """
        实现audio数据推理
        :param audio: 音频数据
        :param sr: 采样率
        :return: 推理结果
        """
        audio = self.__Preprocess_audio_data(audio, sr)
        audio_tensor = self.model_executor.compute_feats_with_audio(audio, 16000) # -> torch.Size([1, T, 80])
        encoder_out, _, _  = self.model.forward_encoder_chunk(audio_tensor, 0, -1)
        encoder_lens = torch.tensor([encoder_out.size(1)], dtype=torch.long, device=encoder_out.device)
        ctc_probs = self.model.ctc_activation(encoder_out)

        ctc_prefix_results = ctc_prefix_beam_search(ctc_probs, encoder_lens, self.beam_size, context_graph=None)
        rescoring_results = attention_rescoring(self.model, ctc_prefix_results, encoder_out, encoder_lens, 0.3, 0.5)

        res = rescoring_results[0]
        result = {}
        result['text'] = ''.join([self.char_dict[x] for x in res.tokens])
        result['confidence'] = res.confidence
        return result

    def ExecInfer_with_audio_file(self, audio_path:str) -> dict:
        """
        实现audio文件推理
        :param audio_path: 音频文件路径
        :return: 推理结果
        """
        result = self.model_executor.transcribe(audio_path)
        return result