/**
 * Script per facilitare l'integrazione con sistemi esterni
 * Questo file fornisce metodi che possono essere utilizzati dal sistema esterno
 * che incorporerà i nostri contenuti
 */

// Funzione per indicare al sistema esterno quando un form viene inviato
function notifyExternalSystem(eventType, data = {}) {
    // Invia messaggi al sistema esterno che incorpora questo contenuto
    if (window.parent && window.parent !== window) {
        window.parent.postMessage({
            source: 'mirell-kiosk',
            type: eventType,
            data: data
        }, '*');
    }
}

// Esponi funzioni per aprire il form wedding in un popup
window.openWeddingModal = function(fullname, phone) {
    // Costruisce l'URL con i parametri
    const params = new URLSearchParams();
    if (fullname) params.append('fullname', fullname);
    if (phone) params.append('phone', phone);
    
    // Notifica al sistema esterno di aprire il modal
    notifyExternalSystem('open-modal', {
        title: 'Registrazione Wedding',
        url: '/wedding?' + params.toString()
    });
    
    return false;
};

// Funzione per ricevere messaggi dal sistema esterno
window.addEventListener('message', function(event) {
    // Verifica che il messaggio provenga da un origine attendibile
    // Qui puoi aggiungere controlli sull'origine se necessario
    
    const message = event.data;
    if (message && message.source === 'external-system') {
        // Gestisci i messaggi dal sistema esterno
        switch (message.type) {
            case 'form-action':
                // Esempio di azione che può essere richiesta dal sistema esterno
                handleFormAction(message.data);
                break;
            case 'close-form':
                // Gestisce la richiesta di chiusura del form
                notifyExternalSystem('form-closed');
                break;
            // Altri tipi di messaggi possono essere gestiti qui
        }
    }
});

// Funzione per gestire azioni sui form richieste dal sistema esterno
function handleFormAction(data) {
    if (data.action === 'submit') {
        // Trova il form e invialo programmicamente
        const form = document.querySelector(data.formSelector || 'form');
        if (form) form.submit();
    } else if (data.action === 'reset') {
        const form = document.querySelector(data.formSelector || 'form');
        if (form) form.reset();
    }
}

// Inizializza dopo che il DOM è caricato
document.addEventListener('DOMContentLoaded', function() {
    // Aggiungi listener ai form per notificare il sistema esterno
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            notifyExternalSystem('form-submitting', {
                formId: this.id || 'unknown',
                action: this.action
            });
        });
    });

    // Notifica che il contenuto è pronto
    notifyExternalSystem('content-ready', {
        pageType: document.querySelector('[data-page-type]')?.dataset.pageType || 'unknown'
    });
});