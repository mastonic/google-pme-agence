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

function MapEvents({ onScan, isScanning }) {
    const map = useMapEvents({
        moveend: () => {
            const c = map.getCenter();
            localStorage.setItem('lp_last_lat', c.lat);
            localStorage.setItem('lp_last_lng', c.lng);
        },
        zoomend: () => localStorage.setItem('lp_last_zoom', map.getZoom()),
    });

    return (
        <div className="absolute top-6 right-6 z-[1000]">
            <button
                onClick={() => { const c = map.getCenter(); onScan(c.lat, c.lng); }}
                disabled={isScanning}
                className="glass hover:bg-white/10 transition-all font-bold py-3 px-5 rounded-xl flex items-center space-x-2 shadow-xl border border-white/10 active:scale-95 disabled:opacity-50"
            >
                {isScanning
                    ? <Loader2 className="w-4 h-4 animate-spin text-brand" />
                    : <Search className="w-4 h-4 text-brand" />
                }
                <span className="text-sm">{isScanning ? 'Analyse...' : 'Scanner ici'}</span>
            </button>
        </div>
    );
}

function MapComponent({ businesses, onScan, isScanning, onSelectBusiness, centerTarget }) {
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
    }, [businesses]);

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
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {centerTarget && <MapPanner centerTarget={centerTarget} />}

                {businesses.filter(b => b.latitude && b.longitude).map((biz) => {
                    const color = biz.potential_score >= 8 ? '#10b981' : biz.potential_score >= 6 ? '#f59e0b' : '#64748b';
                    const scoreIcon = L.divIcon({
                        className: '',
                        html: `<div style="background:${color};color:white;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:11px;box-shadow:0 0 12px ${color}80;border:2px solid rgba(255,255,255,0.3)">${biz.potential_score}</div>`,
                        iconSize: [32, 32], iconAnchor: [16, 16]
                    });
                    return (
                        <Marker key={biz.id} position={[biz.latitude, biz.longitude]} icon={scoreIcon}
                            eventHandlers={{ click: () => onSelectBusiness(biz) }}>
                            <Popup>
                                <div className="text-slate-900">
                                    <h3 className="font-bold text-base">{biz.name}</h3>
                                    <p className="text-xs text-slate-500 mt-1">{biz.address}</p>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}

                <MapEvents onScan={onScan} isScanning={isScanning} />
            </MapContainer>
        </div>
    );
}

export default MapComponent;
