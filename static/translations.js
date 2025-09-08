// Translation system for multi-language support
const translations = {
    en: {
        // Navigation
        profile: "Profile",
        orders: "Orders", 
        payments: "Payments",
        settings: "Settings",
        logout: "Logout",
        help: "Help",

        // Dashboard
        dashboard: "Dashboard",
        dataBalance: "Data Balance",
        subscription: "Subscription", 
        offers: "Offers",
        invitations: "Invitations",

        // Settings
        darkMode: "Dark Mode",
        language: "Language",

        // Language options
        english: "English",
        spanish: "Español",
        french: "Français",

        // Common
        cancel: "Cancel",
        confirm: "Confirm",
        save: "Save",
        close: "Close",
        buy: "Buy",
        subscribe: "Subscribe",
        comingSoon: "Coming Soon",

        // Offers
        globalPriorityData: "Global Priority Data",
        basicMembership: "Basic Membership", 
        fullMembership: "Full Membership",

        // Help
        humanHelp: "Human help:",
        useAiHelp: "Use AI help:",
        orderCallback: "Order Callback",
        chatWithAgent: "Open Chat Now",

        // Beta
        requestBetaAccess: "Request BETA access ($1 eSIM)",
        betaEnrollment: "Beta Enrollment"
    },

    es: {
        // Navigation
        profile: "Perfil",
        orders: "Pedidos",
        payments: "Pagos", 
        settings: "Configuración",
        logout: "Cerrar Sesión",
        help: "Ayuda",

        // Dashboard
        dashboard: "Panel",
        dataBalance: "Saldo de Datos",
        subscription: "Suscripción",
        offers: "Ofertas", 
        invitations: "Invitaciones",

        // Settings
        darkMode: "Modo Oscuro",
        language: "Idioma",

        // Language options
        english: "English",
        spanish: "Español", 
        french: "Francés",

        // Common
        cancel: "Cancelar",
        confirm: "Confirmar",
        save: "Guardar",
        close: "Cerrar",
        buy: "Comprar",
        subscribe: "Suscribirse",
        comingSoon: "Próximamente",

        // Offers
        globalPriorityData: "Datos Globales Prioritarios",
        basicMembership: "Membresía Básica",
        fullMembership: "Membresía Completa",

        // Help
        humanHelp: "Ayuda humana:",
        useAiHelp: "Usar ayuda IA:",
        orderCallback: "Order Callback",
        chatWithAgent: "Open Chat Now",

        // Beta
        requestBetaAccess: "Solicitar acceso BETA ($1 eSIM)",
        betaEnrollment: "Inscripción Beta"
    },

    fr: {
        // Navigation
        profile: "Profil",
        orders: "Commandes",
        payments: "Paiements",
        settings: "Paramètres", 
        logout: "Déconnexion",
        help: "Aide",

        // Dashboard
        dashboard: "Tableau de Bord",
        dataBalance: "Solde de Données",
        subscription: "Abonnement",
        offers: "Offres",
        invitations: "Invitations",

        // Settings
        darkMode: "Mode Sombre",
        language: "Langue",

        // Language options
        english: "English",
        spanish: "Español",
        french: "Français",

        // Common
        cancel: "Annuler",
        confirm: "Confirmer", 
        save: "Enregistrer",
        close: "Fermer",
        buy: "Acheter",
        subscribe: "S'abonner",
        comingSoon: "Bientôt Disponible",

        // Offers
        globalPriorityData: "Données Globales Prioritaires",
        basicMembership: "Adhésion de Base",
        fullMembership: "Adhésion Complète",

        // Help
        humanHelp: "Aide humaine:",
        useAiHelp: "Utiliser l'aide IA:",
        orderCallback: "Order Callback",
        chatWithAgent: "Open Chat Now",

        // Beta
        requestBetaAccess: "Demander l'accès BETA (1$ eSIM)",
        betaEnrollment: "Inscription Bêta"
    }
};

// Translation utility functions
let currentLanguage = localStorage.getItem('language') || 'en';

function t(key) {
    return translations[currentLanguage][key] || translations['en'][key] || key;
}

function setLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        localStorage.setItem('language', lang);
        updatePageTranslations();
    }
}

function updatePageTranslations() {
    // Update all elements with data-translate attribute
    const elementsToTranslate = document.querySelectorAll('[data-translate]');
    elementsToTranslate.forEach(element => {
        const key = element.getAttribute('data-translate');
        const translatedText = t(key);

        if (element.tagName === 'INPUT' && (element.type === 'button' || element.type === 'submit')) {
            element.value = translatedText;
        } else if (element.hasAttribute('placeholder')) {
            element.placeholder = translatedText;
        } else {
            // Preserve any icons by only updating text nodes
            const textNodes = [];
            element.childNodes.forEach(node => {
                if (node.nodeType === Node.TEXT_NODE) {
                    textNodes.push(node);
                }
            });

            if (textNodes.length > 0) {
                textNodes[0].textContent = translatedText;
            } else {
                element.textContent = translatedText;
            }
        }
    });

    // Update specific elements by ID
    updateSpecificElements();
}

function updateSpecificElements() {
    // Update language selector
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        languageSelect.value = currentLanguage;
    }

    // Update any dynamically generated content
    if (window.location.pathname === '/dashboard') {
        updateDashboardTranslations();
    }
}

function updateDashboardTranslations() {
    // Update offer cards if they exist
    const offerCards = document.querySelectorAll('.offer-card');
    offerCards.forEach(card => {
        const title = card.querySelector('h3');
        const button = card.querySelector('.offer-button');

        if (title && title.textContent.includes('Global Priority Data')) {
            title.textContent = t('globalPriorityData');
        } else if (title && title.textContent.includes('Basic Membership')) {
            title.textContent = t('basicMembership');
        } else if (title && title.textContent.includes('Full Membership')) {
            title.textContent = t('fullMembership');
        }

        if (button) {
            if (button.textContent === 'Buy') {
                button.textContent = t('buy');
            } else if (button.textContent === 'Subscribe') {
                button.textContent = t('subscribe');
            } else if (button.textContent === 'Coming Soon') {
                button.textContent = t('comingSoon');
            }
        }
    });
}

// Initialize translations when page loads
document.addEventListener('DOMContentLoaded', function() {
    updatePageTranslations();
});

// Make functions globally available
window.t = t;
window.setLanguage = setLanguage;
window.updatePageTranslations = updatePageTranslations;
window.currentLanguage = currentLanguage;