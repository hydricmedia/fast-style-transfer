from __future__ import print_function
from argparse import ArgumentParser
import sys
sys.path.insert(0, 'src')
import os, random, subprocess, evaluate, shutil
from utils import exists, list_files
import pdb

TMP_DIR = '.fns_frames_%s/' % random.randint(0,99999)
DEVICE = '/gpu:0'
BATCH_SIZE = 4

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('--checkpoint', type=str,
                        dest='checkpoint', help='checkpoint directory or .ckpt file',
                        metavar='CHECKPOINT', required=True)

    parser.add_argument('--in-path', type=str,
                        dest='in_path', help='the src directory for streaming video',
                        metavar='IN_PATH', required=True)

    parser.add_argument('--out-path', type=str,
                        dest='out', help='path to save processed video to',
                        metavar='OUT', required=True)

    parser.add_argument('--tmp-dir', type=str, dest='tmp_dir',
                        help='tmp dir for processing', metavar='TMP_DIR',
                        default=TMP_DIR)

    parser.add_argument('--device', type=str, dest='device',
                        help='device for eval. CPU discouraged. ex: \'/gpu:0\'',
                        metavar='DEVICE', default=DEVICE)

    parser.add_argument('--batch-size', type=int,
                        dest='batch_size',help='batch size for eval. default 4.',
                        metavar='BATCH_SIZE', default=BATCH_SIZE)

    parser.add_argument('--no-disk', type=bool, dest='no_disk',
                        help='Don\'t save intermediate files to disk. Default False',
                        metavar='NO_DISK', default=False)
    return parser

def check_opts(opts):
    exists(opts.checkpoint)
    exists(opts.out)


def main():
    parser = build_parser()
    opts = parser.parse_args()
    import os

    import m3u8

    src_m3u_filepath = opts.in_path
    dest_m3u_filepath = opts.out
    while True:
        #1 get the src and dest m3u8 files  - which files need to be transcoded
        if os.path.isfile(os.path.join(src_m3u_filepath,'test.m3u8')):
            src_m3u8_obj = m3u8.load(os.path.join(src_m3u_filepath,'test.m3u8'))  # this could also be an absolute filename
            src_segment_uris = [x.uri for x in src_m3u8_obj.segments]
        else:
            src_segment_uris = list()
        import os.path
        if os.path.isfile(os.path.join(dest_m3u_filepath,'test.m3u8')):
            dest_m3u8_obj = m3u8.load(os.path.join(dest_m3u_filepath,'test.m3u8'))  # this could also be an absolute filename
            dest_segment_uris = [x.uri for x in dest_m3u8_obj.segments]
        else:
            dest_segment_uris = list()

        segment_uris_to_transcode = set(src_segment_uris).difference(set(dest_segment_uris))

        #3 delete superfluous files
        segment_uris_to_delete = set(dest_segment_uris[:-1]).difference(set(src_segment_uris))
        for segment_uri in segment_uris_to_delete:
            import os
            if os.path.isfile(os.path.join(dest_m3u_filepath,segment_uri)):
                os.remove(os.path.join(dest_m3u_filepath, segment_uri))
                print('Deleting {}'.format(segment_uri))

        #3 transcode the segments which haven't already been transcoded
        for segment_uri in segment_uris_to_transcode:
            evaluate.ffwd_video(os.path.join(src_m3u_filepath, segment_uri), os.path.join(dest_m3u_filepath, segment_uri), opts.checkpoint, opts.device, opts.batch_size)

        if len(segment_uris_to_transcode) > 0:
            #4 copy across m3u8 file
            # import shutil
            src_m3u8_obj.dump(os.path.join(dest_m3u_filepath,'test.m3u8'))
            # shutil.copy(os.path.join(src_m3u_filepath,'test.m3u8'), os.path.join(dest_m3u_filepath,'test.m3u8'))
        else:
            import time
            time.sleep(3)



if __name__ == '__main__':
    main()
