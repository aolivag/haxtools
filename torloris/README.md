# TorLoris

TorLoris es una herramienta de prueba de estrés de bajo ancho de banda que utiliza la red Tor para anonimizar el ataque. El script implementa el ataque Slowloris, que consiste en abrir múltiples conexiones con un servidor web y mantenerlas abiertas el mayor tiempo posible, agotando así los recursos del servidor.

## Características

- **Ataque Slowloris:** Implementa el clásico ataque Slowloris para pruebas de estrés.
- **Anonimato con Tor:** Enruta todo el tráfico a través de la red Tor para proteger la identidad del usuario.
- **Detección y arranque de Tor:** Verifica si Tor se está ejecutando y, de no ser así, intenta iniciarlo automáticamente.
- **Barra de progreso:** Muestra una barra de progreso con `tqdm` para visualizar el estado del ataque.
- **Entrada interactiva:** Si no se proporciona una URL como argumento, el script la solicitará de forma interactiva.
- **Configurable:** Permite configurar el host, el puerto, el número de sockets y otros parámetros a través de la línea de comandos.

## Requisitos

- Python 3.x
- `tqdm`
- Tor

## Instalación

1. Clona el repositorio:
   ```sh
   git clone https://github.com/H4X-Tools/TorLoris.git
   cd TorLoris
   ```

2. Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```

3. Asegúrate de que Tor esté instalado en tu sistema. Puedes descargarlo desde [aquí](https://www.torproject.org/download/).

## Uso

Para ejecutar el script, utiliza el siguiente comando:

```sh
python slow.py <host> [opciones]
```

### Argumentos

- `host`: El host sobre el que se realizará la prueba de estrés.

### Opciones

- `-p, --port`: Puerto del servidor web (por defecto: 80).
- `-s, --sockets`: Número de sockets a utilizar en la prueba (por defecto: 150).
- `-v, --verbose`: Aumenta el nivel de logging.
- `-ua, --randuseragents`: Randomiza los user-agents en cada petición.
- `--https`: Utiliza HTTPS para las peticiones.
- `--sleeptime`: Tiempo de espera entre cada cabecera enviada (por defecto: 15).

### Ejemplo

```sh
python slow.py example.com -s 200 --https
```

## Descargo de responsabilidad

Esta herramienta ha sido creada con fines educativos y de investigación. El autor no se hace responsable del mal uso que se le pueda dar. Utilízala bajo tu propia responsabilidad.
