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
	inode_table = f.read(inode_size)
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
		extent_offset = 0
		for i in range(extent_num):
			file_blk_cnt.append(unpack_from('<H',inode_table,0x38 + extent_offset)[0])
			tmp_high = unpack_from('<H',inode_table,0x3a + extent_offset)[0]
			tmp_low = unpack_from('<I',inode_table,0x3c + extent_offset)[0]
			tmp_blk_num = tmp_high<<32 | tmp_low
			tmp_offset = tmp_blk_num * blk_size
			file_blk_offset.append(tmp_offset)
			extent_offset += 12
			print "\t\t[-] block num : ",hex(file_blk_cnt[i])
			print "\t\t[-] block offset : ",hex(file_blk_offset[i])			
			
		return extent_num, file_blk_cnt, file_blk_offset, file_size
	elif depth > 0x00:
		print "[+] depth > 0!"
		sys.exit(1)

def dir_entry_parse(f, offset, file_blk_num, start):
	f.seek(offset)
	dir_entry = f.read(blk_size * file_blk_num)
	
	file_type_lst = ['file','dir','char dev','blk dev','pipe','socket','sym lnk']
	dir_inode_lst = []
	dir_fname_lst = []
	dir_type_lst = []
	
	offset = 0
	cnt = 0
	
	while(1):
		try:
			tmp_inode = unpack_from('<I',dir_entry,offset)[0]
			entry_size = unpack_from('<H',dir_entry,offset+4)[0]
			name_len = unpack_from('<B',dir_entry,offset+6)[0]
			file_type = int(unpack_from('<B',dir_entry,offset+7)[0])
			file_type_chr = file_type_lst[file_type-1]
			nb = str(name_len) + "s"
			tmp_name = unpack_from(nb,dir_entry,offset+8)[0]
			print "\t-\t",start,"\t\t",file_type_chr,"\t\t",tmp_inode,"\t\t",tmp_name
			dir_inode_lst.append(tmp_inode)
			dir_fname_lst.append(tmp_name)
			dir_type_lst.append(file_type)
			offset += entry_size
			cnt += 1
			start += 1

		except:			
			return dir_inode_lst, dir_type_lst, dir_fname_lst, cnt


def traverse(f, target_inode_lst, select, target_type_lst, target_fname_lst, extent_idx):
	target_blk_group, target_inode_num = get_blk_group_inode_num(target_inode_lst[extent_idx][select])
	blk_grp_offset = target_blk_group * blk_per_group * blk_size
	#print target_blk_group, target_inode_num, hex(blk_grp_offset)
	print "\n\t[+] block group offset : ", hex(blk_grp_offset), "\n\n"

	offset = blk_size + gdt_size * target_blk_group
	f.seek(offset)
	gdt = f.read(gdt_size)
	offset = gdt_parse(gdt) * blk_size
	print "\t[+] offset : ", offset,"\n"
	extent_num, target_blk_num, target_blk_offset, target_file_size = inode_table_parse(f, offset, target_inode_num)

	if target_type_lst[extent_idx][select] == 2:
		##### directory type		
		print "\n=========================================================="
		print "\n\t[+] directory entry information\n"
		print "\t \t[ NUM ]\t\t[ TYPE ]\t[ INODE ]\t[ NAME ]\t\n"		
		cnt = 0
		dir_inode_lst = []
		dir_type_lst = []
		dir_fname_lst = []
		dir_entry_cnt = []
		total_entry_cnt = 0

		for n in range(extent_num):
			tmp_inode_lst, tmp_type_lst, tmp_fname_lst, tmp_entry_cnt = dir_entry_parse(f, target_blk_offset[n], target_blk_num[n], total_entry_cnt)
			dir_inode_lst.append(tmp_inode_lst)
			dir_type_lst.append(tmp_type_lst)
			dir_fname_lst.append(tmp_fname_lst)
			dir_entry_cnt.append(tmp_entry_cnt)
			total_entry_cnt += tmp_entry_cnt

		print "\n=========================================================="
		while(1):
			t_select = int(raw_input("\n\nEnter demical number (-1 to exit) > "))
			if t_select == -1:
				print "\n=========================================================="
				print "\n\n\tTERMINATE THE PROGRAM!\n"
				print "\n=========================================================="
				exit(0)
			break

		for n in range(len(dir_entry_cnt)-1,-1,-1):
			if t_select >= n:
				t_select -= sum(dir_entry_cnt[:n])
				target_extent_idx = n
				break		

		traverse(f, dir_inode_lst, t_select, dir_type_lst, dir_fname_lst, target_extent_idx)
	elif target_type_lst[extent_idx][select] == 1:
		##### file type 	
		fname = target_fname_lst[extent_idx][select]	
		export = open("./export/" + fname, 'wb')
		for i in range(extent_num):			
			tmp_blk_num = target_blk_num[i]
			tmp_blk_offset = target_blk_offset[i]
			f.seek(tmp_blk_offset)
			target_file_size -= blk_size
			if target_file_size < blk_size:
				data = f.read(target_file_size)
			else:		
				data = f.read(tmp_blk_num * blk_size)
			export.write(data)
			
		export.close()
		print "\n[+] file export done\n"

		target_blk_group, target_inode_num = get_blk_group_inode_num(target_inode_lst[0][0])
		blk_grp_offset = target_blk_group * blk_per_group * blk_size		
		offset = blk_size + gdt_size * target_blk_group
		f.seek(offset)
		gdt = f.read(gdt_size)
		offset = gdt_parse(gdt) * blk_size		
		extent_num, target_blk_num, target_blk_offset, target_file_size = inode_table_parse(f, offset, target_inode_num)

		print "\n=========================================================="
		print "\n\t[+] directory entry information\n"
		print "\t \t[ NUM ]\t\t[ TYPE ]\t[ INODE ]\t[ NAME ]\t\n"		
		cnt = 0
		dir_inode_lst = []
		dir_type_lst = []
		dir_fname_lst = []
		dir_entry_cnt = []
		total_entry_cnt = 0

		for n in range(extent_num):
			tmp_inode_lst, tmp_type_lst, tmp_fname_lst, tmp_entry_cnt = dir_entry_parse(f, target_blk_offset[n], target_blk_num[n], total_entry_cnt)
			dir_inode_lst.append(tmp_inode_lst)
			dir_type_lst.append(tmp_type_lst)
			dir_fname_lst.append(tmp_fname_lst)
			dir_entry_cnt.append(tmp_entry_cnt)
			total_entry_cnt += tmp_entry_cnt

		print "\n=========================================================="
		while(1):
			t_select = int(raw_input("\n\nEnter demical number (-1 to exit) > "))
			if t_select == -1:
				print "\n=========================================================="
				print "\n\n\tTERMINATE THE PROGRAM!\n"
				print "\n=========================================================="
				exit(0)
			break

		for n in range(len(dir_entry_cnt)-1,-1,-1):
			if t_select >= n:
				t_select -= sum(dir_entry_cnt[:n])
				target_extent_idx = n
				break		

		traverse(f, dir_inode_lst, t_select, dir_type_lst, dir_fname_lst, target_extent_idx)

		sys.exit(1)
		

############################################ Main START ###########################################

if __name__ == "__main__":
### device selection
	#dev = raw_input('\n[+] Input your device image name : ')	
	#dev = 'galaxy_note.dd'	
	if len(sys.argv) < 2:
		print "\n[+] Usage : python ", sys.argv[0], " <image file>\n"
		sys.exit(1)

	dev = sys.argv[1]
	print "\n[+] image to parse : ",dev

	dir_path = "./export"
	if not os.path.isdir(dir_path):
		os.mkdir(dir_path)
		print "\n[+] export folder : ", dir_path

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
	root_extent, root_blk_num, root_blk_offset, root_file_size = inode_table_parse(f, offset,2)

	root_inode_lst = []
	root_type_lst = []
	root_fname_lst = []
	root_entry_cnt = []

	print "\n=========================================================="
	print "\n\t[+] directory entry information\n"
	print "\t \t[ NUM ]\t\t[ TYPE ]\t[ INODE ]\t[ NAME ]\t\n"	
	tmp_inode_lst, tmp_type_lst, tmp_fname_lst, tmp_entry_cnt = dir_entry_parse(f, root_blk_offset[0], root_blk_num[0], 0)	
	root_inode_lst.append(tmp_inode_lst)
	root_type_lst.append(tmp_type_lst)
	root_fname_lst.append(tmp_fname_lst)
	root_entry_cnt.append(tmp_entry_cnt)
	print "\n=========================================================="
	while(1):
		t_select = int(raw_input("\n\nEnter demical number (-1 to exit) > "))
		if t_select == -1:
			print "\n=========================================================="
			print "\n\n\tTERMINATE THE PROGRAM!\n"
			print "\n=========================================================="
			exit(0)
		break
	traverse(f, root_inode_lst, t_select, root_type_lst, root_fname_lst, 0)

	
