# -*- coding: cp936 -*-
"""
提取BoVW特征(K-means or Sparse coding)

首先是除了需要前面的sift+bow以后，还需要spm或者scspm LLC等，进一步coding pooling
具体内涵还需要进一步理解？

目前一个idea是通过改进后面的coding方法，pyramid方法，替换为分割，分割单元取中心patch
进行VQ,在统计直方图时，进行面积加权统计。

进行0均值1方差预处理的pipeline
scaler = preprocessing.StandardScaler().fit(X)

最大最小化缩放 feature_range=(min, max)
min_max_scaler = preprocessing.MinMaxScaler()

@author: shuaiyi
"""

import cv2
# from sklearn.base import BaseEstimator
from sklearn.base import TransformerMixin
from skimage.io import imread
import matplotlib.pyplot as plt
import numpy as np
import cv2
import logging
logging.getLogger().setLevel(logging.INFO)

from numpy.random import random
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.feature_extraction.image import extract_patches_2d
from sklearn.decomposition import MiniBatchDictionaryLearning

''' surf k-means
#提取surf
def surf(img):
     # surf 阈值越小，特征点越多
    detector = cv2.SURF(350, _extended=True)
    src = cv2.imread(img_path)
    dst = cv2.cvtColor(src, cv2.cv.CV_RGB2GRAY)
    kp, des= detector.detect(dst, None, useProvidedKeypoints = False)
    if len(kp) != 0:
        return kp, des.reshape((len(kp),detector.descriptorSize())) # kp 行 128列
    else:
        return None, None

# 获取bow特征直方图
def computeHistograms(km, descriptors):
    code = km.predict(descriptors)
    histogram_of_words, bin_edges = np.histogram(code,
                                              bins=range(k_means_n + 1),
                                              normed=True)
    return histogram_of_words
'''

def show_dict(components, patch_size, patch_num):
    plt.figure(figsize=(4.2, 4))
    for i, comp in enumerate(components[:100]):
        plt.subplot(10, 10, i + 1)
        plt.imshow(comp.reshape(patch_size),
                   interpolation='none')
        plt.xticks(())
        plt.yticks(())
    plt.suptitle('Dictionary learned from patches\n' +\
                 'Train on %d patches' % patch_num,\
                 fontsize=16)
    plt.subplots_adjust(0.08, 0.02, 0.92, 0.85, 0.08, 0.23)

class BoVWFeature(TransformerMixin):
    """ 
    Extract BoVW Feature
        
    Parameters
    ----------
    codebook_size : int
      the size of codebook, default:1000
    
    method : str
      codebook's compute method , value: 'sc','km'
      
    """
    def __init__(self, codebook_size=512, method='sc'):
        self.codebook_size = codebook_size
        self.method = method
        self.patch_num = 40000
        self.patch_size = 8
        self.sample = 'random'
        self.feature = 'raw' # raw, surf, hog

    
    def fit(self, X, y=None):
        # compute the codes
        print 'Extracting patchs...'
        patchs = []
        num = self.patch_num // X.size
        for x in X:
            img = imread(str(x[0]))
            tmp = extract_patches_2d(img, (self.patch_size,self.patch_size), \
                                     max_patches=num, random_state=np.random.RandomState())
            patchs.append(tmp)
        data = np.vstack(patchs)
        data = data.reshape(data.shape[0], -1)
        
        data -= np.mean(data, axis=0)
        data = data/np.std(data, axis=0)
        
        print 'Learning codebook...'
        if self.method == 'sc':
            self.dico = MiniBatchDictionaryLearning(n_components=self.codebook_size, \
                                               alpha=1, n_iter=100, batch_size =100, verbose=True)
            self.dico.fit(data)
        elif self.method=='km':
            # self.dico = MiniBatchKMeans(n_clusters=self.codebook_size)
            pass
        
        return self
    
    def transform(self, X):
        """         
        Parameters
        ----------
        X : {array-like}, shape = [n_samples, 1]
            Training vectors, where n_samples is the number of samples and
            1 is image path.
      
        Returns
        -------

          array-like = [n_samples, features]
            Class labels predicted by each classifier.
        
        """
        print 'Extracting feature...'
        # setting the dictionary
        self.dico.set_params(transform_algorithm='lars')
        results = []
        for sample in X:
            img = imread(str(sample[0]))
            tmp = extract_patches_2d(img, (self.patch_size,self.patch_size), \
                                     max_patches=300, random_state=np.random.RandomState())
            data = tmp.reshape(tmp.shape[0], -1)
            data = data-np.mean(data, axis=0)
            data = data/np.std(data, axis=0)
            code = self.dico.transform(data)
            results.append(code.sum(axis=0))
        return np.vstack(results)
    
    def get_params(self, deep=True):
        return {"codebook_size": self.codebook_size}
        


