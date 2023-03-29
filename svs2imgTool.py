import os

import shutil
import traceback
import numpy as np
import scipy.misc
import os
from config import read_conf


def svs2tif(src):
    import openslide
    print os.path.exists(src)
    test = openslide.open_slide(src)
    img = np.array(test.read_region((0, 0), 0, test.dimensions))
    scipy.misc.imsave('telst.tif', img)


def svs2imgFile(file_path, group=''):
    try:
        conf = read_conf()
        if isinstance(conf, str):
            return conf
        file_dir = conf.get('file_dir')
        env = conf.get('env')
        if file_dir is None:
            return 'file_dir not in config.conf'
        # print request.json.get('file')

        file_names = file_path.split(os.path.sep)[-1].split('.')
        file_dir = '_'.join(file_names[:-1])
        source = file_dir + '_files'
        source_dzi = file_dir + '.dzi'
        if os.path.exists(source):
            shutil.rmtree(os.path.abspath(source))
        target = 'static/' + group + '/' + source
        target_dzi = 'static/' + group + '/' + source_dzi
        print source, target
        if os.path.exists(target_dzi):
            print 'has changed', file_path
        else:
            if 'Development' in env:
                vipshome = r'D:\Program Files (x86)\vips-dev-w64-all-8.12.2\vips-dev-8.12\bin'
                os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
            import pyvips
            img = pyvips.Image.new_from_file(file_path, access='sequential')
            img.dzsave(file_dir)
            print 'pyvips over', file_path
            shutil.move(source, target)
            shutil.move(source_dzi, target_dzi)
            print 'move dir over'
        return {'message': 'success', 'file_dir': target, 'file_dzi': target_dzi}
    except Exception, e:
        traceback.print_exc()
        return {'message': str(e)}

# svs2tif('static/testIMG/470650.svs')

# import pyvips
# img = pyvips.Image.new_from_file('static/testIMG/470650.svs', access='sequential')
# img.dzsave('test')
# source = 'test_files'
# target = 'static/' + source
# import shutil
# shutil.copytree(source, target)
# print 'over'
if __name__ == '__main__':
    svs2imgFile('/data/Pathology/A3/0.5_roi_0_blur_1_rs_1_bc_0_a_0.4_l_-1_bi_0_-1.0.jpg', 'A3')