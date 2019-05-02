import os
from shutil import copy as shutilCopy, make_archive
from time import sleep, strftime, localtime, time
from psutil import disk_partitions
from configparser import ConfigParser
from json import dumps, loads


class GetFile():
    """
    函数用于初始化变量
    buckFileText                过滤文件,list不存在则不进行复制
    backup                      文件备份的位置,根目录,会存在两个文件夹Bakeup,OldBakeup
    fileJson                    过期删除OldBakeup文件夹里面的文件
    self.backupPath = os.path.join(self.backup, 'Bakeup')           备份的文件夹
    self.oldBackupPath = os.path.join(self.backup, 'OldBakeup')     文件如果发生修改,这个是存放旧文件的文件夹
    self.backupZipPath = os.path.join(self.backup, 'BackZip')       存放备份文件的压缩包的文件夹
    """
    def __init__(self):
        if not os.path.isfile('config.ini'):
            with open('config.ini', 'w') as f:
                f.write(r'''[file]
        fileSuffix = doc,docx,xls,xlsx,ppt,pptx,wps,txt,txet,py
        [path]
        backupPath = C:/Users/zz/Desktop/Test''')
        config = ConfigParser()
        config.read('config.ini', encoding="utf-8")
        self.buckFileText = config.get("file", "fileSuffix")
        self.buckFileText = list('.' + i for i in self.buckFileText.split(','))
        self.backup = config.get("path", "backupPath")
        self.backupPath = os.path.join(self.backup, 'Bakeup')
        self.oldBackupPath = os.path.join(self.backup, 'OldBakeup')
        self.backupZipPath = os.path.join(self.backup, 'BackZip')
        self.fileJson = os.path.join(self.backup, 'file.json')
        for i in (self.backup, self.backupPath, self.oldBackupPath, self.backupZipPath):
            if not os.path.isdir(i):
                try:
                    os.makedirs(i)
                except:
                    pass
        self.data = {}              # json的文件的内容
        self.removable_disk = []    # 可移动的设备

    def update_file(self):
        """
        更新修改的文件,如果有文件发生更改,那样旧的文件就会存放在另一个文件夹,此处是对json文件的更新
        以及对过期的文件的删除
        :return:
        """
        if os.path.isfile(self.fileJson):
            with open(self.fileJson, 'r') as f:
                self.data = loads(f.read())
        else:
            self.data = {}
            with open(self.fileJson, 'w') as f:
                f.write(dumps(self.data))
        t = []
        for k, v in self.data.items():
            if time() - int(v) > 60:  # 大于60秒
                try:
                    os.remove(k)
                except:
                    pass
                t.append(k)
        for i in t:
            try:
                del self.data[i]
            except:
                pass
        with open(self.fileJson, 'w') as f:
            f.write(dumps(self.data))

    def get_removable_disk(self):
        """
        可移动设备的卷标,
        :return:
        """
        self.removable_disk = []
        for i in disk_partitions():
            if 'removable' in i.opts.lower():  # 在这里找到可移动设备,也即是u盘的所在位置
                self.removable_disk.append(i.device)
        if len(self.removable_disk) == 0:
            sleep(7)
        else:
            sleep(2)
        return self.removable_disk

    def get_will_dest_name(self, filename):
        """
        进行文件复制前的目的地址的构造,目的地址的目录,加上从可移动
        磁盘的目录和文件名称
        :param filename: 可移动文件的名称
        :return: 构造出的单个文件的文件名称
        """
        file_path_list = filename.split(os.sep)
        if len(file_path_list) == 1:
            return os.path.join(self.backupPath, filename)  # 会去掉盘符的标签,自动加上分隔符
        else:
            return os.path.join(*([self.backupPath] + file_path_list[1:]))

    def do_copy(self, old, new):
        """
        文件的复制,在这里进行文件夹的建立,文件的复制
        :param old: 可移动文件的文件绝对名称,路径加上文件名
        :param new:复制目的地的路径加文件名
        :return:None
        """
        dir_temp = os.path.split(new)[0]  # 可以将路径名和文件名分开
        if not os.path.isdir(dir_temp):   # 如果不存在文件夹则创建文件夹
            os.makedirs(dir_temp)
        try:
            shutilCopy(old, new)
        except:
            pass


def main():
    procer = GetFile()
    # procer.update_file()
    while True:
        # 1.文件的复制
        procer.update_file()
        for i in procer.get_removable_disk():
            for dir_path, dir_names, file_names in os.walk(i):
                for filename in file_names:
                    # ================1.过滤文件,规则buckFileText,还有就是除去临时文件==========
                    file_split = os.path.splitext(filename)  # 分离文件名中的名称和后缀
                    if (file_split[1].lower() not in procer.buckFileText) or ('~$' in file_split[1]):
                        continue
                    #  ================2.文件的名称的构造====================
                    absolute_file_name = os.path.join(dir_path, filename)
                    will_copy_file = procer.get_will_dest_name(absolute_file_name)
                    # ================3.文件的复制===========================
                    if not os.path.isfile(will_copy_file):
                        procer.do_copy(old=absolute_file_name, new=will_copy_file)
                    # =================3.1文件的更新========================
                    elif os.stat(absolute_file_name).st_mtime > os.stat(will_copy_file).st_mtime:
                        # 构造文件的命名,首先文件夹转移到另一个,然后进行分割,得到路径和名称,这里进行
                        # 复制,存在时间有限制,对于文件的更改,删去原来的文件,重新从可移动设备复制
                        path_temp = os.path.split(will_copy_file.replace(procer.backupPath, procer.oldBackupPath))
                        time_temp = strftime("%Y-%m-%d %H_%M_%S_", localtime(os.stat(will_copy_file).st_mtime))
                        oldbuckupfilename = os.path.join(path_temp[0], time_temp + path_temp[1])
                        procer.do_copy(will_copy_file, oldbuckupfilename)
                        os.remove(will_copy_file)
                        procer.do_copy(old=absolute_file_name, new=will_copy_file)
                        procer.data[oldbuckupfilename] = time()
                        with open(procer.fileJson, 'w') as f:
                            f.write(dumps(procer.data))
                    else:
                        pass
        # 2.文件的压缩
        make_archive(procer.backupZipPath+'/U盘的备份文件', 'zip', root_dir=procer.backupPath)


if __name__ == '__main__':
    main()
