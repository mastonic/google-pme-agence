import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Search, Loader2 } from 'lucide-react';

const customIcon = new L.Icon({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});

// Component that pans the map when centerTarget changes
function MapPanner({ centerTarget }) {
    const map = useMap();
    useEffect(() => {
        if (centerTarget) {
            map.setView([centerTarget.lat, centerTarget.lng], 14, { animate: true });
        }
    }, [centerTarget]);
    return null;
}

export const METIER_SUGGESTIONS = [
    'Plombier', 'Électricien', 'Serrurier', 'Couvreur', 'Peintre en bâtiment', 'Maçon', 'Menuisier',
    'Climaticien', 'Paysagiste', 'Boulangerie', 'Restaurant', 'Coiffeur', 'Esthéticienne', 'Garage',
    'Taxi', 'Kiné', 'Dentiste', 'Agence immobilière', 'Fleuriste', 'Salle de sport',
];

function MapEvents({ onScan, isScanning, metier = '', setMetier }) {
    const map = useMapEvents({
        moveend: () => {
            const c = map.getCenter();
            localStorage.setItem('lp_last_lat', c.lat);
            localStorage.setItem('lp_last_lng', c.lng);
        },
        zoomend: () => localStorage.setItem('lp_last_zoom', map.getZoom()),
    });

    const scan = () => {
        if (isScanning) return;
        const c = map.getCenter();
        onScan(c.lat, c.lng, metier.trim());
    };

    return (
        <form
            onSubmit={(e) => { e.preventDefault(); scan(); }}
            // Les clics et la molette dans le formulaire ne doivent pas déplacer la carte.
            onMouseDown={(e) => e.stopPropagation()}
            onDoubleClick={(e) => e.stopPropagation()}
            onWheel={(e) => e.stopPropagation()}
            className="absolute top-4 right-4 left-4 sm:left-auto sm:top-6 sm:right-6 z-[1000] flex gap-2 bg-slate-900/95 border border-white/10 rounded-xl p-2 shadow-xl"
        >
            <input
                type="text"
                list="lp-metiers-map"
                value={metier}
                onChange={(e) => setMetier(e.target.value)}
                placeholder="Métier (ex. plombier) — vide = tous"
                aria-label="Métier à rechercher"
                maxLength={80}
                className="flex-1 sm:w-64 min-w-0 bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-brand"
            />
            <datalist id="lp-metiers-map">
                {METIER_SUGGESTIONS.map((m) => <option key={m} value={m} />)}
            </datalist>
            {metier && (
                <button type="button" onClick={() => setMetier('')} aria-label="Effacer le métier"
                    className="px-2 text-slate-400 hover:text-white">✕</button>
            )}
            <button
                type="submit"
                disabled={isScanning}
                className="bg-brand hover:bg-brand-dark transition-all font-bold py-2 px-4 rounded-lg flex items-center space-x-2 active:scale-95 disabled:opacity-50 text-white whitespace-nowrap"
            >
                {isScanning
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Search className="w-4 h-4" />
                }
                <span className="text-sm">{isScanning ? 'Analyse...' : metier.trim() ? 'Chercher ici' : 'Scanner ici'}</span>
            </button>
        </form>
    );
}

function MapComponent({ businesses, onScan, isScanning, onSelectBusiness, centerTarget, metier, setMetier }) {
    const getInitialCenter = () => {
        const lat = localStorage.getItem('lp_last_lat');
        const lng = localStorage.getItem('lp_last_lng');
        return lat && lng ? [parseFloat(lat), parseFloat(lng)] : [48.8566, 2.3522];
    };
    const getInitialZoom = () => {
        const z = localStorage.getItem('lp_last_zoom');
        return z ? parseInt(z) : 13;
    };

    const [map, setMap] = React.useState(null);

    useEffect(() => {
        if (map && businesses.length > 0) {
            const markers = businesses.filter(b => b.latitude && b.longitude);
            if (markers.length > 0) {
                map.fitBounds(L.latLngBounds(markers.map(b => [b.latitude, b.longitude])), { padding: [50, 50], maxZoom: 15 });
            }
        }
    }, [businesses, map]);

    useEffect(() => {
        if (map) {
            const ro = new ResizeObserver(() => map.invalidateSize());
            ro.observe(map.getContainer());
            return () => ro.disconnect();
        }
    }, [map]);

    return (
        <div className="w-full h-full relative">
            <MapContainer
                center={getInitialCenter()}
                zoom={getInitialZoom()}
                scrollWheelZoom={true}
                zoomControl={false}
                ref={setMap}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                    maxZoom={19}
                />

                {centerTarget && <MapPanner centerTarget={centerTarget} />}

                {(Array.isArray(businesses) ? businesses : [])
                    .filter(b => Number.isFinite(Number(b.latitude)) && Number.isFinite(Number(b.longitude)))
                    .map((biz) => {
                    const rawOpportunity = Number(biz.opportunity_score);
                    const hasOpportunity = Number.isFinite(rawOpportunity);
                    const opportunity = hasOpportunity ? Math.round(rawOpportunity) : null;
                    const color = !hasOpportunity ? '#475569' : opportunity >= 78 ? '#ef4444' : opportunity >= 62 ? '#f59e0b' : opportunity >= 45 ? '#3b82f6' : '#64748b';
                    const markerLabel = hasOpportunity ? String(opportunity) : '?';
                    const scoreIcon = L.divIcon({
                        className: '',
                        html: `<div title="Opportunity Score ${hasOpportunity ? opportunity + '/100' : 'en calcul'}" style="background:${color};color:white;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;box-shadow:0 0 14px ${color}99;border:2px solid rgba(255,255,255,0.45)">${markerLabel}</div>`,
                        iconSize: [38, 38], iconAnchor: [19, 19]
                    });
                    return (
                        <Marker key={biz.id} position={[biz.latitude, biz.longitude]} icon={scoreIcon}
                            eventHandlers={{ click: () => onSelectBusiness(biz) }}>
                            <Popup>
                                <div className="text-slate-900">
                                    <h3 className="font-bold text-base">{biz.name}</h3>
                                    <p className="text-xs text-slate-500 mt-1">{biz.address}</p>
                                    <p className="text-xs font-semibold mt-2">
                                        Opportunité {Number.isFinite(Number(biz.opportunity_score)) ? Math.round(Number(biz.opportunity_score)) : '—'}/100
                                        {' · '}Digital {Number.isFinite(Number(biz.digital_health_score)) ? Math.round(Number(biz.digital_health_score)) : '—'}/100
                                    </p>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}

                <MapEvents onScan={onScan} isScanning={isScanning} metier={metier} setMetier={setMetier} />
            </MapContainer>
        </div>
    );
}

export default MapComponent;
