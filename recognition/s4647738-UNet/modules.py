# -*- coding: utf-8 -*-
"""modules.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wpmvgGc9HxQ6BB21XRigIeS_xp5P1Gkd
"""

import tensorflow as tf
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Conv2DTranspose, Cropping2D, Concatenate, Dropout, Layer, Add, Input, LeakyReLU, UpSampling2D
from tensorflow.keras.models import Model
from tensorflow.keras import backend as k

class ContextModule(Layer):
  def __init__(self, filters):
    super(ContextModule, self).__init__()
    self.convA = Conv2D(filters = filters,
                        kernel_size = (3,3))
    self.convB = Conv2D(filters = filters,
                        kernel_size = (3,3))
    self.dropout = Dropout(0.3)
  def call(self, inputs):
    x = self.convA(inputs)
    x = self.convB(x)
    return self.dropout(x)

class LocalizationModule(Layer):
  def __init__(self, filters):
    super(LocalizationModule, self).__init__()
    self.convA = Conv2D(filters = filters,
                        kernel_size = (3,3))
    self.convB = Conv2D(filters = filters,
                        kernel_size = (1,1))
  def call(self, inputs):
    x = self.convA(inputs)
    return self.convB(x)

class SegmentationModule(Layer):
  def __init__(self, filters):
    super(SegmentationModule, self).__init__()
    self.conv = Conv2D(filters = filters, 
                       kernel_size = (3, 3), 
                       padding='same')
    self.relu = LeakyReLU(alpha = 0.01)
    self.up = UpSampling2D(size = (2, 2))
  def call(self, inputs):
    x = self.conv(inputs)
    x = self.relu(x)
    return self.up(x)

def ImprovedUnet():
    ### ENCODER ###
    inputs = Input(shape=(256, 256, 1))
    # layer 1
    conv1 = Conv2D(filters = 16, kernel_size = (3,3))(inputs)
    context1 = ContextModule(16)(conv1)
    add1 = Add()([conv1, context1])
    
    # layer 2
    conv2 = Conv2D(filters = 32, kernel_size = (3,3), stride = 2)(add1)
    context2 = ContextModule(32)(conv2)
    add2 = Add()([conv2, context2])

    # layer 3
    conv3 = Conv2D(filters = 64, kernel_size = (3,3), stride = 2)(add2)
    context3 = ContextModule(64)(conv3)
    add3 = Add()([conv3, context3])

    # layer 4
    conv4 = Conv2D(filters = 128, kernel_size = (3,3), stride = 2)(add3)
    context4 = ContextModule(128)(conv4)
    add4 = Add()([conv4, context4])

    # layer 5
    conv5 = Conv2D(filters = 256, kernel_size = (3,3), stride = 2)(add4)
    context5 = ContextModule(256)(conv5)
    add5 = Add()([conv5, context5])
    ### DECODER ###
    up1 = Conv2DTranspose(filters = 128, kernel_size = (3,3))(add5)
    
    # layer 4
    concat1 = Concatenate()[(up1, add4)]
    localization1 = LocalizationModule(128)(concat1)
    up2 = Conv2DTranspose(filters = 64, kernel_size = (3,3))(localization1)
    
    # layer 3
    concat2 = Concatenate()[(up2, add3)]
    localization2 = LocalizationModule(64)(concat2)
    up3 = Conv2DTranspose(filters = 32, kernel_size = (3,3))(localization2)
    seg1 = SegmentationModule(2)(localization2)
    
    # layer 2
    concat3 = Concatenate()[(up3, add2)]
    localization3 = LocalizationModule(32)(concat3)
    up4 = Conv2DTranspose(filters = 16, kernel_size = (3,3))(localization3)
    seg2 = SegmentationModule(2)(localization3)
    add6 = Add()([seg1, seg2])

    # layer 1
    concat4 = Concatenate()[(up4, add1)]
    conv2 = Conv2D(filters = 32, kernel_size = (3,3))(concat4)
    seg3 = SegmentationModule(2)(conv2)
    add7 = Add()([seg3, add6])
    outputs = Conv2D(filters = 2, kernel_size = (3, 3), padding='same', activation='softmax')(add7)
    model = Model(inputs, outputs)
    return model

def dice_similarity(x, y):
    x = k.flatten(x)
    y = k.flatten(y)
    intersect = k.sum(x * y)
    union = k.sum(x) + k.sum(y)
    return 2 * intersect / union

