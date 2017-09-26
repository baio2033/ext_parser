from struct import *
import math



def print_sub(target):
    offset = 0
    while(1):
        try:
            tmp_inode = unpack_from('<I',target,offset)[0]
        except:
            break
        tmp_rec_len = unpack_from('<H',target,offset+0x4)[0]
        tmp_name_len = unpack_from('<B',target,offset+0x06)[0]
        tmp_file_type = unpack_from('<B',target,offset+0x07)[0]
        name_len = '<'+str(tmp_name_len)+'c'
        tmp_name = unpack_from(str(name_len),target,offset+0x08)[0:]
        name = ''
        for i in tmp_name:
            name += str(i)
            

        print "\n\t\t[-] inode : ",tmp_inode
        print "\t\t[-] record length : ",tmp_rec_len
        print "\t\t[-] file_type : ",tmp_file_type
        print "\t\t[-] name : ",name,"\n"
        
        offset += tmp_rec_len
        


if __name__ == "__main__":
    print "\n\n[+] loading diskimage..."
    print "\n[+] diskimage mounted..."

    f = open("ext3.dd","rb")

    f.seek(1024) # Boot sector 2 block
    sp_block = f.read(1024)
    print "\n==============================================="
    print "\n\t[+] super block information\n"
    inode_cnt = unpack_from('<I',sp_block,0x00)[0]
    blk_cnt = unpack_from('<I',sp_block,0x04)[0]

    blk_size_idx = unpack_from('<I',sp_block,0x18)[0]

    blk_size = pow(2,10+blk_size_idx)
    
    blk_perG = unpack_from('<I',sp_block,0x20)[0]
    inode_perG = unpack_from('<I',sp_block,0x28)[0]
    inode_struct_size = unpack_from('<H',sp_block,0x58)[0]
    gdt_size_idx = unpack_from('<H',sp_block,0xfe)[0]
    if hex(gdt_size_idx) == hex(0):
        gdt_size = 32
    else:
        gdt_size = gdt_size_idx

    blk_group_cnt = int(math.ceil(blk_cnt//blk_perG))
    print "\t\t[-] num of inodes : ",inode_cnt
    print "\t\t[-] num of blocks : ",blk_cnt
    print "\t\t[-] size of block : ",blk_size / 1024," kb"
    print "\t\t[-] blocks per group : ",blk_perG
    print "\t\t[-] inodes per group : ",inode_perG
    print "\t\t[-] size of gdt entry : ",gdt_size," bytes"
    print "\t\t[-] num of block groups : ",blk_group_cnt
    print "\t\t[-] inode struct size : ", inode_struct_size, "bytes"
    print "\n==============================================="

    #print "\n\t[+] GDT information"

    offset = 2048
    
    if blk_size_idx == 2:
        offset = blk_size

    f.seek(offset)
    gdt_block = f.read(gdt_size * blk_group_cnt)
    offset = 0x00
    #print "\t 1. start block bitmap | 2. start inode bitmap | 3. start inode table\n"
    #for i in range(blk_group_cnt):
    start_block_bitmap = unpack_from("<I",gdt_block,offset+0)[0]
    start_inode_bitmap = unpack_from("<I",gdt_block,offset+4)[0]
    start_inode_table = unpack_from("<I",gdt_block,offset+8)[0]
    #print "\t\t[-] ",start_block_bitmap,start_inode_bitmap,start_inode_table
    #offset += gdt_size


#root directory
    print"\n==============================================="
    print"\n\t[+] root directory block number "
    offset = blk_size * start_inode_table
    f.seek(offset)
    f.read(256)
    root_inode = f.read(256)

    offset = 0x28
    file_mode = unpack_from('<H',root_inode,0x00)[0]
    root_blk_ptr = []
    for i in range(0,16):
        blk_ptr = unpack_from('<I',root_inode,offset+0)[0]
        root_blk_ptr.append(blk_ptr)
        if blk_ptr != 0:
            print "\t\t[-]#",i," block pointer : ",blk_ptr
        offset += 4

    offset = root_blk_ptr[0]*blk_size
    f.seek(offset)

    print "\n####################################################\n"
#   offset = 0
    root_dir = f.read(blk_size)

    print_sub(root_dir)

    print "\n####################################################\n"



    print"\n\t[+] dir2 information...\n"
    offset = 0
    dir2_inode = unpack_from('<I',root_dir,offset+0xc+0xc+0x14+0xc)[0]
    dir2_gdt_num = (int)(math.ceil(dir2_inode // inode_perG))
    dir2_inode_num = (int)(dir2_inode % inode_perG)
    print "\t\t[+] dir2 inode : ",hex(dir2_inode), " ==> ",dir2_gdt_num," gdt, ",dir2_inode_num, " inode\n"

    offset = gdt_size * dir2_gdt_num

    start_block_bitmap = unpack_from('<I',gdt_block,offset+0x00)[0]
    start_inode_bitmap = unpack_from('<I',gdt_block,offset+0x04)[0]
    start_inode_table = unpack_from('<I',gdt_block,offset+0x08)[0]
    

    print "\t\t[-] gdt #6 inode table start address : ",hex(start_inode_table)

    offset = start_inode_table*blk_size + 256*(dir2_inode_num-1)
    f.seek(offset)

    dir_blk_data = f.read(inode_struct_size)
    filemode = unpack_from('<H',dir_blk_data,0x00)[0]
    offset = 0x28
    dir2_blk_ptr = []
    for i in range(0,15):
        if i > 11:
            double_blk_ptr = unpack_from('<i',dir_blk_data,offset)[0]
            if double_blk_ptr == 0: break
            print "\t\t\t[-] double block pointer #",i," : ",double_blk_ptr
            dir2_blk_ptr.append(double_blk_ptr)
        elif i > 13:
            triple_blk_ptr = unpack_from('<I',dir_blk_data,offset)[0]
            if triple_blk_ptr == 0: break
            print "\t\t\t\t[-] triple block pointer #",i," : ",triple_blk_ptr
            dir2_blk_ptr.append(triple_blk_ptr)
        else: 
            blk_ptr = unpack_from('<I',dir_blk_data,offset)[0]
            if blk_ptr == 0: break
            print "\t\t[-] block pointer # ",i," : ",blk_ptr
            dir2_blk_ptr.append(blk_ptr)
            offset += 4

# dir2 information
    print "\n####################################################\n"

    for i in dir2_blk_ptr:
        print "\n\n\t[-] current block pointer : ",i,"\n"
        offset = blk_size*i
        f.seek(offset)
        obj_dir = f.read(blk_size)
        print_sub(obj_dir)

    print "\n####################################################\n"


    
