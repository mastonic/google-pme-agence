import axios from 'axios';

// Jeton administrateur du cockpit (ADMIN_API_TOKEN côté backend).
// Installé une seule fois sur l'instance axios par défaut : tous les composants
// l'utilisent déjà, donc aucun appel n'a besoin de le gérer.
const STORAGE_KEY = 'lp_admin_token';

let pendingPrompt = null;

function readToken() {
    try {
        return localStorage.getItem(STORAGE_KEY) || '';
    } catch {
        return '';
    }
}

function writeToken(token) {
    try {
        if (token) localStorage.setItem(STORAGE_KEY, token);
        else localStorage.removeItem(STORAGE_KEY);
    } catch {
        // stockage indisponible (navigation privée) : le jeton sera redemandé
    }
}

// Demande le jeton une seule fois même si plusieurs requêtes échouent en parallèle.
function promptForToken() {
    if (!pendingPrompt) {
        pendingPrompt = Promise.resolve().then(() => {
            const token = window.prompt('Jeton administrateur Local-Pulse :', '') || '';
            writeToken(token.trim());
            return token.trim();
        }).finally(() => {
            pendingPrompt = null;
        });
    }
    return pendingPrompt;
}

export function installAdminAuth() {
    axios.interceptors.request.use((config) => {
        const token = readToken();
        if (token) config.headers.Authorization = `Bearer ${token}`;
        return config;
    });

    axios.interceptors.response.use(
        (response) => response,
        async (error) => {
            const config = error.config;
            if (error.response?.status !== 401 || !config || config._adminRetry) {
                throw error;
            }
            // Jeton absent ou invalide : on le redemande, puis on rejoue la requête une fois.
            writeToken('');
            const token = await promptForToken();
            if (!token) throw error;
            config._adminRetry = true;
            config.headers.Authorization = `Bearer ${token}`;
            return axios.request(config);
        },
    );
}
