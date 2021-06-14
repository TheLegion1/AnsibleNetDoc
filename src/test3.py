from PIL import Image
import random
import json
from math import floor
from os import listdir
from bs4 import BeautifulSoup as bs
import os
import re
import shutil

indexFiles = []

vlan_colors = {
        100: (128,50,128,255),#IT
        88: (255,0,0,255),     #DMZ (RED)
        70: (151,99,145,255),  # (976391 antique fuchia)
        75: (232,63,111,255),  # Cameras (e83f6f paradise pink)
        254: (255,191,0,255),  # Management (ffbf00 amber)
        1: (27,153,139,255),   # servers (1b998b persian green)
        51: (43,89,195,255),   # MedArts (2b59c3 cerulean blue)
        27: (37,60,120,255),   # Medical Imaging (253c78 dark cornflower blue)
        26: (113,47,121,255),  # PACU/OR (712f79 Maximum purple)
        570: (133,90,92,255),  # (855a5c Rose Taupe)
        666: (201,166,144,255),# (c9a690 tumbleweed)
        90: (34, 116, 165,255),# (2274a5 Star Command Blue)
        150: (247,153,110,255),# (f7996e atomic tangerine)
        151: (244,96,54,255),  # (f46036 Portland Orange)
        555: (46,41,78,255),   # (2E294E space cadet)
        30: (72,99,156,255),   # (48639c Queen Blue)
        2: (76,76,157,255),    # (4c4c9d liberty)
        575: (251,54,64,255),  # (fb3640 red salsa)
        80: (10,36,99,255),    # (0a2463 royal blue dark)
        15: (115,147,126,255), # (73937E Xanadu)
        76: (0,141,213,255),   # (008DD5 Green Blue Crayola)
        23: (55,63,81,255),    # (373f51 charcoal)
        25: (37,206,209,255),  # (25ced1 dark turqoise)
        800: (102,16,31,255),  # iSCSI (66101f Persian Plum)
        50: (96,70,59,255),    # (60463b dark liver horses)
        21: (34,111,84,255),   # (226f54 bottle green)
        28: (154,109,56,255),  # (9a6d38 golden brown)
        10: (79,109,122,255),  # (4f6d7a cadet)
        20: (138,137,192,255), # (8a89c0 blue bell)
        29: (6,214,160,255),   # (06d6a0 caribbean green)
        110: (38,42,16,255),   # (262a10 pine tree)
        32: (11,85,99,255),    # (0b5563 midnight green eagle green)
        165: (71,19,35,255),   # (471323 Dark Sienna)
        152: (255,153,102,255) # (FF9966)
    } 


def getVlanForPort(port, config_data):
  #get the vlan for the given ports
  search_str = "interface " + port
  #print(config_data)
  start_index = config_data.find(search_str)
  end_index = config_data.find('\ninterface', start_index)
  #print(start_index)
  #print(end_index)
  trunk_str = "trunk"
  access_str = "access vlan"
  port_config = config_data[start_index:end_index]
  if(trunk_str in port_config):
    #print("Port is a trunk port")
    return "trunk"
  elif(access_str in port_config):
    #print("Port is an access port")
    vlan_str = port_config.find('access vlan') + len('access vlan')
    vlan_str_end = port_config.find('\n', vlan_str) 
    vlan_str_value = port_config[vlan_str:vlan_str_end]
    return vlan_str_value
  elif("switchport" in port_config and "vlan" not in port_config):
    return "1"
  else:
    #print("Could not find vlan for port, assuming port has no config data")
    return "None"

def GetPortInfo(fileName):
    ports = {}
    sfps = {}
    port_vlan_mapping = {}
    num_ports = 0
    is_nxos = False
    #open the json file output by Ansible_facts
    with open(fileName) as f:
        data = json.load(f)
        #check is this is a nexus switch
        if("nxos" in data['ansible_net_system']):
            is_nxos = True
        hostname = data["ansible_net_hostname"]
        config_data = data['ansible_net_config']
        if(is_nxos):
            num_switches = 1
        else:
            num_switches = len(data["ansible_net_stacked_serialnums"])
        print(hostname)

                #fill the dictionaries for the ports operational status
        for interface in data["ansible_net_interfaces"]:
                        if("channel" in interface or "GigabitEthernet0/0" in interface):
                                continue            
                        if(is_nxos == False):
                                if(data["ansible_net_interfaces"][interface]["mediatype"] is not None and "App-hosting port" not in data["ansible_net_interfaces"][interface]["mediatype"]):
                                        if("unknown" in data["ansible_net_interfaces"][interface]["mediatype"] or "SFP" in data["ansible_net_interfaces"][interface]["mediatype"]):
                                                num_ports += 1
                                                #print(interface + "Status: " + data["ansible_net_interfaces"][interface]["operstatus"])
                                                sfps[interface] = (data["ansible_net_interfaces"][interface]["operstatus"])
                                                port_vlan_mapping[interface] = getVlanForPort(interface, config_data)
                                        else:
                                                num_ports += 1
                                                #print(interface + " Status: " + data["ansible_net_interfaces"][interface]["operstatus"])
                                                ports[interface] = (data["ansible_net_interfaces"][interface]["operstatus"])
                                                port_vlan_mapping[interface] = getVlanForPort(interface, config_data)
                        else:
                                if("vlan" in interface or "Vlan" in interface or "mgmt" in interface):
                                        continue
                                else:
                                    port_vlan_mapping[interface] = getVlanForPort(interface, config_data)


                                num_ports += 1
                                slash = interface.find('/')
                                #print(interface + " SLASH LOCATED AT: " + str(slash))
                                if(int(interface[slash+1:]) > 48):
                                        sfps[interface] = (data["ansible_net_interfaces"][interface]["state"])
                                else:
                                        ports[interface] = (data["ansible_net_interfaces"][interface]["state"])

    #generate the images of the switches
        GenerateActivePortImage(ports, sfps, int(num_ports), int(num_switches), is_nxos, hostname)
        GenerateVlanPortImage(ports, sfps, port_vlan_mapping, int(num_ports), int(num_switches), is_nxos, hostname)

def port_img(color, src_img, sz):
    color_sqr = Image.new(mode="RGBA", size=(sz,sz), color=color)
    return Image.composite(color_sqr, src_img, src_img)

def GenerateActivePortImage(ports, sfps, num_ports, num_switches, is_nxos, hostname):
    #image variables
        port_size = 64
        padding = 6 #50
        switch_gap = 50 #150
        num_switches = int(num_switches)
        img_width = (28 * (port_size + padding)) + (3*padding)
        img_height = (num_switches * (2 * (port_size + padding) + (padding))) + (num_switches * switch_gap)
        switch_img = Image.new(mode = "RGBA", size = (int(img_width), int(img_height)), color = (120,120,120,0))
        inactive_port = Image.open("rj45_small.png", 'r')
        inactive_sfp = Image.open("sfp_small.png", 'r')
        black = Image.new(mode="RGBA", size=(port_size, port_size), color=(0,0,0,255))
        green = Image.new(mode="RGBA", size=(port_size, port_size), color=(0,128,0,255))
        red = Image.new(mode="RGBA", size=(port_size, port_size), color=(128,0,0,255))
        inactive_port = Image.composite(black, inactive_port, inactive_port)
        inactive_sfp = Image.composite(black, inactive_sfp, inactive_sfp)
        test_port = Image.composite(green, inactive_port, inactive_port)
        test_sfp = Image.composite(green, inactive_sfp, inactive_sfp)
        test_port_aDown = Image.composite(red, inactive_port, inactive_port)
        test_sfp_aDown = Image.composite(red, inactive_sfp, inactive_sfp)
        bck = Image.new(mode="RGBA", size = (port_size-6, port_size-6), color=(255,255,255,0))
        start_x = padding
        start_y = 2*padding
        sw_output = switch_img.copy()

                #generate the active/inactive image
        #generate the image of the switch 
        col = 0
        row = 0
        index = 1
        current_sw = 1
        highest_col = 24
        for port in ports:
                if(col > highest_col):
                        highest_col = col
                if(is_nxos == False):
                        #ios switches are formatted as switch/module/port_number
                        sl_index = str(port).index('/')
                        sw_index = str(port)[sl_index-1: sl_index]
                        module_index = str(port).index('/', sl_index+1)
                        module_num = str(port)[sl_index+1:module_index]
                        port_num = str(port)[module_index+1:]
                        port_num = int(port_num)
                else:
                        #nexus switch
                        #nexus numbers their ports switch/port_number with modules being ports 49- whatever
                        sl_index = str(port).index('/')
                        sw_index = str(port)[sl_index-1: sl_index]
                        port_num = str(port)[sl_index+1:]
                        port_num = int(port_num)
                        module_num = 48-port_num
                        if(module_num < 0):
                                module_num = 0

                if(int(sw_index) != current_sw):
                        #print("Current Switch is: " + sw_index)
                        col = 0
                        current_sw = int(sw_index)

                if(int(port_num) % 2 == 0):
                        row = 1
                        col = round((int(port_num) / 2) - 1)
                        x = start_x + (col * (port_size + padding))
                        y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
                        #print("Placing " + port + " at: X: " + str(row) + " Y: " + str(col) + " port_num: " + str(port_num))
                        if(ports[port] == "up"):
                                sw_output.paste(bck, (x+2, y+2))
                                sw_output.paste(test_port, (x,y), mask=inactive_port)
                        elif("administratively down" in ports[port]):
                                sw_output.paste(bck, (x+2, y+2))
                                sw_output.paste(test_port_aDown, (x,y), mask=inactive_port)
                        else:
                                sw_output.paste(bck, (x+2, y+2))
                                sw_output.paste(inactive_port, (x,y), mask=inactive_port)
                else:
                        row = 0
                        col = round((int(port_num) - 1) / 2)
                        x = start_x + (col * (port_size + padding))
                        y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
                        #print("Placing " + port + " at: X: " + str(row) + " Y: " + str(col) + " port_num: " + str(port_num))
                        if(ports[port] == "up"):
                                sw_output.paste(bck, (x+2, y+2))
                                sw_output.paste(test_port, (x,y), mask=inactive_port)
                        elif("administratively down" in ports[port]):
                                sw_output.paste(bck, (x+2, y+2))
                                sw_output.paste(test_port_aDown, (x,y), mask=inactive_port)
                        else:
                                sw_output.paste(bck, (x+2, y+2))
                                sw_output.paste(inactive_port, (x,y), mask=inactive_port)



        #add in the sfp ports

        col = 24
        normal_col = 0
        for port in sfps:
                if(is_nxos == False):
                        #ios switches are formatted as switch/module/port_number
                        sl_index = str(port).index('/')
                        sw_index = str(port)[sl_index-1: sl_index]
                        module_index = str(port).index('/', sl_index+1)
                        module_num = str(port)[sl_index+1:module_index]
                        port_num = str(port)[module_index+1:]
                        port_num = int(port_num)
                else:
                        #nexus switch
                        #nexus numbers their ports switch/port_number with modules being ports 49- whatever
                        sl_index = str(port).index('/')
                        sw_index = str(port)[sl_index-1: sl_index]
                        port_num = str(port)[sl_index+1:]
                        port_num = int(port_num)
                        module_num = 48-port_num
                        if(module_num < 0):
                                module_num = 1

                if(int(sw_index) != current_sw):
                        #print("Current Switch is: " + sw_index)
                        col = highest_col
                        normal_col = 0
                        current_sw = int(sw_index)

        #    if(int(module_num) == 0):
        #        col = normal_col
        #    else:
        #        col = round((int(port_num) - 1) / 2)

                if(index % 2 == 0):
                        row = 1
                        if(is_nxos):
                                row = 1
                                col = round((int(port_num) / 2) - 1)
                        if(int(module_num) == 0):
                                row = 0
                                if(is_nxos == False):
                                        col = int(str(port)[module_index+1:])-1


                        x = start_x + (col * (port_size + padding)) + (2*padding if int(module_num) == 1 else 0)
                        y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
                        col += 1
                        normal_col += 1
                else:
                        row = 0
                        if(is_nxos):
                                col = round((int(port_num) - 1) / 2)
                        if(int(module_num) == 0):
                                if(is_nxos == False):
                                        col = int(str(port)[module_index+1:])-1

                        x = start_x + (col * (port_size + padding)) + (2*padding if int(module_num) == 1 else 0)
                        y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
                index += 1
                if(sfps[port] == "up"):
                        sw_output.paste(bck, (x+2, y+2))
                        sw_output.paste(test_sfp, (x,y), mask=inactive_sfp)
                elif("administratively down" in sfps[port]):
                        sw_output.paste(bck, (x+2, y+2))
                        sw_output.paste(test_sfp_aDown, (x,y), mask=inactive_sfp)
                else:
                        sw_output.paste(bck, (x+2, y+2))
                        sw_output.paste(inactive_sfp, (x,y), mask=inactive_sfp)

        sw_output.save('html/images/' + hostname + ".png")
        #print("Number of Ports on the Switch:" + str(num_ports))



def GenerateVlanPortImage(ports, sfps, port_vlan_mapping, num_ports, num_switches, is_nxos, hostname):
    #colors for each of the vlans
    
    #image variables
    port_size = 64
    padding = 6 #50
    switch_gap = 50 #150
    #num_switches = floor(num_ports / 48)
    num_switches = int(num_switches)
    #print("Switches: " + str(num_switches))
    img_width = (28 * (port_size + padding)) + (3*padding)
    img_height = (num_switches * (2 * (port_size + padding) + (padding))) + (num_switches * switch_gap)
    switch_img = Image.new(mode = "RGBA", size = (int(img_width), int(img_height)), color = (120,120,120,0))
    #switch_img.show()
    inactive_port = Image.open("rj45_small.png", 'r')
    inactive_sfp = Image.open("sfp_small.png", 'r')
    bck = Image.new(mode="RGBA", size = (port_size-6, port_size-6), color=(255,255,255,0))
    start_x = padding
    start_y = 2*padding
    sw_output = switch_img.copy()

    #generate the active/inactive image
    #generate the image of the switch 
    col = 0
    row = 0
    index = 1
    current_sw = 1
    highest_col = 24
    for port in ports:
            if(col > highest_col):
                    highest_col = col
            if(is_nxos == False):
                    #ios switches are formatted as switch/module/port_number
                    sl_index = str(port).index('/')
                    sw_index = str(port)[sl_index-1: sl_index]
                    module_index = str(port).index('/', sl_index+1)
                    module_num = str(port)[sl_index+1:module_index]
                    port_num = str(port)[module_index+1:]
                    port_num = int(port_num)
            else:
                    #nexus switch
                    #nexus numbers their ports switch/port_number with modules being ports 49- whatever
                    sl_index = str(port).index('/')
                    sw_index = str(port)[sl_index-1: sl_index]
                    port_num = str(port)[sl_index+1:]
                    port_num = int(port_num)
                    module_num = 48-port_num
                    if(module_num < 0):
                            module_num = 0

            if(int(sw_index) != current_sw):
                    #print("Current Switch is: " + sw_index)
                    col = 0
                    current_sw = int(sw_index)

            if(int(port_num) % 2 == 0):
                    row = 1
                    col = round((int(port_num) / 2) - 1)
                    x = start_x + (col * (port_size + padding))
                    y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
                    #print("Placing " + port + " at: X: " + str(row) + " Y: " + str(col) + " port_num: " + str(port_num))
            else:
                    row = 0
                    col = round((int(port_num) - 1) / 2)
                    x = start_x + (col * (port_size + padding))
                    y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
                    #print("Placing " + port + " at: X: " + str(row) + " Y: " + str(col) + " port_num: " + str(port_num))
            
            sw_output.paste(bck, (x+2, y+2))
            if(port in ports):
                if("up" in ports[port]):
                    active_link = Image.new(mode = "RGBA", size = (int(port_size)-10, 10), color = (0,255,0,255))
                    sw_output.paste(active_link, (x+2, y+2))

            
            if("None" in port_vlan_mapping[port]):
                img_to_paste = port_img((10,10,10,255), inactive_port, port_size)
            elif("trunk" in port_vlan_mapping[port]):
                img_to_paste = port_img((207,203,201,255), inactive_port, port_size)
            else:
                img_to_paste = port_img(vlan_colors[int(port_vlan_mapping[port])], inactive_port, port_size)
            
            sw_output.paste(img_to_paste, (x,y), mask=inactive_port)




    #add in the sfp ports

    col = 24
    normal_col = 0
    for port in sfps:
            if(is_nxos == False):
                    #ios switches are formatted as switch/module/port_number
                    sl_index = str(port).index('/')
                    sw_index = str(port)[sl_index-1: sl_index]
                    module_index = str(port).index('/', sl_index+1)
                    module_num = str(port)[sl_index+1:module_index]
                    port_num = str(port)[module_index+1:]
                    port_num = int(port_num)
            else:
                    #nexus switch
                    #nexus numbers their ports switch/port_number with modules being ports 49- whatever
                    sl_index = str(port).index('/')
                    sw_index = str(port)[sl_index-1: sl_index]
                    port_num = str(port)[sl_index+1:]
                    port_num = int(port_num)
                    module_num = 48-port_num
                    if(module_num < 0):
                            module_num = 1

            if(int(sw_index) != current_sw):
                    #print("Current Switch is: " + sw_index)
                    col = highest_col
                    normal_col = 0
                    current_sw = int(sw_index)

            if(index % 2 == 0):
                    row = 1
                    if(is_nxos):
                            row = 1
                            col = round((int(port_num) / 2) - 1)
                    if(int(module_num) == 0):
                            row = 0
                            if(is_nxos == False):
                                    col = int(str(port)[module_index+1:])-1


                    x = start_x + (col * (port_size + padding)) + (2*padding if int(module_num) == 1 else 0)
                    y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
                    col += 1
                    normal_col += 1
            else:
                    row = 0
                    if(is_nxos):
                            col = round((int(port_num) - 1) / 2)
                    if(int(module_num) == 0):
                            if(is_nxos == False):
                                    col = int(str(port)[module_index+1:])-1

                    x = start_x + (col * (port_size + padding)) + (2*padding if int(module_num) == 1 else 0)
                    y = start_y + (row * (port_size + padding)) + ((int(sw_index)-1) * (2 * (port_size + padding))) + ((int(sw_index)-1) * switch_gap)
            index += 1


            sw_output.paste(bck, (x+2, y+2))
            if("None" in port_vlan_mapping[port]):
                img_to_paste = port_img((10,10,10,255), inactive_sfp, port_size)
            elif("trunk" in port_vlan_mapping[port]):
                img_to_paste = port_img((207,203,201,255), inactive_sfp, port_size)
            else:
                img_to_paste = port_img(vlan_colors[int(port_vlan_mapping[port])], inactive_sfp, port_size)
            
            sw_output.paste(img_to_paste, (x,y), mask=inactive_sfp)
            



    sw_output.save('html/images/' + hostname + "_vlans.png")
    #print("Number of Ports on the Switch:" + str(num_ports))

def GenerateDoc(switchFile):
        print("Generating Doc for: " + switchFile)
        web_path = '/var/www/html/'
        with open(switchFile) as f:
                data = json.load(f)
                is_nxos = False
                if( "nxos" in data["ansible_net_system"]):
                        is_nxos = True
                #information about the switch
                hostname = data["ansible_net_hostname"]
                ios_version = data["ansible_net_version"]
                if(is_nxos == False):
                        sn_list = data["ansible_net_stacked_serialnums"]
                else:
                        sn_list = data["ansible_net_serialnum"]
                cdp_neighbors = data["ansible_net_neighbors"]
                ip_addr = data["ansible_net_all_ipv4_addresses"]

                template_file = "template_updated.html"
                new_file = hostname + ".html"

                #generate the html file
                base = os.path.dirname(os.path.abspath(template_file))
                html = open(os.path.join(base, template_file))
                soup = bs(html, 'html.parser')
                #hostname
                sw_name = soup.find("h2", {"id":"hostname"})
                sw_name_new = sw_name.find(text=re.compile('SWITCH-NAME')).replace_with(hostname)

                #IOS Version
                sw_name = soup.find("p", {"id":"ios_version"})
                version_str = "IOS Version: "
                if(is_nxos):
                        version_str = "NXOS Version: "
                sw_name_new = sw_name.find(text=re.compile('IOS_VER')).replace_with(version_str + ios_version)

                #switch Image
                img_tag = soup.find("img", {"id":"switch_img"})
                img_tag['src'] = 'images/' + hostname + ".png"

                #javascript code
                h = soup.find("head")
                script_tag = soup.new_tag('script')
                script_tag.string = 'function handleChange(checkbox){if(checkbox.checked == true){document.getElementById("switch_img").src = "' + 'images/' + hostname + "_vlans.png" + '"; expand();}else{document.getElementById("switch_img").src = "' + 'images/' + hostname + ".png" + '"; expand();}}'
                h.append(script_tag)

                #The Color Legend
                u_list = soup.find("ul", {"id": "legend"})
                
                #trunk port
                #print(vlan_colors[vlan])
                list_item = soup.new_tag("li", **{"class": "vlan"})

                svg = soup.new_tag("svg", **{"width": "20", "height": "20"})
                rct = soup.new_tag("rect", **{"width": "20", "height": "20", "style": "fill:rgba(207,203,201,255)" + ';stroke-width:3;stroke:rgb(0,0,0);'})
                #list_item.string = "Vlan " + str(vlan)
                list_item.append(svg)
                svg.append(rct)
                list_item.append("Trunk Ports")
                u_list.append(list_item)

                for vlan in vlan_colors:
                    #print(vlan_colors[vlan])
                    list_item = soup.new_tag("li", **{"class": "vlan"})
                   
                    svg = soup.new_tag("svg", **{"width": "20", "height": "20"})
                    rct = soup.new_tag("rect", **{"width": "20", "height": "20", "style": "fill:rgba" + str(vlan_colors[vlan]) + ';stroke-width:3;stroke:rgb(0,0,0);'})
                    #list_item.string = "Vlan " + str(vlan)
                    list_item.append(svg)
                    svg.append(rct)
                    list_item.append("Vlan " + str(vlan))
                    u_list.append(list_item)

                if(len(vlan_colors) % 2 != 0):
                    s = soup.new_tag("li", **{"class": "vlan"})
                    svg = soup.new_tag("svg", **{"width": "20", "height": "20"})
                    rct = soup.new_tag("rect", **{"width": "20", "height": "20", "style": "fill:rgba(255,255,255,255);stroke-width:3;stroke:rgb(255,255,255);"})
                    svg.append(rct)
                    s.append(svg)
                    u_list.append(s)


                #list of serial numbers
                sn_ulist = soup.find("ul", {"id":"SN"})
                if(is_nxos == False):
                        for sn in sn_list:
                                li_new_tag = soup.new_tag('li')
                                li_new_tag.string = sn
                                sn_ulist.append(li_new_tag)
                else:
                        #nexus switch isnt stacked so it only has 1 serial number
                        li_new_tag = soup.new_tag('li')
                        li_new_tag.string = sn_list
                        sn_ulist.append(li_new_tag)

                #list of IP addresses
                sn_ulist = soup.find("ul", {"id":"IP"})
                for ip in ip_addr:
                        li_new_tag = soup.new_tag('li')
                        li_new_tag.string = ip
                        sn_ulist.append(li_new_tag)


                #CDP Neighbors
                sn_ulist = soup.find("div", {"id":"neighbors"})
                for cdp in cdp_neighbors:
                        li_new_tag = soup.new_tag("h6", **{'class': "w3-text-teal"})
                        li_new_tag.string = cdp
                        sn_ulist.append(li_new_tag)
                        conn = soup.new_tag('ul')
                        client = soup.new_tag('p')
                        if(data["ansible_net_neighbors"][cdp][0]["host"] is None):
                                cdp_host = "LLDP Neighbor"
                        else:
                                cdp_host = data["ansible_net_neighbors"][cdp][0]["host"]
                        client.string = str(cdp_host) + " - " + str(data["ansible_net_neighbors"][cdp][0]["port"])
                        conn.append(client)
                        sn_ulist.append(conn)

                #config donwload links
                config_list = soup.find("ul", {"id": "configDL"})
                config_file_list = listdir('/var/www/html/Backups')
                relevant_files = []
                for file in config_file_list:
                        if hostname in file:
                                relevant_files.append(file)
                for file in relevant_files:
                        list_item = soup.new_tag("li")
                        list_item_sub = soup.new_tag("a", href='Backups/' + file, download=file)
                        list_item_sub.string = file[9:file.rfind('_')]
                        list_item.append(list_item_sub)
                        config_list.append(list_item)

                with open('html/' + new_file, "wb") as f_output:
                        f_output.write(soup.prettify("utf-8"))
                        indexFiles.append(new_file)

def GenerateIndexHtml():
        index_file = 'index.html'
        base = os.path.dirname(os.path.abspath(index_file))
        html = open(os.path.join(base, index_file))
        soup = bs(html, 'html.parser')

        sn_ulist = soup.find("ul", {"id":"toc"})
        for file in indexFiles:
                li_new_tag = soup.new_tag('li')
                a_tag = soup.new_tag('button', href=file, **{"class": "button button1"})
                a_tag.string = file[:file.index('.')]
                a_tag['onclick'] = "document.location='" + file + "'"
                li_new_tag.append(a_tag)
                sn_ulist.append(li_new_tag)

        with open('html/index.html', "wb") as f_output:
                f_output.write(soup.prettify("utf-8"))

if __name__ == "__main__":
        files = listdir('/home/support/networkDocumentation/switches')
        for file in files:
                GetPortInfo('/home/support/networkDocumentation/switches/' + file)
                GenerateDoc('/home/support/networkDocumentation/switches/' + file)

        GenerateIndexHtml()

        script_files = listdir('html')
        for file in script_files:
                if("image" in file):
                        continue
                else:
                        shutil.copy('html/' + file, '/var/www/html')

        #copy images over
        image_files = listdir('html/images')
        for file in image_files:
                        shutil.copy('html/images/' + file, '/var/www/html/images/')
