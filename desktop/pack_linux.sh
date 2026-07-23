#!/bin/bash
set -e

BaseDir=$(pwd)
BuildDir="$BaseDir/backend/build"
DistName="ArgosGuard-Linux-v3.6.4"
PackDir="$BaseDir/desktop/$DistName"

echo -e "\e[1;36m========================================\e[0m"
echo -e "\e[1;36m    Empaquetado Autónomo para Linux     \e[0m"
echo -e "\e[1;36m========================================\e[0m"

# 1. Verificar si el binario compilado existe
if [ ! -f "$BuildDir/ArgosGuard" ]; then
    echo -e "\e[1;31mError: No se encontró el binario compilado en $BuildDir/ArgosGuard.\e[0m"
    echo -e "\e[1;33mPor favor, ejecuta primero: ./build.sh\e[0m"
    exit 1
fi

# 2. Crear estructura limpia de distribución
echo -e "\n\e[1;33m[1/4] Creando estructura del paquete...\e[0m"
rm -rf "$PackDir"
mkdir -p "$PackDir/chrome"

# Copiar binario principal
cp "$BuildDir/ArgosGuard" "$PackDir/"
echo -e "\e[1;32m-> Binario copiado a $PackDir/ArgosGuard\e[0m"

# 3. Descargar Chromium y ChromeDriver Portable
echo -e "\n\e[1;33m[2/4] Preparando entorno Chromium portable (100% autocontenido)...\e[0m"

# Versión específica de Chrome for Testing estable y segura
CHROME_VER="126.0.6478.126"
CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VER/linux64/chrome-linux64.zip"
DRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VER/linux64/chromedriver-linux64.zip"

TempDir=$(mktemp -d)
cd "$TempDir"

echo "Descargando Chromium v$CHROME_VER..."
if wget -q --show-progress "$CHROME_URL"; then
    echo "Descargando ChromeDriver..."
    wget -q --show-progress "$DRIVER_URL"
    
    echo "Descomprimiendo recursos..."
    unzip -q chrome-linux64.zip
    unzip -q chromedriver-linux64.zip
    
    # Mover a la carpeta de empaquetado
    cp -r chrome-linux64/* "$PackDir/chrome/"
    cp chromedriver-linux64/chromedriver "$PackDir/chrome/"
    
    chmod +x "$PackDir/chrome/chrome"
    chmod +x "$PackDir/chrome/chromedriver"
    echo -e "\e[1;32m-> Chromium y ChromeDriver portables descargados y configurados.\e[0m"
else
    echo -e "\e[1;31mAdvertencia: No se pudo descargar Chromium portable automáticamente.\e[0m"
    echo -e "\e[1;33mEl paquete requerirá que el host tenga Google Chrome o Chromium instalado.\e[0m"
fi

rm -rf "$TempDir"
cd "$BaseDir"

# 4. Crear script lanzador (wrapper launcher)
echo -e "\n\e[1;33m[3/4] Creando script lanzador (ArgosGuardLauncher.sh)...\e[0m"
cat << 'EOF' > "$PackDir/ArgosGuardLauncher.sh"
#!/bin/bash
# Script de inicio para Argos Guard Enterprise con entorno de Chrome local
export CHROME_PATH="$(dirname "$0")/chrome/chrome"
export CHROMEDRIVER_PATH="$(dirname "$0")/chrome/chromedriver"

# Ejecutar el binario nativo
exec "$(dirname "$0")/ArgosGuard" "$@"
EOF

chmod +x "$PackDir/ArgosGuardLauncher.sh"
echo -e "\e[1;32m-> Lanzador creado.\e[0m"

# 5. Comprimir el paquete completo
echo -e "\n\e[1;33m[4/4] Comprimiendo distribución a .tar.gz...\e[0m"
cd "$BaseDir/desktop"
tar -czf "$DistName.tar.gz" "$DistName"
echo -e "\e[1;32m-> Paquete comprimido creado con éxito en: desktop/$DistName.tar.gz\e[0m"

cd "$BaseDir"
echo -e "\n\e[1;36m========================================\e[0m"
echo -e "\e[1;32m Empaquetado completo y 100% autónomo. \e[0m"
echo -e "\e[1;36m========================================\e[0m"
