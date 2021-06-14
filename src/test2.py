import json

config_data = ""

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
    print("Port is a trunk port")
    return "trunk"
  elif(access_str in port_config):
    print("Port is an access port")
    vlan_str = port_config.find('access vlan') + len('access vlan')
    vlan_str_end = port_config.find('\n', vlan_str) 
    vlan_str_value = port_config[vlan_str:vlan_str_end]
    return vlan_str_value
  elif("switchport" in port_config and "vlan" not in port_config):
    return "1"
  else:
    print("oh shit")
    return "None"

if __name__ == "__main__":
  switchFile = '/home/support/networkDocumentation/switches/MDF-CORE'
  port = 'Ethernet1/34'
  with open(switchFile) as f:
    data = json.load(f)
    config_data = data["ansible_net_config"]


  port_vlan_map = {}
  for interface in data["ansible_net_interfaces"]:
    if("channel" in interface or "vlan" in interface or "Vlan" in interface or "mgmt" in interface):
      continue
    port_vlan_map[interface] = getVlanForPort(interface, config_data)
    print(interface, ' ', port_vlan_map[interface])
    


