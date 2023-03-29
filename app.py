#! /usr/bin/env python
# coding: utf-8
import chardet
import cgi
import os
import sys
import subprocess
import traceback
import json
import shutil

from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, url_for
# from celery import Celery
from config import read_conf
from jy_word.web_tool import send_msg_by_dd, format_time, zip_dir
from jy_word.File import File
from jy_word.Word import pic_b64encode
from svs2imgTool import svs2imgFile


reload(sys)
sys.setdefaultencoding('utf-8')


# # 配置消息代理的路径，如果是在远程服务器上，则配置远程服务器中redis的URL
# app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
# # 要存储 Celery 任务的状态或运行结果时就必须要配置
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
# # 初始化Celery
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# # 将Flask中的配置直接传递给Celery
# celery.conf.update(app.config)
app = Flask(__name__)
restart_time = format_time(frm='%Y-%m%d-%H:%M:%S')
dir_name = os.path.dirname(__file__)
static_dir = os.path.join(dir_name, 'static')
project_dir = os.path.dirname(dir_name)


@app.route('/')
def hello_world():
    conf = read_conf()
    system_name = conf.get('system_name')
    return render_template('index.html',
                           static_dir=static_dir.rstrip('/'),
                           restart_time=restart_time, system_name=system_name, conf=conf)


@app.route('/test/')
def test():
    rq= request.args or {}
    return render_template('index1.html', dzi1=rq.get('dzi1'), dzi2=rq.get('dzi2'), group=rq.get('group'))


@app.errorhandler(404)
def page_not_found(e):
    conf = read_conf()
    system_name = conf.get('system_name')
    print request.path
    # print 'system_name', system_name
    return render_template('index.html', static_dir=static_dir.rstrip('/'), restart_time=restart_time, system_name=system_name, conf=conf)


@app.route("/tcm/api/", methods=["GET", "POST", "PUT", "DELETE"])
def tcm_api():
    method = request.method
    data = request.args if method == 'GET' else request.json
    url = request.headers.get('API-URL')
    api_service = request.headers.get('API-SERVICE')
    success_status = request.headers.get('SUCCESS-STATUS')
    api_method = request.headers.get('API-METHOD')
    if api_method is not None:
        method = api_method
    response_data = sort_request1(method, url, api_service, data=data)
    return jsonify(response_data)


@app.route("/tcm/save/file/", methods=["POST", 'OPTIONS'])
def save_file():
    try:
        conf = read_conf()
        if isinstance(conf, str):
            return conf
        file_dir = conf.get('file_dir')
        if file_dir is None:
            return 'file_dir not in config.conf'
        rq = request.json
        if rq is None:
            return 'nothing is requested'
        content = rq.get('content')
        dir_path = os.path.join(file_dir, 'annotate', 'input')
        if os.path.exists(dir_path) is False:
            os.makedirs(dir_path)
        file_name = rq.get('file_name') or ''
        postfix = rq.get('postfix') or 'txt'
        file_name = '%s%s.%s' % (file_name, format_time(frm='%Y%m%d%H%M%S'), postfix)
        path = os.path.join(dir_path, file_name)
        print path
        my_file.write(path, content)
        return jsonify({'path': path, "message": 'success'})
    except Exception, e:
        traceback.print_exc()
        send_msg_by_dd(traceback.format_exc())
        return jsonify({'message': str(e)})


@app.route('/tcm/download/', methods=["GET", "POST", "PUT", "DELETE", 'OPTIONS'])
def download_file():
    rq = request.args.to_dict()
    file_path = rq.get('file_path')
    if file_path is None:
        return 'Sorry, no path.'
    file_path = cgi.escape(file_path)
    dir_name = os.path.dirname(file_path)
    file_name = os.path.relpath(file_path, dir_name)
    # file_name = rq.get('file_name')
    attachment_filename = rq.get('attachment_filename')
    t = format_time(frm='%Y%m%d%H%M%S')
    if '..' in dir_name or 'password' in file_path:
        return 'Sorry, unavailable path.'
    if 'passwd' in file_path:
        return 'Sorry, unavailable path.'
    conf = read_conf()
    if isinstance(conf, str):
        return conf
    env = conf.get('env')
    if env and env in ['KOBARS']:
        if file_path not in ['/gpfs/www/kobas3/site/kobas-2.1.1/kobas-2.1.1.tar.gz',
                             '/gpfs/www/kobas3/site/kobas-2.1.1/kobas-3.0.3.tar.gz']:
            if dir_name.startswith('/gpfs/user/budc/kobas_2019/data/example') is False \
                    and dir_name.startswith('/gpfs/user/budc/kobas_2019/data/online') is False \
                    and dir_name.startswith('/gpfs/user/budc/app/app_data/output/') is False:
                return 'Sorry, unavailable path.'
    available_path_prefix = conf.get('available_path_prefix') or ''
    available_path_prefixs = available_path_prefix.split(',')
    if len(available_path_prefixs) > 0:
        error = True
        for prefix in available_path_prefixs:
            prefix = prefix.rstrip('/')
            if dir_name.startswith(prefix):
                error = False
                break
        if error:
            return 'Sorry, unavailable path.'
    if attachment_filename is None:
        file_names = file_name.split('.')
        attachment_filename = '%s_%s.%s' % ('.'.join(file_names[:-1]), t, file_names[-1])
    if os.path.exists(file_path) is False:
        return 'Sorry, file_path dose not exists.'
    return send_from_directory(dir_name, file_name, as_attachment=True, attachment_filename=attachment_filename)


@app.route("/jyweb/<action_name>/crud/", methods=["GET", "POST", "PUT", "DELETE"])
def upgrade_crud(action_name):
    conf = read_conf()
    if isinstance(conf, str):
        return conf
    file_dir = conf.get('file_dir')
    if file_dir is None:
        return 'file_dir not in config.conf'
    dir_name = os.path.join(file_dir, action_name)
    if os.path.exists(dir_name) is False:
        os.makedirs(dir_name)
    method = request.headers.get('API-METHOD') or request.method
    t = format_time(frm='%Y%m%d%H%M%S')
    if method == 'POST':
        rq = request.json
        rq['add_time'] = t
        path_new = os.path.join(dir_name, '%s_%s.json' % (action_name, t))
        my_file.write(path_new, rq)
    if method.lower() == 'delete':
        rq = request.json
        add_time = rq.get('add_time')
        path_delete = os.path.join(dir_name, '%s_%s.json' % (action_name, add_time))
        if os.path.exists(path_delete):
            item_delete = my_file.read(path_delete)
            if item_delete.get('account') == rq.get('account'):
                os.remove(path_delete)
    if method.lower() == 'put':
        rq = request.json
        add_time = rq.get('add_time')
        path_put = os.path.join(dir_name, '%s_%s.json' % (action_name, add_time))
        if os.path.exists(path_put):
            item_put = my_file.read(path_put)
            item_put.update(rq)
            my_file.write(path_put, item_put)
    items = []
    for i in os.listdir(dir_name):
        path = os.path.join(dir_name, i)
        item = my_file.read(path)
        items.append(item)
    account = request.args.get('account') if method == 'GET' else request.json.get('account')
    items = filter(lambda x: x.get('account') == account, items)
    items.reverse()
    return jsonify(items)


@app.route('/tcm/file/', methods=['POST'])
def get_file():
    rq = request.json
    query_path = rq.get('query_path') or ''
    postfix = rq.get('postfix') or []
    root_path = rq.get('root_path') or ''
    root_dir = rq.get('root_dir') or ''
    env_key = rq.get('env_key') or 'AY_USER_DATA_DIR'
    conf = read_conf()
    if isinstance(conf, str):
        return conf
    # print conf
    # JINGD_DATA_ROOT = os.environ.get('JINGD_DATA_ROOT') or conf.get('jingd_data_root')
    JINGD_DATA_ROOT = os.environ.get(env_key) or conf.get('jingd_data_root') or ''
    if root_dir:
        JINGD_DATA_ROOT = root_dir
        if root_path and root_path.startswith(root_dir):
            root_path = root_dir[len(root_dir):]
    path = os.path.join(JINGD_DATA_ROOT, root_path, query_path)
    if os.path.exists(path) is False:
        os.makedirs(path)
        return jsonify({'message': 'Path not exists, %s' % path})
    file2 = File(path)
    data = file2.get_file_list('s', '', postfix=postfix)
    data['data']['create_time'] = int(os.path.getctime(path) * 1000)
    data['data']['data_root'] = JINGD_DATA_ROOT
    data['data']['sep'] = os.path.sep
    return jsonify(data)


@app.route('/zip/dir/', methods=['POST'])
def zip_dir_rq():
    rq = request.json or {}
    dir_name = rq.get('dir') or ''
    parent_dir = os.path.dirname(dir_name)
    file_name = rq.get('file_name') or ''
    zip_name = os.path.relpath(dir_name, parent_dir) + '_'+ file_name
    file_list = rq.get('file_list')
    zip_path = os.path.join(parent_dir, zip_name)
    # zip_path = parent_dir + '/' + zip_name
    if os.path.exists(zip_path) is False:
        while True:
            zipStatus = zip_dir(parent_dir, dir_name, zip_name, file_list)
            if zipStatus == 5:
                break
    return json.dumps({'message': 'success',  'file_path': zip_path})


@app.route('/file/content/', methods=['POST'])
def get_file_content():
    rq = request.json or {}
    dir_name = rq.get('dir') or ''
    file_name = rq.get('file_name') or ''
    file_name = cgi.escape(file_name)
    file_path = rq.get('file_path') or ''
    to_json = True
    if 'to_json' in rq:
        to_json = rq.get('to_json')
    to_string = False
    if 'to_string' in rq:
        to_string = rq.get('to_string')
    path = file_path or os.path.join(dir_name, file_name)
    path = cgi.escape(path)
    if os.path.exists(path) is False:
        return json.dumps({'message': 'Path not exists, %s' % path})
    if '../' in path:
        return json.dumps({'message': 'Path is illegal, %s' % path})
    if '..' in path or 'password' in path:
        return 'Sorry, unavailable path.'
    if 'passwd' in path:
        return 'Sorry, unavailable path.'
    sheet_name = rq.get('sheet_name')
    data = my_file.read(path, to_json=to_json, to_string=to_string, sheet_name=sheet_name)
    try:
        encoding = chardet.detect(data[0])['encoding']
        # print encoding
        data = data.decode(encoding, 'ignore').encode('utf-8')
    except:
        traceback.print_exc()
    return json.dumps({'message': 'success', 'data': data, 'file_path': path})


@app.route('/file/origin/<file_name>', methods=['GET', 'POST'])
def get_file_origin(file_name):
    rq = request.json or {}
    conf = read_conf()
    if isinstance(conf, str):
        return conf
    # print conf
    # JINGD_DATA_ROOT = os.environ.get('JINGD_DATA_ROOT') or conf.get('jingd_data_root')
    dir_name = conf.get('fasta_dir') or ''

    file_name = file_name or ''

    path = os.path.join(dir_name, file_name)
    path = cgi.escape(path)
    if os.path.exists(path) is False:
        return json.dumps({'message': 'Path not exists, %s' % path})
    if '../' in path:
        return json.dumps({'message': 'Path is illegal, %s' % path})
    if '..' in path or 'password' in path:
        return 'Sorry, unavailable path.'
    if 'passwd' in path:
        return 'Sorry, unavailable path.'
    return send_from_directory(dir_name, file_name, as_attachment=True, attachment_filename=file_name)


@app.route('/transfer/img/', methods=['POST'])
def transfer_img():
    rq = request.json
    if rq is None:
        return jsonify({'message': '请求错误'})
    file_path = rq.get('file_path')
    if file_path is None:
        return jsonify({'message': 'file_path: %s' % file_path})
    if os.path.exists(file_path) is False:
        return jsonify({'message': 'file not exists: %s' % file_path})
    # if file_path.endswith('.pdf'):
    #     with open(file_path, 'rb') as f:
    #         str64 = base64.b64decode(f.read())
    #         encoding = chardet.detect(str64[0])['encoding']
    #         print encoding
    #         str64 = str64.decode(encoding, 'ignore').encode('utf-8')
    #         print str64
    # else:
    #     str64 = pic_b64encode(file_path)
    str64 = pic_b64encode(file_path)
    data = {'img': str64, 'file_path': file_path}
    import json
    return json.dumps(data)


def update_static(src_dir, postfix1=''):
    import shutil
    src_dist_dir = os.path.join(src_dir, 'dist')
    src_static_dir = os.path.join(src_dist_dir, 'static')
    for postfix in ['js', 'css']:
        src = os.path.join(src_dist_dir, 'umi.%s' % postfix)
        src_file_name = 'umi'
        file_name = src_file_name
        if postfix1:
            file_name = 'umi_%s' % (postfix1)
        des = os.path.join(static_dir, '%s.%s' % (file_name, postfix))
        if os.path.exists(src):
            print src, des
            shutil.copy(src, des)
        else:
            print 'error', src, des
    if os.path.exists(src_static_dir):
        for i in os.listdir(src_static_dir):
            src = os.path.join(src_static_dir, i)
            des = os.path.join(static_dir, i)
            if os.path.exists(src):
                shutil.copy(src, des)



@app.route("/upload/file/", methods=["POST", 'OPTIONS'])
def upload_report():
    try:
        conf = read_conf()
        if isinstance(conf, str):
            return conf
        file_dir = conf.get('file_dir')
        if file_dir is None:
            return 'file_dir not in config.conf'
        # print request.json.get('file')
        if len(request.files) == 0:
            return jsonify({"success": False, "message": 'select file'})
        for k in request.files:
            f = request.files[k]
            name_array = f.filename.split('.')
            dir_path = os.path.join(file_dir, name_array[-1])
            if os.path.exists(dir_path) is False:
                os.makedirs(dir_path)
            # t = format_time(frm='%Y%m%d%H%M%S')
            file_name = f.filename
            path = os.path.join(dir_path, file_name)
            f.save(path)
            return jsonify({'path': path, "message": 'success'})
        return jsonify({'len': len(request.files)})
    except Exception, e:
        traceback.print_exc()
        return jsonify({'message': str(e)})


@app.route("/svs/2/imgs/", methods=["POST", 'OPTIONS'])
def svs2imgs():
    try:
        # print request.json.get('file')
        rq = request.json
        file_path = rq.get('file_path')
        group = rq.get('group')
        svs1 = svs2imgFile(os.path.join(file_path, 'orig_0.jpg'), group)
        svs2 = svs2imgFile(os.path.join(file_path, '0.5_roi_0_blur_1_rs_1_bc_0_a_0.4_l_-1_bi_0_-1.0.jpg'), group)
        dzi1 = svs1.get('file_dzi')
        message1 = svs1.get('message')
        dzi2 = svs2.get('file_dzi')
        message2 = svs2.get('message')
        return jsonify({
            'dzi1': dzi1,
            'dzi2': dzi2,
            'message': 'Pic1: svs2img\n%s\nPic2: svs2img\n%s\n' % (message1, message2)
        })
    except Exception, e:
        traceback.print_exc()
        return jsonify({'message': str(e)})



@app.route("/svs/2/img/", methods=["POST", 'OPTIONS'])
def svs2img():
    try:
        # print request.json.get('file')
        rq = request.json
        file_path = rq.get('file_path')
        return jsonify(svs2imgFile(file_path))
    except Exception, e:
        traceback.print_exc()
        return jsonify({'message': str(e)})


if __name__ == '__main__':

    print 'xxx'
    from jy_word.web_tool import get_host, killport
    port = 9027
    host_info = get_host(port)
    text = '/detection/admin/'
    '98a749a93a86d15af5b9634c2db53f71'
    host_ip = host_info.get('ip')
    # killport(9005)
    killport(port)    # host_ip = '192.168.105.66'
    update_static(os.path.join(project_dir, 'Pathology'), 'Pathology')
    # shutil.copytree(r'D:\pythonproject\KOBARSWeb\dist', r'D:\pythonproject\TCMWeb\templates\kobars')
    app.run(host=host_ip, port=port)