from xml.dom import minidom


with open("xml-file.xml", "r") as xml_file:
    bgpconfig = minidom.parse(xml_file)
print(bgpconfig)    