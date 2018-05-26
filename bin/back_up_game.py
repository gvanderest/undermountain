"""Backup the data folder to a specific ID file."""
import tarfile
import os
import os.path
from hashlib import sha256

def backup_areas(areas):


sha256(data).hexdigest()
backup_path = "{}/{}.tar.gz".format(settings.BACKUPS_FOLDER, backup_id)

if os.path.exists(backup_path):
    os.remove(backup_path)

backup = tarfile.open(backup_path, "w:gz")
folder_name = settings.DATA_FOLDER.split("/")[-1]
backup.add(settings.DATA_FOLDER, arcname=folder_name)

print("Backup ID generated: {}".format(backup_id))
print("Backup saved to {}".format(backup_path))
print("Backed up {} files.".format(len(backup.getnames())))

backup.close()