# Scraper de Planteles de Promiedos

Este proyecto es un scraper que obtiene automáticamente los datos de los planteles de los equipos de la Liga Profesional Argentina desde la página [Promiedos](https://www.promiedos.com.ar/).

## Características

- Obtiene información completa de los planteles de todos los equipos
- Utiliza URLs preconfiguradas para acceder directamente a la página de cada equipo
- Extrae datos de jugadores como nombre, número, posición, edad, fecha de nacimiento y altura
- Guarda la información en archivos JSON individuales para cada equipo

## Requisitos

- Node.js (versión 14 o superior)
- npm

## Instalación

1. Clona o descarga este repositorio
2. Navega al directorio del proyecto
3. Instala las dependencias:

```bash
npm install
```

## Uso

Para obtener los planteles de todos los equipos, ejecuta:

```bash
node obtener-planteles-todos.js
```

El script leerá la información de los equipos desde el archivo `equipos/info_equipos.json`, visitará la página de cada equipo y extraerá los datos del plantel, guardando los resultados en la carpeta `planteles/`.

## Estructura del Proyecto

- `obtener-planteles-todos.js`: Script principal para obtener los planteles de todos los equipos
- `extraer-plantel.js`: Módulo que extrae los datos del plantel de una página HTML
- `equipos/info_equipos.json`: Archivo con información de los equipos, incluyendo sus URLs
- `planteles/`: Directorio donde se guardan los datos de los planteles extraídos
- `package.json`: Configuración del proyecto y dependencias

## Estructura de los Datos

### Archivo de entrada (equipos/info_equipos.json)

```json
[
  {
    "posicion": "1",
    "nombre": "River",
    "url": "https://www.promiedos.com.ar/team/river-plate/igi",
    "nombreCompleto": "River Plate",
    "proximosPartidos": [...],
    "seccionesDisponibles": [...]
  },
  {
    "posicion": "2",
    "nombre": "Boca Jrs.",
    "url": "https://www.promiedos.com.ar/team/boca-juniors/igg",
    "nombreCompleto": "Boca Juniors",
    "proximosPartidos": [...],
    "seccionesDisponibles": [...]
  },
  ...
]
```

### Archivos de salida (planteles/<nombre-equipo>_plantel.json)

```json
[
  {
    "numero": "1",
    "pais": "Argentina",
    "nombre": "Franco Armani",
    "posicionEspecifica": "Portero",
    "edad": "37",
    "nacimiento": "16/10/1986",
    "altura": "1,89",
    "categoriaGeneral": "Arqueros",
    "equipo": "River Plate",
    "equipoSlug": "river-plate",
    "urlEquipo": "https://www.promiedos.com.ar/team/river-plate/igi"
  },
  ...
]
```

## Tecnologías Utilizadas

- [Puppeteer](https://pptr.dev/): Biblioteca de Node.js que proporciona una API de alto nivel para controlar Chrome/Chromium
- [Cheerio](https://cheerio.js.org/): Implementación de jQuery para el servidor, facilita el análisis de HTML
- [fs](https://nodejs.org/api/fs.html): Módulo nativo de Node.js para interactuar con el sistema de archivos
- [path](https://nodejs.org/api/path.html): Módulo nativo de Node.js para manejar rutas de archivos

## Configuración

El script está configurado para:

- Esperar a que las páginas se carguen completamente antes de extraer datos
- Usar tiempos de espera aleatorios entre solicitudes para evitar sobrecargar el servidor
- Usar un agente de usuario similar a un navegador normal para evitar bloqueos
- Manejar errores y continuar con el siguiente equipo si hay problemas con alguno

## Licencia

ISC