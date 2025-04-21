document.addEventListener('DOMContentLoaded', () => {
    const fromCurrency = document.getElementById('from_currency');
    const toCurrency = document.getElementById('to_currency');
    const currencySymbol = document.getElementById('currencySymbol');
    
    const updateCurrencySymbol = () => {
        currencySymbol.textContent = fromCurrency.value;
    };
    
    const updateToCurrency = () => {
        toCurrency.value = fromCurrency.value === 'USD' ? 'VES' : 'USD';
    };
    
    const updateFromCurrency = () => {
        fromCurrency.value = toCurrency.value === 'VES' ? 'USD' : 'VES';
        updateCurrencySymbol();
    };
    
    fromCurrency.addEventListener('change', () => {
        updateCurrencySymbol();
        updateToCurrency();
    });

    toCurrency.addEventListener('change', updateFromCurrency);
    
    updateCurrencySymbol();
}); 