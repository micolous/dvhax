#!/usr/bin/env python
# Format reference: http://dvswitch.alioth.debian.org/wiki/DV_format/
# Copyright 2015 Michael Farrell <http://micolous.id.au>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import argparse
# python-enum34
from enum import Enum

DV_PACK_SIZE = 5 # bytes
DV_BLOCK_SIZE = 80 # bytes
DV_SEQUENCE_SIZE = 150 # blocks

class BlockTypeMajor(Enum):
	header = 0x00
	subcode = 0x20
	vaux = 0x40
	audio = 0x60
	video = 0x80
	
class APT(Enum):
	iec61834 = 0x00
	smpte314m = 0x01

class FrameAspectRatio(Enum):
	r4_3 = 0x00
	r16_9_letterbox = 0x01
	r16_9_fullframe = 0x02
	unknown = 0x07


class DvPack(object):
	def __init__(self, d):
		self._d = d
		self._base_parse()
		self.parse()
	
	def _base_parse(self):
		self.type_code = ord(self._d[0])

	def parse(self):
		raise NotImplemented, 'DvPack.parse is not implemented'

	def pretty(self):
		return '''\
    Pack:
     Pack Type : 0x%02X (%s)
''' % (self.type_code, self.__class__.__name__)

class DvPackUnknown(DvPack):
	def parse(self): pass


class DvPackVauxSourceControl(DvPack):
	def parse(self):
		assert self.type_code == 0x61, 'Type code for pack must be 0x61'
		
		self.copy_protection = (ord(self._d[1]) & 0xC0) != 0x00
		self.aspect_ratio = FrameAspectRatio(ord(self._d[2]) & 0x07)
		self.frame_different_from_previous = bool(ord(self._d[3]) & 0x20)
		self.field_1_encoded_before_field_2 = bool(ord(self._d[3]) & 0x40) 
		self.both_fields_present = bool(ord(self._d[3]) & 0x40)

	def pretty(self):
		o = super(DvPackVauxSourceControl, self).pretty()
		return o + '''\
     Copy protection     : %s
     Aspect ratio        : %s
     Frame differs       : %s
     Field 1 before 2    : %s
     Both fields present : %s
''' % (self.copy_protection, self.aspect_ratio, self.frame_different_from_previous, self.field_1_encoded_before_field_2, self.both_fields_present)

class DvPackNoInfo(DvPack):
	def parse(self):
		assert self.type_code == 0xFF


PACK_TYPES = {
	0x61: DvPackVauxSourceControl,
	0xFF: DvPackNoInfo,
}


class DvBlock(object):
	def __init__(self, d):
		self._d = d
		self._base_parse()
		self._d = self._d[3:]
		self.parse()

	def _base_parse(self):
		self.block_type = ord(self._d[0])
		self.block_type_major = BlockTypeMajor(self.block_type & 0xE0)
		
		self.block_sequence_number = (ord(self._d[1]) & 0xF0) >> 4
		assert self.block_sequence_number <= 11, "sequence number must not exceed 11"
		self.channel_number = (ord(self._d[1]) & 0x08) >> 3
		self.block_number = ord(self._d[2])
		

	def parse(self):
		raise NotImplemented, 'DvBlock.parse is not implemented'
	
	def pretty(self):
		return '''\
  Block Type (Maj) : %s
  Sequence Number  : %d
  Channel Number   : %d
  Block Number     : %d
''' % (self.block_type_major, self.block_sequence_number, self.channel_number, self.block_number)

class DvBlockUnknown(DvBlock):
	def parse(self): pass

		
class DvBlockHeader(DvBlock):
	def parse(self):
		assert self.block_type == 0x1F, 'Unexpected header type'
		self.header_variant = ord(self._d[0])
		self.field_count = None
		if self.header_variant == 0x3F:
			self.field_count = 60
		elif self.header_variant == 0xBF:
			self.field_count = 50
		self.track_application_id = APT(ord(self._d[1]) & 0x07)
		self.audio_application_id = APT(ord(self._d[2]) & 0x07)
		self.audio_valid_flag = (ord(self._d[2]) & 0x80) != 0x80
		self.video_application_id = APT(ord(self._d[3]) & 0x07)
		self.video_valid_flag = (ord(self._d[3]) & 0x80) != 0x80
		self.subcode_application_id = APT(ord(self._d[4]) & 0x07)
		self.subcode_valid_flag = (ord(self._d[4]) & 0x80) != 0x80

	def pretty(self):
		o = super(DvBlockHeader, self).pretty()
		return o + '''\
  Header:
   Track APT     : %s
   Audio APT     : %s
   Audio valid   : %s
   Video APT     : %s
   Video valid   : %s
   Subcode APT   : %s
   Subcode valid : %s
''' % (self.track_application_id, self.audio_application_id, self.audio_valid_flag, self.video_application_id, self.video_valid_flag, self.subcode_application_id, self.subcode_valid_flag)



class DvBlockSubcode(DvBlock):
	def parse(self):
		pass

class DvBlockVaux(DvBlock):
	def parse(self):
		self.packs = []
		for x in range(15):
			pack_type = ord(self._d[0])
			if pack_type in PACK_TYPES:
				self.packs.append(PACK_TYPES[pack_type](self._d[:DV_PACK_SIZE]))
			else:
				self.packs.append(DvPackUnknown(self._d[:DV_PACK_SIZE]))
			
			self._d = self._d[DV_PACK_SIZE:]
		
		assert len(self._d) == 2, 'Expected 2 extra bytes'

	def pretty(self):
		o = super(DvBlockVaux, self).pretty()
		return o + '''\
  Packs:
%s
''' % ('\n'.join((x.pretty() for x in self.packs)), )

class DvBlockAaux(DvBlock):
	def parse(self): pass

class DvBlockVideo(DvBlock):
	def parse(self): pass

BLOCK_TYPES = {
	0x1F: DvBlockHeader,

	0x3F: DvBlockSubcode,

	0x50: DvBlockVaux,
	0x51: DvBlockVaux,
	0x52: DvBlockVaux,
	0x53: DvBlockVaux,
	0x54: DvBlockVaux,
	0x55: DvBlockVaux,
	0x56: DvBlockVaux,
	0x57: DvBlockVaux,
	0x58: DvBlockVaux,
	0x59: DvBlockVaux,
	0x5A: DvBlockVaux,
	0x5B: DvBlockVaux,
	0x5C: DvBlockVaux,
	0x5D: DvBlockVaux,
	0x5E: DvBlockVaux,
	0x5F: DvBlockVaux,

	0x70: DvBlockAaux,
	0x71: DvBlockAaux,
	0x72: DvBlockAaux,
	0x73: DvBlockAaux,
	0x74: DvBlockAaux,
	0x75: DvBlockAaux,
	0x76: DvBlockAaux,
	0x77: DvBlockAaux,
	0x78: DvBlockAaux,
	0x79: DvBlockAaux,
	0x7A: DvBlockAaux,
	0x7B: DvBlockAaux,
	0x7C: DvBlockAaux,
	0x7D: DvBlockAaux,
	0x7E: DvBlockAaux,
	0x7F: DvBlockAaux,

	0x90: DvBlockVideo,
	0x91: DvBlockVideo,
	0x92: DvBlockVideo,
	0x93: DvBlockVideo,
	0x94: DvBlockVideo,
	0x95: DvBlockVideo,
	0x96: DvBlockVideo,
	0x97: DvBlockVideo,
	0x98: DvBlockVideo,
	0x99: DvBlockVideo,
	0x9A: DvBlockVideo,
	0x9B: DvBlockVideo,
	0x9C: DvBlockVideo,
	0x9D: DvBlockVideo,
	0x9E: DvBlockVideo,
	0x9F: DvBlockVideo,

}
		

class DvSequence(object):
	def __init__(self, d):
		self._d = d
		o = []
		for x in range(DV_SEQUENCE_SIZE):
			# parse
			o.append(self.parse_block(self._d[:DV_BLOCK_SIZE]))
			
			# shift
			self._d = self._d[DV_BLOCK_SIZE:]
	
		self.blocks = o
	
	def parse_block(self, d):
		# peek at the block type
		t = ord(d[0])
		if t in BLOCK_TYPES:
			return BLOCK_TYPES[t](d)
		else:
			# unknown data
			return DvBlockUnknown(d)

	def pretty(self):
		o = 'Sequence:\n'
		for i, x in enumerate(self.blocks):
			o += ' Block #%d, 0x%02X (%s):\n' % (i, x.block_type, x.__class__.__name__,)
			o += x.pretty()
		return o


class DvParser(object):
	def __init__(self, input_f, max_sequences=1):
		self._i = input_f

		self.sequences = []	
		if max_sequences is True:
			while self._i:
				self.sequences.append(self.parse_sequence())
		else:
			for x in range(max_sequences):
				self.sequences.append(self.parse_sequence())
	
	
	def parse_sequence(self):
		return DvSequence(self._i.read(DV_SEQUENCE_SIZE * DV_BLOCK_SIZE))
		

		

def dvhax_pretty(options):
	input_f = options.input[0]

	o = DvParser(input_f)
	
	for x in o.sequences:
		print x.pretty()


def dvhax_show_aspect_ratio(options):
	input_f = options.input[0]
	o = DvParser(input_f, max_sequences=1)
	
	# Find the aspect ratio data
	for block in o.sequences[0].blocks:
		if not isinstance(block, DvBlockVaux):
			continue
		
		# This may be what we want
		for pack in block.packs:
			if not isinstance(pack, DvPackVauxSourceControl):
				continue
			
			# This is the metadata block desired
			print pack.aspect_ratio.name
			return
	

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('input', nargs=1, type=argparse.FileType('rb'), help='Input file name')
	
	subparsers = parser.add_subparsers(help='Command to execute')
	
	pretty = subparsers.add_parser('pretty')
	pretty.set_defaults(func=dvhax_pretty)
	
	show_aspect_ratio = subparsers.add_parser('ar')
	show_aspect_ratio.set_defaults(func=dvhax_show_aspect_ratio)
	
	options = parser.parse_args()
	options.func(options)


if __name__ == '__main__':
	main()

