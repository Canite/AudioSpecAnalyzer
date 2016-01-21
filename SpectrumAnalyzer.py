import pygame, os, sys, random, math, alsaaudio, wave, mad, ao
import numpy as np
from struct import unpack
from pygame.locals import *

class Bar:
    def __init__(self, ch, nh):
        self.curheight = ch
        self.nextheight = nh

def smoothApproach(a, b, FACTOR):
    return ((b - a) * FACTOR)

def piff(val, cs, sr):
    return int(2*cs*val / sr)

def scaleFreq(freqmat, prev_freqmat, maxfreq, height):
    scaled_freqs = []
    for i in xrange(len(freqmat)):
        if (freqmat[i] >= (prev_freqmat[i]*maxfreq/height) and min(freqmat[i] / maxfreq, 1)*height > 10):
            scaled_freqs.append(min(freqmat[i] / maxfreq, 1)*height)
        else:
            if (prev_freqmat[i] < 1):
                scaled_freqs.append(0.0)
            else:
                scaled_freqs.append(prev_freqmat[i]*0.9)
    return np.array(scaled_freqs)

def calcFreqLevels(data, cs, sr, nb, factor, freq, weighting):
    #weighting = [2,2,8,8,16,32,64,64]
    #weighting = [1]*nb

    #data = unpack("%db" % (len(data)), data)
    #data = np.array(data, dtype='b')
    data = unpack("%dh" % (len(data)/2), data)
    data = np.array(data, dtype='h')

    fourier = np.fft.rfft(data)
    fourier = np.delete(fourier, len(fourier) - 1)

    power = np.abs(fourier)
    matrix = []
    prev_freq = 0.0
    for i in xrange(nb):
        if (len(power[piff(int(prev_freq), cs, sr):piff(int(freq), cs, sr)]) != 0):
            matrix.append(np.mean(power[piff(int(prev_freq),cs,sr)     : piff(int(freq),cs,sr)     :1]))
        else:
            matrix.append(0.0)
        prev_freq = freq
        freq = freq*factor

    matrix = np.divide(np.multiply(matrix, weighting), 8000)
    #matrix = matrix.clip(0, 12)
    return matrix

def main():
    global DISPLAYSURF, SCREEN_WIDTH, SCREEN_HEIGHT, CHUNK_SIZE, MIN_FREQ, MAX_FREQ
    audiofilename = sys.argv[1]
    _filename, filetype = os.path.splitext(audiofilename)
    SCREEN_HEIGHT = 480
    SCREEN_WIDTH = 640
    CHUNK_SIZE = 2048
    MIN_FREQ = 200
    MAX_FREQ = 20000
    pygame.init()
    DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    numbars = 32
    factor = 2.0
    freq = 8000.0 / (factor ** (numbars - 1))
    while (freq < 16):
        factor -= 0.1
        freq = 8000.0 / (factor ** (numbars - 1))

    weighting = []
    weighting.append(factor)
    for i in xrange(1, numbars):
        if (i % 2 == 0):
            weighting.append(weighting[-1] * (factor*1.1))
        else:
            weighting.append(weighting[-1])

    if (filetype == '.wav'):
        audiofile = wave.open(audiofilename, 'r')
        samplerate = audiofile.getframerate()
        nchannels = audiofile.getnchannels()
        data = audiofile.readframes(CHUNK_SIZE)
        soundoutput = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NORMAL)
        soundoutput.setchannels(nchannels)
        soundoutput.setrate(samplerate)
        soundoutput.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        soundoutput.setperiodsize(CHUNK_SIZE)
    elif (filetype == '.mp3'):
        mf = mad.MadFile(audiofilename)
        samplerate = mf.samplerate()
        data = mf.read()
        soundoutput = ao.AudioDevice(0, rate=samplerate)

    curtime = pygame.time.get_ticks()
    pygame.display.set_caption('Spectrum Analyzer')

    prev_freqmat = [0]*numbars

    while (data != ''):
        if (filetype == '.wav'):
            soundoutput.write(data)
        elif (filetype == '.mp3'):
            soundoutput.play(data, len(data))

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

        DISPLAYSURF.fill((0,0,0))

        freqmat = calcFreqLevels(data, len(data)/2, samplerate, numbars, factor, freq, weighting)
        #max_freq = np.max(freqmat)
        scaled_freqs = scaleFreq(freqmat, prev_freqmat, 2400.0, float(SCREEN_HEIGHT))
        for i in xrange(numbars):
            pygame.draw.rect(DISPLAYSURF, (255, 255, 255), (SCREEN_WIDTH/numbars * i, SCREEN_HEIGHT - (scaled_freqs[i]), SCREEN_WIDTH/numbars, (scaled_freqs[i])))
        pygame.display.flip()

        prev_freqmat = scaled_freqs

        if (filetype == '.wav'):
            data = audiofile.readframes(CHUNK_SIZE)
        elif (filetype == '.mp3'):
            data = mf.read()

if __name__ == '__main__':
    main()
