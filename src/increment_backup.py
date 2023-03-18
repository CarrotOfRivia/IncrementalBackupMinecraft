from datetime import datetime
import ftplib
import os
import os.path as osp
import yaml
import subprocess
from glob import glob

from ftplib import FTP_TLS
from omegaconf import DictConfig
from tendo import singleton


class IncrementBackup:
    def __init__(self, cfg: DictConfig) -> None:
        now = datetime.now()
        self._ftp = None
        self.cfg = cfg

        self.workdir = self.cfg.workdir
        self.modify_yaml = osp.join(self.workdir, "modify.yaml")
        self.str_now = now.strftime("%Y-%m-%d_%H-%M-%S")
        self.savedir = osp.join(self.workdir, f"backup_{self.str_now}")

        self._modify_dict = None

    def run(self):
        # prevents multiple process working on the same backup
        # only one instance of the program can run at a time
        me = singleton.SingleInstance()

        if self.archive_needed():
            self.archive_workdir()
            
        self.download_folder(self.cfg.ftp.src_folder, self.savedir, self.ftp, self.modify_dict)
        with open(self.modify_yaml, "w") as f:
            yaml.safe_dump(self.modify_dict, f)

        print("SUCCESS!!")

    def archive_needed(self):
        backup_folders = glob(osp.join(self.workdir, "backup_*"))
        backup_cnt = len(backup_folders)
        if isinstance(self.cfg.backup_threshold, int):
            backup_threshold = self.cfg.backup_threshold
        else:
            assert isinstance(self.cfg.backup_threshold, str), self.cfg.backup_threshold.__class__
            backup_threshold = eval(self.cfg.backup_threshold)
        return backup_cnt >= backup_threshold

    def archive_workdir(self):
        all_backups = glob(osp.join(self.workdir, "backup_*"))
        all_backups.sort()
        lastest_backup = osp.basename(all_backups[-1]).split("backup_")[-1]
        save_name = f"backup_until_{lastest_backup}.tar.gz"
        cmd_tar = f"tar -cavf {save_name} {self.workdir}"
        cmd_mv = f"mv {save_name} {self.cfg.archive_root}"
        cmd_rm = f"rm -r {self.workdir}"
        print(f"compressing working directory as {save_name}...")
        subprocess.run(cmd_tar, shell=True, check=True)
        print(f"moving compressed file {save_name} to {self.cfg.archive_root}")
        subprocess.run(cmd_mv, shell=True, check=True)
        print("removing current work dir...")
        subprocess.run(cmd_rm, shell=True, check=True)
        print("achive work dir complete!")

    def download_folder(self, src, dst, ftp: ftplib.FTP, modify_dict):
        #path & destination are str of the form "/dir/folder/something/"
        #path should be the abs path to the root FOLDER of the file tree to download
        
        ftp.cwd(src)
        #list children:
        
        for folder_or_file in ftp.mlsd():
            if folder_or_file[1]["type"] == "dir":
                #this will check if file is folder:
                ftp.cwd(osp.join(src, folder_or_file[0]))
                #if so, explore it:
                self.download_folder(osp.join(src, folder_or_file[0]), osp.join(dst, folder_or_file[0]), ftp, modify_dict)
            else:
                #not a folder with accessible content
                #download & return
                #possibly need a permission exception catch:
                modify_time = folder_or_file[1]["modify"]
                fname = folder_or_file[0]
                ffull = str(osp.join(src, fname))
                if ffull in modify_dict and modify_dict[ffull] == modify_time:
                    print(f"Skipping {fname}")
                    continue

                os.makedirs(dst, exist_ok=True)
                dst_f = osp.join(dst, fname)
                with open(dst_f, "wb") as f:
                    try:
                        ftp.retrbinary("RETR "+fname, f.write)
                    except ftplib.error_perm:
                        print(f"Failed to download file: {dst_f}")
                        os.remove(dst_f)
                        continue
                    modify_dict[ffull] = modify_time
                    print(fname + " downloaded")
        return

    @property
    def ftp(self):
        if self._ftp is None:
            ftp = FTP_TLS()
            ftp.connect(**self.cfg.ftp.connect)
            ftp.login(**self.cfg.ftp.login)
            self._ftp = ftp
        return self._ftp
    
    @property
    def modify_dict(self):
        if self._modify_dict is None:
            if osp.exists(self.modify_yaml):
                with open(self.modify_yaml) as f:
                    self._modify_dict = yaml.safe_load(f)
            else:
                self._modify_dict = {}
        return self._modify_dict
