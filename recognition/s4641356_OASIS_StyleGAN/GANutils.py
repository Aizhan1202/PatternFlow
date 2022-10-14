from cProfile import label
from PIL import Image
from matplotlib import pyplot as plt
import matplotlib
import numpy as np
import tensorflow as tf
import os
import shutil
import csv

from modules import StyleGAN


def denormalise(data: np.array) -> np.array:
    """
    Take output of GAN and undo data preprocessing procedure to return
    a matrix of integer greyscale image pixel intensities suitable to
    convert directly into an image.

    Args:
        data (np.array): normalised data

    Returns:
        np.array: denormalized data
    """
    # data = np.array(data) #cast to numpy array from any array like (Allows Tensor Compatibility)
    # decentered = data + mean
    # return (decentered * 255).astype(np.uint8)
    return (data*255).astype(np.uint8)


def create_image(data: np.array, filename: str = None) -> Image:
    """
    Creates an new PNG image from a generated data matrix.
    Saves image to output folder if a name is specified

    Args:
        data (np.array): uint8 single channel matrix of greyscale image pixel intensities
        name (str or NoneType, optional): filename and path to save image, If None image is not saved. Defaults to None.
        output_folder (str, optional): path of output folder. Defaults to "output/".

    Returns:
        Image: Generated image
    """
    TARGET_RES = 256
    PADDING = 35 #I would share these constants with OASIS_Loader but I'm erring on the side of caution and keeping everything wrapped inside at least one class/function
    
    im = Image.fromarray(data[:,:,0],'L').resize((TARGET_RES-PADDING,TARGET_RES-PADDING))
    back = Image.new('L', (TARGET_RES,TARGET_RES), im.getdata()[0]) #sample colour of top left (which should be background) so padding has matching colour 
    back.paste(im,(PADDING//2,PADDING//2))#Passed data will have extreneous channel dimension, we "decompress" back to original image size by upsampling then adding back the black image padding.
    im = back.convert("RGBA")
    if filename is not None:
        im.save(filename+".png")
    return im

def random_generator_inputs(num_images: int,latent_dim: int,noise_start: int,noise_end: int) -> list[np.array]:
    """_summary_ TODO

    Args:
        num_images (int): _description_
        latent_dim (int): _description_
        noise_start (int): _description_
        noise_end (int): _description_

    Returns:
        list[np.array]: _description_
    """

    latent_vectors = tf.random.normal(shape = (num_images,latent_dim))
    input_tensors = [latent_vectors]
    curr_res = noise_start
    while curr_res <= noise_end:
        input_tensors.append(tf.random.normal(shape = (num_images,curr_res,curr_res,latent_dim)))
        input_tensors.append(tf.random.normal(shape = (num_images,curr_res,curr_res,latent_dim)))
        curr_res = curr_res*2
    return input_tensors

def make_fresh_folder(folder_path: str) -> None:
    """
    Generates a folder at the specified location, wiping any existing contents
    If the specified folder already existed. Parents are created if neccessary,
    but are not cleared if they exist already.

    Args:
        folder_path (str): path to specified folder. If no folder exists at the location a new one is created. If a folder exists at the location it is wiped.
    """
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def save_training_history(history: dict[list[float]], filename: str) -> None: #TODO docsttinfs
     with open(filename + ".csv", mode = 'a', newline='') as f:
        csv.writer(f).writerows(zip(*history.values())) #we pass in the arbitrary length set of *args (various history compoents)

def load_training_history(csv_location: str) -> dict[list[float]]:
    #TODO doctring
    history = {metric: [] for metric in StyleGAN.METRICS}
    with open(csv_location, mode= 'r', newline= '') as f:
        reader = csv.DictReader(f, fieldnames= StyleGAN.METRICS)
        for row in reader:
            for metric in StyleGAN.METRICS:
                history[metric].append(row[metric])
    return history 



def plot_training(history: dict[list[float]], output_file: str, epochs_covered: int, epoch_range: tuple[int,int] = None) -> None:
    #TODO docstring
    
    history_length = len(history[StyleGAN.METRICS[0]])
    batch_size = history_length//epochs_covered
    
    #truncate to specified range if required
    if epoch_range is not None:
        start,end = epoch_range
        history = {metric: history[metric][start*batch_size:end*batch_size] for metric in history} #troublesome conversions as we store per batch not just epoch
    
    
    #plot losses
    plt.figure(figsize=(14, 10), dpi=80)
    for metric in StyleGAN.METRICS:
        plt.plot(history[metric])
    plt.title("StyleGAN Training Losses")
    plt.xlabel("Epoch")
    plt.xticks(np.linspace(0,history_length,10), labels = list(map(int,np.linspace(0, epochs_covered, 10)))) #Manually scale x-axis to epochs instead of batches
    plt.ylabel("Loss")
    plt.yticks(np.round(np.linspace(*plt.ylim(), 15), 4)) #restrict y tick count without explicitly reading data's max
    plt.gca().yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.4f')) #round ytick values to not be disgusting
    plt.legend(StyleGAN.METRICS)
    plt.savefig(output_file)
    
    #Show plot. Due to the immense size of the plotted vectors using imshow directly bricks my machine for a hot minute, so we take the cheeky alternate approach
    Image.open(output_file).show()
    
