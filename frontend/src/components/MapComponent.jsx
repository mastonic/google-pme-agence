import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Search, Loader2 } from 'lucide-react';

const customIcon = new L.Icon({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

function MapEvents({ onScan, isScanning }) {
    const map = useMapEvents({
        moveend: () => {
            const center = map.getCenter();
            localStorage.setItem('lp_last_lat', center.lat);
            localStorage.setItem('lp_last_lng', center.lng);
        },
        zoomend: () => {
            localStorage.setItem('lp_last_zoom', map.getZoom());
        }
    });

    return (
        <div className="absolute top-6 right-6 z-[1000]">
            <button
                onClick={() => {
                    const center = map.getCenter();
                    onScan(center.lat, center.lng);
                }}
                disabled={isScanning}
                className="glass hover:bg-white/10 transition-all font-bold py-3 px-6 rounded-xl flex items-center space-x-2 shadow-xl border border-white/10 group active:scale-95 disabled:opacity-50"
            >
                {isScanning ? (
                    <Loader2 className="w-5 h-5 animate-spin text-brand" />
                ) : (
                    <Search className="w-5 h-5 text-brand group-hover:scale-110 transition-transform" />
                )}
                <span>{isScanning ? 'Analyse en cours...' : 'Scanner cette zone'}</span>
            </button>
        </div>
    );
}

function MapComponent({ businesses, onScan, isScanning, onSelectBusiness }) {
    // Read from localStorage or default to Paris
    const getInitialCenter = () => {
        const lat = localStorage.getItem('lp_last_lat');
        const lng = localStorage.getItem('lp_last_lng');
        if (lat && lng) {
            return [parseFloat(lat), parseFloat(lng)];
        }
        return [48.8566, 2.3522]; // Paris default
    };

    const getInitialZoom = () => {
        const zoom = localStorage.getItem('lp_last_zoom');
        return zoom ? parseInt(zoom, 10) : 13;
    };

    const initialCenter = getInitialCenter();
    const initialZoom = getInitialZoom();

    console.log('Map initial state:', { initialCenter, initialZoom });

    const MapViewSetter = () => {
        const map = useMapEvents({});
        React.useEffect(() => {
            const lat = localStorage.getItem('lp_last_lat');
            const lng = localStorage.getItem('lp_last_lng');
            const zoom = localStorage.getItem('lp_last_zoom');
            if (lat && lng && map) {
                map.setView([parseFloat(lat), parseFloat(lng)], zoom ? parseInt(zoom, 10) : map.getZoom());
            }
        }, [map]);
        return null;
    };

    return (
        <div className="w-full h-full">
            <MapContainer center={initialCenter} zoom={initialZoom} scrollWheelZoom={true} zoomControl={false}>
                <MapViewSetter />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {businesses.filter(b => b.latitude && b.longitude).map((biz) => (
                    <Marker
                        key={biz.id}
                        position={[biz.latitude, biz.longitude]}
                        icon={customIcon}
                        eventHandlers={{
                            click: () => onSelectBusiness(biz),
                        }}
                    >
                        <Popup className="lp-popup">
                            <div className="text-slate-900 !m-0">
                                <h3 className="font-bold text-lg">{biz.name}</h3>
                                <p className="text-xs text-slate-500 mb-2">{biz.address}</p>
                                <div className="flex items-center justify-between">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Potentiel</span>
                                    <span className="text-brand font-bold text-xl">{biz.potential_score}</span>
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}

                <MapEvents onScan={onScan} isScanning={isScanning} />
            </MapContainer>
        </div>
    );
}

export default MapComponent;
