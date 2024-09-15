import pygame as pg
import os

base_path = "images/"

def load_image(path, scale_times=None, scale=None):
    image = pg.image.load(base_path + path).convert()

    if scale:
        image = pg.transform.scale(image, scale)
    elif scale_times:
        image = pg.transform.scale(image, (image.get_width() * scale_times, image.get_height() * scale_times))
    image.set_colorkey((0, 0, 0))
    return image

def load_images(path, scale_times=None, scale=None):
    images = []

    for img_path in os.listdir(base_path + path):
        images.append(load_image(path + "/" + img_path, scale_times, scale))

    return images

class Animation:
    def __init__(self, images, img_cooldown=200, loop=True):
        self.images = images
        self.img_cooldown = img_cooldown
        self.loop = loop
        self.frame_index = 0
        self.cur_time = 0

    def update(self):
        time = pg.time.get_ticks()
        if self.loop:
            if time - self.cur_time >= self.img_cooldown:
                self.cur_time = time
                if self.frame_index < len(self.images) - 1:
                    self.frame_index += 1
                else:
                    self.frame_index = 0
        else:
            if time - self.cur_time >= self.img_cooldown:
                self.cur_time = time
                if self.frame_index < len(self.images) - 1:
                    self.frame_index += 1

    def render_image(self):
        return self.images[self.frame_index]
