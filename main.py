from datetime import datetime
import os
import pyaudio
from wave import open
from playsound import playsound
from pydub import AudioSegment

from shutil import rmtree

import AudioUtils
import MainUI
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog
import sys
from librosa import load, get_duration  # Optional. Use any library you like to read audio files.
from soundfile import write  # Optional. Use any library you like to write audio files.
from slicer2 import Slicer

def cutAudio(filePath):
    audio, sr = load(filePath, sr=None, mono=False)  # Load an audio file with librosa.
    slicer = Slicer(
        sr=sr,
        threshold=-40,
        min_length=5000,
        min_interval=300,
        hop_size=10,
        max_sil_kept=500
    )
    chunkList = []
    chunks, sil_tags = slicer.slice(audio)
    for i, chunk in enumerate(chunks):
        if len(chunk.shape) > 1:
            chunk = chunk.T  # Swap axes if the audio is stereo.
        write(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),
                           f'clips\\clips_{i}.wav'), chunk, sr)  # Save sliced audio files with soundfile.
        chunkList.append(f"clips_{i}.wav")
    list2 = []
    for sil_tag in sil_tags:
        start = sil_tag[0] * slicer.hop_size / sr
        end = sil_tag[1] * slicer.hop_size / sr
        list1 = [start, end]
        print(start, end)
        list2.append(list1)
    return list2, chunkList


CHUNK = 1024  # 每个缓冲区的帧数
FORMAT = pyaudio.paInt16  # 采样位数
CHANNELS = 2  # 单声道
RATE = 44100  # 采样频率


def record_audio(wave_out_path, record_second):
    """ 录音功能 """
    p = pyaudio.PyAudio()  # 实例化对象
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)  # 打开流，传入响应参数
    wf = open(wave_out_path, 'wb')  # 打开 wav 文件。
    wf.setnchannels(CHANNELS)  # 声道设置
    wf.setsampwidth(p.get_sample_size(FORMAT))  # 采样位数设置
    wf.setframerate(RATE)  # 采样频率设置

    for _ in range(0, int(RATE * record_second / CHUNK)):
        data = stream.read(CHUNK)
        wf.writeframes(data)  # 写入数据
    stream.stop_stream()  # 关闭流
    stream.close()
    p.terminate()
    wf.close()


def get_duration_librosa(file_path):
    audio_data, sample_rate = load(file_path)
    duration = get_duration(y=audio_data, sr=sample_rate)
    return duration


def cutBgm(file_path):
    audio = AudioSegment.from_wav(file_path)
    global bgmCutList
    for i, cut in enumerate(bgmCutList):
        if i != len(bgmCutList) - 1:
            AudioUtils.cutAudio(audio, bgmCutList[i], bgmCutList[i + 1],
                                os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),
                                             f'bgmClip\\bgmClip_{i}.wav'))


def initFile(path):
    real_path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), path)
    if os.path.exists(real_path):
        rmtree(real_path)
        os.mkdir(real_path)
    else:
        os.mkdir(real_path)


class MainDialog(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)
        self.ui = MainUI.Ui_Dialog()
        self.ui.setupUi(self)

    def clickChooseFileBtn(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "请选择音频文件路径",
                                                                   os.path.dirname(os.path.realpath(sys.argv[0])),
                                                                   "Audio Files(*.wav;*.mp3);;All Files(*)")
        self.ui.lineEdit.setText(fileName)

    def clickCutBtn(self):
        self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':开始切片\n')
        filePath = self.ui.lineEdit.text()
        sil_list, chunkList = cutAudio(filePath)
        for chunk in chunkList:
            hasRecordChunkDict[chunk] = 0
            useRecordOrRaw[chunk] = 0
            global clipCount
            clipCount += 1
        self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':切片完成\n')
        global bgmCutList
        bgmCutList = []
        for i, sil in enumerate(sil_list):
            self.addLog("静音片段" + str(i) + ": " + str(sil[0]) + " " + str(sil[1]) + "\n")
            bgmCutList.append(sil[0])
            bgmCutList.append(sil[1])
        self.ui.comboBox.addItems(chunkList)

    def clickBGMBtn(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "请选择音频文件路径", "",
                                                                   "Audio Files(*.wav;*.mp3);;All Files(*)")
        global bgmCutList
        if len(bgmCutList) == 0:
            self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':导入BGM失败，请先切割音频\n')
            return
        self.ui.lineEdit_2.setText(fileName)
        self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':导入BGM\n' + fileName + '\n')
        cutBgm(fileName)
        global hasBgm
        hasBgm = True

    def clickPlayRaw(self):
        clipName = self.ui.comboBox.currentText()
        clipPath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'clips\\' + clipName)
        self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':播放片段 ' + clipName + '\n')
        playsound(clipPath)

    def clickRecord(self):
        clipName = self.ui.comboBox.currentText()
        clipPath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'clips\\' + clipName)
        duration = get_duration_librosa(clipPath)
        filename = 'out/out_' + clipName.split('_')[1]
        self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':开始录制 ' + filename + '\n')
        record_audio(filename, duration)
        self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':结束录制 ' + filename + '\n')
        hasRecordChunkDict[clipName] = 1
        global hasBgm
        if hasBgm:
            soundPath1 = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),
                                      filename)
            soundPath2 = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),
                                      f"bgmClip\\bgmClip_{2 * int(clipName.split('_')[1].split('.')[0]) + 1}.wav")
            AudioUtils.mergeAudio(soundPath1, soundPath2,
                                  f"output\\output_{int(clipName.split('_')[1].split('.')[0])}.wav")

    def clickPlayRecord(self):
        clipName = self.ui.comboBox.currentText()
        if hasRecordChunkDict[clipName] == 1 and useRecordOrRaw[clipName] == 0:
            global hasBgm
            if not hasBgm:
                filename = 'out\\out_' + clipName.split('_')[1]
                filePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), filename)
                self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':播放录制片段 ' + filename + '\n')
                playsound(filePath)
            else:
                filename = 'output\\output_' + clipName.split('_')[1]
                filePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), filename)
                self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ':播放录制片段 ' + filename + '\n')
                playsound(filePath)
        else:
            self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + clipName + '还未录制' + '\n')

    def clickSummon(self):
        for i in hasRecordChunkDict:
            if hasRecordChunkDict[i] == 0 and useRecordOrRaw[i] == 0:
                self.addLog(
                    datetime.now().strftime('%Y.%m.%d %H:%M:%S') + '请先录制完所有片段或使用原有片段\n')
                return
        self.addLog(datetime.now().strftime('%Y.%m.%d %H:%M:%S') + '开始合成\n')
        audioPathList = []
        if hasBgm:
            audioPathList.append(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "bgmClip\\bgmClip_0.wav"))
            for i in range(clipCount):
                if useRecordOrRaw['clips_' + str(i) + '.wav'] == 1:
                    soundPath1 = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),
                                              f'clips\\clips_{i}.wav')
                    soundPath2 = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),
                                              f"bgmClip\\bgmClip_{2 * i + 1}.wav")
                    AudioUtils.mergeAudio(soundPath1, soundPath2,
                                          f"output\\output_{i}.wav")
                audioPathList.append(
                    os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), f'output\\output_{i}.wav'))
                audioPathList.append(
                    os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), f"bgmClip\\bgmClip_{2 * (i + 1)}.wav"))
        else:
            for i in range(clipCount):
                audioPathList.append(
                    os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), f'out\\out_{i}.wav'))
        AudioUtils.addAudio(audioPathList, f'output\\out.wav')

    def clickCheckBox(self):
        clipname = self.ui.comboBox.currentText()
        is_checked = self.ui.checkBox.isChecked()
        if is_checked:
            useRecordOrRaw[clipname] = 1
        else:
            useRecordOrRaw[clipname] = 0

    def clickComboBox(self):
        clipname = self.ui.comboBox.currentText()
        if useRecordOrRaw[clipname]:
            self.ui.checkBox.setChecked(True)
        else:
            self.ui.checkBox.setChecked(False)

    def addLog(self, msg):
        self.ui.label.setText(self.ui.label.text() + msg)


if __name__ == '__main__':
    initFile('bgmClip')
    initFile('clips')
    initFile('output')
    initFile('out')
    bgmCutList = []
    hasRecordChunkDict = {}
    useRecordOrRaw = {}
    clipCount = 0
    hasBgm = False
    myapp = QApplication(sys.argv)
    myDlg = MainDialog()
    myDlg.show()
    sys.exit(myapp.exec_())
