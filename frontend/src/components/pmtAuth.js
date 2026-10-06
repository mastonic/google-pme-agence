import axios from 'axios';

// Session du module transport sanitaire : jeton Bearer ajouté à toutes les
// requêtes /pmt. Un 401 renvoie vers l'écran de connexion.

const KEY = 'lp_pmt_session';

export const loadSession = () => {
    try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch { return null; }
};

export const saveSession = (session) => {
    try {
        if (session) localStorage.setItem(KEY, JSON.stringify(session));
        else localStorage.removeItem(KEY);
    } catch { /* stockage indisponible : la session ne survivra pas au rechargement */ }
};

let installed = false;

export function installPmtInterceptors(onUnauthorized) {
    if (installed) return;
    installed = true;
    axios.interceptors.request.use(config => {
        const session = loadSession();
        if (session?.token && String(config.url || '').startsWith('/pmt') && !config.url.startsWith('/pmt/auth/login')) {
            config.headers = { ...(config.headers || {}), Authorization: `Bearer ${session.token}` };
        }
        return config;
    });
    axios.interceptors.response.use(r => r, error => {
        const url = String(error?.config?.url || '');
        if (error?.response?.status === 401 && url.startsWith('/pmt') && !url.startsWith('/pmt/auth/login')) {
            saveSession(null);
            onUnauthorized?.();
        }
        return Promise.reject(error);
    });
}

// Les fiches et scans sont protégés : on les télécharge avec le jeton puis on
// les ouvre localement (un simple lien n'enverrait pas l'en-tête Authorization).
export async function openProtected(url) {
    const w = window.open('', '_blank');
    try {
        const r = await axios.get(url, { responseType: 'blob' });
        const objectUrl = URL.createObjectURL(r.data);
        if (w) w.location = objectUrl; else window.location.assign(objectUrl);
        setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
    } catch (e) {
        if (w) w.close();
        window.alert(e?.response?.status === 404 ? 'Document introuvable.' : 'Ouverture impossible.');
    }
}
