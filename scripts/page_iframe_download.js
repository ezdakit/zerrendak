const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function captureIframeContent(url, aux_folder, file_name) {
  console.log('Iniciando captura de contenido del iframe...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  console.log('Navegador iniciado.');

  // Construye la URL completa con el parámetro accept
  const fullUrl = `${url}?accept=1`;

  console.log(`Navegando a: ${fullUrl}`);

  try {
      await page.goto(fullUrl, { timeout: 20000 }); // 20s el tiempo de espera
      console.log('Navegación completada con éxito en el primer intento.');
  } catch (error) {
      console.error('Error en el primer intento de navegación:', error);
      
      // Solo si el primer intento falla, ejecutar el segundo con más tiempo
      try {
          console.log('Intentando segundo intento con timeout extendido...');
          await page.goto(fullUrl, { timeout: 40000 }); // 40s el tiempo de espera
          console.log('Navegación completada con éxito en el segundo intento.');
      } catch (error) {
          console.error('Error también en el segundo intento de navegación:', error);
          // Continuar con la ejecución, incluso si ambos intentos fallan
      }
  }

  try {
      console.log('Esperando selector del iframe');
      await page.waitForSelector('iframe#inner-iframe', {timeout: 10000}); //10 seconds timeout
      const iframe = await page.frameLocator('iframe#inner-iframe');
      console.log('Selector del iframe encontrado');

      // Espera explícita para asegurar que el contenido dinámico se cargue
      await page.waitForTimeout(20000); // Espera 20 segundos

      // Crea el directorio auxiliar si no existe
      const aux_path = path.join(__dirname, '..', aux_folder);
      if (!fs.existsSync(aux_path)) {
          fs.mkdirSync(aux_path);
          console.log(`Directorio '${aux_path}' creado.`);
      }

      try {
          const content = await iframe.locator('body').innerHTML();
          const filePath = path.join(aux_path, `${file_name}`);
          fs.writeFileSync(filePath, content);
          console.log(`Contenido capturado y guardado en ${filePath}.`);
      } catch (error) {
          console.error(`Error al capturar el contenido del iframe`, error);
      }

  } catch (error) {
      console.error('Error al procesar el iFrame:', error);
  }
  
  console.log('Cerrando el navegador.');
  await browser.close();

  console.log('Captura de contenido del iframe completada.');
}

// Obtener los argumentos de la línea de comandos
const url = process.argv[2];
const aux_folder = process.argv[3];
const file_name = process.argv[4]
captureIframeContent(url, aux_folder, file_name);
