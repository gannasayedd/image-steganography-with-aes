from matplotlib.image import imread 
import matplotlib.pyplot as plt
# %matplotlib inline
import matplotlib.image as mpimg
from PIL import Image
import numpy as np
import cv2
import types
import os
os.chdir(r"C:\Users\gogos\OneDrive\سطح المكتب\python")


def message_to_binary(message):
    if type(message) == str:
        return ''.join([format(ord(i), '08b') for i in message])
    elif type(message) == bytes or type(message) == np.ndarray:
        return [format(i, '08b') for i in message]
    elif type(message) == int or type(message) == np.uint8:
        return format(message, '08b')
    else:
        raise TypeError("Input type not supported")
# ________________________________________________________________________________________________________________________________

def hide_message(image , secret_message):  
    # Calculate the maximum bytes to encode
    n_bytes = image.shape[0] * image.shape[1] * 3 // 8
    print("Maximum bytes to encode:", n_bytes)
    if len(secret_message) > n_bytes:
        raise ValueError("Error: Insufficient bytes, need bigger image or less data.")
    
    secret_message += "====="  # Delimiter to indicate end of message
    binary_secret_msg = message_to_binary(secret_message)

    data_index = 0

    for values in image:
        for pixel in values:
            r, g, b = message_to_binary(pixel)

            # Modify Red channel LSB
            if data_index < len(binary_secret_msg):
                pixel[0] = int(r[:-1] + binary_secret_msg[data_index], 2)
                data_index += 1

            # Modify Green channel LSB
            if data_index < len(binary_secret_msg):
                pixel[1] = int(g[:-1] + binary_secret_msg[data_index], 2)
                data_index += 1
            
            # Modify Blue channel LSB
            if data_index < len(binary_secret_msg):
                pixel[2] = int(b[:-1] + binary_secret_msg[data_index], 2)
                data_index += 1
            
            if data_index >= len(binary_secret_msg):
                break

    return image

# ________________________________________________________________________________________________________________________________
def binary_to_message(binary_data):
    all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
    decoded_message = ""
    for byte in all_bytes:
        decoded_message += chr(int(byte, 2))
        if decoded_message[-5:] == "=====":  # Check for the delimiter
            break
    return decoded_message[:-5]  # Remove the delimiter from the final message

# ________________________________________________________________________________________________________________________________
def decode_message(image):
    binary_data = ""
    for values in image:
        for pixel in values:
            r, g, b = message_to_binary(pixel)
            binary_data += r[-1]  # Extract LSB of Red channel
            binary_data += g[-1]  # Extract LSB of Green channel
            binary_data += b[-1]  # Extract LSB of Blue channel

    decoded_message = binary_to_message(binary_data)
    return decoded_message

# ________________________________________________________________________________________________________________________________

# def encode_text_in_image(image_path, secret_message, output_path):
#     image = cv2.imread(image_path)
#     modified_image = hide_message(image, secret_message)
#     cv2.imwrite(output_path, modified_image)


def encode_data():
    image_path = input("Enter the path of the image: ")
    image = cv2.imread(image_path)

    #deatils of the image
    print("Image shape:", image.shape)
    print("ORIGINAL IMAGE:")
    resized_image = cv2.resize(image, (400, 400))
    cv2.imshow("Original Image", resized_image)

    data = input("Enter the secret message to hide: ")
    if (len(data) == 0):
        raise ValueError("Error: Secret message cannot be empty.")
        
    
    filename = input("Enter the output filename (with extension, e.g., output.png): ")
    encode_image = hide_message(image, data)
    cv2.imwrite(filename, encode_image)
# ________________________________________________________________________________________________________________________________
def decode_data():
    image_path = input("Enter the path of the image to decode: ")
    image = cv2.imread(image_path)
    decoded_message = decode_message(image)
    print("Decoded message:", decoded_message)        

# ________________________________________________________________________________________________________________________________  

# Image Steganography

def Steganography():
    a = input("Image Steganography \n 1. Encode the data \n 2. Decode the data \n Your input is: ")
    userinput = int(a)
    if (userinput == 1):
        print("\nEncoding....")
        encode_data()
    elif (userinput == 2):  
        print("\nDecoding....")
        print("Decoded message is:", decode_data())
    else:
        raise Exception("Enter correct input")
Steganography() #encode image
