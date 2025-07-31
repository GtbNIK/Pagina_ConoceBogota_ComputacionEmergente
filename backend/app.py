from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import random
import nltk
from nltk.stem import SnowballStemmer
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import pytz

# Cargar variables de entorno
load_dotenv()

# Descargar recursos necesarios de NLTK si no existen
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permitir solicitudes desde cualquier origen

# Configurar Flask para servir archivos estáticos del frontend
app = Flask(__name__, 
            static_folder='../frontend',  # Ruta a los archivos estáticos (CSS, JS, imágenes)
            template_folder='../frontend')  # Ruta a los templates (HTML)

class AITouristChatbot:
    def __init__(self):
        self.stemmer = SnowballStemmer('spanish')
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.default_city = os.getenv('DEFAULT_CITY', 'Bogota')
        self.default_country = os.getenv('DEFAULT_COUNTRY', 'CO')

        # Inicializar cliente OpenAI con la nueva API
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)

        self.load_intents()

    def load_intents(self):
        try:
            with open('data/intents.json', 'r', encoding='utf-8') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            # Crear el directorio data si no existe
            os.makedirs('data', exist_ok=True)
            self.data = {
                "intents": [
                    {
                        "tag": "saludo",
                        "patterns": ["hola", "buenos días", "buenas tardes", "hey", "saludos", "hi", "hello"],
                        "responses": [
                            "¡Hola! 👋 Soy tu guía turístico inteligente especializado en Bogotá, Colombia. ¿En qué te puedo ayudar hoy?",
                            "¡Bienvenido! 🌟 Estoy aquí para ayudarte a descubrir lo mejor de Bogotá, la capital de Colombia."
                        ]
                    },
                    {
                        "tag": "hora_actual",
                        "patterns": [
                            "¿qué hora es?", "hora actual", "¿qué horas son?",
                            "dime la hora", "hora", "time", "¿cuál es la hora?",
                            "¿qué hora es en bogotá?", "hora bogotá", "hora colombia"
                        ],
                        "responses": ["Te voy a consultar la hora actual de Bogotá, Colombia..."]
                    },
                    {
                        "tag": "clima_actual",
                        "patterns": [
                            "¿qué clima hace hoy?", "clima actual", "temperatura hoy",
                            "¿va a llover hoy?", "¿cómo está el clima?", "pronóstico del tiempo",
                            "¿qué temperatura hace?", "clima bogotá", "tiempo hoy",
                            "¿necesito paraguas?", "¿debo llevar abrigo?"
                        ],
                        "responses": ["Te voy a consultar el clima actual de Bogotá, Colombia..."]
                    },
                    {
                        "tag": "lugares_turisticos",
                        "patterns": [
                            "¿qué lugares puedo visitar?", "sitios turísticos", "lugares para visitar",
                            "¿qué ver en bogotá?", "recomendaciones turísticas", "atracciones",
                            "museos", "parques", "monumentos", "que hacer en bogota"
                        ],
                        "responses": [
                            "🏛️ **Lugares imperdibles en Bogotá, Colombia:**\n• Monserrate - Cerro emblemático con vista panorámica\n• Museo del Oro - Tesoro precolombino único\n• La Candelaria - Centro histórico colonial\n• Jardín Botánico José Celestino Mutis\n• Museo Nacional de Colombia\n• Parque Simón Bolívar - Pulmón verde de la ciudad"
                        ]
                    },
                    {
                        "tag": "restaurantes",
                        "patterns": [
                            "¿dónde puedo comer?", "restaurantes", "comida típica", "ajiaco",
                            "¿dónde comer bien?", "gastronomía", "platos típicos", "comida bogotana"
                        ],
                        "responses": [
                            "🍽️ **Restaurantes recomendados en Bogotá:**\n• Andrés Carne de Res (Chía) - Experiencia gastronómica única\n• La Puerta Falsa - Ajiaco tradicional desde 1816\n• El Chato - Cocina colombiana contemporánea\n• Criterion - Alta cocina francesa\n• Casa San Isidro - Comida típica bogotana\n• Prudencia - Cocina de autor colombiana"
                        ]
                    },
                    {
                        "tag": "transporte",
                        "patterns": [
                            "¿cómo me muevo?", "transporte", "transmilenio", "uber", "taxi",
                            "¿cómo llegar?", "movilidad", "metro", "bus"
                        ],
                        "responses": [
                            "🚌 **Opciones de transporte en Bogotá:**\n• TransMilenio - Sistema BRT principal\n• SITP - Buses urbanos integrados\n• Uber/Taxi/DiDi - Transporte privado\n• Bicicletas públicas (BiciRed)\n• Metro de Bogotá (en construcción - Primera Línea)\n• Ciclovías dominicales - 120 km los domingos"
                        ]
                    },
                    {
                        "tag": "otras_ciudades",
                        "patterns": [
                            "medellín", "cali", "cartagena", "barranquilla", "méxico", "argentina"
                        ],
                        "responses": [
                            "🏛️ Soy tu guía especializado únicamente en **Bogotá, Colombia**. Te puedo ayudar con información sobre lugares turísticos, restaurantes, clima, transporte y todo lo que necesites saber sobre la capital colombiana. ¿Qué te gustaría conocer sobre Bogotá? 😊"
                        ]
                    }
                ]
            }
            # Guardar el archivo de intents por defecto
            with open('data/intents.json', 'w', encoding='utf-8') as file:
                json.dump(self.data, file, ensure_ascii=False, indent=2)

    def obtener_hora_actual(self):
        """Obtiene la hora actual de Bogotá, Colombia"""
        try:
            # Zona horaria de Bogotá (Colombia)
            zona_bogota = pytz.timezone('America/Bogota')
            ahora = datetime.now(zona_bogota)
            
            # Formatear la hora
            hora_formateada = ahora.strftime("%H:%M:%S")
            fecha_formateada = ahora.strftime("%A, %d de %B de %Y")
            
            # Traducir el día de la semana al español
            dias_semana = {
                'Monday': 'Lunes',
                'Tuesday': 'Martes', 
                'Wednesday': 'Miércoles',
                'Thursday': 'Jueves',
                'Friday': 'Viernes',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            
            # Traducir los meses al español
            meses = {
                'January': 'enero', 'February': 'febrero', 'March': 'marzo',
                'April': 'abril', 'May': 'mayo', 'June': 'junio',
                'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
                'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
            }
            
            # Reemplazar día y mes en español
            for eng, esp in dias_semana.items():
                fecha_formateada = fecha_formateada.replace(eng, esp)
            for eng, esp in meses.items():
                fecha_formateada = fecha_formateada.replace(eng, esp)
            
            # Determinar saludo según la hora
            hora_num = ahora.hour
            if 5 <= hora_num < 12:
                saludo = "Buenos días"
            elif 12 <= hora_num < 18:
                saludo = "Buenas tardes"
            else:
                saludo = "Buenas noches"
            
            return (
                f"🕐 **Hora actual en Bogotá, Colombia:**\n"
                f"• **Hora:** {hora_formateada}\n"
                f"• **Fecha:** {fecha_formateada}\n"
                f"• **Zona horaria:** COT (UTC-5)\n\n"
                f"{saludo}! 😊"
            )
            
        except Exception as e:
            print("Error al obtener la hora:", str(e))
            return "⏰ No pude obtener la hora actual en este momento."

    def obtener_clima(self, ciudad=None):
        if not self.openweather_api_key:
            return "❌ Falta la clave de API de OpenWeather."

        ciudad = ciudad or self.default_city
        pais = self.default_country

        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={ciudad},{pais}&appid={self.openweather_api_key}"
            f"&lang=es&units=metric"
        )

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                descripcion = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                sensacion = data["main"]["feels_like"]
                humedad = data["main"]["humidity"]
                viento = data["wind"]["speed"]

                # Obtener hora actual para el reporte
                zona_bogota = pytz.timezone('America/Bogota')
                ahora = datetime.now(zona_bogota)
                hora_reporte = ahora.strftime("%H:%M")

                # Recomendaciones basadas en el clima
                recomendacion = ""
                if temp < 15:
                    recomendacion = "\n🧥 Recomendación: Lleva abrigo, hace frío."
                elif temp > 25:
                    recomendacion = "\n☀️ Recomendación: Usa protector solar y mantente hidratado."
                elif "lluvia" in descripcion.lower() or "rain" in descripcion.lower():
                    recomendacion = "\n☔ Recomendación: No olvides el paraguas."

                return (
                    f"🌤️ **Clima actual en {ciudad}** (actualizado a las {hora_reporte}):\n"
                    f"• Condición: {descripcion.title()}\n"
                    f"• Temperatura: {temp}°C\n"
                    f"• Sensación térmica: {sensacion}°C\n"
                    f"• Humedad: {humedad}%\n"
                    f"• Viento: {viento} m/s{recomendacion}"
                )
            else:
                print("Error al consultar clima:", response.status_code, response.text)
                return "🌥️ No pude obtener la información del clima en este momento."
        except Exception as e:
            print("Excepción al consultar clima:", str(e))
            return "⚠️ Ocurrió un error al intentar obtener el clima."

    def responder_con_openai(self, mensaje_usuario):
        if not self.openai_api_key:
            return "⚠️ No tengo acceso a la inteligencia artificial en este momento."

        try:
            # Obtener hora actual para contexto
            zona_bogota = pytz.timezone('America/Bogota')
            ahora = datetime.now(zona_bogota)
            contexto_tiempo = f"Hora actual en Bogotá: {ahora.strftime('%H:%M:%S del %d/%m/%Y')}"
            
            # Usar la nueva API de OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": f"""Eres un guía turístico experto EXCLUSIVAMENTE especializado en Bogotá, Colombia. 
                    {contexto_tiempo}
                    
                    REGLAS IMPORTANTES:
                    - SOLO respondes sobre Bogotá, Colombia
                    - Si te preguntan sobre otras ciudades o países, redirige la conversación a Bogotá
                    - No proporciones información de otros destinos
                    - Siempre enfócate en atracciones, restaurantes, clima y servicios de Bogotá únicamente
                    
                    Proporciona información útil, actualizada y práctica SOLO sobre:
                    - Lugares turísticos y atracciones de Bogotá
                    - Restaurantes y gastronomía local de Bogotá
                    - Transporte y movilidad en Bogotá
                    - Actividades culturales y eventos en Bogotá
                    - Consejos de seguridad y recomendaciones para Bogotá
                    - Historia y cultura bogotana
                    - Clima y hora actual de Bogotá
                    
                    Si te preguntan sobre otros lugares, responde algo como:
                    "Soy un guía especializado únicamente en Bogotá, Colombia. Te puedo ayudar con información sobre [tema relacionado] en Bogotá. ¿Te gustaría saber sobre [sugerencia específica de Bogotá]?"
                    
                    Responde de manera conversacional, útil y con emojis apropiados. 
                    Mantén las respuestas concisas pero informativas."""
                    },
                    {"role": "user", "content": mensaje_usuario}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print("Error OpenAI:", str(e))
            return "🤖 Lo siento, hubo un error al generar una respuesta inteligente. Por favor, intenta de nuevo."

    def validar_pregunta_bogota(self, mensaje):
        """Valida si la pregunta es específica de Bogotá o si menciona otras ciudades"""
        mensaje_lower = mensaje.lower()
        
        # Palabras clave de otras ciudades/países que deberían ser redirigidas
        otras_ciudades = [
            'medellín', 'medellin', 'cali', 'cartagena', 'barranquilla', 'bucaramanga',
            'pereira', 'manizales', 'armenia', 'ibagué', 'pasto', 'neiva', 'villavicencio',
            'méxico', 'mexico', 'argentina', 'brasil', 'peru', 'chile', 'ecuador',
            'venezuela', 'panama', 'costa rica', 'madrid', 'barcelona', 'paris',
            'londres', 'nueva york', 'miami', 'los angeles', 'toronto', 'vancouver'
        ]
        
        # Si menciona otras ciudades, devolver mensaje de redirección
        for ciudad in otras_ciudades:
            if ciudad in mensaje_lower:
                return f"🏛️ Soy tu guía especializado únicamente en **Bogotá, Colombia**. No tengo información sobre {ciudad.title()}, pero puedo ayudarte con todo lo que necesites saber sobre Bogotá. ¿Te gustaría conocer sobre lugares turísticos, restaurantes, clima o transporte en Bogotá? 😊"
        
        return None  # La pregunta es válida para Bogotá

    def responder(self, mensaje):
        mensaje_lower = mensaje.lower()
        
        # Primero validar si la pregunta es sobre Bogotá
        validacion = self.validar_pregunta_bogota(mensaje)
        if validacion:
            return validacion

        # Buscar coincidencias en los patrones predefinidos
        for intent in self.data.get("intents", []):
            if any(patron.lower() in mensaje_lower for patron in intent["patterns"]):
                if intent["tag"] == "clima_actual":
                    return self.obtener_clima()
                elif intent["tag"] == "hora_actual":
                    return self.obtener_hora_actual()
                else:
                    return random.choice(intent["responses"])

        # Si no encuentra coincidencia, usar OpenAI
        return self.responder_con_openai(mensaje)

# Instancia del chatbot
chatbot = AITouristChatbot()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        mensaje = data.get("message", "").strip()
        
        if not mensaje:
            return jsonify({"response": "Por favor, escribe un mensaje."})
        
        respuesta = chatbot.responder(mensaje)
        return jsonify({"response": respuesta})
    except Exception as e:
        print("Error en /chat:", str(e))
        return jsonify({"response": "Lo siento, ocurrió un error. Por favor, intenta de nuevo."})

# Ruta para archivos estáticos (CSS, JS, imágenes)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.static_folder, 'static'), filename)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route("/weather")
def weather():
    try:
        clima = chatbot.obtener_clima()
        return jsonify({"formatted": clima})
    except Exception as e:
        print("Error en /weather:", str(e))
        return jsonify({"error": "Error obteniendo el clima"})

@app.route("/time")
def time():
    try:
        hora = chatbot.obtener_hora_actual()
        return jsonify({"formatted": hora})
    except Exception as e:
        print("Error en /time:", str(e))
        return jsonify({"error": "Error obteniendo la hora"})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
