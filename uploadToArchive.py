# 
# Upload to ukmon from Python
#

import boto3
import os


def uploadOneFile(arch_dir, dir_file, s3, targf):
    target = 'ukmon-shared'
    spls = arch_dir.split('_')
    ymd = spls[1]

    outf = targf + ymd[:4] + '/' + ymd[:6] + '/' + ymd + '/' + dir_file
    # s3.meta.client.upload_file(os.path.join(arch_dir, dir_file), target, outf)
    print(outf)
    return


def uploadToArchive(arch_dir):
    try:
        targf = os.getenv('S3FOLDER')
        key = os.getenv('AWS_ACCESS_KEY_ID')
        secr = os.getenv('AWS_SECRET_ACCESS_KEY')
        reg = os.getenv('AWS_DEFAULT_REGION')
    except Exception:
        print('unable to identify target folder')
        return 

    conn = boto3.session(aws_access_key_id=key, aws_secret_access_key=secr, region_name=reg)
    s3 = conn.resource('s3')

    dir_contents = os.listdir(arch_dir)
    for dir_file in dir_contents:
        file_name, file_ext = os.path.splitext(dir_file)
        file_ext = file_ext.lower()
        if ('FTPdetectinfo' in dir_file) and (file_ext == '.txt') and ('_original' not in file_name) and ('_backup' not in file_name):
            uploadOneFile(arch_dir, dir_file, s3, targf)
        if (file_ext == '.mp4') and ('FF_' in file_name):
            uploadOneFile(arch_dir, dir_file, s3, targf)
        elif file_ext in ('.jpg', '.kml', '.cal', '.json', '.csv') and ('DETECTED' not in file_name) and ('CAPTURED' not in file_name): 
            uploadOneFile(arch_dir, dir_file, s3, targf)
        elif dir_file == 'mask.bmp' or dir_file == 'flat.bmp' or dir_file == '.config':
            uploadOneFile(arch_dir, dir_file, s3, targf)
    return
