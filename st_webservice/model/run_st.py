
# coding: utf-8

# In[1]:

import uuid
import flask
import gc

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import tensorflow as tf
import time
import functools
import os
#os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # force tensorflow to use CPU for Heroku
#os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import json
import math as mt

from matplotlib.ticker import StrMethodFormatter

from PIL import Image

from tensorflow.keras import backend as K
from tensorflow.keras.applications import VGG16, VGG19, InceptionV3
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg16_prp
from tensorflow.keras.applications.vgg19 import preprocess_input as vgg19_prp
from tensorflow.keras.applications.inception_v3 import preprocess_input as inc_prp

import tensorflow.contrib.eager as tfe

from tensorflow.python.keras.preprocessing import image as kp_image
from tensorflow.python.keras import models, losses, layers

#from google.colab import files

import IPython.display
from st_webservice import celery

# In[2]:


#mpl.rcParams['figure.figsize'] = (10,10)
#mpl.rcParams['axes.grid'] = False


# In[3]:


tf.enable_eager_execution()
print("Eager execution: {}".format(tf.executing_eagerly()))

content_layers = ['block5_conv2'] 
style_layers = ['block1_conv1',
                'block2_conv1',
                'block3_conv1', 
                'block4_conv1', 
                'block5_conv1']

content_layers_inc = ['mixed6']
style_layers_inc = [
    'mixed5', 'mixed6', 'mixed7', 'mixed8', 'mixed9'
]

num_content_layers = len(content_layers)
num_style_layers = len(style_layers)
num_content_layers_inc = len(content_layers_inc)
num_style_layers_inc = len(style_layers_inc)


# ### Mount google drive

# In[4]:


# Uncomment these lines to import your google drive
#from google.colab import drive
#drive.mount('/content/gdrive')


# ### **Setup image directory** (change image paths and download your own images)

# In[5]:

'''
style_dir = '/test_images/style'
content_dir = '/test_images/content'
if not os.path.exists(style_dir):
    os.makedirs(style_dir)
    get_ipython().system('wget --quiet -P /test_images/style/ https://i.imgur.com/Jjm8lsX.jpg')
    get_ipython().system('wget --quiet -P /test_images/style/ https://i.imgur.com/hSkxYmV.jpg')
    get_ipython().system('wget --quiet -P /test_images/style/ https://i.imgur.com/K5Vd72D.jpg')
    
    
if not os.path.exists(content_dir):
    os.makedirs(content_dir)
    get_ipython().system('wget --quiet -P /test_images/content/ https://i.imgur.com/2P5MbaW.jpg')
    get_ipython().system('wget --quiet -P /test_images/content/ https://i.imgur.com/BsrOXBL.jpg')
    get_ipython().system('wget --quiet -P /test_images/content/ https://i.imgur.com/GuAB8OE.jpg')


# In[11]:


content_image_path = "test_images/content/GuAB8OE.jpg"
style_image_path = "test_images/style/K5Vd72D.jpg"
'''

# ### Read and plot the downloaded images

# In[12]:


def read_image(src, img_w, img_h):
  
    img = Image.open(src)
    
    #scale the image according to its max size
    long = max(img.size)
    scale = img_w/long
    
    img = img.resize((round(img.size[0]*scale), round(img.size[1]*scale)), Image.ANTIALIAS)
  
    img = kp_image.img_to_array(img)
  
    # broadcast the image array such that it has a batch dimension 
    img_resized = np.expand_dims(img, axis=0)

    return img_resized 


# In[38]:


def plot_image(image, title=""):
  
  output = image.copy()
  if len(image.shape) == 4:
    # Remove the batch dimension
    output = np.squeeze(image, axis=0)
  # Normalize for display 
  output = output.astype('uint8')
  plt.gca().get_yaxis().set_visible(False)
  plt.gca().get_xaxis().set_visible(False)
  plt.title(title)
  plt.imshow(output)


# In[14]:


def plot_side_by_side(content_image_path, style_image_path, result_image=None, 
                      st_title='Style image', ct_title='Content Image', results=False):
  
  plt.figure(figsize=(18,18))
  
  content_image = read_image(content_image_path).astype('uint8')
  style_image = read_image(style_image_path).astype('uint8')
  
  if results and result_image is not None:
    
    plt.subplot(1, 3, 1)
    plot_image(content_image, ct_title)
    
    plt.subplot(1, 3, 2)
    plot_image(style_image, st_title)
  
    plt.subplot(1, 3, 3)
    plot_image(result_image, 'Result Image')
   
  else:
    
    plt.subplot(1, 2, 1)
    plot_image(content_image, ct_title)

    plt.subplot(1, 2, 2)
    plot_image(style_image, st_title)
  
  
  
  plt.show()


# In[15]:


# plot_side_by_side(content_image_path, style_image_path)


# ### Preprocessing of content and style images

# #### 1. VGG-based preprocessing

# In[16]:


def preprocess_img(img_path, img_w, img_h, prp_type):
    img = read_image(img_path, img_w, img_h)
    img = prp_type(img)
    return img


# #### 2. VGG-based deprocessing - confirm image shape and add each channel by its mean

# In[17]:


def deprocess_img(processed_img, inception=False):
    x = processed_img.copy()
    if len(x.shape) == 4:
        x = np.squeeze(x, 0)
    assert len(x.shape) == 3, ("Input to deprocess image must be an image of "
                             "dimension [1, height, width, channel] or [height, width, channel]")

    if len(x.shape) != 3:
        message = "Invalid input to deprocessing image." 
        return
        
    if inception:
      x *= 255.
      x += 0.5
      x /= 2.
    
    # perform the inverse of the preprocessing step
    # add channel mean values from vgg literature and convert BGR to RGB
    x[:, :, 0] += 103.939
    x[:, :, 1] += 116.779
    x[:, :, 2] += 123.68
    
    if inception==False:
      x = x[:, :, ::-1]

    x = np.clip(x, 0, 255)
    return x


# #### 3. VGG processing test

# In[18]:

'''
style_image_vgg = preprocess_img(style_image_path, prp_type=vgg16_prp)
plot_image(style_image_vgg)


# In[19]:


style_image_vgg = deprocess_img(style_image_vgg, inception=False)
plot_image(style_image_vgg)
'''

# ### Model layers for feature selection

# In[20]:





# ### Build VGG Model

# In[21]:


def get_model(model_name, inception=False):
    # load pretrained VGG, trained on imagenet data
    loaded_model = model_name(include_top=False, weights='imagenet')
    loaded_model.trainable = False
    # Get output layers corresponding to style and content layers 
    
    if inception:
      style_outputs = [loaded_model.get_layer(name).output for name in style_layers_inc]
      content_outputs = [loaded_model.get_layer(name).output for name in content_layers_inc]
    
    else:
      style_outputs = [loaded_model.get_layer(name).output for name in style_layers]
      content_outputs = [loaded_model.get_layer(name).output for name in content_layers]
      
    model_outputs = style_outputs + content_outputs

    return models.Model(loaded_model.input, model_outputs), loaded_model.name


# ### Define content loss

# In[22]:


def get_content_loss(base_content, target):
    return tf.reduce_mean(tf.square(base_content - target))


# ### Define style loss

# In[23]:


def gram_matrix(input_tensor):
    channels = int(input_tensor.shape[-1])
    a = tf.reshape(input_tensor, [-1, channels])
    n = tf.shape(a)[0]
    gram = tf.matmul(a, a, transpose_a=True)
    return gram / tf.cast(n, tf.float32)


# In[24]:


def get_style_loss(base_style, gram_target):
    height, width, channels = base_style.get_shape().as_list()
    gram_style = gram_matrix(base_style)
    return tf.reduce_mean(tf.square(gram_style - gram_target))# / (4. * (channels ** 2) * (width * height) ** 2)


# ### Compute vgg model representations on input images

# In[25]:


def get_feature_representations(model, img_w, img_h, content_path, style_path, prp_type):
    
    content_image = preprocess_img(content_path, img_w, img_h, prp_type)
    style_image = preprocess_img(style_path, img_w, img_h, prp_type)

    #TODO: err InvalidArgumentError: input depth must be evenly divisible by filter depth: 4 vs 3 [Op:Conv2D]
    # batch compute content and style features
    style_outputs = model(style_image)
    content_outputs = model(content_image)
    


    # Get the style and content feature representations from our model  
    style_features = [style_layer[0] for style_layer in style_outputs[:num_style_layers]]
    content_features = [content_layer[0] for content_layer in content_outputs[num_style_layers:]]
    
    return style_features, content_features


# ### Compute loss function

# In[26]:


def compute_loss(model, loss_weights, init_image, gram_style_features, content_features):
    
    style_weight, content_weight = loss_weights
    
    model_outputs = model(init_image)

    style_output_features = model_outputs[:num_style_layers]
    content_output_features = model_outputs[num_style_layers:]

    style_score = 0
    content_score = 0

    # Accumulate style losses from all layers
    weight_per_style_layer = 1.0 / float(num_style_layers)
    for target_style, comb_style in zip(gram_style_features, style_output_features):
        style_score += weight_per_style_layer * get_style_loss(comb_style[0], target_style)

    # Accumulate content losses from all layers 
    weight_per_content_layer = 1.0 / float(num_content_layers)
    for target_content, comb_content in zip(content_features, content_output_features):
        content_score += weight_per_content_layer * get_content_loss(comb_content[0], target_content)

    style_score *= style_weight
    content_score *= content_weight

    # Get total loss
    loss = style_score + content_score 
    return loss, style_score, content_score


# ### Compute gradients

# In[27]:


def compute_gradients(cfg):
    with tf.GradientTape() as tape: 
        all_loss = compute_loss(**cfg)
        
    total_loss = all_loss[0]
    return tape.gradient(total_loss, cfg['init_image']), all_loss


# ### Plot learning curve

# In[28]:


def plot_learning_curve(iterations, total_losses, style_losses, content_losses, img_file_name):
  
  plt.figure(figsize=(8, 8))
  
  plt.xlabel('Iterations')
  plt.ylabel('Losses')
  plt.title('Style Transfer: Loss function by iterations')
  
  plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.1e}'))
  plt.plot(iterations[1:], total_losses, label="Total loss")
  plt.plot(iterations[1:], style_losses, label="Style loss")
  plt.plot(iterations[1:], content_losses, label="Content loss")
  plt.legend()

  '''
  acc_norm = []
  acc_znorm = []
  for total_loss in total_losses:
    normalized_loss = 1 - (total_loss - (max(total_losses)/(0 - max(total_losses))))
    acc_norm.append(normalized_loss)
    print(normalized_loss)
    
  for total_loss in acc_norm:
    normalized_loss = (total_loss - min(acc_norm)) / (max(acc_norm) - min(acc_norm))
    acc_znorm.append(normalized_loss)
    print(normalized_loss)

  ax[1].set_xlabel('Iterations')
  ax[1].set_ylabel('Accuracy')
  ax[1].set_title('Style Transfer: Total Accuracy by iterations')
  ax[1].yaxis.set_major_formatter(StrMethodFormatter('{x:,.3f}'))
  ax[1].plot(iterations[1:], acc_znorm, label="Total accuracy")
  ax[1].legend()
  '''
  
  plt.savefig(img_file_name)
  print('Saved loss figure to drive.')
  #plt.tight_layout()
  #plt.show()


# In[29]:


def plot_time(iterations, times, img_file_name):
  plt.figure(figsize=(8,8))
  
  plt.title("Style Transfer computation time by iterations")
  plt.xlabel("Iterations")
  plt.ylabel("Time (s)")
  
  plt.plot(iterations[1:], times[1:], label="Time")
  
  plt.savefig(img_file_name)
  print('Saved time figure to drive.')
  #plt.tight_layout()
  #plt.show()


# ### Display results

# In[30]:


def show_results(best_img, content_path, style_path, show_large_final=True):
  
  plot_side_by_side(content_path, style_path)
  
  if show_large_final:
    plt.title('Output Image')
    plot_image(best_img)
    plt.show()


# ### Save image to disk

# In[42]:


def save_image(best_img, path):
  best_img = best_img.astype('uint8')
  img = Image.fromarray(best_img)
  img.save(path)
  print('Saved image to drive.')


# In[43]:


def save_config(total_losses, style_losses, content_losses, iterations, times, image_path):
  output_conf = {
          'total_losses': total_losses,
          'style_losses': style_losses,
          'content_losses': content_losses,
          'iterations': iterations,
          'times': times
  }

  output_conf['total_losses'] = total_losses
  output_conf['style_losses'] = style_losses
  output_conf['content_losses'] = content_losses
  output_conf['times'] = times
  output_conf['iterations'] = iterations

  with open(image_path + '_cfg.txt', 'w') as file:
    file.write(str(output_conf))
  print('Saved config to cloud drive.')


# ### Optimization method

# In[49]:

@celery.task(name='run_style_transfer')
def run_style_transfer(content_path, 
                       style_path,
                       result_path,
                       loss_path,
                       exec_path,
                       num_iterations=300,
                       img_w=256,
                       img_h=256,
                       model_name=VGG16,
                       content_weight=1e3, 
                       style_weight=1e-2,
                       lr=5,
                       beta1=0.99,
                       epsilon=1e-1,
                       cfg_path='output/'): 
  
    inception = False
    
    if model_name==InceptionV3:
      inception = True
      prp_type = inc_prp 
    elif model_name==VGG19:
      prp_type = vgg19_prp
    elif model_name==VGG16:
      prp_type = vgg16_prp
    else:
      raise TypeError("Unsupported model architecture.")
     
    model, name = get_model(model_name, inception=False) 
    # print(model)
    for layer in model.layers:
        layer.trainable = False

    # Get the style and content feature representations (from our specified intermediate layers) 
    style_features, content_features = get_feature_representations(model, img_w, img_h, content_path, style_path, prp_type)
    gram_style_features = [gram_matrix(style_feature) for style_feature in style_features]

    # Set initial image
    init_image = preprocess_img(content_path, img_w, img_h, prp_type)
    init_image = tfe.Variable(init_image, dtype=tf.float32)
    
    # Create the optimizer
    opt = tf.train.AdamOptimizer(learning_rate=lr, beta1=beta1, epsilon=epsilon)

    # Store our best result
    best_loss, best_img = float('inf'), None

    # Create a nice config 
    loss_weights = (style_weight, content_weight)
    cfg = {
      'model': model,
      'loss_weights': loss_weights,
      'init_image': init_image,
      'gram_style_features': gram_style_features,
      'content_features': content_features
    }

    # For displaying
    num_rows = 5
    num_cols = 5
    display_interval = num_iterations/(num_rows*num_cols)
    start_time = time.time()
    global_start = time.time()
    
    norm_means = np.array([103.939, 116.779, 123.68])
    min_vals = -norm_means
    max_vals = 255 - norm_means   
    
    start_time = time.time()
    iter_start_time = time.time()
    
    
    
    # Uncomment these lines to save the results to your Google Drive (you first need to have it mounted)
    #save_image(best_img, cfg_path + image_title)
    #save_config(total_losses_np, style_losses_np, content_losses_np, iterations, times_np, cfg_path + image_title)
    
    '''
    plt.figure(figsize=(14,4))
    for i,img in enumerate(imgs):
        plt.subplot(num_rows,num_cols,i+1)
        output = img.copy()
        if len(img.shape) == 4:
          # Remove the batch dimension
          output = np.squeeze(img, axis=0)
        # Normalize for display 
        output = output.astype('uint8')
        plt.gca().get_yaxis().set_visible(False)
        plt.gca().get_xaxis().set_visible(False)
        plt.imshow(output)
    plt.show()
	'''

    for i in range(num_iterations):
        

        grads, all_loss = compute_gradients(cfg)
        loss, style_score, content_score = all_loss
        opt.apply_gradients([(grads, init_image)])
        clipped = tf.clip_by_value(init_image, min_vals, max_vals)
        init_image.assign(clipped)


        if loss < best_loss:
            best_loss = loss
            best_img = deprocess_img(init_image.numpy(), inception=False)

        times.append(time.time() - start_time)
        times_np.append('{:.4f}'.format(time.time() - start_time))
        iterations_times.append(i)

        if i % display_interval == 0:

            #plot_img = init_image.numpy()
            #plot_img = deprocess_img(plot_img, inception=inception)
            
            #lists for plotting
            #imgs.append(plot_img)
            
            iterations.append(i)
            times_iter.append(time.time() - iter_start_time)
            times_np_iter.append('{:.4f}'.format(time.time() - iter_start_time))

            #skip initialization step
            if i != 0:
              total_losses.append(loss)
              style_losses.append(style_score)
              content_losses.append(content_score)
              total_losses_np.append('{:.4e}'.format(loss.numpy()))
              style_losses_np.append('{:.4e}'.format(style_score.numpy()))
              content_losses_np.append('{:.4e}'.format(content_score.numpy()))
           
            
            #plot_image(plot_img)
            #plt.show()
            
            print('Iteration: {}'.format(i))        
            print('Total loss: {:.4e}, ' 
                'Style loss: {:.4e}, '
                'Content loss: {:.4e}, '
                'Time: {:.4f}s'.format(loss, style_score, content_score, time.time() - iter_start_time))

            iter_start_time = time.time()

        start_time = time.time()

    total_time = '{:.4f}s'.format(time.time() - global_start)
    print('Total time: {:.4f}s'.format(time.time() - global_start))
    
    save_image(best_img, result_path)

    plot_learning_curve(iterations, total_losses, style_losses, content_losses, loss_path)
    plot_time(iterations, times, exec_path)

    result_dict = {
        'total_losses': json.dumps(total_losses_np),
        'content_losses': json.dumps(content_losses_np),
        'style_losses': json.dumps(style_losses_np),
        'iterations': iterations,
        'times': times,
        'total_time': total_time,
        'model_name': name,
        'gen_image_width': best_img.shape[0],
        'gen_image_height': best_img.shape[1],
    }
    
    return result_dict

# In[51]:

'''
# Set the export location in your Google Drive
image_path = 'output/'
image_title = 'neil_picasso_vgg19_def_100'


# In[52]:


best_img, total_loss, style_losses, content_losses, iterations, times = run_style_transfer(content_image_path, 
                                     style_image_path, image_title=image_title,
                                     content_weight=1e3, style_weight=1e-2, lr=5,
                                     model_name=VGG19, num_iterations=100, cfg_path=image_path)


# In[53]:


plot_side_by_side(content_image_path, style_image_path, result_image=best_img, results=True)


# In[54]:


plot_image(best_img, 'Output image')


# In[55]:


plot_learning_curve(iterations, total_loss, style_losses, content_losses, image_path + image_title)


# In[56]:


plot_time(iterations, times, image_path + image_title)

'''