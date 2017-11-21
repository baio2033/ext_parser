'''
	ext4 parser python script
	Jungwan Choi
	Korea Univ. CYDF
	baio2033@korea.ac.kr
'''
from struct import *
import math
import os, sys

def get_blk_group_inode_num(target_inode_num):
	return target_inode_num/inode_per_group, target_inode_num%inode_per_group

def gdt_parse(gdt_blk):
	offset = 0
	blk_bitmap = unpack_from('<I',gdt_blk,offset)[0]
	inode_bitmap = unpack_from('<I',gdt_blk,offset+4)[0]
	inode_table = unpack_from('<I',gdt_blk,offset+8)[0]
	print "\n=========================================================="
	print "\n\t[+] GDT block information\n"
	print "\n\t\t[-] block bitmap start block : ",blk_bitmap
	print "\t\t[-] inode bitmap start block : ",inode_bitmap
	print "\t\t[-] inode table start block : ",inode_table
	print "\n=========================================================="
	return inode_table


def inode_table_parse(f, offset,num):
	f.seek(offset+inode_size*(num-1))
	inode_table = f.read(offset)
	file_size = unpack_from('<I',inode_table,0x04)[0]
	signature = unpack_from('<H',inode_table,0x28)[0]
	extent_num = unpack_from('<H', inode_table, 0x2a)[0]
	depth = unpack_from('<H',inode_table,0x2e)[0]
	print "\n=========================================================="
	print "\n\t[+] inode table information\n"
	print "\n\t\t[-] signature : ",hex(signature)
	print "\t\t[-] extent num : ",extent_num
	print "\t\t[-] file size : ",file_size
	if depth == 0x00:
		print "\t\t[-] depth of tree : ",hex(depth)
		file_blk_cnt = []
		file_blk_offset = []
		for i in range(extent_num):
			file_blk_cnt.append(unpack_from('<H',inode_table,0x38)[0])
			tmp_high = unpack_from('<H',inode_table,0x3a)[0]
			tmp_low = unpack_from('<I',inode_table,0x3c)[0]
			tmp_blk_num = tmp_high<<32 | tmp_low
			tmp_offset = tmp_blk_num * blk_size
			file_blk_offset.append(tmp_offset)
			print "\t\t[-] block num : ",hex(file_blk_cnt[i])
			print "\t\t[-] block offset : ",hex(file_blk_offset[i])
			return extent_num, file_blk_cnt, file_blk_offset
	elif depth > 0x00:
		print "[+] depth > 0!"
		sys.exit(1)

def dir_entry_parse(f, offset, file_blk_num):
	f.seek(offset)
	dir_entry = f.read(blk_size * file_blk_num)
	print "\n=========================================================="
	print "\n\t[+] directory entry information\n"
	file_type_lst = ['file','dir','char dev','blk dev','pipe','socket','sym lnk']
	dir_inode_lst = []
	dir_fname_lst = []
	dir_type_lst = []
	
	offset = 0
	cnt = 0
	print "\t \t[ NUM ]\t\t[ TYPE ]\t[ INODE ]\t[ NAME ]\t\n"
	while(1):
		try:
			tmp_inode = unpack_from('<I',dir_entry,offset)[0]
			entry_size = unpack_from('<H',dir_entry,offset+4)[0]
			name_len = unpack_from('<B',dir_entry,offset+6)[0]
			file_type = int(unpack_from('<B',dir_entry,offset+7)[0])
			file_type_chr = file_type_lst[file_type-1]
			nb = str(name_len) + "s"
			tmp_name = unpack_from(nb,dir_entry,offset+8)[0]
			print "\t-\t",cnt,"\t\t",file_type_chr,"\t\t",tmp_inode,"\t\t",tmp_name
			dir_inode_lst.append(tmp_inode)
			dir_fname_lst.append(tmp_name)
			dir_type_lst.append(file_type)
			offset += entry_size
			cnt += 1

		except:
			print "\n=========================================================="
			select = raw_input("\n\nEnter demical number (-1 to exit) > ")
			if int(select) == -1:
				print "\n=========================================================="
				print "\n\n\tTERMINATE THE PROGRAM!\n"
				print "\n=========================================================="
				exit(0)
			elif int(select) >= cnt:
				print "\n\t[*] check your number!"
			else:
				return dir_inode_lst, int(select), dir_type_lst, dir_fname_lst


def traverse(f, target_inode_lst, select, target_type_lst, target_fname_lst):
	target_blk_group, target_inode_num = get_blk_group_inode_num(target_inode_lst[select])
	blk_grp_offset = target_blk_group * blk_per_group * blk_size
	#print target_blk_group, target_inode_num, hex(blk_grp_offset)
	
	if target_blk_group != 0 and target_blk_group % 2 == 0:
		offset = blk_grp_offset + blk_size * 2	
	elif target_blk_group == 0:
		offset = blk_grp_offset + blk_size + gdt_size * target_blk_group
		f.seek(offset)
		gdt = f.read(gdt_size)
		offset = gdt_parse(gdt) * blk_size
	else:
		offset = blk_grp_offset
		f.seek(offset)
		chk_sb = f.read(blk_size)
		magic_num = unpack_from('<H', chk_sb, 0x38)[0]
		if magic_num == 0xef53:
			offset = blk_grp_offset + blk_size + gdt_size * target_blk_group
			f.seek(offset)
			#print hex(f.tell())
			gdt = f.read(gdt_size)
			offset = gdt_parse(gdt) * blk_size
		else:
			offset = blk_grp_offset + blk_size * 2

	extent_num, target_blk_num, target_blk_offset = inode_table_parse(f, offset, target_inode_num)

	if target_type_lst[select] == 2:
		##### directory type				
		cnt = 0
		for i in target_blk_num:
			#print i
			tmp_inode_lst,t_select, tmp_type_lst, tmp_fname_lst = dir_entry_parse(f, target_blk_offset[cnt], i)
			traverse(f, tmp_inode_lst, t_select, tmp_type_lst, tmp_fname_lst)
			cnt += 1
	elif target_type_lst[select] == 1:
		##### file type 	
		fname = target_fname_lst[select]	
		export = open(fname, 'wb')
		for i in range(extent_num):			
			tmp_blk_num = target_blk_num[i]
			tmp_blk_offset = target_blk_offset[i]
			f.seek(tmp_blk_offset)
			data = f.read(tmp_blk_num * blk_size)
			export.write(data)
			
		export.close()
		print "\n[+] file export done\n"
		sys.exit(1)
		

############################################ Main START ###########################################

if __name__ == "__main__":
### device selection
	#dev = raw_input('\n[+] Input your device image name : ')	
	dev = 'galaxy_note.dd'
	print "\n[+] image to parse : ",dev

	f = open(dev,"rb")

### super block parsing
	f.seek(1024)
	sp_block = f.read(1024)
	print "\n=========================================================="
	print "\n\t[+] super block information\n"
	inode_cnt = unpack_from('<I', sp_block, 0x00)[0]
	blk_cnt = unpack_from('<I', sp_block, 0x04)[0]
	blk_size_idx = unpack_from('<I', sp_block, 0x18)[0]
	blk_size = pow(2,10+blk_size_idx)
	blk_per_group = unpack_from('<I', sp_block, 0x20)[0]
	inode_per_group = unpack_from('<I', sp_block, 0x28)[0]
	inode_size = unpack_from('<H', sp_block, 0x58)[0]
	gdt_size_idx = unpack_from('<H', sp_block, 0xfe)[0]

	if hex(gdt_size_idx) == hex(0):
		gdt_size = 32
	else:
		gdt_size = gdt_size_idx

	blk_group_cnt = int(math.ceil(blk_cnt//blk_per_group))
	print "\t\t[-] num of inodes : ",inode_cnt
	print "\t\t]-] num of blocks : ",blk_cnt
	print "\t\t[-] size of block : ",blk_size / 1024," kb"
	print "\t\t[-] blocks per group : ",blk_per_group
	print "\t\t[-] inodes per group : ",inode_per_group
	print "\t\t[-] size of gdt entry : ",gdt_size," bytes"
	print "\t\t[-] num of block groups : ",blk_group_cnt
	print "\t\t[-] inode struct size : ",inode_size, "bytes"
	print "\n==========================================================\n"

### GDT block parsing
	offset = 2048
	if blk_size_idx == 2:
		offset = blk_size

	f.seek(offset)
	gdt_blk = f.read(gdt_size * blk_group_cnt)
	inode_table_blk = gdt_parse(gdt_blk)

### root directory
	offset = inode_table_blk * blk_size

	root_blk_num = []
	root_blk_offset = []
	root_extent, root_blk_num, root_blk_offset = inode_table_parse(f, offset,2)

	root_inode_lst, select, root_type_lst, root_fname_lst = dir_entry_parse(f, root_blk_offset[0], root_blk_num[0])
	traverse(f, root_inode_lst, select, root_type_lst, root_fname_lst)

	
