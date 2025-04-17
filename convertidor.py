from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def get_bcv_rate():
    """Obtiene la tasa oficial del BCV"""
    try:
        url = "https://www.bcv.org.ve/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        print(f"Intentando conectar a {url}...")
        # Desactivar la verificación de certificados SSL
        response = requests.get(url, headers=headers, timeout=15, verify=False)

        print(f"Código de estado: {response.status_code}")
        if response.status_code != 200:
            print("Error: status", response.status_code)
            return "Error de conexión"

        print("Conexión exitosa, analizando contenido...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Método 1: Buscar por ID "dolar"
        dollar_element = soup.find(id="dolar")
        if dollar_element:
            print("Elemento con id 'dolar' encontrado")
            strong_element = dollar_element.find('strong')
            if strong_element:
                rate_text = strong_element.text.strip()
                print(f"Texto extraído: {rate_text}")
                return rate_text.replace(',', '.')
        
        # Método 2: Buscar por clase "dolar" o similar
        dollar_divs = soup.find_all(class_=lambda c: c and ('dolar' in c.lower() or 'dólar' in c.lower()))
        for div in dollar_divs:
            strong_element = div.find('strong')
            if strong_element:
                rate_text = strong_element.text.strip()
                if re.search(r'\d+[.,]\d+', rate_text):
                    print(f"Encontrado valor en clase dolar: {rate_text}")
                    return rate_text.replace(',', '.')
        
        # Método 3: Buscar por texto que contenga "Dólar" o "USD"
        for div in soup.find_all(['div', 'span', 'p']):
            if div.text and ('Dólar' in div.text or 'USD' in div.text):
                strong_element = div.find('strong')
                if strong_element:
                    rate_text = strong_element.text.strip()
                    if re.search(r'\d+[.,]\d+', rate_text):
                        print(f"Encontrado valor cerca de texto Dólar/USD: {rate_text}")
                        return rate_text.replace(',', '.')
        
        # Método 4: Buscar cualquier strong con formato de moneda
        print("Buscando cualquier elemento strong con formato de moneda...")
        for strong in soup.find_all('strong'):
            text = strong.text.strip()
            if re.search(r'\d+[.,]\d+', text):
                print(f"Encontrado posible valor: {text}")
                return text.replace(',', '.')
        
        # Método 5: Buscar en toda la página por patrones de cotización
        page_text = soup.get_text()
        matches = re.findall(r'USD\s*[\d.,]+', page_text)
        if matches:
            for match in matches:
                rate = re.search(r'[\d.,]+', match)
                if rate:
                    print(f"Encontrado valor en texto de página: {rate.group(0)}")
                    return rate.group(0).replace(',', '.')
        
        print("No se pudo encontrar la cotización del dólar")
        return "No disponible"
    except requests.exceptions.SSLError as e:
        print(f"Error SSL al conectar con BCV: {e}")
        # Intentar con una URL alternativa
        try:
            print("Intentando con URL alternativa...")
            alt_url = "http://www.bcv.org.ve/"
            response = requests.get(alt_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Repetir los métodos de búsqueda...
                # Método 1: Buscar por ID "dolar"
                dollar_element = soup.find(id="dolar")
                if dollar_element:
                    strong_element = dollar_element.find('strong')
                    if strong_element:
                        rate_text = strong_element.text.strip()
                        return rate_text.replace(',', '.')
                
                # Método 2: Buscar por clase "dolar" o similar
                dollar_divs = soup.find_all(class_=lambda c: c and ('dolar' in c.lower() or 'dólar' in c.lower()))
                for div in dollar_divs:
                    strong_element = div.find('strong')
                    if strong_element:
                        rate_text = strong_element.text.strip()
                        if re.search(r'\d+[.,]\d+', rate_text):
                            return rate_text.replace(',', '.')
                
                # Método 3: Buscar por texto que contenga "Dólar" o "USD"
                for div in soup.find_all(['div', 'span', 'p']):
                    if div.text and ('Dólar' in div.text or 'USD' in div.text):
                        strong_element = div.find('strong')
                        if strong_element:
                            rate_text = strong_element.text.strip()
                            if re.search(r'\d+[.,]\d+', rate_text):
                                return rate_text.replace(',', '.')
                
                # Método 4: Buscar cualquier strong con formato de moneda
                for strong in soup.find_all('strong'):
                    text = strong.text.strip()
                    if re.search(r'\d+[.,]\d+', text):
                        return text.replace(',', '.')
                
                # Método 5: Buscar en toda la página por patrones de cotización
                page_text = soup.get_text()
                matches = re.findall(r'USD\s*[\d.,]+', page_text)
                if matches:
                    for match in matches:
                        rate = re.search(r'[\d.,]+', match)
                        if rate:
                            return rate.group(0).replace(',', '.')
        except Exception as alt_e:
            print(f"Error con URL alternativa: {alt_e}")
        
        return "Error de conexión SSL"
    except Exception as e:
        print(f"Error obteniendo tasa BCV: {e}")
        return "Error de conexión"

def get_parallel_rate():
    """
    Obtiene la tasa del dólar paralelo desde El Nacional.
    """
    try:
        url = "https://www.elnacional.com/economia/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar el div con la clave "mipc-cotizaciones"
        cotizaciones_div = soup.find('div', {'class': 'mipc-cotizaciones'})
        if cotizaciones_div:
            # Buscar el div con la clave "wrapper" dentro de cotizaciones
            wrapper_div = cotizaciones_div.find('div', {'class': 'wrapper'})
            if wrapper_div:
                # Buscar el span que contiene el div con clase "monitor-dolar"
                monitor_dolar_div = wrapper_div.find('div', {'class': 'monitor-dolar'})
                if monitor_dolar_div:
                    # Extraer el precio del dólar paralelo
                    rate_text = monitor_dolar_div.text.strip()
                    # Extraer solo los números con formato decimal
                    match = re.search(r'\d+[.,]\d+', rate_text)
                    if match:
                        return match.group(0).replace(',', '.')
        
        # Si no se encuentra con la estructura esperada, intentar métodos alternativos
        # Buscar directamente por la clase "monitor-dolar"
        monitor_dolar = soup.find('div', {'class': 'monitor-dolar'})
        if monitor_dolar:
            rate_text = monitor_dolar.text.strip()
            match = re.search(r'\d+[.,]\d+', rate_text)
            if match:
                return match.group(0).replace(',', '.')
        
        return "No disponible"
    except Exception as e:
        print(f"Error obteniendo tasa paralela: {e}")
        return "Error de conexión"

def promedio_bcv_paralelo():
    bcv_rate = get_bcv_rate()
    parallel_rate = get_parallel_rate()
    return (float(bcv_rate) + float(parallel_rate)) / 2 
    
   

@app.route('/', methods=['GET', 'POST'])
def index():
    # Obtener las cotizaciones
    bcv_rate = get_bcv_rate()
    parallel_rate = get_parallel_rate()
    promedio = promedio_bcv_paralelo()
    
    # Inicializar variables
    amount = 0
    bcv_result = 0
    parallel_result = 0
    promedio_result = 0
    conversion_type = "usd_to_bs"
    
    # Procesar el formulario si es una solicitud POST
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            conversion_type = request.form.get('conversion_type')
            
            # Calcular resultados solo si tenemos tasas válidas
            if bcv_rate != "No disponible" and bcv_rate != "Error de conexión" and bcv_rate != "Error de conexión SSL":
                bcv_rate_float = float(bcv_rate)
                if conversion_type == "usd_to_bs":
                    bcv_result = amount * bcv_rate_float
                else:
                    bcv_result = amount / bcv_rate_float
            
            if parallel_rate != "No disponible" and parallel_rate != "Error de conexión":
                parallel_rate_float = float(parallel_rate)
                if conversion_type == "usd_to_bs":
                    parallel_result = amount * parallel_rate_float
                else:
                    parallel_result = amount / parallel_rate_float
            
            # Calcular resultado con el promedio
            if promedio != "No disponible" and promedio != "Error de conexión":
                promedio_float = float(promedio)
                if conversion_type == "usd_to_bs":
                    promedio_result = amount * promedio_float
                else:
                    promedio_result = amount / promedio_float
                    
        except ValueError:
            pass
    
    # Renderizar la plantilla con todos los datos necesarios
    return render_template('index.html', 
                          bcv_rate=bcv_rate, 
                          parallel_rate=parallel_rate,
                          promedio=promedio,
                          amount=amount,
                          bcv_result=bcv_result,
                          parallel_result=parallel_result,
                          promedio_result=promedio_result,
                          conversion_type=conversion_type)

if __name__ == '__main__':
    app.run(debug=True)