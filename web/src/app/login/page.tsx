"use client";

import { Suspense, useEffect } from "react";
import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { AlephMark } from "@/components/aleph-mark";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 text-center">
      <div className="flex items-center gap-2.5">
        <AlephMark />
        <span className="text-base font-semibold uppercase tracking-[0.22em]">ALEPH</span>
      </div>
      <Suspense fallback={<SignInPanel expired={false} />}>
        <LoginInner />
      </Suspense>
    </div>
  );
}

function LoginInner() {
  const params = useSearchParams();
  return (
    <SignInPanel
      expired={params.get("reason") === "expired"}
      callbackUrl={params.get("callbackUrl") || "/"}
    />
  );
}

function SignInPanel({ expired, callbackUrl = "/" }: { expired: boolean; callbackUrl?: string }) {
  useEffect(() => {
    // Login normal: auto-redirige a Microsoft. Sesión expirada: deja que el usuario decida (evita bucles).
    if (!expired) void signIn("microsoft-entra-id", { callbackUrl });
  }, [expired, callbackUrl]);

  return (
    <div className="flex max-w-xs flex-col items-center gap-4">
      <p className="text-sm text-muted-foreground">
        {expired
          ? "Tu sesión expiró. Vuelve a iniciar sesión para continuar."
          : "Plataforma de evaluación financiera · CG Constructora. Inicia sesión con tu cuenta corporativa de Microsoft."}
      </p>
      <button
        type="button"
        onClick={() => void signIn("microsoft-entra-id", { callbackUrl })}
        className="inline-flex items-center gap-2 rounded-[var(--radius-data)] bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-[opacity,transform] [transition-timing-function:var(--ease-out)] hover:opacity-90 active:scale-[0.98]"
      >
        Entrar con Microsoft
      </button>
      {!expired && <p className="text-xs text-muted-foreground">Redirigiendo a Microsoft…</p>}
    </div>
  );
}
