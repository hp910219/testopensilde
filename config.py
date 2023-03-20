# -*- coding: utf-8 -*-
# !/usr/bin/python
# Create Date 2019/6/11 0011
__author__ = 'huohuo'
import ConfigParser
import os
import shutil
from glob import glob
dir_name = os.path.dirname(__file__)
conf_path = os.path.join(dir_name, 'config.conf')
static_dir = os.path.join(dir_name, 'static')


def read_conf():
    cf = ConfigParser.ConfigParser()
    cf.read(conf_path)
    env = cf.get('Env', 'env')
    ports = cf.items('Ports')
    if cf.has_section(env):
        items = dict(cf.items(env))
        data = {
            'ports': dict(ports),
            'env': env
        }
        data.update(items)
        return data
    return 'No such env %s' % env


def getFileDir(filename):
    conf = read_conf()
    if isinstance(conf, str):
        return conf
    file_dir = conf.get('file_dir')
    if file_dir is None:
        return 'file_dir not in config.conf'
    name_array = filename.split('.')
    dir_path = os.path.join(file_dir, name_array[-1])
    return dir_path


def write_conf(env):
    config = ConfigParser.ConfigParser()
    # [Env]
    # env: Development4
    #
    # [Ports]
    # api: 8000
    # auth: 6011
    # detection: 6021

    # [KOBARS]
    # port: 8010
    # endpoint: http://192.168.130.12
    # file_dir: /data/tcm
    # JINGD_DATA_ROOT: /mnt/glocal5/userData
    # system_name: /tumor
    # project_action: 项目
    # sample_action: 样本
    # page_title: KOBARS
    # umi_name: umi_kobars
    config.add_section('Env')
    config.set('Env', 'env', env)

    config.add_section('Ports')
    config.set('Ports', 'api', 8000)
    config.set('Ports', 'auth', 6011)
    config.set('Ports', 'detection', 6021)

    config.add_section(env)
    config.set(env, 'file_dir', '/data/' + env)
    config.set(env, 'system_name', env)
    config.set(env, 'project_action', '项目')
    config.set(env, 'project_action', '样本')
    with open(conf_path, 'w+') as f:
        config.write(f)


def jyMoveFile(src_file, des):
    sDir, sName = os.path.split(src_file)
    if os.path.isfile(src_file):
        if os.path.exists(des) is False:
            os.makedirs(des)
        shutil.move(src_file, os.path.join(des, sName))
    print 'move over'


def jyMoveDir(src, des):
    file_list = glob(src)
    for src_file in file_list:
        print src_file
        jyMoveFile(src_file, des)
    print 'move over'
    # os.rmdir(src)


if __name__ == "__main__":
    # print read_conf()
    # write_conf('TEST')
    # jyMoveFile()
    pass
    

