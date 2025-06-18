import subprocess
import re

class SNMPHelper:
    OIDS = {
        'Descrição do Sistema': '1.3.6.1.2.1.1.1.0',
        'Object ID': '1.3.6.1.2.1.1.2.0',
        'Tempo de Atividade': '1.3.6.1.2.1.1.3.0',
        'Nome SNMP': '1.3.6.1.2.1.1.5.0',
        'Contato': '1.3.6.1.2.1.1.4.0',
        'Serviços': '1.3.6.1.2.1.1.7.0',
        'Número de Interfaces': '1.3.6.1.2.1.2.1.0',
        'CPU Idle (%)': '1.3.6.1.4.1.2021.11.11.0',
        'Memória Total (kB)': '1.3.6.1.4.1.2021.4.5.0',
        'Memória Livre (kB)': '1.3.6.1.4.1.2021.4.6.0',
    }

    @staticmethod
    def snmp_get(ip, community, oid):
        try:
            result = subprocess.check_output(
                ['snmpget', '-v1', '-c', community, ip, oid],
                stderr=subprocess.STDOUT
            ).decode(errors='ignore')
            match = re.search(r'=\s+\w+:\s+(.+)', result)
            if match:
                return match.group(1).strip()
            return result.strip()
        except Exception:
            return None

    @classmethod
    def get_all_info(cls, ip, community='public'):
        info = {}
        for desc, oid in cls.OIDS.items():
            value = cls.snmp_get(ip, community, oid)
            if value:
                info[desc] = value
        return info
