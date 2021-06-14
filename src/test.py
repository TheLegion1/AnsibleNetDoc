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
#parse the json data from Ansible
def GenerateImage(fileName):
    ports = {}
    sfps = {}
    hostname = ""
    num_ports = 0
    is_nxos = False
    with open(fileName) as f:
        data = json.load(f)
        if( "nxos" in data["ansible_net_system"]):
            is_nxos = True
        hostname = data["ansible_net_hostname"]
        if(is_nxos):
                num_switches = 1
        else:
            num_switches = len(data["ansible_net_stacked_serialnums"])
        print(hostname)


        for interface in data["ansible_net_interfaces"]:
            if("channel" in interface or "GigabitEthernet0/0" in interface):
                continue
            if(is_nxos == False):
                if(data["ansible_net_interfaces"][interface]["mediatype"] is not None and "App-hosting port" not in data["ansible_net_interfaces"][interface]["mediatype"]):
                    if("unknown" in data["ansible_net_interfaces"][interface]["mediatype"] or "SFP" in data["ansible_net_interfaces"][interface]["mediatype"]):
                        num_ports += 1
                        #print(interface + "Status: " + data["ansible_net_interfaces"][interface]["operstatus"])
                        sfps[interface] = (data["ansible_net_interfaces"][interface]["operstatus"])
                    else:
                        num_ports += 1
                        #print(interface + " Status: " + data["ansible_net_interfaces"][interface]["operstatus"])
                        ports[interface] = (data["ansible_net_interfaces"][interface]["operstatus"])
            else:
                if("vlan" in interface or "Vlan" in interface or "mgmt" in interface):
                    continue

                num_ports += 1
                slash = interface.find('/')
                #print(interface + " SLASH LOCATED AT: " + str(slash))
                if(int(interface[slash+1:]) > 48):
                    sfps[interface] = (data["ansible_net_interfaces"][interface]["state"])
                else:
                    ports[interface] = (data["ansible_net_interfaces"][interface]["state"])

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
    green = Image.new(mode="RGBA", size=(port_size, port_size), color=(0,128,0,255))
    red = Image.new(mode="RGBA", size=(port_size, port_size), color=(128,0,0,255))
    test_port = Image.composite(green, inactive_port, inactive_port)
    test_sfp = Image.composite(green, inactive_sfp, inactive_sfp)
    test_port_aDown = Image.composite(red, inactive_port, inactive_port)
    test_sfp_aDown = Image.composite(red, inactive_sfp, inactive_sfp)
    bck = Image.new(mode="RGBA", size = (port_size-6, port_size-6), color=(255,255,255,255))
    start_x = padding
    start_y = 2*padding
    sw_output = switch_img.copy()

    #vlan color information
    vlans = {
        100: (0,128,255,255),
        32: (93, 0, 166, 255),
        254: (255, 0, 0, 255)
    }



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

        template_file = "template.html"
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
        GenerateImage('/home/support/networkDocumentation/switches/' + file)
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
