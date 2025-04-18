from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

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
        
        print("Obteniendo tasas de cambio...")
        response_bcv = requests.get(url_bcv, headers=headers, verify=False, timeout=5)
        if response_bcv.status_code == 200:
            soup = BeautifulSoup(response_bcv.content, 'html.parser')
            dollar_element = soup.find(id="dolar")
            if dollar_element:
                strong_element = dollar_element.find('strong')
                if strong_element:
                    rates['bcv'] = "{:.2f}".format(float(strong_element.text.strip().replace(',', '.')))
        
        # Obtener tasa paralela
        url_parallel = "https://www.elnacional.com/economia/"
        response_parallel = requests.get(url_parallel, headers=headers, timeout=5)
        if response_parallel.status_code == 200:
            soup = BeautifulSoup(response_parallel.content, 'html.parser')
            cotizaciones_div = soup.find('div', {'class': 'mipc-cotizaciones'})
            if cotizaciones_div:
                wrapper_div = cotizaciones_div.find('div', {'class': 'wrapper'})
                if wrapper_div:
                    monitor_dolar_div = wrapper_div.find('div', {'class': 'monitor-dolar'})
                    if monitor_dolar_div:
                        rate_text = monitor_dolar_div.text.strip()
                        match = re.search(r'\d+[.,]\d+', rate_text)
                        if match:
                            rates['parallel'] = "{:.2f}".format(float(match.group(0).replace(',', '.')))
        
        # Calcular promedio si ambas tasas están disponibles
        if rates['bcv'] != "No disponible" and rates['parallel'] != "No disponible":
            rates['promedio'] = "{:.2f}".format((float(rates['bcv']) + float(rates['parallel'])) / 2)
            
        print("Tasas obtenidas exitosamente")
        return rates
        
    except Exception as e:
        print(f"Error obteniendo tasas: {e}")
        return rates

@app.route('/', methods=['GET', 'POST'])
def index():
    # Obtener todas las tasas en una sola llamada
    rates = get_exchange_rates()
    
    result = None
    amount = None
    to_currency = None
    if request.method == 'POST':
        amount = float(request.form['amount'])
        from_currency = request.form['from_currency']
        to_currency = request.form['to_currency']
        
        if from_currency == 'USD' and to_currency == 'VES':
            # Convertir USD a VES
            bcv_result = amount * float(rates['bcv'])
            parallel_result = amount * float(rates['parallel'])
            promedio_result = amount * float(rates['promedio'])
            result = {
                'bcv': bcv_result,
                'parallel': parallel_result,
                'promedio': promedio_result
            }
        else:
            # Convertir VES a USD
            bcv_result = amount / float(rates['bcv'])
            parallel_result = amount / float(rates['parallel'])
            promedio_result = amount / float(rates['promedio'])
            result = {
                'bcv': bcv_result,
                'parallel': parallel_result,
                'promedio': promedio_result
            }
    
    return render_template('index.html',
                         result=result,
                         amount=amount,
                         to_currency=to_currency,
                         bcv_rate=rates['bcv'],
                         parallel_rate=rates['parallel'],
                         promedio=rates['promedio'])

if __name__ == '__main__':
    app.run(debug=True)
