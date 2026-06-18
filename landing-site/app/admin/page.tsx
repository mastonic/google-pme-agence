"use client"

import { useState } from "react"

const WHITELIST = [
  "tontonmasto1@protonmail.com",
  "tontonmasto2@protonmail.com",
  "rigahludovic@gmail.com",
]

export default function AdminGatePage() {
  const [email, setEmail]   = useState("")
  const [denied, setDenied] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (WHITELIST.includes(email.trim().toLowerCase())) {
      window.location.href = "/app/"
    } else {
      setDenied(true)
    }
  }

  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "center",
      minHeight: "100vh", background: "#060D17", fontFamily: "'Inter', system-ui, sans-serif",
      padding: "24px",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600&display=swap');
        * { box-sizing: border-box; }
        .display { font-family: 'Syne', sans-serif; }
        @keyframes pulse-ring {
          0% { transform: scale(1); opacity: 0.6; }
          100% { transform: scale(2.2); opacity: 0; }
        }
        .pulse-dot {
          position: relative; display: inline-block;
          width: 10px; height: 10px; border-radius: 50%; background: #00E5B4;
        }
        .pulse-dot::before, .pulse-dot::after {
          content: ''; position: absolute; inset: 0;
          border-radius: 50%; background: #00E5B4;
          animation: pulse-ring 2s ease-out infinite;
        }
        .pulse-dot::after { animation-delay: 1s; }
        input:focus { outline: none; border-color: #00E5B4 !important; }
      `}</style>

      <div style={{
        width: "100%", maxWidth: 400,
        background: "#0A1622", border: "1px solid #1A3050",
        borderRadius: 20, padding: "40px 36px",
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 32, justifyContent: "center" }}>
          <span className="pulse-dot" />
          <span className="display" style={{ fontSize: 18, fontWeight: 800, color: "#fff" }}>
            Local<span style={{ color: "#00E5B4" }}>Pulse</span>
          </span>
        </div>

        <h1 style={{ fontSize: 22, fontWeight: 700, color: "#fff", marginBottom: 8, textAlign: "center" }}>
          Accès Administration
        </h1>
        <p style={{ fontSize: 14, color: "#6B8099", textAlign: "center", marginBottom: 28, lineHeight: 1.5 }}>
          Entrez votre adresse e-mail pour accéder à l&apos;outil.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <input
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setDenied(false) }}
            placeholder="votre@email.com"
            required
            autoFocus
            style={{
              background: "#0F1D2B", border: "1px solid #1A3050",
              borderRadius: 10, padding: "13px 16px",
              color: "#E8EDF2", fontSize: 14,
              transition: "border-color 0.2s",
            }}
          />

          {denied && (
            <div style={{
              background: "#ff444415", border: "1px solid #ff444430",
              borderRadius: 10, padding: "12px 16px",
              fontSize: 13, color: "#ff6666", lineHeight: 1.4,
            }}>
              Accès refusé. Cet e-mail n&apos;est pas autorisé.
            </div>
          )}

          <button
            type="submit"
            style={{
              background: "#00E5B4", color: "#060D17",
              border: "none", borderRadius: 10,
              padding: "14px", fontSize: 15, fontWeight: 600,
              cursor: "pointer", transition: "opacity 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.88")}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
          >
            Accéder →
          </button>
        </form>

        <p style={{ marginTop: 24, fontSize: 12, color: "#2E3F52", textAlign: "center" }}>
          Accès réservé à l&apos;équipe LocalPulse
        </p>
      </div>
    </div>
  )
}
