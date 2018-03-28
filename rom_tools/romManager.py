import level
import subprocess
from shutil import copy2 as fileCopy


def __validSNES(addr):
	if (addr < 0) or (addr >0x1000000):
		return False
	else:
		m = ((addr & 0xFF0000) >> 16) % 2 == 0
		b = addr & 0x8000 != 0
		return m != b

def __assertValid(addr):
	if not __validSNES(addr):
		raise IndexError 
	else:
		return addr

def __PCtoSNES(addr):
	a = ((addr << 1) & 0xFF0000) + 0x800000
	b = addr & 0xFFFF
	return a|b


def __SNEStoPC(addr):
	"""Converts LORAM addresses to PC Addresses."""
	return ((addr & 0x7f0000) >> 1) | (addr & 0x7FFF)

def __intSplit(n):
	""" Splits and Endians pointers for "ROM MODE" """
	l = []
	a=n
	while a > 0:
		l = l + [a&0xFF]
		a = a >> 8
	return l

def __backupFile(filename):
	try: 
		fileCopy(filename, filename + ".bak")
	except:
		print("FILE DOESN'T EXIST")





class RomManager(object):
	"""docstring for RomManager"""

	def __init__(self,romname = None):
		#NOTE all these values are rough estimate placeholders, replace eventually.
		self.freeBlock = 0x220000
		self.lastBlock = 0x277FFF
		self.freeHeader = 0x78000
		self.lastHeader = 0x7FFFF


		if romname != None:
			self.loadRom(romname)


	def loadRom(self, filename):
		__backupFile(filename)
		self.rom = open(filename, "r+b")

	def saveRom(self):
		self.rom.close()
		self.rom = None


	def placeBlock(self, block):
		""" Given a block of compressed level data, places it in the next spot, returns PC address"""
		length = len(block)
		offset = self.freeBlock
		self.freeBlock += length
		print("Placing block of size: 0x%x at address: 0x%x\nnew freeBlock: 0x%x" % (length, offset, self.freeBlock))
		self.writeToRom(offset, block)
		print("Space left in levelData Banks: 0x%x" % (self.lastBlock - self.freeBlock))
		return offset

	def placeHeader(self, header):
		#TODO place headers for real
		#TODO lots of keeping track of headers information
		#TODO everything?
		print("Not Yet Implimented")

	def writeToRom(self, offset, data):
		self.rom.seek(offset)
		self.rom.write(data)
	
	def placeLevels(self, levelList):
		""" Take a list of Level objects, insert all of these into the ROM """
		
		### Create lists of all the compressed level data, and the headers
		temp = list(zip(*[(x.data.getCompressed(), x.header) for x in levelList]))
		data = temp[0]
		headers = temp[1]
		

		for i in range(len(data)):
			### Desired order:
				# Place Door Data (in bank 83)
					# so we can place the door pointers in level header
				# place level data in bank (wherever)
					# so we can place the data pointer in the header
				# Place level header in bank 8F
			



			## Run through the list, placing data 
			addr = self.placeBlock(data[i])
			convert = __intSplit(__assertValid(__PCtoSNES(addr)))
			## and setting headers pointers approprietly
			headers[i].setDataPointer(convert)
			
		## TODO Place the headers some day


l = level.Level()
r=RomManager()

