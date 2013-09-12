#!/usr/bin/env python

'''
Decode 90 seconds of the first audio stream
and output it into a wav file
'''

import sys
import struct
import wave

from pyav import Media

waveData = []
def audioDump2(buf, bufLen):

    global waveData	
    for i in range(bufLen):
        waveData.append(struct.pack('B', buf[i]))

# faster than audioDump2
def audioDump(buf, bufLen):
    
    import ctypes
    global waveData	
    waveData.append(ctypes.string_at(buf, bufLen))

def writeWav(wp):

    global waveData
    # write data to wav object
    wp.writeframes(''.join(waveData))
    wp.close()

if __name__ == '__main__':
    
    # cmdline
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-m', '--media', 
            help='play media')
    parser.add_option('--length', 
            help='decode at max seconds of audio',
            type='int',
            default=90)
    
    (options, args) = parser.parse_args()

    m = Media(options.media)
    # dump info
    mediaInfo = m.info()

    # select first audio stream
    astreams = [ i for i, s in enumerate(mediaInfo['stream']) if s['type'] == 'audio' ]
    if astreams:
        astream = astreams[0]
    else:
        print 'No audio stream in %s' % mediaInfo['name']
        sys.exit(2)
    
    # prepare wav file
    wp = wave.open('out.wav', 'w')
    
    astreamInfo = mediaInfo['stream'][astream]
    
    try:
        # nchannels, sampwidth, framerate, nframes, comptype, compname 
        wp.setparams( (astreamInfo['channels'], 
           astreamInfo['bytes_per_sample'], 
           astreamInfo['sample_rate'], 
           0, 
           'NONE', 
           'not compressed') )
    except wave.Error, e:
        print 'wrong parameters for wav file: %s' % e
        sys.exit(1)

    # size in bytes required for 1 second of audio
    secondSize = astreamInfo['channels'] * astreamInfo['bytes_per_sample'] * astreamInfo['sample_rate']
    decodedSize = 0

    for p in m:

        if p.streamIndex() == astream:
            p.decode()
            if p.decoded:
                # find a way to retrieve data after decoding
                print 'writing %s bytes...' % p.dataSize
                audioDump(p.frame.contents.data[0], p.dataSize)
                
                decodedSize += p.dataSize
                # stop after ~ 90s (default)
                # exact size will vary depending on dataSize
                if decodedSize >= options.length*secondSize:
                    break

    writeWav(wp)