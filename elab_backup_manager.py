import os
import json
import shutil
import socket
import datetime
import subprocess


class TextColor:
    def __init__(self):
        self.color_table = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
        }

    def color_text(self, input_string, color):
        if isinstance(color, str):
            color = self.color_table.get(color, None)
        r, g, b = color
        ansi_rgb = f'\x1b[38;2;{r};{g};{b}m'
        ansi_reset = '\x1b[0m'
        output_string = f'{ansi_rgb}{input_string}{ansi_reset}'
        return output_string


class PathManager:
    def __init__(self):
        self.current_user = os.getlogin()
        self.system_hostname = socket.gethostname()

    def get_elab_path(self):
        return os.path.join('/home', self.current_user, 'elab')

    def get_picolog_path(self):
        return os.path.join('/home', self.current_user, 'Documents', 'PicoLog')

    def get_remote_path(self):
        return os.path.join(self.get_elab_path(), 'Raspberry Pi Picolog Backups', self.system_hostname)


class FileSystemOperations:
    def __init__(self):
        self.path_manager = PathManager()

    def load_credentials(self, filepath=None):
        if filepath is None:
            filepath = 'elab_credentials.json'
        with open(filepath, 'r') as file:
            contents = file.read()
        file_dict = json.loads(contents)
        return file_dict

    def local_directory_check(self):
        elab_path = self.path_manager.get_elab_path()
        print(f'Checking for {elab_path}...')
        if not os.path.isdir(elab_path):
            os.mkdir(elab_path)
            print(f'Created {elab_path}.')
        else:
            print('Found.')

    def remote_directory_check(self):
        remote_path = self.path_manager.get_remote_path()
        print(f'Checking for remote path {remote_path}...')
        if not os.path.isdir(remote_path):
            os.mkdir(remote_path)
            print(f'Created {remote_path}.')
        else:
            print('Found.')

    def mount_elab(self, credentials):
        elab_path = self.path_manager.get_elab_path()
        command = f'sudo mount -v -t cifs //njdc/Elab {elab_path} -o username="{credentials["username"]}",password="{credentials["password"]}",domain=magnetikallc,uid=1000'
        print('Attempting to mount elab server...')
        try:
            output = subprocess.run(command, shell=True, check=True, capture_output=True)
            print('Successfully mounted.')
        except subprocess.CalledProcessError as e:
            if 'Permission denied' in e.stderr.decode():
                print('Permission Denied!')

    def unmount_elab(self):
        command = 'sudo umount -a -t cifs -l'
        print('Unmounting elab server...')
        subprocess.run(command, shell=True, check=True)
        print('Successfully unmounted.')

    def get_file_change_time(self, file_path):
        ctime = os.stat(file_path).st_ctime
        return datetime.datetime.fromtimestamp(ctime).strftime('%Y-%m-%d_%H%M')

    def copy_backup_to_elab(self):
        backup_filepath = os.path.join(self.path_manager.get_picolog_path(), 'BACKUP.picolog')
        new_filename = f'{self.get_file_change_time(backup_filepath)}.picolog'
        new_filepath = os.path.join(self.path_manager.get_remote_path(), new_filename)
        print(f'Copying {backup_filepath} to elab...')
        shutil.copy(backup_filepath, new_filepath)


def main():
    file_ops = FileSystemOperations()
    credentials = file_ops.load_credentials()
    file_ops.local_directory_check()
    file_ops.mount_elab(credentials)
    file_ops.remote_directory_check()
    file_ops.copy_backup_to_elab()
    file_ops.unmount_elab()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        file_ops = FileSystemOperations()
        file_ops.unmount_elab()
        raise e