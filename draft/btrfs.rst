Single disk
===========

root@smithers$ lsblk
NAME                      MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
sdd                         8:48   1   2,7T  0 disk
├─sdd2                      8:50   1   1,8T  0 part /btrfs
└─sdd1                      8:49   1 931,3G  0 part
sdb                         8:16   0 931,5G  0 disk
sdc                         8:32   0 465,8G  0 disk
├─sdc2                      8:34   0   500M  0 part /boot
├─sdc3                      8:35   0 125,9G  0 part
│ ├─bx100-var_lib_libvirt 253:1    0   120G  0 lvm  /var/lib/libvirt
│ └─bx100-swap            253:0    0   5,9G  0 lvm  [SWAP]
├─sdc1                      8:33   0   200M  0 part /boot/efi
└─sdc4                      8:36   0 339,2G  0 part /home
sda                         8:0    0 931,5G  0 disk
└─sda1                      8:1    0 931,5G  0 part

root@smithers$ df /btrfs
Sys. de fichiers blocs de 1K   Utilisé Disponible Uti% Monté sur
/dev/sdd2         1953703364 419060332 1534050996  22% /btrfs

root@smithers$ btrfs filesystem show /btrfs
Label: none  uuid: 0b90e842-ec83-4733-9c4b-8699ca9acd5a
	Total devices 1 FS bytes used 398.71GiB
	devid    1 size 1.82TiB used 401.02GiB path /dev/sdd2

root@smithers$ btrfs filesystem usage /btrfs
Overall:
    Device size:		   1.82TiB
    Device allocated:		 401.02GiB
    Device unallocated:		   1.43TiB
    Device missing:		     0.00B
    Used:			 399.23GiB
    Free (estimated):		   1.43TiB	(min: 731.90GiB)
    Data ratio:			      1.00
    Metadata ratio:		      2.00
    Global reserve:		 427.56MiB	(used: 0.00B)

Data,single: Size:399.01GiB, Used:398.19GiB
   /dev/sdd2	 399.01GiB

Metadata,DUP: Size:1.00GiB, Used:529.58MiB
   /dev/sdd2	   2.00GiB

System,DUP: Size:8.00MiB, Used:64.00KiB
   /dev/sdd2	  16.00MiB

Unallocated:
   /dev/sdd2	   1.43TiB

manage and query devices in the filesystem
root@smithers$ btrfs device usage /btrfs
/dev/sdd2, ID: 1
   Device size:             1.82TiB
   Device slack:            3.50KiB
   Data,single:           399.01GiB
   Metadata,DUP:            2.00GiB
   System,DUP:             16.00MiB
   Unallocated:             1.43TiB


Add second disk
===============

root@smithers$ btrfs device add /dev/sda1 /btrfs -f
root@smithers$ btrfs device usage /btrfs
/dev/sda1, ID: 2
   Device size:           931.51GiB
   Device slack:              0.00B
   Unallocated:           931.51GiB

/dev/sdd2, ID: 1
   Device size:             1.82TiB
   Device slack:            3.50KiB
   Data,single:           399.01GiB
   Metadata,DUP:            2.00GiB
   System,DUP:             16.00MiB
   Unallocated:             1.43TiB

root@smithers$ time btrfs balance start -dconvert=raid1 -mconvert=raid1 /btrfs
Done, had to relocate 402 out of 402 chunks

real	120m53.416s
user	0m0.001s
sys	7m33.899s

