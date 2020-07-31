#!/usr/bin/env python
# coding: utf-8

# In[1]:


svg_maker_version = "4.1"

import pymongo
import pandas as pd
import math
import numpy as np
import re
import requests
import statistics
import os
import time
from datetime import datetime
import json

def t0():
    global t_start
    t_start = datetime.utcnow()
    
def t1():
    print("done in %1.3f s"%(datetime.utcnow()-t_start).total_seconds())
    
t_start_all = datetime.utcnow()


# In[ ]:





# In[2]:


#
# SETTINGS in this cell
#
#

# check to filter pmts. pmt must be smaller than this value
float_pmt_less_than = 800

# string that contains the mongo uri
uri_mongo = os.environ["DAQ_URI"]

#path where the svgs should be sved
path_out  = "../"

# slows down the system
float_sleeptime     = 0.00#4 # 


# color scheme for datarates
# (key is rate in percent, value is list of 3 rgb values)
#

dict_colors_from_website = {
    "light_blue":  (  23, 162, 184),
    "dark_blue":   (  12,  17, 120),
    "green":       (   6, 214, 160),
    "yellow":      ( 211, 158,   0),
    "red":         ( 189,  33,  48),

    
    
    # own colors
    "white_blue":  (  120, 120, 211),
}


   

dict_color_scheme_all = [
    {
        10: dict_colors_from_website["green"],
        30: dict_colors_from_website["light_blue"],
        50: dict_colors_from_website["dark_blue"],
        90: dict_colors_from_website["yellow"],
        #90: dict_colors_from_website["red"],
    },
    {
        10: dict_colors_from_website["green"],
        40: dict_colors_from_website["light_blue"],
        70: dict_colors_from_website["dark_blue"],
        80: dict_colors_from_website["yellow"],
        90: dict_colors_from_website["red"],
    },
    {
        10: dict_colors_from_website["light_blue"],
        90: dict_colors_from_website["dark_blue"],
    },
    {
        10: dict_colors_from_website["green"],
        50: dict_colors_from_website["light_blue"],
        90: dict_colors_from_website["dark_blue"],
    },
    {
        10: dict_colors_from_website["dark_blue"],
        50: dict_colors_from_website["light_blue"],
        90: dict_colors_from_website["green"],
    },
    {
        10: dict_colors_from_website["dark_blue"],
        50: dict_colors_from_website["light_blue"],
        90: dict_colors_from_website["green"],
        95: dict_colors_from_website["yellow"],
        99: dict_colors_from_website["red"],
    },
    
]

dict_color_scheme = dict_color_scheme_all[5]


# In[ ]:





# In[ ]:





# In[ ]:





# In[3]:


print("Connection to database")
t0()


myclient = pymongo.MongoClient(uri_mongo)
db = myclient["daq"]

t1()


# In[4]:



dict_filter_cable = {"pmt":{'$lt': float_pmt_less_than}}
dict_filter_board = {}

print("load cable map with filter:\n  \33[33m" + str(dict_filter_cable) + "\33[0m")
t0()
list_cable_map_raw = list(db["cable_map"].find(dict_filter_cable))
t1()

print("load board map with filter:\n  \33[33m" +str(dict_filter_board) + "\33[0m")
t0()
list_board_map_raw = list(db["board_map"].find(dict_filter_board))
t1()


# In[5]:


print("adding keys to channel and board map")
t0()
# add keys to lists to find channel and board faster
dict_cable_map = {channel_info["pmt"]:channel_info for channel_info in list_cable_map_raw}
dict_board_map = {board_info["board"]:board_info for board_info in list_board_map_raw}
t1()

print("create lists with pmts and boards")
t0()
list_pmts      = sorted(list(dict_cable_map.keys()))
list_boards    = sorted(list(dict_board_map.keys()))
t1()


print("removing pmt entry from coords")
t0()
for pmt_id in dict_cable_map:
    print(f"{pmt_id:6.0f}", end = "")
    if "coords" in dict_cable_map[pmt_id]:
        if "pmt" in dict_cable_map[pmt_id]["coords"]:
            dict_cable_map[pmt_id]["coords"] = dict_cable_map[pmt_id]["coords"]["pmt"]
            print(" \33[32mfixed\33[0m")
    else:
        print(" \33[33mno coords\33[0m")
t1()


# In[6]:


print("defining functions")
t0()

def str_get_rdrlnk_from_int_board_info(dict_board_info):
    try:
        return(dict_board_info["host"][6:] + "." + str(dict_board_info["link"]))
    except:
        return("X.X")


def add_pmtID_to_dict_crates(str_type, crate, slot, channel, content):
    global dicts_crates
    global dicts_int_max_crates_content
    
    
    # add missing structure
    if not str_type in dicts_crates:
        dicts_crates[str_type] = {}
    if not crate in dicts_crates[str_type]:
        dicts_crates[str_type][crate]= {}
    if not slot in dicts_crates[str_type][crate]:
        dicts_crates[str_type][crate][slot]= {}
    
    if not str_type in dicts_int_max_crates_content["max_channels"]:
        dicts_int_max_crates_content["max_channels"][str_type] = 0
        dicts_int_max_crates_content["max_slots"][str_type] = 0
        dicts_int_max_crates_content["max_crates"][str_type] = 0
    
    
    dicts_crates[str_type][crate][slot][channel] = content
    
    dicts_int_max_crates_content["max_crates"][str_type]   = max(dicts_int_max_crates_content["max_crates"][str_type],   len(dicts_crates[str_type]))
    dicts_int_max_crates_content["max_slots"][str_type]    = max(dicts_int_max_crates_content["max_slots"][str_type],    slot)
    dicts_int_max_crates_content["max_channels"][str_type] = max(dicts_int_max_crates_content["max_channels"][str_type], channel)
    
    return()


def print_recursive_length(dict, maxlevel = float("inf"), level = 0):
    level_up = level + 1
    for key in dict:
        try:
            print("  "* level + str(key) + ": \33[33m" + str(len(dict[key])) + "\33[0m")
            if level_up <= maxlevel:
                print_recursive_length(dict[key], maxlevel, level_up)
        except:
            int_tmp=1

def get_full_pos_from_int_pmtID(str_type, int_pmtID):
    if not str_type in list(dicts_crates.keys()):
        print("\33[31mERROR: str_type wrong\33[0m")
        return()
    try:
        return([dict_cable_map[int_pmtID][str_type + "_" + str_level] for str_level in ["crate", "slot", "channel"]])
    except:
        return()



    
t1()


# In[ ]:





# In[ ]:





# In[ ]:





# In[7]:


# grouping for pmt (then pmt_id (channels) is alwas same):
#  1st level: type of sorting
#  2nd level: crate or reader_link (will be as big block)
#  3rd level: slot or opt_bd (will be horizontal position in crate)
#  4th level: channel (will be vertical position in slot)


print("check all pmts for info")
t0()

# initialize dictionaries
dicts_crates = {}
dicts_int_max_crates_content = {
    "max_channels": {},
    "max_slots":    {},
    "max_crates":   {},
}
dict_crates_base_pos = {}


set_str_array_names = set()
int_n_char_max_pmt  = len(str(max(list_pmts)))
int_n_char_len_pmts = len(str(len(list_pmts)))
dict_array_pmts = {}

dict_array_float_x = {}
dict_array_float_y = {}
    


int_pmt = 0
# get all vme crates, readers, adcs, and positions
for int_pmt_id in list_pmts:
    int_pmt += 1
    print(
        "\r  pmt_" + str(int_pmt_id).rjust(int_n_char_max_pmt, "0") +
        " (" + str(int_pmt).rjust(int_n_char_len_pmts) + "/" + str(len(list_pmts)) + ")",
        end = ""
    )
    
    # get infos from cable_map
    dict_pmt_info = dict_cable_map[int_pmt_id]
    
    
    if int_pmt_id in [0, 500, 656]:
        #print(f"""\n\t\33[32mcoords: {dict_pmt_info}\33[0m""")
        print(f"""\n\t\33[32m{dict_cable_map[int_pmt_id]}\33[0m""")
        
        
    
    
    
    str_array_name = dict_pmt_info["array"]
    # add HE to pmts with id >= 500
    if int_pmt_id >= 500:
        str_array_name += "-High Energy"
        dict_cable_map[int_pmt_id]["array"] = str_array_name
    
    
    
    # get board infos from board map
    int_adc_sn = dict_pmt_info["adc"]
    dict_board_info = dict_board_map[int_adc_sn]
    
    # get path for type.crate.slot.channel
    str_opt_crate = str_get_rdrlnk_from_int_board_info(dict_board_info)
    int_opt_slot  = dict_board_info["opt_bd"]
    int_opt_ch    = dict_pmt_info["adc_channel"]
    
    add_pmtID_to_dict_crates("opt", str_opt_crate, int_opt_slot, int_opt_ch, int_pmt_id)
    
    int_vme_crate = dict_board_info["crate"]
    int_vme_slot  = dict_board_info["slot"]
    int_vme_ch    = dict_pmt_info["adc_channel"]
    add_pmtID_to_dict_crates("vme", int_vme_crate, int_vme_slot, int_vme_ch, int_pmt_id)
    
    int_amp_crate = dict_pmt_info["amp_crate"]
    int_amp_slot  = dict_pmt_info["amp_slot"]
    int_amp_ch    = dict_pmt_info["amp_channel"]
    
    add_pmtID_to_dict_crates("amp", int_amp_crate, int_amp_slot, int_amp_ch, int_pmt_id)
    
    # add array infos
    set_str_array_names.add(str_array_name)
    if not dict_pmt_info["array"] in dict_array_pmts:
        dict_array_pmts[str_array_name] = []
        dict_array_float_x[str_array_name] = []
        dict_array_float_y[str_array_name] = []
        
    dict_array_pmts[str_array_name].append(int_pmt_id)
    
    
    if "coords" in dict_pmt_info:
        # if "pmt" in dict_pmt_info["coords"]:
            # dict_array_float_x[str_array_name].append(dict_pmt_info["coords"]["pmt"][0])
            # dict_array_float_y[str_array_name].append(dict_pmt_info["coords"]["pmt"][1])
        # else:
            dict_array_float_x[str_array_name].append(dict_pmt_info["coords"][0])
            dict_array_float_y[str_array_name].append(dict_pmt_info["coords"][1])
            
    elif int_pmt_id >= 500:
        # if "pmt" in dict_cable_map[int_pmt_id-500]["coords"]:
            # dict_array_float_x[str_array_name].append(dict_cable_map[int_pmt_id-500]["coords"]["pmt"][0])
            # dict_array_float_y[str_array_name].append(dict_cable_map[int_pmt_id-500]["coords"]["pmt"][1])
            # dict_cable_map[int_pmt_id]["coords"] = dict_cable_map[int_pmt_id-500]["coords"]["pmt"]
        # else:
            dict_array_float_x[str_array_name].append(dict_cable_map[int_pmt_id-500]["coords"][0])
            dict_array_float_y[str_array_name].append(dict_cable_map[int_pmt_id-500]["coords"][1])
            dict_cable_map[int_pmt_id]["coords"] = dict_cable_map[int_pmt_id-500]["coords"]
            
    # add info to dict_cable_map
    
    dict_cable_map[int_pmt_id]["opt_crate"]   = str_opt_crate
    dict_cable_map[int_pmt_id]["opt_slot"]    = int_opt_slot
    dict_cable_map[int_pmt_id]["opt_channel"] = int_opt_ch
    
    dict_cable_map[int_pmt_id]["vme_crate"]   = int_vme_crate
    dict_cable_map[int_pmt_id]["vme_slot"]    = int_vme_slot
    dict_cable_map[int_pmt_id]["vme_channel"] = int_vme_ch
    
    
    if float_sleeptime > 0:
        time.sleep(float_sleeptime)

dict_pmt_to_rdr_lnk = {pmt_id:dict_cable_map[pmt_id]["opt_crate"] for pmt_id in dict_cable_map}

print()
t1()


# In[8]:


print("order arrays by smallest number")
t0()

int_min_pmt_id = [min(dict_array_pmts[str_array_name]) for str_array_name in set_str_array_names]
int_sorted_array_id = np.argsort(int_min_pmt_id)
str_array_names = [list(set_str_array_names)[index] for index in int_sorted_array_id]

print(str_array_names)
t1()


# In[ ]:





# In[ ]:





# In[9]:


# define geometry of viewport here
print("calclating size of svg fields")
t0()

svg_viewport_header_height = 20
svg_viewport_legend_width  = 75
svg_viewport_footer_height = 40
svg_viewport_history_total_height = 250
svg_viewport_history_total_width  = 500

svg_margin = 15

svg_viewport_draw_field_width = 400
svg_viewport_draw_field_height = 250

svg_viewport_legend_start_height = 75
svg_layout_legend_height     = svg_viewport_header_height + svg_viewport_draw_field_height


# bar with gradient
svg_layout_legend_bar_width  = svg_margin * .5
svg_layout_legend_bar_x      = svg_viewport_draw_field_width + svg_margin / 2 + svg_layout_legend_bar_width
svg_layout_legend_bar_y      = svg_margin + svg_viewport_legend_start_height
svg_layout_legend_bar_height = 100 # svg_layout_legend_height - 4.5 * svg_margin



# legend text
svg_layout_legend_unit_x     = svg_viewport_draw_field_width + svg_margin
svg_layout_legend_unit_y     = svg_viewport_legend_start_height + svg_margin / 2

svg_layout_legend_text_x     = svg_viewport_draw_field_width + svg_margin * 2
svg_layout_legend_text_100_y = svg_layout_legend_bar_y + svg_layout_legend_bar_height/4*0
svg_layout_legend_text_075_y = svg_layout_legend_bar_y + svg_layout_legend_bar_height/4*1
svg_layout_legend_text_050_y = svg_layout_legend_bar_y + svg_layout_legend_bar_height/4*2
svg_layout_legend_text_025_y = svg_layout_legend_bar_y + svg_layout_legend_bar_height/4*3
svg_layout_legend_text_000_y = svg_layout_legend_bar_y + svg_layout_legend_bar_height/4*4

svg_layout_legend_text_x_tot = svg_layout_legend_bar_x
svg_layout_legend_text_y_min = svg_layout_legend_height - 2*svg_margin/3*3
svg_layout_legend_text_y_max = svg_layout_legend_height - 2*svg_margin/3*2
svg_layout_legend_text_y_tot = svg_layout_legend_height - 2*svg_margin/3*1



svg_layout_total_width  = svg_viewport_draw_field_width + svg_viewport_legend_width
svg_layout_total_height = svg_viewport_header_height + svg_viewport_footer_height + svg_viewport_draw_field_height


svg_coord_pmt_text_x    = 5
svg_coord_pmt_text_y1   = svg_layout_legend_height + svg_viewport_footer_height/3
svg_coord_pmt_text_y2   = svg_layout_legend_height + svg_viewport_footer_height/3*2

svg_coord_pmt_meta_x    = 75
svg_coord_pmt_meta_y1   = svg_layout_legend_height + svg_viewport_footer_height/5
svg_coord_pmt_meta_y2   = svg_layout_legend_height + svg_viewport_footer_height/5*2
svg_coord_pmt_meta_y3   = svg_layout_legend_height + svg_viewport_footer_height/5*3
svg_coord_pmt_meta_y4   = svg_layout_legend_height + svg_viewport_footer_height/5*4


# legend
svg_hist_width_y_axis   = 3
svg_hist_width_pmt_list = 3



# history 

svg_coord_axis_x_left   = svg_hist_width_y_axis*svg_margin
svg_coord_axis_x_right  = svg_layout_total_width - svg_hist_width_pmt_list * svg_margin
svg_coord_axis_y_bottom = svg_viewport_history_total_height - 2*svg_margin
svg_coord_axis_y_top    = 2*svg_margin

svg_coord_label_y_xaxis = svg_viewport_history_total_height - svg_margin*1.8
svg_coord_label_x_yaxis = svg_margin*(svg_hist_width_y_axis-.2)

svg_history_draw_width  = svg_layout_total_width - svg_coord_axis_x_left - svg_hist_width_pmt_list * svg_margin
svg_history_draw_height = svg_viewport_history_total_height - svg_coord_axis_y_top - 2 * svg_margin


svg_coord_label_000_xaxis = svg_coord_axis_x_left + 0/4 * svg_history_draw_width
svg_coord_label_025_xaxis = svg_coord_axis_x_left + 1/4 * svg_history_draw_width
svg_coord_label_050_xaxis = svg_coord_axis_x_left + 2/4 * svg_history_draw_width
svg_coord_label_075_xaxis = svg_coord_axis_x_left + 3/4 * svg_history_draw_width
svg_coord_label_100_xaxis = svg_coord_axis_x_left + 4/4 * svg_history_draw_width
svg_coord_label_000_yaxis = svg_coord_axis_y_bottom - 0/4 * svg_history_draw_height
svg_coord_label_025_yaxis = svg_coord_axis_y_bottom - 1/4 * svg_history_draw_height
svg_coord_label_050_yaxis = svg_coord_axis_y_bottom - 2/4 * svg_history_draw_height
svg_coord_label_075_yaxis = svg_coord_axis_y_bottom - 3/4 * svg_history_draw_height
svg_coord_label_100_yaxis = svg_coord_axis_y_bottom - 4/4 * svg_history_draw_height
svg_coord_label_xaxis     = svg_viewport_history_total_height-svg_margin
svg_coord_rate_label_y    = svg_margin/3*2


svg_coord_pmt_label_x     = svg_layout_total_width - svg_margin/2 
svg_coord_pmt_label_y     = 2*svg_margin
svg_coord_time_label_x    = svg_margin/2
svg_coord_time_label_y    = svg_margin/3




# calculate all coordinates of fields
# header
svg_replace = {
# meta data
"svg_maker_version"           : svg_maker_version,

# global size
"svg_layout_total_width"      : svg_layout_total_width,
"svg_layout_total_height"     : svg_layout_total_height,
    
# header
"svg_coord_header_x"          : 0,
"svg_coord_header_y"          : 0,
"svg_coord_header_width"      : svg_viewport_draw_field_width,
"svg_coord_header_height"     : svg_viewport_header_height,

# draw area
"svg_coord_draw_x"            : 0,
"svg_coord_draw_y"            : svg_viewport_header_height,
"svg_coord_draw_width"        : svg_viewport_draw_field_width,
"svg_coord_draw_height"       : svg_viewport_draw_field_height,

# footer
"svg_coord_footer_x"          : 0,
"svg_coord_footer_y"          : svg_layout_legend_height,
"svg_coord_footer_width"      : svg_layout_total_width,
"svg_coord_footer_height"     : svg_viewport_footer_height,

# legend
"svg_coord_legend_x"          : svg_viewport_draw_field_width,
"svg_coord_legend_y"          : svg_viewport_legend_start_height,
"svg_coord_legend_width"      : svg_viewport_legend_width,
"svg_coord_legend_height"     : svg_layout_legend_height,
    
    
# text for legend
"svg_coord_legend_bar_x"      : svg_layout_legend_bar_x,
"svg_coord_legend_bar_y"      : svg_layout_legend_bar_y,
"svg_coord_legend_bar_width"  : svg_layout_legend_bar_width,
"svg_coord_legend_bar_height" : svg_layout_legend_bar_height,
"svg_coord_legend_text_x"     : svg_layout_legend_text_x,
"svg_coord_legend_text_y100"  : svg_layout_legend_text_100_y,
"svg_coord_legend_text_y075"  : svg_layout_legend_text_075_y,
"svg_coord_legend_text_y050"  : svg_layout_legend_text_050_y,
"svg_coord_legend_text_y025"  : svg_layout_legend_text_025_y,
"svg_coord_legend_text_y000"  : svg_layout_legend_text_000_y,
"svg_coord_legend_unit_x"     : svg_layout_legend_unit_x,
"svg_coord_legend_unit_y"     : svg_layout_legend_unit_y,
"svg_layout_legend_text_x_tot": svg_layout_legend_text_x_tot,
"svg_layout_legend_text_y_min": svg_layout_legend_text_y_min,
"svg_layout_legend_text_y_max": svg_layout_legend_text_y_max,
"svg_layout_legend_text_y_tot": svg_layout_legend_text_y_tot,

"svg_coord_reader_x"          : svg_layout_total_width - svg_margin,
"svg_coord_pmt_meta_y1"       : svg_coord_pmt_meta_y1,
"svg_coord_pmt_meta_y2"       : svg_coord_pmt_meta_y2,
"svg_coord_pmt_meta_y3"       : svg_coord_pmt_meta_y3,
"svg_coord_pmt_meta_y4"       : svg_coord_pmt_meta_y4,


# history
# axis
"svg_viewport_history_total_height" : svg_viewport_history_total_height,
"svg_viewport_history_total_width"  : svg_viewport_history_total_width,
"svg_coord_history_axis_x_left"       : svg_coord_axis_x_left,
"svg_coord_history_axis_x_right"      : svg_coord_axis_x_right,
"svg_coord_history_axis_y_bottom"     : svg_coord_axis_y_bottom,
"svg_coord_history_axis_y_top"        : svg_coord_axis_y_top,
"svg_coord_history_label_x_yaxis"     : svg_coord_label_x_yaxis,
"svg_coord_history_label_y_xaxis"     : svg_coord_label_y_xaxis,
# axis labels
"svg_coord_history_label_000_xaxis"   : svg_coord_label_000_xaxis,
"svg_coord_history_label_025_xaxis"   : svg_coord_label_025_xaxis,
"svg_coord_history_label_050_xaxis"   : svg_coord_label_050_xaxis,
"svg_coord_history_label_075_xaxis"   : svg_coord_label_075_xaxis,
"svg_coord_history_label_100_xaxis"   : svg_coord_label_100_xaxis,
"svg_coord_history_label_xaxis"       : svg_coord_label_xaxis,
    
"svg_coord_history_label_000_yaxis"   : svg_coord_label_000_yaxis,
"svg_coord_history_label_025_yaxis"   : svg_coord_label_025_yaxis,
"svg_coord_history_label_050_yaxis"   : svg_coord_label_050_yaxis,
"svg_coord_history_label_075_yaxis"   : svg_coord_label_075_yaxis,
"svg_coord_history_label_100_yaxis"   : svg_coord_label_100_yaxis,
"svg_coord_history_rate_label_y"      : svg_coord_rate_label_y,

"svg_coord_history_pmt_label_x"       : svg_coord_pmt_label_x,
"svg_coord_history_pmt_label_y"       : svg_coord_pmt_label_y,
"svg_coord_history_time_label_x"      : svg_coord_time_label_x,
"svg_coord_history_time_label_y"      : svg_coord_time_label_y,
    

}

t1()


# In[ ]:





# In[10]:


# add color scheme to replace list

svg_replace["svg_gradient_stops"] = "\n".join(
    [
    ((' '*8)+'<stop offset="{}%" style="stop-color:rgb{};" />'.format(percent, dict_color_scheme[percent])) for percent in dict_color_scheme
    ]
)
#print(svg_replace["svg_gradient_stops"])


# In[ ]:





# In[ ]:





# In[ ]:





# In[11]:


print("calulate and defining all functions that map pmt info to x,y coordinates")
t0()

list_ignore_arrays = ["top-High Energy"]


str_array_names_to_show = str_array_names.copy()
tmp = [str_array_names_to_show.remove(x) for x in list_ignore_arrays]


# draw area
int_width_per_array  = (svg_viewport_draw_field_width - (1+len(str_array_names_to_show)) * svg_margin)/len(str_array_names_to_show)
int_height_per_array = svg_viewport_draw_field_height - 2* svg_margin

int_widths  = []
int_heights = []
int_means   = {}
i = 0
# generate coordinates for arrays
for array in str_array_names_to_show:
    
    
    int_tmp_max_x = max(dict_array_float_x[array])
    int_tmp_min_x = min(dict_array_float_x[array])
    int_tmp_max_y = max(dict_array_float_x[array])
    int_tmp_min_y = min(dict_array_float_x[array])
    
    int_widths.append(int_tmp_max_x - int_tmp_min_x)
    int_heights.append(int_tmp_max_y - int_tmp_min_y)
    int_means[array] = {
        "x": round(statistics.mean(dict_array_float_x[array]),4),
        "y": round(statistics.mean(dict_array_float_x[array]),4),
    }
    
# get scaling for pmt arrays
float_scale = min(
    int_width_per_array / max(int_widths),
    int_height_per_array / max(int_heights)
)

# calulate the radius of the pmt cirlces
# 3 inch pmts in cm and scalled
float_pmt_radius_real    = 3/2 * 2.54 * float_scale
float_pmt_radius_scaled  = 3.5

# calulate offsets for individual arrays
float_array_offset = {}# svg_margin, svg_margin + svg_viewport_header_height
for i in range(len(str_array_names_to_show)):
    str_array_name = str_array_names[i]
    float_array_offset[str_array_name] = {
        "x": (i+.5) * int_width_per_array + (1+i) * svg_margin,
        "y": int_height_per_array / 2 + svg_viewport_header_height + svg_margin
    }



float_array_offset["top-High Energy"] = {
    "x": 0 + svg_viewport_draw_field_width /2,
    "y": svg_viewport_header_height + svg_viewport_draw_field_height/2,
}

# function that calulates the svg position from 
def svg_xy_from_real_xy(coords, offset={"x":0, "y":0}):
    if offset == False:
        return(svg_coord_outside)
    x = coords[0] * float_scale + offset["x"]
    y = -1 * coords[1] * float_scale + offset["y"]
    return({"x":x, "y":y, "r": float_pmt_radius_real})
 

def svg_xy_from_crate_pos(str_type, dict_pmt_info):
    crate = dict_pmt_info[str_type+"_crate"]
    
    if str_type in ["amp"]:
        slot  = dicts_int_max_crates_content["max_slots"][str_type] - dict_pmt_info[str_type+"_slot"]
        
        if dict_pmt_info["array"] in list_ignore_arrays:
            # put pmts outside if HE-channel
            
            return(svg_coord_outside)
    else:
        slot  = dict_pmt_info[str_type+"_slot"]
    
    
    float_pmt_cellsize_local = float_pmt_cellsize
    if str_type == "vme":
        float_pmt_cellsize_local = float_pmt_radius_vme * 2
    
    
    pmt_radius = float_pmt_cellsize_local / 2
    
    
    channel = dicts_int_max_crates_content["max_channels"][str_type] - dict_pmt_info[str_type+"_channel"]
    
    x = dict_crates_base_pos[str_type]["float_base_x"][crate]
    y = dict_crates_base_pos[str_type]["float_base_y"][crate]

    x += (slot + .5) * float_pmt_cellsize_local
    y -= (channel + .5) * float_pmt_cellsize_local
    
    return({"x":x, "y":y, "r": pmt_radius})

t1()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[12]:


print("calculate base pos, and widths")
t0()

float_pmt_cellsize_default = float_pmt_radius_scaled * 2


svg_coord_outside = {
    "x": svg_layout_total_width  + 10 * float_pmt_cellsize_default,
    "y": svg_layout_total_height + 10 * float_pmt_cellsize_default,
    "r": 0,
}


float_draw_area_x0     = 0
float_draw_area_y0     = svg_viewport_header_height
float_draw_area_width  = svg_viewport_draw_field_width
float_draw_area_height = svg_viewport_draw_field_height

float_pmt_radius_vme   = float_pmt_radius_scaled

for str_type in dicts_crates:
    
    print(str_type)
    
    int_n_crates = dicts_int_max_crates_content["max_crates"][str_type]
    int_n_slots  = dicts_int_max_crates_content["max_slots"][str_type]
    int_n_ch     = dicts_int_max_crates_content["max_channels"][str_type]
    
    float_pmt_cellsize = float_pmt_cellsize_default
    
    
    if str_type == "vme":
        float_pmt_radius_vme = float_draw_area_width / (4 * (int_n_slots+1)) / 2
        float_pmt_cellsize   = float_pmt_radius_vme * 2
    
    float_height = (int_n_ch + 1) * float_pmt_cellsize + svg_margin
    
    float_width  = (int_n_slots    + 1) * float_pmt_cellsize
    
    
    
    
    
    
    float_base_x = {}
    float_base_y = {}
    
    # bottom left position in draw area (add shift later right before storing)
    
    list_crate_names_for_iterations = sorted(dicts_crates[str_type])
    
    bool_top_to_bottom = True
    if str_type in ["amp"]:
        list_crate_names_for_iterations.reverse()
    
    float_x_start = svg_margin/2
    float_y_start = svg_margin/2
        
    float_x_rel = float_x_start
    float_y_rel = float_y_start
    
    
    if not str_type in ["vme"]:
        # generate base pos for each crate
        for crate_name in list_crate_names_for_iterations:

            float_y_rel += float_height + svg_margin/2

            if float_y_rel >= float_draw_area_height:
                float_y_rel  = float_height + svg_margin
                float_x_rel += float_width  + svg_margin


            float_base_x[crate_name] = float_x_rel
            float_base_y[crate_name] = float_y_rel + float_draw_area_y0
        
            print("  - {:>6}: ({:6.2f}, {:6.2f}, {:6.2f})".format(crate_name, float_x_rel, float_y_rel + float_draw_area_y0, float_pmt_cellsize/2))
            
    elif str_type == "vme":
        list_crate_names_for_iterations = [0,1,2,4,3]
        int_crate_counter = -1
        for crate_name in list_crate_names_for_iterations:
            int_crate_counter += 1
            
            
            if crate_name == 3:
                float_y_rel = 2 * float_height + 2 * svg_margin
                float_x_rel = 2 * float_width
            else:
                float_y_rel = float_height + svg_margin
                float_x_rel = float_width * int_crate_counter
                
            
            float_base_x[crate_name] = float_x_rel
            float_base_y[crate_name] = float_y_rel + float_draw_area_y0
            
            
        
            print("  - {:>6}: ({:6.2f}, {:6.2f}, {:6.2f})".format(crate_name, float_x_rel, float_y_rel + float_draw_area_y0, float_pmt_cellsize/2))
        
    
    dict_crates_base_pos[str_type] = {
        "float_width_crate":   float_width,
        "float_height_crate":  float_height,
        "int_n_crate":         int_n_crates,
        "float_base_x":        float_base_x,
        "float_base_y":        float_base_y,
        "float_pmt_radius":    float_pmt_cellsize/2,
    }
    

t1()


# In[ ]:





# In[ ]:





# In[13]:


# add multiple header types to file
print("add header content to svg-replace-string")
t0()

str_list_content_header = []


# add meta data
str_list_content_header.append(('''
    <metadata id='map_pmt_id_to_link' property='{data}' ></metadata>
''').format(
    data = json.dumps(dict_pmt_to_rdr_lnk),
))
str_list_content_header.append(('''
    <metadata id='list_all_links' property='{data}' ></metadata>
''').format(
    data = json.dumps(list(dicts_crates["opt"].keys())),
))

str_list_content_header.append(('''
    <metadata id='dict_color_scheme' property='{data}' ></metadata>
''').format(
    data = json.dumps(dict_color_scheme),
))




# header for standard tpc layouts
for str_array_name in str_array_names_to_show:
    float_offsets = float_array_offset[str_array_name]
    str_list_content_header.append('''    <text
        x="''' + str(float_offsets["x"]) + '''"
        y="''' + str(svg_viewport_header_height + svg_margin) + '''"
        class="array"
    >''' + str_array_name + '''</text>''')

# add host header

header_x = svg_viewport_draw_field_width/2
header_y = svg_viewport_header_height/2
dict_str_headers ={
    "opt": "Optical Links", 
    "vme": "VME crates",
    "amp": "Amplifiers",

}

str_list_content_header.append(
f'''
    <text
       x="{header_x}"
       y="{header_y}"
       class="array_HE"
    >High Energy Array (top)</text>
''')

print("adding crate names")
for str_type in dicts_crates:
    
    dict_crate_base_pos = dict_crates_base_pos[str_type]
    
    str_list_content_header.append(('''
    <text
       x="{}"
       y="{}"
       class="{}"
    >{}</text>'''
    ).format(header_x, header_y, str_type, dict_str_headers[str_type]))

    for crate_name in dicts_crates[str_type]:
        
        float_crate_base_pos_x = dict_crate_base_pos["float_base_x"][crate_name]
        float_crate_base_pos_y = dict_crate_base_pos["float_base_y"][crate_name]
        
        
        x_0 = float_crate_base_pos_x
        y_0 = float_crate_base_pos_y - dict_crate_base_pos["float_height_crate"]
        
        x_t = x_0 + dict_crate_base_pos["float_width_crate"] / 2
        y_t = y_0 + svg_margin/2
        
        
        float_pmt_cellsize_type = dict_crate_base_pos["float_pmt_radius"] * 2
        
        str_list_content_header.append(('''
        <text
           x="{x_t}"
           y="{y_t}"
           class="{str_type} infotext"
           id="title_crate_{str_type}_{crate_name}"
        >{crate_name}</text>
        <rect
            x="{x_0}"
            y="{y_0}"
            width="{width}"
            height="{height}"
            class="{str_type} crate_box" />
        '''
        ).format(
            x_t        = x_t,
            y_t        = y_t,
            str_type   = str_type,
            crate_name = crate_name,
            x_0        = x_0,
            y_0        = y_0,
            height     = dict_crate_base_pos["float_height_crate"],
            width      = dict_crate_base_pos["float_width_crate"]
        ))
        
        
        
        if str_type == "opt":
            str_list_content_header.append(('''
            <circle
                cx="{x_0}"
                cy="{y_0}"
                r="{radius}"
                class="{str_type} crate_box_header"
                id="rate_opt_circ_{crate_name}"
                style="stroke:none;"
            />
            <text
               x="{x_1}"
               y="{y_0}"
               class="{str_type} text_info_small_right"
               text-anchor="end"
               id="rate_opt_txt_{crate_name}"
            ></text>
        '''
        ).format(
            str_type   = str_type,
            crate_name = crate_name,
            x_0        = x_0 + svg_margin * .5,
            y_0        = y_0 + svg_margin * .5,
            x_1        = x_0 + dict_crate_base_pos["float_width_crate"] - svg_margin * .1,
            radius     = svg_margin * .4,
        ))
            
        
        
        int_n_ch = dicts_int_max_crates_content["max_channels"][str_type]
        int_n_slot = dicts_int_max_crates_content["max_slots"][str_type]
        
        
        
        float_y_slotmarker_top    = y_0 + svg_margin
        float_y_slotmarker_bottom = y_0 + svg_margin + (int_n_ch+1) * float_pmt_cellsize_type
        
        for slot in range(int_n_slot):
            str_list_content_header.append(('''
        <line
            x1="{x1}"
            x2="{x2}"
            y1="{y1}"
            y2="{y2}"
            class="{str_type} slot_line"
            
        />
        ''').format(
                x1 = x_0 + float_pmt_cellsize_type * (slot+1),
                x2 = x_0 + float_pmt_cellsize_type * (slot+1),
                y1 = float_y_slotmarker_top,
                y2 = float_y_slotmarker_bottom,
                str_type = str_type
            ))
    


    if float_sleeptime > 0:
        time.sleep(float_sleeptime)


t1()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[14]:


print("adding pmts to svg")
t0()

str_list_content_pmts = []

for int_pmt_id in range(max(list_pmts)):
    
    str_pmt_id = str(int_pmt_id)
    print("\r  pmt " + str_pmt_id + ": " + str(int_pmt_id+1) + "/" + str(max(list_pmts)), end = "")
    
    str_list_content_pmt = ["", ""]
    
    # default values outside window
    dict_pos = {
        "array": svg_coord_outside,
        "array_HE": svg_coord_outside,
        "vme": svg_coord_outside,
        "opt": svg_coord_outside,
        "amp": svg_coord_outside,
        "off": svg_coord_outside,
    }
    
    
    if int_pmt_id in list_pmts:
        dict_pmt_info = dict_cable_map[int_pmt_id]
        
    
        # block with Infotexts 
        str_info_1 = "ADC: {}, {} (sn, channel)".format(dict_pmt_info["adc"], dict_pmt_info["adc_channel"])
        str_info_2 = "OPT: {}, {}, {} (rdr.link, slot, channel)".format(dict_pmt_info["opt_crate"], dict_pmt_info["opt_slot"], dict_pmt_info["opt_channel"])
        str_info_3 = "VME: {}, {}, {} (crate, slot, channel)".format(dict_pmt_info["vme_crate"], dict_pmt_info["vme_slot"], dict_pmt_info["vme_channel"])
        #str_info_4 = "array: {}".format(dict_pmt_info["array"])
        str_info_4 = "AMP: {}, {}, {} (crate, slot, channel)".format(dict_pmt_info["amp_crate"], dict_pmt_info["amp_slot"], dict_pmt_info["amp_channel"])
        
        print(f"""\33[33m{dict_pmt_info["coords"]}\33[0m""", end = "")
        if dict_pmt_info["array"] in list_ignore_arrays:
            dict_pos["array"]    = svg_xy_from_real_xy(dict_pmt_info["coords"], False)
            dict_pos["array_HE"] = svg_xy_from_real_xy(dict_pmt_info["coords"], float_array_offset[dict_pmt_info["array"]])
        else:
            dict_pos["array"]    = svg_xy_from_real_xy(dict_pmt_info["coords"], float_array_offset[dict_pmt_info["array"]])
            
        dict_pos["vme"] = svg_xy_from_crate_pos("vme", dict_pmt_info)
        dict_pos["opt"] = svg_xy_from_crate_pos("opt", dict_pmt_info)
        dict_pos["amp"] = svg_xy_from_crate_pos("amp", dict_pmt_info)
        
        
    
        str_pos_alternatives = "posstart{}posend".format(json.dumps(dict_pos))
        

    
    
    
        str_list_content_pmt.append('''
        <g>
            <circle
                cx="''' + str(dict_pos["array"]["x"]) + '''"
                cy="''' + str(dict_pos["array"]["y"]) + '''"
                r="''' + str(float_pmt_radius_scaled) + '''"
                class='pmt'''+str_pmt_id+''' pmt '''+str_pos_alternatives+''' '
                id="pmt'''+str_pmt_id+'''"
            />
            <text
                class="pmt_text pmt_text_info"
                x="'''+str(dict_pos["array"]["x"])+'''"
                y="'''+str(dict_pos["array"]["y"])+'''"
                id="txt_pmt'''+str_pmt_id+'''"
            >'''+str_pmt_id+'''</text>

            <text
                class="text_info_large hidden"
                x="'''+str(svg_coord_pmt_text_x)+'''"
                y="'''+str(svg_coord_pmt_text_y1)+'''"
            >PMT '''+str_pmt_id+'''</text>
            <text
                id="txt_pmt_2_''' + str_pmt_id+'''"
                class="text_info_large hidden"
                x="'''+str(svg_coord_pmt_text_x)+'''"
                y="'''+str(svg_coord_pmt_text_y2)+'''"
            >no data yet</text>
            <text
                class="text_info_small hidden"
                x="'''+str(svg_coord_pmt_meta_x)+'''"
                y="'''+str(svg_coord_pmt_meta_y1)+'''"
                >'''+str_info_1+'''</text>
            <text
                class="text_info_small hidden"
                x="'''+str(svg_coord_pmt_meta_x)+'''"
                y="'''+str(svg_coord_pmt_meta_y2)+'''"
                >'''+str_info_2+'''</text>
            <text
                class="text_info_small hidden"
                x="'''+str(svg_coord_pmt_meta_x)+'''"
                y="'''+str(svg_coord_pmt_meta_y3)+'''"
                >'''+str_info_3+'''</text>
            <text
                class="text_info_small hidden"
                x="'''+str(svg_coord_pmt_meta_x)+'''"
                y="'''+str(svg_coord_pmt_meta_y4)+'''"
                >'''+str_info_4+'''</text>
        </g>''')

        str_list_content_pmts.extend(str_list_content_pmt)
    
    else:
        # if pmt is not in list
        print(" is fake pmt")
        
        str_pos_alternatives = "posstart{}posend".format(json.dumps(dict_pos))

                                                            
        str_list_content_pmt.append('''
            <circle
                cx="''' + str(svg_coord_outside["x"]) + '''"
                cy="''' + str(svg_coord_outside["y"]) + '''"
                r="''' + str(float_pmt_radius_scaled) + '''"
                class='pmt'''+str_pmt_id+''' pmt '''+str_pos_alternatives+''' ' 
                id="pmt'''+str_pmt_id+'''"
            />
            <text
                class="pmt_text pmt_text_info"
                x="'''+str(svg_coord_outside["x"])+'''"
                y="'''+str(svg_coord_outside["y"])+'''"
                id="txt_pmt'''+str_pmt_id+'''"
            >'''+str_pmt_id+'''</text>
            <text
                id="txt_pmt_2_''' + str_pmt_id+'''"
                class="text_info_large hidden"
                x="'''+str(svg_coord_pmt_text_x)+'''"
                y="'''+str(svg_coord_pmt_text_y2)+'''"
            >no data yet</text>''')
        
        str_list_content_pmts.extend(str_list_content_pmt)
                                    
                                    


print("")
t1()


# In[ ]:





# In[15]:


float_array_offset


# In[ ]:





# In[ ]:





# In[16]:


svg_replace["CONTENT_HEADER"] = "\n".join(str_list_content_header)
svg_replace["CONTENT_PMTS"]   = "\n".join(str_list_content_pmts)

print("loading svg preset for pmt view and write data to new file")
t0()

with open("svg_layout.svg_preset", 'r') as file:
    svg_preset = file.read()
    

for key in svg_replace:
    svg_preset = svg_preset.replace("%%"+key+"%%", str(svg_replace[key]))

    

text_file = open(path_out + "monitor_tpc_layout.svg", "w")
n = text_file.write(svg_preset)
text_file.close()

print("svg created: {}monitor_tpc_layout.svg".format(path_out))

print("loading svg preset for legend and write data to new file")

with open("monitor_history.svg_preset", 'r') as file:
    svg_preset2 = file.read()

for key in svg_replace:
    svg_preset2 = svg_preset2.replace("%%"+key+"%%", str(svg_replace[key]))


text_file2 = open(path_out + "monitor_history.svg", "w")
n = text_file2.write(svg_preset2)
text_file2.close()

print("svg created: {}monitor_history.svg".format(path_out))

t1()


# In[ ]:





# In[ ]:





# In[17]:


print("everything done in %1.3f s"%(datetime.utcnow()-t_start_all).total_seconds())


# In[ ]:





# In[ ]:





# In[ ]:




