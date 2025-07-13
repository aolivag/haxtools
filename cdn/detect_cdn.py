#!/usr/bin/env python3
import requests
import socket
import dns.resolver
import whois
import argparse

# Diccionario de firmas conocidas de CDN/WAF
# Se comprueban cabeceras, CNAMEs y servidores de nombres (NS)
SIGNATURES = {
    "Cloudflare": {
        "headers": {"server": "cloudflare", "cf-ray": ""},
        "cnames": ["cloudflare.net", ".cdn.cloudflare.net"],
        "nameservers": ["cloudflare.com"]
    },
    "Sucuri": {
        "headers": {"server": "sucuri", "x-sucuri-id": ""},
        "cnames": ["sucuri.net"],
        "nameservers": ["sucuri.net"]
    },
    "Akamai": {
        "headers": {"server": "AkamaiGHost", "x-akamai-transformed": ""},
        "cnames": ["akamai.net", "akamaiedge.net", "akamaitechnologies.com"],
        "nameservers": ["akamaidns.net", "akam.net"]
    },
    "AWS CloudFront / Route 53": {
        "headers": {"via": "CloudFront", "x-amz-cf-id": ""},
        "cnames": ["cloudfront.net"],
        "nameservers": ["awsdns"]
    },
    "Fastly": {
        "headers": {"x-served-by": "", "x-cache": "HIT"},
        "cnames": ["fastly.net"],
        "nameservers": ["fastly.net"]
    },
    "Incapsula": {
        "headers": {"x-iinfo": ""},
        "cnames": ["incapdns.net"],
        "nameservers": ["incapdns.net"]
    },
    "Google Cloud CDN": {
        "headers": {"via": "1.1 google"},
        "cnames": [],
        "nameservers": ["google.com"]
    },
    "BunnyCDN": {
        "headers": {"server": "BunnyCDN"},
        "cnames": ["b-cdn.net"],
        "nameservers": ["bunny.net"]
    },
    "StackPath": {
        "headers": {"server": "StackPath_Nginx"},
        "cnames": ["stackpathdns.com"],
        "nameservers": ["stackpathdns.com"]
    }
}

def get_domain_from_url(url):
    """Extrae el nombre de dominio de una URL."""
    if "://" in url:
        url = url.split('://')[1]
    url = url.split('/')[0]
    return url

def check_cdn(url):
    """
    Analiza un sitio web para identificar su CDN o WAF usando múltiples técnicas.
    """
    domain = get_domain_from_url(url)
    full_url = f"https://{domain}"
    
    # 1. Comprobar cabeceras HTTP
    try:
        headers_req = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(full_url, headers=headers_req, timeout=10, allow_redirects=True, verify=True)
        response_headers = {k.lower(): v.lower() for k, v in response.headers.items()}

        for name, sigs in SIGNATURES.items():
            for header, value in sigs.get("headers", {}).items():
                if header in response_headers:
                    if not value or value in response_headers[header]:
                        return f"Sitio probablemente protegido por: {name} (detectado por cabecera: {header})"
    except requests.exceptions.RequestException as e:
        print(f"Aviso: No se pudo comprobar las cabeceras HTTP: {e}")

    # 2. Comprobar CNAME
    try:
        cname = socket.getfqdn(domain)
        if cname and cname != domain:
            for name, sigs in SIGNATURES.items():
                for cname_sig in sigs.get("cnames", []):
                    if cname_sig in cname:
                        return f"Sitio probablemente protegido por: {name} (detectado por CNAME: {cname})"
    except socket.gaierror:
        return f"Error: No se pudo resolver el dominio {domain}. Verifica el nombre del sitio."
    except Exception as e:
        print(f"Aviso: Ocurrió un error al comprobar CNAME: {e}")

    # 3. Comprobar registros NS (DNS)
    try:
        resolver = dns.resolver.Resolver(configure=False) # Evitar que intente leer /etc/resolv.conf
        resolver.nameservers = ['8.8.8.8'] # Usar un servidor DNS público
        ns_records = resolver.resolve(domain, 'NS')
        for record in ns_records:
            ns_server = str(record).rstrip('.')
            for name, sigs in SIGNATURES.items():
                for ns_sig in sigs.get("nameservers", []):
                    if ns_sig in ns_server:
                        return f"Sitio probablemente protegido por: {name} (detectado por registro NS: {ns_server})"
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout) as e:
        print(f"Aviso: No se pudieron obtener los registros NS: {e}")
    except Exception as e:
        print(f"Aviso: Ocurrió un error al comprobar NS: {e}")

    # 4. Comprobar Nameservers en WHOIS
    try:
        w = whois.whois(domain)
        if w.name_servers:
            for ns_server in w.name_servers:
                ns_server = ns_server.lower()
                for name, sigs in SIGNATURES.items():
                    for ns_sig in sigs.get("nameservers", []):
                        if ns_sig in ns_server:
                            return f"Sitio probablemente protegido por: {name} (detectado por WHOIS Nameserver: {ns_server})"
    except Exception as e:
        print(f"Aviso: No se pudo realizar la consulta WHOIS o no se encontraron nameservers: {e}")

    return "No se pudo identificar un CDN o WAF conocido con los métodos actuales."

def main():
    """Función principal para ejecutar el script."""
    parser = argparse.ArgumentParser(description="Identifica el CDN o WAF de un sitio web.")
    parser.add_argument("sitio", nargs='?', help="El sitio web a analizar (ej: example.com)")
    args = parser.parse_args()

    print("--- Identificador de CDN y WAF ---")

    target_site = args.sitio
    if not target_site:
        try:
            target_site = input("Introduce el sitio web a analizar (ej: example.com): ")
        except EOFError:
            print("\nNo se recibió ninguna entrada. Finalizando.")
            return

    if not target_site:
        parser.print_help()
        return

    result = check_cdn(target_site)
    print(result)

if __name__ == "__main__":
    main()
