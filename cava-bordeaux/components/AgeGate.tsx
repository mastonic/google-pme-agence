"use client";

import { useEffect, useState } from "react";

const COOKIE_NAME = "cdb_age_verified";
const COOKIE_MAX_AGE_DAYS = 30;

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

function writeCookie(name: string, value: string, days: number) {
  const maxAge = days * 24 * 60 * 60;
  document.cookie = `${name}=${value}; max-age=${maxAge}; path=/; SameSite=Lax`;
}

export default function AgeGate() {
  const [status, setStatus] = useState<"checking" | "verified" | "gate" | "blocked">(
    "checking"
  );

  useEffect(() => {
    const cookie = readCookie(COOKIE_NAME);
    setStatus(cookie === "1" ? "verified" : "gate");
  }, []);

  useEffect(() => {
    document.body.style.overflow = status === "gate" || status === "blocked" ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [status]);

  if (status === "checking" || status === "verified") {
    return null;
  }

  const isBlocked = status === "blocked";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Verificación de edad"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-ink/90 px-4 backdrop-blur-sm"
    >
      <div className="w-full max-w-md rounded-lg border border-gold-500/30 bg-cream p-8 text-center shadow-2xl">
        <p className="font-serif text-2xl text-bordeaux-800">Cava de Bordeaux</p>

        {isBlocked ? (
          <div className="mt-6 space-y-4">
            <p className="text-ink/90">
              Lo sentimos, este sitio está reservado a personas mayores de 18 años. No es
              posible continuar la navegación.
            </p>
            <button
              type="button"
              onClick={() => setStatus("gate")}
              className="text-sm text-bordeaux-600 underline underline-offset-2"
            >
              Volver
            </button>
          </div>
        ) : (
          <div className="mt-6 space-y-6">
            <p className="text-ink/90">
              Este sitio presenta bebidas alcohólicas. Debes ser mayor de 18 años para
              acceder al catálogo y realizar una compra.
            </p>
            <p className="text-sm font-medium text-ink">¿Confirmas que eres mayor de 18 años?</p>
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
              <button
                type="button"
                onClick={() => {
                  writeCookie(COOKIE_NAME, "1", COOKIE_MAX_AGE_DAYS);
                  setStatus("verified");
                }}
                className="rounded-md bg-bordeaux-700 px-6 py-3 text-sm font-semibold text-cream transition hover:bg-bordeaux-800"
              >
                Sí, soy mayor de 18 años
              </button>
              <button
                type="button"
                onClick={() => setStatus("blocked")}
                className="rounded-md border border-ink/20 px-6 py-3 text-sm font-semibold text-ink/70 transition hover:bg-ink/5"
              >
                No
              </button>
            </div>
            <p className="text-xs text-ink/50">
              Venta exclusiva a mayores de edad. Consumo con moderación.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
