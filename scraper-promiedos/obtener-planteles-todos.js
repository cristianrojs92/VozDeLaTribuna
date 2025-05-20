const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const { extraerDatosPlantel } = require('./extraer-plantel.js');

const BASE_URL = 'https://www.promiedos.com.ar';
// Actualizada la ruta al archivo JSON con información de equipos
const EQUIPOS_INFO_PATH = path.join(__dirname, 'equipos', 'info_equipos.json'); 
const OUTPUT_DIR = path.join(__dirname, 'planteles'); // Usamos __dirname para asegurar la ruta correcta

// Función para crear un nombre de archivo "slug" a partir del nombre del equipo
function slugify(text) {
    if (!text) return 'equipo-desconocido';
    return text.toString().toLowerCase()
        .replace(/\s+/g, '-')           // Reemplazar espacios con -
        .replace(/[^\w-]+/g, '')       // Quitar caracteres no alfanuméricos (excepto guiones)
        .replace(/--+/g, '-')         // Reemplazar múltiples guiones con uno solo
        .replace(/^-+/, '')             // Quitar guiones al inicio
        .replace(/-+$/, '');            // Quitar guiones al final
}

// Extrae la parte del slug de la URL del equipo
function extractSlugFromUrl(url) {
    // Ejemplo de URL: https://www.promiedos.com.ar/team/river-plate/igi
    // Queremos extraer "river-plate"
    const parts = url.split('/');
    if (parts.length >= 2) {
        return parts[parts.length - 2]; // El penúltimo elemento debe ser el slug
    }
    return null;
}

async function obtenerTodosLosPlanteles() {
    console.log(`Asegurando que el directorio de salida exista: ${OUTPUT_DIR}`);
    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
        console.log(`Directorio creado: ${OUTPUT_DIR}`);
    }

    // Asegurar que el directorio de equipos existe
    const equiposDir = path.dirname(EQUIPOS_INFO_PATH);
    if (!fs.existsSync(equiposDir)) {
        fs.mkdirSync(equiposDir, { recursive: true });
        console.log(`Directorio de equipos creado: ${equiposDir}`);
    }

    let browser;
    try {
        // Leer el archivo JSON con la información de los equipos
        console.log(`Leyendo información de equipos desde: ${EQUIPOS_INFO_PATH}`);
        
        if (!fs.existsSync(EQUIPOS_INFO_PATH)) {
            // Si el archivo no existe en la nueva ubicación, intentar copiarlo de la ubicación anterior
            const oldPath = path.join(__dirname, '..', 'info_equipos.json');
            if (fs.existsSync(oldPath)) {
                console.log(`Copiando archivo de equipos desde ${oldPath} a ${EQUIPOS_INFO_PATH}...`);
                fs.copyFileSync(oldPath, EQUIPOS_INFO_PATH);
                console.log('Archivo copiado exitosamente.');
            } else {
                throw new Error(`El archivo de información de equipos no existe en ninguna ubicación: ${EQUIPOS_INFO_PATH}`);
            }
        }
        
        const equiposInfoRaw = fs.readFileSync(EQUIPOS_INFO_PATH, 'utf8');
        const equiposInfo = JSON.parse(equiposInfoRaw);
        
        if (!Array.isArray(equiposInfo) || equiposInfo.length === 0) {
            throw new Error('El archivo de información de equipos no contiene datos válidos.');
        }
        
        console.log(`Se cargaron ${equiposInfo.length} equipos desde el archivo JSON.`);
        
        // Iniciar Puppeteer
        console.log('Iniciando Puppeteer...');
        browser = await puppeteer.launch({ 
            headless: true, // 'new' es la opción moderna, true es compatible con versiones anteriores
            args: ['--no-sandbox', '--disable-setuid-sandbox'] // Común para entornos CI/contenedores
        });
        
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        
        // Procesar cada equipo
        for (const equipo of equiposInfo) {
            if (!equipo.url || !equipo.nombre) {
                console.warn(`Equipo omitido por falta de URL o nombre: ${JSON.stringify(equipo)}`);
                continue;
            }
            
            const nombreEquipo = equipo.nombreCompleto || equipo.nombre;
            
            // Obtener el slug desde la URL para nombrar el archivo
            const slug = extractSlugFromUrl(equipo.url);
            if (!slug) {
                console.warn(`No se pudo extraer el slug de la URL: ${equipo.url}`);
                continue;
            }
            
            const filePath = path.join(OUTPUT_DIR, `${slug}_plantel.json`);
            console.log(`Procesando equipo: ${nombreEquipo} (${equipo.url})`);
            
            try {
                await page.goto(equipo.url, { waitUntil: 'networkidle2', timeout: 90000 }); // Aumentado timeout
                const htmlContent = await page.content();
                
                console.log(`Extrayendo plantel para ${nombreEquipo}...`);
                const plantelData = extraerDatosPlantel(htmlContent);

                if (plantelData && plantelData.length > 0) {
                    // Añadir información adicional del equipo
                    const plantelEnriquecido = plantelData.map(jugador => ({
                        ...jugador,
                        equipo: nombreEquipo,
                        equipoSlug: slug,
                        urlEquipo: equipo.url
                    }));
                    
                    fs.writeFileSync(filePath, JSON.stringify(plantelEnriquecido, null, 2));
                    console.log(`Plantel de ${nombreEquipo} guardado en ${filePath}`);
                } else {
                    console.log(`No se extrajeron datos del plantel para ${nombreEquipo}, o la sección 'PLANTEL' no fue encontrada en la página.`);
                }
            } catch (err) {
                console.error(`Error procesando el equipo ${nombreEquipo} (${equipo.url}): ${err.message}`);
            }
            
            const delay = 2000 + Math.random() * 2500; // Delay aleatorio para evitar sobrecarga
            console.log(`Esperando ${Math.round(delay/1000)}s...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }

        console.log('Proceso completado.');

    } catch (error) {
        console.error(`Error general en el script: ${error}`);
        if (error.stack) {
            console.error(error.stack);
        }
    } finally {
        if (browser) {
            console.log('Cerrando navegador...');
            await browser.close();
        }
    }
}

obtenerTodosLosPlanteles(); 