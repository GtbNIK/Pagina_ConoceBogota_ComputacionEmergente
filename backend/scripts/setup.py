import os
import subprocess
import sys

def install_requirements():
    """Instalar las dependencias necesarias"""
    print("🔧 Instalando dependencias...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False
    
    return True

def create_directories():
    """Crear directorios necesarios"""
    directories = [
        "templates",
        "static/css",
        "static/js",
        "data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Directorio creado: {directory}")

def check_env_file():
    """Verificar que el archivo .env existe y tiene las claves necesarias"""
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
        
    required_keys = ['OPENWEATHER_API_KEY', 'OPENAI_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if key not in content or f"{key}=" not in content:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Faltan las siguientes claves en .env: {', '.join(missing_keys)}")
        return False
    
    print("✅ Archivo .env configurado correctamente")
    return True

def main():
    print("🚀 Configurando el Chatbot Turístico IA...")
    
    # Crear directorios
    create_directories()
    
    # Verificar archivo .env
    if not check_env_file():
        print("\n📝 Por favor, asegúrate de tener un archivo .env con:")
        print("OPENWEATHER_API_KEY=tu_clave_aqui")
        print("OPENAI_API_KEY=tu_clave_aqui")
        return
    
    # Instalar dependencias
    if not install_requirements():
        return
    
    print("\n🎉 ¡Configuración completada!")
    print("\n📋 Para ejecutar el chatbot:")
    print("1. Asegúrate de que el archivo .env tenga tus claves de API")
    print("2. Ejecuta: python app.py")
    print("3. Abre tu navegador en: http://localhost:5000")

if __name__ == "__main__":
    main()
