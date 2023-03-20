import os
vipshome = r'D:\Program Files (x86)\vips-dev-w64-all-8.12.2\vips-dev-8.12\bin'
os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
import openslide
import numpy as np
import scipy.misc
import os


def svs2tif(src):
    print os.path.exists(src)
    test = openslide.open_slide(src)
    img = np.array(test.read_region((0, 0), 0, test.dimensions))
    scipy.misc.imsave('test.tif', img)


# svs2tif('static/testIMG/470650.svs')

# import pyvips
#
# img = pyvips.Image.new_from_file('static/testIMG/470650.svs', access='sequential')
# img.dzsave('test')