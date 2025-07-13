# Identificador de CDN y WAF

Este script de Python (`detect_cdn.py`) te ayuda a identificar si un sitio web está utilizando un servicio de CDN (Content Delivery Network) o WAF (Web Application Firewall) basándose en varias técnicas de detección.

## Características

- **Análisis de Cabeceras HTTP:** Examina las cabeceras de respuesta HTTP en busca de firmas conocidas de CDN/WAF.
- **Comprobación de Registros CNAME:** Busca patrones en los registros CNAME del dominio que apunten a servicios de CDN.
- **Análisis de Registros NS (DNS):** Consulta los servidores de nombres (NS) del dominio para identificar proveedores de CDN/WAF.
- **Consulta WHOIS:** Extrae los servidores de nombres de la información WHOIS del dominio para una detección adicional.

## Instalación

Para ejecutar este script, necesitarás Python 3 y las siguientes librerías. Puedes instalarlas usando `pip`:

```bash
pip install requests dnspython python-whois
```

## Uso

El script puede ejecutarse de dos maneras:

1.  **Interactivo:** Si ejecutas el script sin argumentos, te pedirá que introduzcas el sitio web a analizar.

    ```bash
    python3 detect_cdn.py
    ```

2.  **Con argumento:** Puedes pasar el sitio web directamente como un argumento al script.

    ```bash
    python3 detect_cdn.py example.com
    ```

    Reemplaza `example.com` con el dominio que deseas analizar.

## Ejemplos

```bash
python3 detect_cdn.py cloudflare.com
# Salida esperada: Sitio probablemente protegido por: Cloudflare (detectado por cabecera: server)

python3 detect_cdn.py sucuri.net
# Salida esperada: Sitio probablemente protegido por: Sucuri (detectado por cabecera: server)
```

## Firmas Soportadas

El script incluye firmas para los siguientes CDN/WAFs:

-   Cloudflare
-   Sucuri
-   Akamai
-   AWS CloudFront / Route 53
-   Fastly
-   Incapsula
-   Google Cloud CDN
-   BunnyCDN
-   StackPath

## Contribuciones

¡Las contribuciones son bienvenidas! Si conoces nuevas firmas de CDN/WAF o tienes ideas para mejorar la detección, no dudes en abrir un issue o enviar un pull request.
