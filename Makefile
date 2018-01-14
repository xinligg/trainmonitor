
PRODUCT := S13A
ROOTFSSRC := ct-s13a-rootfs
RTFSIMGFILE := rootfs.ext4
ROOTFSFILE := rootfs.tar.gz
DATAPTFILE := data.tar.gz
UPDATEFILE := update.tar.gz

MEASUREMENT := M
LDPARTSIZE := 14
LDMOUNTDIR := mount
RTPARTSIZE := 512
RTMOUNTDIR := mount

WORKDIR := $(shell pwd)
ROOTFS_BUILD := build_rootfs
DATA_TMP := data

EXCLUDE_LIST := .svn .git readme *.a *.o
EXCLUDE_LIST_FILE := rsync.exclude

all: build
clean: clean_ldroot clean_rootfs clean_rootfs_img
build: ldrootfs rootfs

exclude_file:
	@rm -rf $(EXCLUDE_LIST_FILE)
	@for EXCLUDE in $(EXCLUDE_LIST); do echo $${EXCLUDE} >> $(EXCLUDE_LIST_FILE); done

rootfs: clean_rootfs
	@printf "Build rootfs ... "
	@rm -rf $(ROOTFS_BUILD)
	@mkdir $(ROOTFS_BUILD)
	@for EXCLUDE in $(EXCLUDE_LIST); do echo $${EXCLUDE} >> $(EXCLUDE_LIST_FILE); done
	@sudo rsync -a --exclude-from=$(EXCLUDE_LIST_FILE) $(ROOTFSSRC)/ $(ROOTFS_BUILD)
	@sudo ./mini.sh $(ROOTFS_BUILD)
	@(cd $(ROOTFS_BUILD) ;\
	tar zcf data.tgz data ;\
	rm -rf data/* ;\
	tar zcf $(WORKDIR)/$(ROOTFSFILE) *)
	@md5sum $(ROOTFSFILE) > $(ROOTFSFILE).md5
	@touch $(DATAPTFILE)
	@md5sum $(DATAPTFILE) > $(DATAPTFILE).md5
	@rm -rf $(EXCLUDE_LIST_FILE)
	@printf "done\n"

rootfs_img: 
	@printf "Build rootfs ..."
	@rm -f $(RTFSIMGFILE)
	@dd if=/dev/zero of=$(RTFSIMGFILE) bs=1$(MEASUREMENT) count=$(RTPARTSIZE) > /dev/null 2>&1
	@mkfs.ext4 -F -q $(RTFSIMGFILE)
	@mkdir $(RTMOUNTDIR)
	@sudo mount $(RTFSIMGFILE) $(RTMOUNTDIR)
	@for EXCLUDE in $(EXCLUDE_LIST); do echo $${EXCLUDE} >> $(EXCLUDE_LIST_FILE); done
	@sudo rsync -a --exclude-from=$(EXCLUDE_LIST_FILE) $(ROOTFSSRC)/ $(RTMOUNTDIR)
	@sudo umount $(RTMOUNTDIR)
	@rm -rf $(RTMOUNTDIR) $(EXCLUDE_LIST_FILE)
	@printf "done\n"

clean_rootfs:
	@printf "Clean rootfs ... "
	@rm -f $(ROOTFSFILE) $(DATAPTFILE) $(UPDATEFILE) $(EXCLUDE_LIST_FILE)
	@rm -f $(ROOTFSFILE).md5 $(DATAPTFILE).md5 $(UPDATEFILE).md5
	@printf "done\n"

clean_rootfs_img:
	@rm -f $(RTFSIMGFILE)
