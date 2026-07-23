#!/bin/bash
# ==============================================================================
# Pipeline de Empaquetado Debian Enterprise (.deb) - Argos Guard
# ==============================================================================
set -e

# Directorios de trabajo
BaseDir=$(pwd)
BuildDir="$BaseDir/backend/build"
DebBuildDir="$BaseDir/desktop/build_deb"
IconSource="$BaseDir/frontend/public/icono_argos.bmp"
OutputDir="$BaseDir/dist"

echo -e "\e[1;36m==================================================\e[0m"
# El titulo debe reflejar el pipeline de empaquetado Debian
echo -e "\e[1;36m       Empaquetado Debian (.deb) - Argos Guard     \e[0m"
echo -e "\e[1;36m==================================================\e[0m"

# 1. Verificar binario compilado
if [ ! -f "$BuildDir/ArgosGuard" ]; then
    echo -e "\e[1;31mError: No se encontro el binario compilado en $BuildDir/ArgosGuard.\e[0m"
    echo -e "\e[1;33mPor favor, ejecuta primero: ./build.sh\e[0m"
    exit 1
fi

# 2. Limpiar y recrear arbol de directorios de Debian en un filesystem nativo (/tmp)
echo -e "\n\e[1;33m[1/6] Creando arbol de directorios Debian en filesystem nativo...\e[0m"
DebBuildDir=$(mktemp -d -t argosguard-deb-XXXXXX)

# Registrar trampa para limpiar el directorio temporal si falla el script
trap 'rm -rf "$DebBuildDir"' EXIT

mkdir -p "$DebBuildDir/DEBIAN"
mkdir -p "$DebBuildDir/opt/argosguard"
mkdir -p "$DebBuildDir/usr/local/bin"
mkdir -p "$DebBuildDir/usr/share/applications"
mkdir -p "$DebBuildDir/usr/share/pixmaps"

# 3. Convertir icono oficial BMP a PNG usando Python (PIL)
echo -e "\n\e[1;33m[2/6] Convirtiendo icono oficial BMP a PNG...\e[0m"
if [ -f "$IconSource" ]; then
    python3 -c "
from PIL import Image
try:
    img = Image.open('$IconSource')
    img.save('$DebBuildDir/usr/share/pixmaps/argosguard.png', 'PNG')
    print('Icono convertido con exito y guardado en /usr/share/pixmaps/argosguard.png')
except Exception as e:
    print('Error convirtiendo icono:', e)
    import sys
    sys.exit(1)
"
else
    echo -e "\e[1;31mError: No se encontro el icono oficial en $IconSource\e[0m"
    exit 1
fi

# 4. Copiar binario compilado
echo -e "\n\e[1;33m[3/6] Copiando binarios y archivos al directorio de empaquetado...\e[0m"
cp "$BuildDir/ArgosGuard" "$DebBuildDir/opt/argosguard/"
chmod 755 "$DebBuildDir/opt/argosguard/ArgosGuard"

# Crear script lanzador en /usr/local/bin
cat << 'EOF' > "$DebBuildDir/usr/local/bin/argosguard"
#!/bin/bash
# Lanzador oficial para Argos Guard Enterprise
export CHROME_PATH="/usr/bin/google-chrome"
export CHROMEDRIVER_PATH="/usr/bin/chromedriver"
exec /opt/argosguard/ArgosGuard "$@"
EOF
chmod 755 "$DebBuildDir/usr/local/bin/argosguard"

# 5. Generar archivos de control y metadatos de Debian
echo -e "\n\e[1;33m[4/6] Creando archivo DEBIAN/control...\e[0m"
cat << 'EOF' > "$DebBuildDir/DEBIAN/control"
Package: argosguard
Version: 3.6.4
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Argos Guard Team <info@argosguard.com>
Depends: xvfb, xauth, python3, google-chrome-stable | chromium
Description: Argos Guard Enterprise Client
 Sistema de monitoreo y OSINT para Argos Guard Enterprise con frontend integrado en modo kiosco.
EOF

# Crear script postinst para ajustar permisos y actualizar caches
cat << 'EOF' > "$DebBuildDir/DEBIAN/postinst"
#!/bin/bash
set -e
chmod 755 /opt/argosguard/ArgosGuard
chmod 755 /usr/local/bin/argosguard
echo "Argos Guard instalado correctamente en /opt/argosguard y enlazado en /usr/local/bin/argosguard."
EOF
chmod 755 "$DebBuildDir/DEBIAN/postinst"

# 6. Generar archivo .desktop para integracion de escritorio
echo -e "\n\e[1;33m[5/6] Creando acceso directo de escritorio (.desktop)...\e[0m"
cat << 'EOF' > "$DebBuildDir/usr/share/applications/argosguard.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Argos Guard
Comment=Argos Guard Enterprise Client
Exec=/usr/local/bin/argosguard
Icon=argosguard
Terminal=false
Categories=Utility;Security;
StartupWMClass=Argos Guard Enterprise
EOF
chmod 644 "$DebBuildDir/usr/share/applications/argosguard.desktop"

# 7. Ejecutar dpkg-deb --build
echo -e "\n\e[1;33m[6/6] Construyendo archivo .deb con dpkg-deb...\e[0m"
mkdir -p "$OutputDir"

# Sanitizar permisos para cumplir estándares estrictos de Debian
chmod 755 "$DebBuildDir/DEBIAN"
chmod 644 "$DebBuildDir/DEBIAN/control"
chmod 755 "$DebBuildDir/DEBIAN/postinst"

dpkg-deb --build "$DebBuildDir" "$OutputDir/argosguard_3.6.4_amd64.deb"

echo -e "\n\e[1;36m==================================================\e[0m"
echo -e "\e[1;32m Paquete Debian creado con exito en:\e[0m"
echo -e "\e[1;32m -> $OutputDir/argosguard_3.6.4_amd64.deb\e[0m"
echo -e "\e[1;36m==================================================\e[0m"
