import React, { useEffect, useRef, useState } from 'react'
import { Camera, X, Search } from 'lucide-react'
import { loadParapheurs } from '../store.js'

export default function Scanner({ onFound }) {
  const [mode, setMode] = useState('manual') // 'camera' | 'manual'
  const [manualRef, setManualRef] = useState('')
  const [error, setError] = useState('')
  const [scanning, setScanning] = useState(false)
  const videoRef = useRef(null)
  const streamRef = useRef(null)

  useEffect(() => {
    return () => stopCamera()
  }, [])

  async function startCamera() {
    setError('')
    setScanning(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
      }
      setMode('camera')
      scanLoop()
    } catch (e) {
      setError('Impossible d\'accéder à la caméra. Utilisez la recherche manuelle.')
      setScanning(false)
    }
  }

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    setScanning(false)
  }

  async function scanLoop() {
    if (!('BarcodeDetector' in window)) {
      setError('Détecteur QR non disponible. Utilisez la recherche manuelle.')
      stopCamera()
      return
    }
    const detector = new BarcodeDetector({ formats: ['qr_code'] })
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    const tick = async () => {
      if (!videoRef.current || !streamRef.current) return
      const video = videoRef.current
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        ctx.drawImage(video, 0, 0)
        try {
          const barcodes = await detector.detect(canvas)
          if (barcodes.length > 0) {
            const raw = barcodes[0].rawValue
            handleQRData(raw)
            return
          }
        } catch {}
      }
      if (streamRef.current) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }

  function handleQRData(raw) {
    stopCamera()
    // Format: CAPSUD-PAR:{id}:{ref}
    const match = raw.match(/^CAPSUD-PAR:([^:]+):(.+)$/)
    if (!match) {
      setError(`QR Code non reconnu : ${raw}`)
      return
    }
    const [, id, ref] = match
    const list = loadParapheurs()
    const found = list.find(p => p.id === id)
    if (!found) {
      setError(`Parapheur ${ref} introuvable sur cet appareil.`)
      return
    }
    onFound(found)
  }

  function handleManualSearch() {
    const ref = manualRef.trim().toUpperCase()
    const list = loadParapheurs()
    const found = list.find(p => p.reference === ref || p.reference.includes(ref))
    if (found) {
      onFound(found)
    } else {
      setError(`Aucun parapheur trouvé pour "${manualRef}"`)
    }
  }

  return (
    <div className="fade-in">
      <div className="header-banner" style={{ marginBottom: 16 }}>
        <h2>Scanner QR</h2>
        <p>Accès rapide par code QR ou référence</p>
      </div>

      {mode === 'camera' ? (
        <div className="card">
          <div className="scanner-area">
            <video ref={videoRef} style={{ width: '100%', height: '100%', objectFit: 'cover' }} playsInline muted />
            <div className="scanner-overlay">
              <div className="scanner-frame" />
            </div>
          </div>
          <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--cs-muted)', margin: '12px 0' }}>
            Pointez la caméra vers le QR Code du parapheur
          </p>
          <button className="btn btn-secondary btn-full" onClick={() => { stopCamera(); setMode('manual') }}>
            <X size={16} /> Arrêter le scan
          </button>
        </div>
      ) : (
        <div className="card">
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'var(--cs-gris)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', color: 'var(--cs-bleu)' }}>
              <Camera size={36} />
            </div>
            <p style={{ fontSize: 14, color: 'var(--cs-muted)', marginBottom: 16 }}>
              Scannez le QR Code collé sur le dossier physique
            </p>
            <button className="btn btn-primary btn-full" onClick={startCamera}>
              <Camera size={16} /> Ouvrir la caméra
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="alert-item danger" style={{ marginTop: 12 }}>
          <div className="alert-icon">⚠️</div>
          <div className="alert-body">
            <div className="alert-title">Erreur</div>
            <div className="alert-desc">{error}</div>
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: 12 }}>
        <div className="section-title">Recherche manuelle</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            className="form-input"
            style={{ flex: 1 }}
            placeholder="Ex: PAR-2026-1234"
            value={manualRef}
            onChange={e => setManualRef(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleManualSearch()}
          />
          <button className="btn btn-primary" onClick={handleManualSearch} disabled={!manualRef.trim()}>
            <Search size={16} />
          </button>
        </div>
        <p className="form-hint" style={{ marginTop: 6 }}>Entrez la référence imprimée sur la fiche QR</p>
      </div>

      <div className="card">
        <div className="section-title">Comment ça marche ?</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {[
            ['1', 'Créez un parapheur depuis le dashboard'],
            ['2', 'Imprimez la fiche avec le QR Code unique'],
            ['3', 'Collez-la sur le dossier physique'],
            ['4', 'Scannez depuis n\'importe quel smartphone pour suivre et valider'],
          ].map(([n, t]) => (
            <div key={n} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--cs-bleu)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>{n}</div>
              <p style={{ fontSize: 13, color: 'var(--cs-texte)', paddingTop: 3 }}>{t}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
