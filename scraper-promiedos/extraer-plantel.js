const fs = require('fs');
const cheerio = require('cheerio');

// Ya no se definen aquí HTML_FILE_PATH y OUTPUT_JSON_PATH como constantes globales para el script principal

function extraerDatosPlantel(htmlContent) {
    const $ = cheerio.load(htmlContent);
    const plantel = [];
    let categoriaActual = '';

    const plantelBlock = $('div.content-block__header:contains("PLANTEL")').parent();

    if (plantelBlock.length === 0) {
        // En lugar de console.log, podríamos devolver un error o un array vacío y dejar que quien llama maneje el log
        // console.log("No se encontró el bloque del plantel con el encabezado 'PLANTEL'.");
        return plantel; // Opcionalmente: throw new Error("Bloque de plantel no encontrado");
    }

    const tablaPlantel = plantelBlock.find('table.table-block.table_table__LTgjZ.table');

    if (tablaPlantel.length === 0) {
        // console.log("No se encontró la tabla del plantel.");
        return plantel; // Opcionalmente: throw new Error("Tabla de plantel no encontrada");
    }

    tablaPlantel.find('tbody.tbody_tablebody__cDt0I tr').each((i, el) => {
        const $row = $(el);
        const $firstCell = $row.find('td').first();

        if ($firstCell.attr('colspan') === '4' && $firstCell.hasClass('td_green__SfXLh')) {
            categoriaActual = $firstCell.text().trim();
        } else if ($row.hasClass('row_row_type2__uX1vx')) {
            const jugador = {};
            const playerInfoCell = $row.find('td').eq(0);
            
            jugador.numero = playerInfoCell.find('div.player-table_numberBlock__GM5w4').clone().children().remove().end().text().trim() || 'N/A';
            const paisImg = playerInfoCell.find('div.player-table_countryBlock__E8V4p img');
            jugador.pais = paisImg.length ? paisImg.attr('alt') : 'N/A';
            jugador.nombre = playerInfoCell.find('p.player-table_title__cUnIu').text().trim();
            jugador.posicionEspecifica = playerInfoCell.find('p.player-table_text__Htlo6').text().trim();
            
            jugador.edad = $row.find('td').eq(1).text().trim();
            jugador.nacimiento = $row.find('td').eq(2).text().trim();
            jugador.altura = $row.find('td').eq(3).text().trim();
            jugador.categoriaGeneral = categoriaActual;

            if (categoriaActual === 'Dir' && jugador.posicionEspecifica === 'Entrenador') {
                 jugador.numero = playerInfoCell.find('div.player-table_numberBlock__GM5w4.player-table_staff__yqbGR').clone().children().remove().end().text().trim() || 'DT';
            }
            plantel.push(jugador);
        }
    });

    return plantel;
}

// Exportar la función para que pueda ser utilizada por otros módulos
module.exports = { extraerDatosPlantel };

// El siguiente bloque solo se ejecutará si el script se corre directamente
// y no cuando es importado por otro módulo (require.main === module)
if (require.main === module) {
    const HTML_FILE_PATH_TEST = './boca_ejemplo.html'; // Ruta para prueba
    const OUTPUT_JSON_PATH_TEST = './plantel_boca_ejemplo_test.json'; // Archivo de salida para prueba

    fs.readFile(HTML_FILE_PATH_TEST, 'utf8', (err, htmlContent) => {
        if (err) {
            console.error(`Error al leer el archivo HTML de prueba: ${err}`);
            return;
        }

        try {
            const datosPlantel = extraerDatosPlantel(htmlContent);

            if (datosPlantel.length > 0) {
                fs.writeFile(OUTPUT_JSON_PATH_TEST, JSON.stringify(datosPlantel, null, 2), (writeErr) => {
                    if (writeErr) {
                        console.error(`Error al escribir el archivo JSON de prueba: ${writeErr}`);
                    } else {
                        console.log(`Los datos del plantel de prueba se han guardado en: ${OUTPUT_JSON_PATH_TEST}`);
                    }
                });
            } else {
                console.log('No se extrajeron datos del plantel en la prueba o el bloque/tabla no fue encontrado.');
            }
        } catch (error) {
            console.error(`Error al extraer datos del plantel en la prueba: ${error.message}`);
        }
    });
} 