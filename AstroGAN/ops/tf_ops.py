'''

   Operations I commonly use in tensorflow

'''

import tensorflow as tf
import numpy as np
import math

   
'''
   Concatenate conditioning vector on feature map axis.
   Useful for conditional gans and stuff
'''
def conv_cond_concat(x, y):
   x_shapes = x.get_shape()
   y_shapes = y.get_shape()
   return tf.concat([x, y*tf.ones([x_shapes[0], x_shapes[1], x_shapes[2], y_shapes[3]])], 3)

'''
   Kullback Leibler divergence
   https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence
   https://github.com/fastforwardlabs/vae-tf/blob/master/vae.py#L178
'''
def kullbackleibler(mu, log_sigma):
   return -0.5*tf.reduce_sum(1+2*log_sigma-mu**2-tf.exp(2*log_sigma),1)

'''
   Image Gradient Difference Loss
   seen in here https://arxiv.org/abs/1511.05440
'''   
def loss_gradient_difference(true, generated):
    true_x_shifted_right = true[:,1:,:,:]
    true_x_shifted_left = true[:,:-1,:,:]
    true_x_gradient = tf.abs(true_x_shifted_right - true_x_shifted_left)

    generated_x_shifted_right = generated[:,1:,:,:]
    generated_x_shifted_left = generated[:,:-1,:,:]
    generated_x_gradient = tf.abs(generated_x_shifted_right - generated_x_shifted_left)

    loss_x_gradient = tf.nn.l2_loss(true_x_gradient - generated_x_gradient)

    true_y_shifted_right = true[:,:,1:,:]
    true_y_shifted_left = true[:,:,:-1,:]
    true_y_gradient = tf.abs(true_y_shifted_right - true_y_shifted_left)

    generated_y_shifted_right = generated[:,:,1:,:]
    generated_y_shifted_left = generated[:,:,:-1,:]
    generated_y_gradient = tf.abs(generated_y_shifted_right - generated_y_shifted_left)
    
    loss_y_gradient = tf.nn.l2_loss(true_y_gradient - generated_y_gradient)

    loss = loss_x_gradient + loss_y_gradient
    return loss

'''
   Batch normalization
   https://arxiv.org/abs/1502.03167
'''
def bn(x):
   return tf.layers.batch_normalization(x)


'''
   Layer normalizes a 2D tensor along its second axis, which corresponds to batch
'''
def ln(x, s, b, epsilon = 1e-5):
   m, v = tf.nn.moments(x, [1], keep_dims=True)
   normalized_input = (x - m) / tf.sqrt(v + epsilon)
   return normalised_input * s + b


'''
   Instance normalization
   https://arxiv.org/abs/1607.08022
'''
def instance_norm(x, epsilon=1e-5):
   mean, var = tf.nn.moments(x, [1, 2], keep_dims=True)
   return tf.div(tf.subtract(x, mean), tf.sqrt(tf.add(var, epsilon)))

'''
   2d transpose convolution, but resizing first then performing conv2d
   with kernel size 1 and stride of 1
   See http://distill.pub/2016/deconv-checkerboard/

   The new height and width can be anything, but default to the current shape * 2
'''
def upconv2d(x, filters, method='nn', name=None, new_height=None, new_width=None, kernel_size=3):

   if method == 'bilinear': resize = tf.image.resize_images
   if method == 'bicubic':  resize = tf.image.resize_bicubic
   if method == 'area':     resize = tf.image.resize_area
   if method == 'nn':       resize = tf.image.resize_nearest_neighbor

   shapes = x.get_shape().as_list()
   height = shapes[1]
   width  = shapes[2]

   # resize image using method of nearest neighbor
   if new_height is None and new_width is None:
      x_resize = resize(x, [height*2, width*2])
   else:
      x_resize = resize(x, [new_height, new_width])

   # conv with stride 1 and padding to keep same size
   conv = tf.layers.conv2d(x_resize, filters, kernel_size, strides=1, name=name, padding='SAME')
   return conv

''' 
   Phase shift. PS is the phase shift function and _phase_shift is a helper
   https://github.com/tetrachrome/subpixel 
'''
def _phase_shift(I, r):
  bsize, a, b, c = I.get_shape().as_list()
  bsize = tf.shape(I)[0] # Handling Dimension(None) type for undefined batch dim
  X = tf.reshape(I, (bsize, a, b, r, r))
  X = tf.transpose(X, (0, 1, 2, 4, 3))  # bsize, a, b, 1, 1
  X = tf.split(X, a, 1)  # a, [bsize, b, r, r]
  X = tf.concat(2, [tf.squeeze(x) for x in X])  # bsize, b, a*r, r
  X = tf.split(X, b, 1)  # b, [bsize, a*r, r]
  X = tf.concat(2, [tf.squeeze(x) for x in X])  # bsize, a*r, b*r
  return tf.reshape(X, (bsize, a*r, b*r, 1))

def PS(X, r, depth):
  # X: input tensor of shape [batch, height, width, depth]
  # r: upsampleing ratio. 2 for doubleing the size 
  # depth: num channels of output
  #    Example: 
  #      X = [batch, 32, 32, 16]
  #      Y = PS(X, 2, 4)
  #      Y -> [batch, 64, 64, 4] 
  Xc = tf.split(3, depth, X)
  X = tf.concat(3, [_phase_shift(x, r) for x in Xc])
  return X

'''
   L1 penalty, as seen in https://arxiv.org/pdf/1609.02612.pdf
'''
def l1Penalty(x, scale=0.1, name="L1Penalty"):
    l1P = tf.contrib.layers.l1_regularizer(scale)
    return l1P(x)


######## activation functions ###########
'''
   Swish: Self gated activation function
   https://arxiv.org/pdf/1710.05941.pdf   
'''
def swish(x):
   return x*tf.nn.sigmoid(x)

'''
   Regular relu
'''
def relu(x):
   return tf.nn.relu(x)

'''
   Leaky RELU
   https://arxiv.org/pdf/1502.01852.pdf
'''
def lrelu(x, leak=0.2):
   return tf.maximum(leak*x, x)

'''
   Exponential linear units
   https://arxiv.org/abs/1511.07289
'''
def elu(x):
   return tf.nn.elu(x)

'''
   Tanh
'''
def tanh(x):
   return tf.nn.tanh(x)

'''
   Sigmoid
'''
def sig(x):
   return tf.nn.sigmoid(x)

'''
   Self normalizing neural networks paper
   https://arxiv.org/pdf/1706.02515.pdf
'''
def selu(x):
   alpha = 1.6732632423543772848170429916717
   scale = 1.0507009873554804934193349852946
   return scale*tf.where(x>=0.0, x, alpha*tf.nn.elu(x))

# activation function concats
'''
   Concatenated ReLU
   http://arxiv.org/abs/1603.05201
'''
def concat_relu(x):
   axis = len(x.get_shape())-1
   return tf.nn.relu(tf.concat([x, -x], axis))

'''
   Like concatenated relu, but with elu
   http://arxiv.org/abs/1603.05201
'''
def concat_elu(x):
   axis = len(x.get_shape())-1
   return tf.nn.elu(tf.concat(values=[x, -x], axis=axis))

'''
   Like concat relu/elu, but with selu
'''
def concat_selu(x):
   axis = len(x.get_shape())-1
   return selu(tf.concat([x, -x], axis))

###### end activation functions #########
