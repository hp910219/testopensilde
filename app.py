import os
import shutil
import traceback
from flask import Flask, render_template, jsonify, request
from config import read_conf, jyMoveDir

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


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


@app.route("/svs/2/img/", methods=["POST", 'OPTIONS'])
def svs2img():
    try:

        conf = read_conf()
        if isinstance(conf, str):
            return conf
        file_dir = conf.get('file_dir')
        env = conf.get('env')
        if file_dir is None:
            return 'file_dir not in config.conf'
        # print request.json.get('file')
        rq = request.json
        if 'Development' in env:
            vipshome = r'D:\Program Files (x86)\vips-dev-w64-all-8.12.2\vips-dev-8.12\bin'
            os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
        file_path = rq.get('file_path')
        import pyvips

        img = pyvips.Image.new_from_file(file_path, access='sequential')
        file_names = file_path.split(os.path.sep)[-1].split('.')
        file_dir = '_'.join(file_names[:-1])
        source = file_dir + '_files'
        if os.path.exists(source):
            shutil.rmtree(os.path.abspath(source))
        target = 'static/' + source
        if os.path.exists(target):
            shutil.rmtree(os.path.abspath(target))
        print source, target
        img.dzsave(file_dir)
        print 'pyvips over'
        shutil.move(source, target)
        print 'move dir over'
        return jsonify({'message': 'success', 'file_dir': target})
    except Exception, e:
        traceback.print_exc()
        return jsonify({'message': str(e)})




if __name__ == '__main__':
    app.run()
