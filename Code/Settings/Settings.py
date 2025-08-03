import pygame
import random
from pytmx.util_pygame import load_pygame
from os.path import join, dirname
from os import walk
from pathlib import Path

WINDOW_WIDTH, WINDOW_HEIGHT =  320, 240 
INT_WIDTH  =  320
INT_HEIGHT =  240 
TILE_SIZE = 16

MAPS_DIR = join('Maps')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SPRITES_DIR = BASE_DIR / 'Sprites'

