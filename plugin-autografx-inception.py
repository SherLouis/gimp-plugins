#!/usr/bin/env python

from gimpfu import *

"""
  # TODO: algorithm: 
  # TODO: Get the selection
  # TODO: Figure out the "aspect ratio" of the selection vs the image
  # TODO: crop the image to fit the same aspect ratio of the selection
  # TODO: Create a copy of the image (all visible layers)
  # TODO: resize / transform this copy to fit the selection (4 corners)
  # TODO: Merge the resized image to the current image.
  # TODO: Repeat as long as the result is different than the last image
"""


class Point:
  def __init__(self, x, y):
    self.x = x
    self.y = y

class Rectangle:
  def __init__(self, p1, p2):
    self.p1 = p1
    self.p2 = p2

  def get_width(self):
    return self.p2.x - self.p1.x

  def get_height(self):
    return self.p2.y - self.p1.y


def _get_selection_box(img, saved_selection):
  current_selection = pdb.gimp_selection_save(img)
  pdb.gimp_image_select_item(img, 2, saved_selection)
  (_, x1, y1, x2, y2) = pdb.gimp_selection_bounds(img)
  _restore_selection(img, current_selection)
  return Rectangle(Point(x1,y1), Point(x2,y2))

def _copy_visible_to_new_layer(img, new_layer_name):
  current_selection = pdb.gimp_selection_save(img)
  pdb.gimp_selection_all(img)
  pdb.gimp_edit_copy_visible(img)
  fsel = pdb.gimp_edit_paste(_get_active_or_top_layer(img), False)
  pdb.gimp_floating_sel_to_layer(fsel)
  img.active_layer.name = new_layer_name
  _restore_selection(img, current_selection)

def _restore_selection(img, saved_selection):
  pdb.gimp_image_select_item(img, 2, saved_selection)
  pdb.gimp_image_remove_channel(img, saved_selection)
  top_visible_layer = _get_top_visible_layer(img)
  pdb.gimp_image_set_active_layer(img, top_visible_layer)

def _crop_lyr_to_size_center(lyr, new_w, new_h):
  offx = -(lyr.width - new_w) / 2
  offy = -(lyr.height - new_h) / 2
  pdb.gimp_layer_resize(lyr, new_w, new_h, offx, offy)

def _get_scale_factor(w0, h0, w1, h1):
  w_factor = float(w1)/float(w0)
  h_factor = float(h1)/float(h0)
  return max(w_factor, h_factor)

def _get_top_visible_layer(img):
  return [lyr for lyr in img.layers if lyr.visible][0]

def _get_active_or_top_layer(img):
  if img.active_layer:
    return img.active_layer
  return _get_top_visible_layer(img)

def autografx_inception(img, drawable, iters):
  pdb.gimp_image_undo_group_start(img)

  if not img.active_layer:
    pdb.gimp_image_set_active_layer(img, _get_top_visible_layer(img))
  
  selection = pdb.gimp_selection_save(img) # save selection
  image_width = img.width
  image_height = img.height
  sel_rect = _get_selection_box(img, selection)
  sel_w = sel_rect.get_width()
  sel_h = sel_rect.get_height()
  
  for iter in range(iters):
    # Make a copy of the visible image to a new layer (copy)
    _copy_visible_to_new_layer(img, "copy")

    # Scale the layer to selection size
    scale_factor = _get_scale_factor(image_width, image_height, sel_w, sel_h)
    new_w = int(image_width * scale_factor)
    new_h = int(image_height * scale_factor)
    pdb.gimp_layer_scale(img.active_layer, new_w, new_h, True)

    # Crop the layer to fit selection dimensions
    _crop_lyr_to_size_center(img.active_layer, sel_w, sel_h)

    # Move the layer to selection
    pdb.gimp_layer_set_offsets(img.active_layer, sel_rect.p1.x, sel_rect.p1.y)

    # Merge the layer
    lyr = pdb.gimp_image_merge_down(img, img.active_layer, 1)
    pdb.gimp_image_set_active_layer(img, lyr)

  pdb.gimp_image_undo_group_end(img)

  return

register(
  "Autografx_Inception",
  "Include 'screenshot' of image in a selection",
  "Ex. a picture of a painter painting the same picture. The selection must be of only 4 points",
  "Louis Harris",
  "Louis Harris",
  "2022",
  "<Image>/Autografx/Inception...",
  "RGB*, GRAY*",
  [
      (PF_INT, "iters", "Number of iterations", 1)
  ],
  [],
  autografx_inception
)

main()