import socket
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from scapy.all import ARP, Ether, srp
from getmac import get_mac_address
from mac_vendor_lookup import MACVendorLookup

MAX_WORKERS = 200
PING_TIMEOUT = 0.4 

class HostScanner:
    @staticmethod
    def get_hostname(ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return None

    @staticmethod
    def check_host(ip, ping_cmd):
        ip_str = str(ip)
        try:
            import subprocess
            if subprocess.run(ping_cmd + [ip_str], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL).returncode == 0:
                mac = get_mac_address(ip=ip_str)
                vendor = MACVendorLookup.get_vendor(mac) if mac else None
                return {
                    'ip': ip_str,
                    'mac': mac,
                    'vendor': vendor,
                    'name': HostScanner.get_hostname(ip_str),
                    'snmp_info': None
                }
        except Exception as e:
            return None
        return None

    @staticmethod
    def arp_scan(network):
        hosts = []
        try:
            arp_request = ARP(pdst=str(network))
            broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast / arp_request
            answered_list = srp(arp_request_broadcast, timeout=0.4, verbose=False)[0]

            for sent, received in answered_list:
                mac = received.hwsrc
                vendor = MACVendorLookup.get_vendor(mac) if mac else None
                hosts.append({
                    'ip': received.psrc,
                    'mac': mac,
                    'vendor': vendor,
                    'name': HostScanner.get_hostname(received.psrc),
                    'snmp_info': None
                })
        except Exception as e:
            print(f"ARP scan error: {e}")
        return hosts

    @staticmethod
    def ping_scan(network):
        hosts = []
        ping_cmd = ['ping', '-n', '1', '-w', str(int(PING_TIMEOUT * 1000))] if platform.system() == 'Windows' else ['ping', '-c', '1', '-W', str(PING_TIMEOUT), '-i', '0.2']
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(HostScanner.check_host, ip, ping_cmd): ip for ip in network.hosts()}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    hosts.append(result)
        return hosts

    @staticmethod
    def scan_host(ip_str):
        mac = get_mac_address(ip=ip_str)
        vendor = MACVendorLookup.get_vendor(mac) if mac else None
        return {
            'ip': ip_str,
            'mac': mac,
            'vendor': vendor,
            'name': HostScanner.get_hostname(ip_str),
            'snmp_info': None
        }
