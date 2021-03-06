#!/usr/bin/python
'''
@author: Matthew C. Jones, CPA, CISA, OSCP
IS Audits & Consulting, LLC
TJS Deemer Dana LLP

Nmap XML output parsing functions / utilities

See README.md for licensing information and credits

'''
import argparse
import os

try:
    from lxml import etree
except:
    print "lxml module not installed try: "
    print "pip install lxml"
    print "     ----- OR -----"
    print "apt-get install python-lxml"
    

def main():
   
    #------------------------------------------------------------------------------
    # Configure Argparse to handle command line arguments
    #------------------------------------------------------------------------------
    desc = "Nmap parsing automation script; "
    desc += "currently only export capabilities but more advanced processing to come! "
    desc += "exports to both text and html if no output options (--text, --html) are specified."
    
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('nmap_input', action='store', nargs='?',
                        help='Single XML or directory containing Nmap XML files to process \n \
                                (defaults to working directory if none specified)'
    )
    parser.add_argument('-o', '--outdir', action='store',
                        help='Output directory (default to specified target directory)'
    )
    parser.add_argument('--text',
                        help='Output to text',
                        action='store_true'
    )
    parser.add_argument('--html',
                        help='Output to html',
                        action='store_true'
    )
    parser.add_argument('--xsl', action='store',
                        help='Nmap xml stylesheet (defaults to xml-stylesheet from nmap XML files)'
    )
    parser.add_argument('-p', '--parse',
                        help='Parse nessus output files',
                        action='store_true'
    )
    args = parser.parse_args()
    
    target = args.nmap_input
    outdir = args.outdir
    xsl = args.xsl
    is_text = args.text
    is_html = args.html
    is_parse = args.parse
    
    #------------------------------------------------------------------------------
    # Main stuff
    #------------------------------------------------------------------------------
    
    if not target:
        target = os.getcwd()
        print 'no  input file or directory specified - using working directory:'
        print target
        print ''
        
    
    # No output directory specified - use same directory as input target file/dir
    if not outdir:
        if os.path.isfile(target):
            outdir = os.path.dirname(target)
        else:
            outdir = target
        print 'no output directory specified - using ' + outdir
        print ''
    
    if is_parse:
        parse_xml(target)
    
    # No output options specified - enable all!
    elif not is_text and not is_html:
        is_text = True
        is_html = True
    
    print 'Text output enabled: ' + str(is_text)
    print 'HTML output enabled: ' + str(is_html)
    
    infile_list = []
    
    if os.path.isfile(target):
        infile_list.append(target)
    else:
        for infile in os.listdir(target):
            if os.path.isfile(os.path.join(target,infile)) and infile[-3:] == "xml":
                infile_list.append(os.path.join(target,infile))
    
    for infile in infile_list:
        outfile_base = os.path.join(outdir,os.path.splitext(os.path.basename(infile))[0])
        if is_text:
            nmap_out_to_txt(infile,outfile_base+'.txt')
        if is_html:
            nmap_out_to_html(infile,outfile_base+'.html',xsl)
            
    print "\n\nComplete!"
    print "Output data located at " + outdir

def nmap_out_to_html(infile, outfile, xsl=''):
    '''
    accepts an nmap xml file and exports to html
    '''
    
    output = ''
    dom = etree.parse(infile)
    
    try:
        if xsl:
            xslt = etree.parse(xsl)
        else:
            docroot = dom.getroot()
            pi = docroot.getprevious()
            if isinstance(pi,etree._XSLTProcessingInstruction):
                xsl = pi.attrib['href']
                xslt = pi.parseXSL()
        
        transform = etree.XSLT(xslt)
        output = etree.tostring(transform(dom), pretty_print=True)
        
        output_file(outfile,output)
        
    except:
        print ''
        print '[!] Error parsing XSL for file '
        print ' -  make sure that the XSL transform is present and valid:'
        print ' -  ' + xsl
    
def nmap_out_to_txt(infile, outfile):
    output = ''

    e = etree.parse(infile).getroot()
    
    for child in e.iter('output'):
        output += child.text
    
    output_file(outfile,output)
    
def output_file(outfile, output, overwrite=True):
    if overwrite == True:
        f = open(outfile, 'w+')
    else:
        f = open(outfile, 'w')
    
    f.write(output)
    f.close

def parse_xml(filename_xml):
    parser = NmapParser(filename_xml)


class NmapScan(object):
    def __init__(self):
        self.startstr=''
        self.profile_name=''
        self.scanner=''
        self.version=''
        self.args=''
        self.services=''
        self.protocol=''
        self.numservices=''
        self.type=''
        self.output=''
        self.hosts=[]

class NmapHost(object):
    def __init__(self):
        self.status=''      #up or down
        self.addr_ipv4=''
        self.addr_ipv6=''
        self.addr_mac=''
        self.addr_mac_vendor=''
        self.hostnames=[]
        self.os_name=''
        self.os_accuracy=0
        self.os_type=''
        self.os_family=''
        self.os_vendor=''
        self.os_gen=''
        self.ports=[]
        self.host_scripts=[]
        
class NmapHostScript(object):
    def __init__(self):
        self.host_script_id=''
        self.host_script_output=''
        
class NmapPort(object):
    def __init__(self):
        self.protocol=''    #tcp, udp
        self.portid=0       #port number
        self.state=''       #open, closed, etc
        self.svc_name=''
        self.svc_product=''
        self.svc_version=''
        self.svc_extrainfo=''
        self.svc_conf=0
        self.port_scripts=[]

class NmapPortScript(object):
    def __init__(self):
        self.port_script_id=''
        self.port_script_output=''
        
class NmapParser(object):
    def __init__(self, filename_xml):
        self.reports=[]
        if filename_xml == None or filename_xml == "":
            print "[!] No filename specified!"
            exit(1)
 
        # Parse input values in order to find valid .xml files
        self._xml_source = []
        if os.path.isdir(filename_xml):
            if not filename_xml.endswith("/"):
                filename_xml += "/"
            # Automatic searching of files into specified directory
            for path, dirs, files in os.walk(filename_xml):
                for f in files:
                    if f.endswith(".xml"):
                        self._xml_source.append(filename_xml + f)
                break
        elif filename_xml.endswith(".xml"):
            if not os.path.exists(filename_xml):
                print "[!] File specified '%s' not exist!" % filename_xml
                exit(3)
            self._xml_source.append(filename_xml)

        if not self._xml_source:
            print "[!] No file .xml to parse was found!"
            exit(3)
        
        # For each .xml file found...
        for file_nmaprun in self._xml_source:
            # Parse and extract information
            self._parse_results(file_nmaprun)

    def _parse_results(self, file_nmaprun):
        
        tree = etree.parse(file_nmaprun)
        
        nmaprun = tree.getroot()    
        nmap_scan=NmapScan()
        nmap_scan.startstr = nmaprun.get('startstr')
        nmap_scan.profile_name = nmaprun.get('profile_name')
        nmap_scan.scanner = nmaprun.get('scanner')
        nmap_scan.version = nmaprun.get('version')
        nmap_scan.args = nmaprun.get('args')
        
        scaninfo = nmaprun.find('scaninfo')
        nmap_scan.services = scaninfo.get('services')
        nmap_scan.protocol = scaninfo.get('protocol')
        nmap_scan.numservices = scaninfo.get('numservices')
        nmap_scan.type = scaninfo.get('type')
        
        output = nmaprun.find('output')
        if output is not None:
            nmap_scan.output = output.text
        
        for host in nmaprun.findall('host'):
            nmap_host=NmapHost()
            
            nmap_host.status = host.find('status').get('state')
            
            for address in host.findall('address'):
                if address.get('addrtype')=='ipv4':
                    nmap_host.addr_ipv4=address.get('addr')
                if address.get('addrtype')=='ipv6':
                    nmap_host.addr_ipv6=address.get('addr')
                if address.get('addrtype')=='mac':
                    nmap_host.addr_mac=address.get('addr')
                    nmap_host.addr_mac_vendor=address.get('vendor')
            
            hostnames = host.find('hostnames')
            for hostname in hostnames.findall('hostname'):
                nmap_host.hostnames.append(hostname.get('name'))
            
            os=host.find('os')
            if os is not None:
                osmatch=os.find('osmatch')
                if osmatch is not None:
                    nmap_host.os_name = osmatch.get('name')
                    nmap_host.os_accuracy = int(osmatch.get('accuracy'))
                    osclass=osmatch.find('osclass')
                    if osclass is not None:
                        nmap_host.os_type=osclass.get('type')
                        nmap_host.os_family=osclass.get('osfamily')
                        nmap_host.os_vendor=osclass.get('vendor')
                        nmap_host.os_gen=osclass.get('osgen')
            
            hostscript=host.find('hostscript')
            if hostscript is not None:
                scripts=hostscript.findall('script')
                for script in scripts:
                    nmap_host_script=NmapHostScript()
                    nmap_host_script.host_script_id=script.get('id')
                    nmap_host_script.host_script_output=script.get('output')
                    nmap_host.host_scripts.append(nmap_host_script)
                
            
            ports=host.find('ports')
            for port in ports.findall('port'):
                nmap_port=NmapPort()
                nmap_port.protocol=port.get('protocol')
                nmap_port.portid=port.get('portid')
                nmap_port.state=port.find('state').get('state')
                nmap_port.svc_name=port.find('service').get('name')
                nmap_port.svc_product=port.find('service').get('product')
                nmap_port.svc_version=port.find('service').get('version')
                nmap_port.svc_extrainfo=port.find('service').get('extrainfo')
                nmap_port.svc_conf=port.find('service').get('conf')
                
                scripts=port.findall('script')
                for script in scripts:
                    nmap_port_script=NmapPortScript()
                    nmap_port_script.port_script_id=script.get('id')
                    nmap_port_script.port_script_output=script.get('output')
                    nmap_port.port_scripts.append(nmap_port_script)
                
                nmap_host.ports.append(nmap_port)
            
            nmap_scan.hosts.append(nmap_host)
            
        self.reports.append(nmap_scan)
            
    
if __name__ == '__main__':
    main()