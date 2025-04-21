from flask import Flask, render_template, request, url_for
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import locale

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Añadir la función now() al contexto de la plantilla
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Filtro personalizado para formatear números
@app.template_filter('format_number')
def format_number(value):
    try:
        if isinstance(value, str):
            if value in ["No disponible", "Error en la conversión"]:
                return value
            value = float(value)
        # Formatear el número con punto como separador de miles y coma para decimales
        parts = f"{value:,.2f}".split('.')
        return f"{parts[0].replace(',', '.')},{parts[1]}"
    except (ValueError, IndexError):
        return value

def extraer_paralelo():
    url = "https://ve.dolarapi.com/v1/dolares/paralelo"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanzará una excepción si el status code no es 200
        data = response.json()
        promedio = data.get("promedio")

        if promedio:
            logger.info(f"💵 Dólar paralelo: {promedio} Bs")
            return "{:.2f}".format(float(promedio))
        logger.warning("No se pudo obtener el valor del dólar paralelo")
        return "No disponible"
    except requests.RequestException as e:
        logger.error(f"❌ Error al obtener la cotización paralela: {e}")
        return "No disponible"
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Error al procesar el valor del dólar paralelo: {e}")
        return "No disponible"

def get_exchange_rates():
    """
    Obtiene todas las tasas de cambio en una sola función para reducir llamadas HTTP.
    Retorna un diccionario con todas las tasas.
    """
    rates = {
        'bcv': "No disponible",
        'parallel': "No disponible",
        'promedio': "No disponible"
    }
    
    try:
        # Obtener tasa BCV
        url_bcv = "https://www.bcv.org.ve/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        logger.info("Obteniendo tasas de cambio...")
        response_bcv = requests.get(url_bcv, headers=headers, verify=False, timeout=5)
        response_bcv.raise_for_status()
        
        # Extraer el valor del dólar BCV usando BeautifulSoup
        soup = BeautifulSoup(response_bcv.content, 'html.parser')
        dollar_element = soup.find(id="dolar")
        if dollar_element and (strong_element := dollar_element.find('strong')):
            bcv_value = strong_element.text.strip().replace(',', '.')
            rates['bcv'] = "{:.2f}".format(float(bcv_value))
            logger.info(f"Tasa BCV obtenida: {rates['bcv']}")
        else:
            logger.warning("No se encontró el valor del dólar BCV en la página")
        
        # Obtener tasa paralela
        logger.info("Obteniendo tasa paralela...")
        rates['parallel'] = extraer_paralelo()
        
        # Calcular promedio si ambas tasas están disponibles
        if rates['bcv'] != "No disponible" and rates['parallel'] != "No disponible":
            try:
                bcv_value = float(rates['bcv'])
                parallel_value = float(rates['parallel'])
                rates['promedio'] = "{:.2f}".format((bcv_value + parallel_value) / 2)
                logger.info(f"Promedio calculado: {rates['promedio']}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error al calcular el promedio: {e}")
        else:
            logger.warning("No se puede calcular el promedio porque faltan tasas")
            
        return rates
        
    except requests.RequestException as e:
        logger.error(f"Error en la solicitud HTTP: {e}")
        return rates
    except Exception as e:
        logger.error(f"Error inesperado obteniendo tasas: {e}")
        return rates

@app.route('/', methods=['GET', 'POST'])
def index():
    rates = get_exchange_rates()
    result = None
    amount = None
    to_currency = 'VES'  # Valor por defecto
    
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            from_currency = request.form['from_currency']
            to_currency = request.form['to_currency']
            
            if any(rate == "No disponible" for rate in [rates['bcv'], rates['parallel'], rates['promedio']]):
                result = {key: "No disponible" for key in ['bcv', 'parallel', 'promedio']}
            else:
                # Convertir los valores a float una sola vez
                bcv_rate = float(rates['bcv'])
                parallel_rate = float(rates['parallel'])
                promedio_rate = float(rates['promedio'])
                
                if from_currency == 'USD' and to_currency == 'VES':
                    # Convertir USD a VES
                    result = {
                        'bcv': "{:.2f}".format(amount * bcv_rate),
                        'parallel': "{:.2f}".format(amount * parallel_rate),
                        'promedio': "{:.2f}".format(amount * promedio_rate)
                    }
                else:
                    # Convertir VES a USD
                    result = {
                        'bcv': "{:.2f}".format(amount / bcv_rate),
                        'parallel': "{:.2f}".format(amount / parallel_rate),
                        'promedio': "{:.2f}".format(amount / promedio_rate)
                    }
        except (ValueError, TypeError) as e:
            logger.error(f"Error en la conversión: {e}")
            result = {key: "Error en la conversión" for key in ['bcv', 'parallel', 'promedio']}
    
    logger.info(f"Moneda destino: {to_currency}")
    
    return render_template('index.html',
                         result=result,
                         amount=amount,
                         to_currency=to_currency,
                         bcv_rate=rates['bcv'],
                         parallel_rate=rates['parallel'],
                         promedio=rates['promedio'])

if __name__ == '__main__':
    app.run(debug=True)