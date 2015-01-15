#!/usr/bin/env python

import argparse
from dvhax import FrameAspectRatio, DV_PACK_SIZE, DV_BLOCK_SIZE, DV_SEQUENCE_SIZE
from os import SEEK_CUR, SEEK_END


def arpatch(dv_file, aspect_ratio):
	print 'Patching AR to %s' % (aspect_ratio.name,)

	# Find a header to check we're OK
	assert dv_file.read(1) == '\x1F', 'Expected header block'
	
	# Seek to EOF
	dv_file.seek(0, SEEK_END)
	dv_file_len = dv_file.tell()
	
	# Seek to end of first block
	dv_file.seek(DV_BLOCK_SIZE)

	while dv_file.tell() < dv_file_len:
		# Now keep seeking forward until we find the block we want (0x50 - 0x5F)
		while dv_file.read(1) not in 'PQRSTUVWXYZ[\\]^_':
			dv_file.seek(DV_BLOCK_SIZE - 1, SEEK_CUR)

		# skip past the base metadata
		dv_file.seek(2, SEEK_CUR)

		# 15 pieces
		for x in range(15):
			pack_type = dv_file.read(1)
			
			if pack_type == 'a': # 0x61
				# skip past copy protection flag to AR
				dv_file.seek(1, SEEK_CUR)
				
				# read existing AR
				ar_data = ord(dv_file.read(1))
				
				# overwrite with desired ar
				ar_data = (ar_data & 0xF8) | aspect_ratio.value
				
				# go back
				dv_file.seek(-1, SEEK_CUR)
				
				# write back
				dv_file.write(chr(ar_data))
				
				# drop out
				offset = dv_file.tell() - 1
				print 'Patched AR at %d bytes (0x%X)' % (offset, offset,)
			else:
				dv_file.seek(DV_PACK_SIZE - 1, SEEK_CUR)
			
		
		# Two bonus bytes we don't care for
		dv_file.seek(2, SEEK_CUR)

	dv_file.flush()
	dv_file.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('dvfile',
		nargs=1,
		help='DV file to patch',
		type=argparse.FileType('r+b')
	)
	parser.add_argument('--ar', required=True, help='Aspect ratio to set')
	options = parser.parse_args()
	
	ar = FrameAspectRatio[options.ar]
	arpatch(options.dvfile[0], ar)


if __name__ == '__main__':
	main()

