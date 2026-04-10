"""
Piper TTS Plugin - Using piper-tts Python API
"""

import os
import tempfile
import wave
import rclpy.logging

try:
    from piper import PiperVoice
except ImportError:
    PiperVoice = None

try:
    from sound_play.sound_play_plugin import SoundPlayPlugin
except ImportError:
    from sound_play_plugin import SoundPlayPlugin


class PiperTTSPlugin(SoundPlayPlugin):
    # 音频格式常量
    AUDIO_CHANNELS = 1  # 单声道
    AUDIO_SAMPLE_WIDTH = 2  # 16-bit (2 bytes)
    
    def __init__(self):
        super(PiperTTSPlugin, self).__init__()
        
        # 创建独立 logger
        self.logger = rclpy.logging.get_logger('sound_play.piper_plugin')
        
        # Piper 配置（可通过 ROS 参数覆盖）
        self.model_path = '/opt/piper/models/zh_CN-huayan-medium.onnx'
        self.config_path = self.model_path + '.json'
        self.voice = None
        
        # 验证可用性并加载模型
        self._check_availability()
    
    def _check_availability(self):
        if PiperVoice is None:
            self.logger.error("piper-tts 库未安装，请运行: pip install piper-tts")
            return
        
        if not os.path.exists(self.model_path):
            self.logger.error(f"模型未找到: {self.model_path}")
            return
        
        if not os.path.exists(self.config_path):
            self.logger.warn(f"配置文件未找到: {self.config_path}")
        
        try:
            # 加载 Piper 语音模型
            self.voice = PiperVoice.load(self.model_path, config_path=self.config_path, use_cuda=False)
            self.logger.info("Piper TTS 初始化成功")
            self.logger.info(f"模型: {self.model_path}")
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
            self.voice = None
    
    def sound_play_say_plugin(self, text, voice):
        if self.voice is None:
            self.logger.error("语音模型未加载")
            return None

        # 创建临时文件
        fd, wavfilename = tempfile.mkstemp(
            suffix='.wav',
            prefix='piper_tts_'
        )
        os.close(fd)

        try:
            # 可选：自定义合成参数
            try:
                from piper import SynthesisConfig
                syn_config = SynthesisConfig()
            except Exception:
                syn_config = None

            with wave.open(wavfilename, 'wb') as wav_file:
                if syn_config:
                    self.voice.synthesize_wav(text, wav_file, syn_config=syn_config)
                else:
                    self.voice.synthesize_wav(text, wav_file)

            # 验证文件
            if not os.path.exists(wavfilename):
                self.logger.error("输出文件未生成")
                return None

            if os.path.getsize(wavfilename) == 0:
                self.logger.error("输出文件为空")
                os.remove(wavfilename)
                return None

            self.logger.debug(f"TTS 合成成功: {wavfilename}")
            return wavfilename

        except Exception as e:
            self.logger.error(f"TTS 合成异常: {e}")
            if os.path.exists(wavfilename):
                os.remove(wavfilename)
            return None

