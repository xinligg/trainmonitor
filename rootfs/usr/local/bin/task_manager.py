#!/usr/bin/python
import os
import shutil

class TaskManager:
	task_dict={}
	exist_app={}
	SSC_TASK_UNRUNNING=0x00000000
	SSC_TASK_RUNNING='0x00000001'
#	SSC_TASK_RUNNING='0x1'
	SSC_TASK_COMPLETED=0x00000002
	SSC_TASK_UNCOMPLETED=0x00000004
	SSC_TASK_TESTING=0x00000008
	SSC_TASK_DEFAULT=0x00000010
	SSC_TASK_INSTALL=0x00000020
	SSC_TASK_UPDATE=0x00000040
	SSC_TASK_UNINSTALL_CLIENT=0x00000080
	SSC_TASK_UNINSTALL_DATA=0x00000100
	SSC_TASK_UNINSTALL_ALL=0x00000200
	SSC_TASK_INVALID=0x80000000

	execute_func_flag=False
	
	def __init__(self, filename):
#		self.init_exist_app()
		print "now to parse task"
		self.parse_taskconf(filename)
		
	def parse_taskconf(self, filename):
		file=open(filename,"rU");
		flag="guid"
		for line in file.readlines():
			if len(line) > 5 :
				if flag=="guid" :
					guid=line.replace("GUID={","").replace("}\n","")
					flag="status"
				else:
					status=line.replace("Status=","").replace("\n","")
					if self.exist_app.has_key(guid):
						'''ignore those non-existed app'''
						status=long(status, 16)
						self.task_dict[guid]=status
						print status
					flag="guid"
		file.close()
		if long(status, 16)==long(self.SSC_TASK_RUNNING, 16):
			print "now to run wsysrt"
			os.system("/opt/wsysrt/client &")
		print flag,status

	def get_task_status(self, guid):
		return self.task_dict[guid]

	def set_task_status(self, guid, status):
		self.task_dict[guid]=status

	def add_task(self,guid, status):
		self.set_task_status(guid, status)

	def del_task(self, guid):
		del self.task_dict[guid]

	def write_back(self,filename):
		file=open(filename,"w")
		confline=["GUID={%s}\nStatus=0x%x\n" % (guid,self.task_dict[guid]) for guid in self.task_dict.keys()]
		for line in confline:
			file.write(line)
		file.close()
			
	def work(self):
		#management task
#		self.execute_task(self.SSC_TASK_UNINSTALL_CLIENT, self.execute_uninstall_client_task)
#		self.execute_task(self.SSC_TASK_UNINSTALL_DATA, self.execute_uninstall_data_task)
#		self.execute_task(self.SSC_TASK_UNINSTALL_ALL, self.execute_uninstall_all_task)
#		self.execute_task(self.SSC_TASK_INSTALL, self.execute_install_task)
#		self.execute_task(self.SSC_TASK_UPDATE, self.execute_update_task)
#		self.write_back(TASK_CONF)
		#execute task
#		self.execute_task(self.SSC_TASK_TESTING, self.execute_run_task)
#		self.execute_task(self.SSC_TASK_UNRUNNING, self.execute_run_task)
		self.execute_task(self.SSC_TASK_RUNNING, self.execute_run_task)

		#if self.execute_func_flag==False:
		#   self.execute_default_target()
#		self.execute_default_target()

	def execute_task(self, spec_status, execute_function):
		for guid in self.task_dict.keys():
			status=self.task_dict[guid]
			if status==spec_status:
				os.system("/opt/wsysrt/client &")
#				execute_function(guid, status)
#				self.execute_func_flag=True

	def execute_install_task(self,guid, status):
		print "execute execute_install_task"
		try:
			shutil.move("/mnt/hidpart/install/apps/*","/mnt/hidpart/StarOS/apps/")
			self.set_task_status(guid, self.SSC_TASK_COMPLETED)
		except IOError:
			self.set_task_status(guid, self.SSC_TASK_UNCOMPLETED)

	def execute_update_task(self,guid, status):
		print "execute execute_install_task"
		try:
			shutil.move("/mnt/hidpart/install/apps/*","/mnt/hidpart/StarOS/apps/")
			self.set_task_status(guid, self.SSC_TASK_COMPLETED)
		except IOError:
			self.set_task_status(guid, self.SSC_TASK_UNCOMPLETED)

	def execute_uninstall_client_task(self,guid, status):
		print "execute execute_uninstall_client_task"
		(phy_dir, data_dir, run_dir, install_dir)=self.exist_app[guid]
		os.system("[ -d %s ] && rm -rf %s" % (install_dir, install_dir))
		os.system("rm -rf %s" % phy_dir)
		self.set_task_status(guid, self.SSC_TASK_COMPLETED)

	def execute_uninstall_data_task(self,guid, status):
		print "execute execute_uninstall_data_task"
		(phy_dir, data_dir, run_dir,install_dir)=self.exist_app[guid]
		''' just for StarCenter2.5'''
		os.system("[ -d /mnt/hidpart/Data/apps/StarCenter2.5 ] && rm -rf /mnt/hidpart/Data/apps/StarCenter2.5")
		os.system("rm -rf %s" % data_dir)
		self.set_task_status(guid, self.SSC_TASK_COMPLETED)

	def execute_uninstall_all_task(self,guid, status):
		print "execute execute_uninstall_all_task"
		self.execute_uninstall_data_task(guid, status)
		self.execute_uninstall_client_task(guid, status)

	def execute_run_task(self,guid, status):
		print "execute execute_run_task"
#		self.set_task_status(guid, self.SSC_TASK_RUNNING)
#		(phy_dir, data_dir, run_dir,install_dir)=self.exist_app[guid]
#		self.set_task_status(guid, self.SSC_TASK_COMPLETED)
#		self.write_back(TASK_CONF)
#		os.system("cd %s; LD_LIBRARY_PATH=. ./client 1>/dev/tty9 2>/dev/tty10; cd -" % run_dir)
		os.system("/opt/wsysrt/client &")

	def init_exist_app(self):
		app_dirs=os.listdir("/mnt/hidpart/StarOS/apps/")
		for app_dir in app_dirs:
			try:
				file_stat=os.stat("/mnt/hidpart/StarOS/apps/%s/guid.conf" % app_dir)
			except OSError:
				continue
			file=open("/mnt/hidpart/StarOS/apps/%s/guid.conf" % app_dir,"rU")
			file.readline()
			guid=file.readline().replace("GUID={","").replace("}\n","")
			try:
				os.stat("/mnt/hidpart/Data/apps/%s" % app_dir)
				data_dir="/mnt/hidpart/Data/apps/%s" % app_dir
			except OSError:
				data_dir=None
			self.exist_app[guid]=("/mnt/hidpart/StarOS/apps/%s" % app_dir, data_dir, "/opt/%s" % app_dir, "/mnt/hidpart/install/apps/%s" % app_dir)
			file.close()

	def execute_default_target(self):
		print "execute execute default target"
		file=open("/mnt/hidpart/Data/default_task.conf","rU")
		guid=file.readline().replace("GUID={","").replace("}\n","")
		file.close()
		(phy_dir, data_dir, run_dir, install_dir)=self.exist_app[guid]
		os.chdir(run_dir)
		os.system("/mnt/hidpart/StarOS/scripts/shell/start_conky.sh&")
		os.system("%s/client 1>/dev/tty9 2>/dev/tty10" % run_dir)

TASK_CONF="/mnt/Data/task.conf"
os.system("cp /mnt/Data/task.conf /tmp")
taskmanager=TaskManager(TASK_CONF)
taskmanager.work()
