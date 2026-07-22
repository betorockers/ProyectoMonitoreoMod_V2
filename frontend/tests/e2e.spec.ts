import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Argos Guard Enterprise E2E', () => {
  const screenshotsDir = path.join(__dirname, '../../docs/manual/capturas');
  
  test.beforeAll(() => {
    if (!fs.existsSync(screenshotsDir)) {
      fs.mkdirSync(screenshotsDir, { recursive: true });
    }
  });

  test('Flujo Completo de Setup, Login y Pruebas Duras', async ({ page }) => {
    // 1. Setup Wizard
    await page.goto('/');
    
    // Wait for the initialization to finish
    await page.waitForFunction(() => {
      return !document.body.innerText.includes('INICIALIZANDO TERMINAL...');
    }, { timeout: 15000 });
    await page.waitForTimeout(1000); // Give it a sec to render
    
    // Check if we are on the setup page
    const isSetup = await page.isVisible('text="Inicialización del Sistema"');
    
    if (isSetup) {
      console.log("Ejecutando Setup Wizard...");
      await page.fill('input[placeholder="Nombre Real del Usuario"]', 'omar toledo');
      await page.fill('input[placeholder="Nombre de Usuario (Login)"]', 'BetoDev');
      await page.fill('input[placeholder="Contraseña Maestra"]', '@B3t0R0ck3rs');
      await page.fill('input[placeholder="Confirmar Contraseña"]', '@B3t0R0ck3rs');
      await page.fill('input[placeholder="ARGOS-XXXX-XXXX-XXXX-XXXX"]', 'ARGOS-DEV-9GVN-ZI53-FMQY');
      
      await page.screenshot({ path: path.join(screenshotsDir, '01_setup_wizard.png') });
      await page.click('button:has-text("INICIALIZAR SISTEMA")');
      await page.waitForTimeout(4000);
    }
    
    // 2. Login
    console.log("Login...");
    await page.goto('/');
    await page.waitForFunction(() => {
      return !document.body.innerText.includes('INICIALIZANDO TERMINAL...');
    }, { timeout: 15000 });
    await page.waitForTimeout(1000);

    const isLogin = await page.isVisible('text="Argos Guard Enterprise"');
    if (isLogin) {
      await page.fill('input[placeholder="Identificación de Usuario"]', 'BetoDev');
      await page.fill('input[placeholder="Código de Acceso"]', '@B3t0R0ck3rs');
      await page.screenshot({ path: path.join(screenshotsDir, '02_login.png') });
      await page.click('button:has-text("Inicializar Enlace")');
    }
    
    // Wait for Dashboard to load
    console.log("Esperando Dashboard...");
    await expect(page.locator('text="Monitoreo Activo"')).toBeVisible({ timeout: 15000 });
    await page.screenshot({ path: path.join(screenshotsDir, '03_dashboard.png') });

    // 3. Modulo OSINT - RUT
    console.log("Probando OSINT RUT...");
    await page.click('text="OSINT"');
    await expect(page.locator('text="OSINT & WEB ANALYTICS"')).toBeVisible();
    
    await page.click('button:has-text("RUT")');
    await page.fill('input[placeholder="Ej: 12345678-9"]', '16691169-9');
    await page.click('button:has-text("BUSCAR")');
    
    // Wait for the table to render (OSINT scraping can take a bit)
    await expect(page.locator('text="DATOS DE INTELIGENCIA OBTENIDOS"')).toBeVisible({ timeout: 60000 });
    await page.screenshot({ path: path.join(screenshotsDir, '04_osint_rut_result.png') });
    
    // 4. Modulo OSINT - PPU
    console.log("Probando OSINT PPU...");
    await page.click('text="PPU"');
    await page.fill('input[placeholder="Ej: AB1234 o ABCD12"]', 'RJWX98');
    await page.click('button:has-text("BUSCAR")');
    await page.waitForTimeout(3000); // Give it a sec to show "Analizando..."
    await expect(page.locator('text="DATOS DE INTELIGENCIA OBTENIDOS"')).toBeVisible({ timeout: 35000 });
    await page.screenshot({ path: path.join(screenshotsDir, '05_osint_ppu.png') });
    
    // 5. Configuración y Telegram
    console.log("Configurando Telegram y Equipos...");
    await page.click('text="Configuración"');
    await page.click('button:has-text("Notificaciones")'); 
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(screenshotsDir, '06_config_panel.png') });
    
    // Fill telegram token
    await page.fill('input[placeholder="1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxx"]', '8967512488:AAGIcJfbd7ui19ROj5psNb9rmqcKELTbjQY');
    await page.fill('input[placeholder="-100xxxxxxxxx"]', '8036765324');
    await page.click('button:has-text("Guardar Credenciales")');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Probar Conexión")');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotsDir, '07_config_telegram.png') });
    
    // 6. Agregar equipo para monitoreo activo
    await page.click('text="Monitoreo Activo"');
    await page.fill('input[placeholder="ej. 192.168.1.1 o betograf.cl"]', '8.8.8.8');
    await page.fill('input[placeholder="ej. Servidor Core"]', 'Google DNS Test');
    await page.click('button:has-text("Registrar")');
    await page.waitForTimeout(4000); // wait for ping/geomap metadata to fetch
    await page.screenshot({ path: path.join(screenshotsDir, '08_add_target.png') });

    // 7. Mapa Táctico - Traceroute
    console.log("Probando Mapa Táctico...");
    await page.click('text="Mapa Táctico"');
    // wait for map to load
    await page.waitForSelector('.leaflet-container');
    await page.waitForTimeout(3000);
    
    // Encontrar y hacer clic en el marcador (asumiendo que 8.8.8.8 tiene lat/lon y Leaflet renderizó un CircleMarker con path)
    const marker = page.locator('path.leaflet-interactive').first();
    if (await marker.isVisible()) {
      await marker.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: path.join(screenshotsDir, '09_tactical_map_popup.png') });
      
      const traceButton = page.locator('button:has-text("Traceroute Map")');
      if (await traceButton.isVisible()) {
         await traceButton.click();
         console.log("Esperando Traceroute (hasta 60s)...");
         // wait for trace to finish (button text goes back from 'Trazando...' to 'Traceroute Map' or similar)
         await page.waitForTimeout(15000);
         await page.screenshot({ path: path.join(screenshotsDir, '10_tactical_map_traceroute.png') });
      }
    }
    
    console.log("¡Pruebas E2E Completadas!");
  });
});
