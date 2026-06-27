import argparse

def is_valid_ip(ip):
    parts = ip.strip().split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def get_ip_class(ip):
    first_octet = int(ip.split('.')[0])
    if 1 <= first_octet <= 126:
        return 'Class A'
    elif 128 <= first_octet <= 191:
        return 'Class B'
    elif 192 <= first_octet <= 223:
        return 'Class C'
    elif 224 <= first_octet <= 239:
        return 'Class D (Multicast)'
    elif 240 <= first_octet <= 254:
        return 'Class E (Reserved)'
    else:
        return 'Invalid Class'

def is_private_ip(ip):
    octets = list(map(int, ip.split('.')))
    if octets[0] == 10:
        return True
    elif octets[0] == 172 and 16 <= octets[1] <= 31:
        return True
    elif octets[0] == 192 and octets[1] == 168:
        return True
    return False

def analyze_ip(ip):
    if not is_valid_ip(ip):
        return f"❌ Invalid IP: {ip}"
    
    ip_class = get_ip_class(ip)
    privacy = "Private" if is_private_ip(ip) else "Public"
    return f"✅ IP: {ip} | {ip_class} | {privacy}"

def main():
    parser = argparse.ArgumentParser(description="IP Analyzer: Private/Public + Class Identifier")
    parser.add_argument("ip", help="IP address to analyze")
    args = parser.parse_args()

    result = analyze_ip(args.ip)
    print(result)

if __name__ == "__main__":
    main()

