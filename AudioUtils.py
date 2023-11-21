from pydub import AudioSegment


def mergeAudio(sound1Path, sound2Path, outputPath):
    sound1 = AudioSegment.from_wav(sound1Path)
    sound2 = AudioSegment.from_wav(sound2Path)

    output = sound1.overlay(sound2)  # 把sound2叠加到sound1上面
    # output = sound1.overlay(sound2,position=5000)  # 把sound2叠加到sound1上面，从第5秒开始叠加
    output.export(outputPath, format="wav")  # 保存文件


def addAudio(audioPathList, outPath):
    output = AudioSegment.from_wav(audioPathList[0])
    for i, audioPath in enumerate(audioPathList):
        if i != 0:
            output += AudioSegment.from_wav(audioPath)
    output.export(outPath, format="wav")  # 保存文件


def cutAudio(audio, startTime, endTime, exportPath):
    audio_chunk = audio[startTime * 1000:endTime * 1000]
    audio_chunk.export(exportPath, format="wav")
