class MACVendorLookup:
    """Realiza resolução de fabricante a partir do endereço MAC.

    Primeiro tenta uma tabela local de OUIs comuns.
    Caso não encontre, faz uma consulta rápida à API pública macvendors.com.
    Caso a consulta falhe, retorna "Unknown".
    """

    LOCAL_OUI = {
        '00:1A:2B': 'Cisco',
        '00:1B:63': 'Apple',
        '00:1C:B3': 'Dell',
        '00:09:6B': 'Intel',
        '00:0C:29': 'VMware',
        '00:50:56': 'VMware',
        'F4:5C:89': 'Samsung',
        '3C:5A:B4': 'Google',
        'FC:FB:FB': 'Amazon',
        '00:15:5D': 'Microsoft',
        'B8:27:EB': 'Raspberry Pi',
        'DC:A6:32': 'TP-Link',
        'D8:CB:8A': 'Xiaomi',
        '00:1E:C2': 'Hewlett Packard',
        '00:21:5A': 'ASUSTek',
        '00:25:9C': 'Hon Hai (Foxconn)',
        '00:0D:93': 'Sony',
        '00:13:CE': 'Nintendo',
        '00:17:88': 'LG',
        '00:18:82': 'Motorola',
        '00:1D:D8': 'Lenovo',
        '00:1D:72': 'Acer',
    }

    @staticmethod
    def get_vendor(mac: str) -> str:
        """Tenta descobrir o fabricante associado a um endereço MAC."""
        if not mac:
            return "Unknown"

        try:
            oui_parts = mac.upper().replace('-', ':').replace('.', ':').split(':')[:3]
            if len(oui_parts) < 3:
                return "Unknown"
            oui = ':'.join(oui_parts)

            # Primeiro tenta tabela local
            if oui in MACVendorLookup.LOCAL_OUI:
                return MACVendorLookup.LOCAL_OUI[oui]

            # Fallback: consulta rápida API pública (timeout curto)
            import urllib.request
            url = f'https://api.macvendors.com/{"-".join(oui_parts)}'
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    vendor = response.read().decode().strip()
                    return vendor if vendor else "Unknown"
            except Exception:
                pass
        except Exception:
            pass

        return "Unknown" 