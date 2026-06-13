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
      <p className="max-w-xs text-sm text-muted-foreground">
        Plataforma de evaluación financiera · CG Constructora. Inicia sesión con tu cuenta
        corporativa de Microsoft.
      </p>
      <Suspense fallback={<Hint />}>
        <SignInTrigger />
      </Suspense>
    </div>
  );
}

function SignInTrigger() {
  const callbackUrl = useSearchParams().get("callbackUrl") || "/";
  useEffect(() => {
    void signIn("microsoft-entra-id", { callbackUrl });
  }, [callbackUrl]);
  return (
    <div className="flex flex-col items-center gap-3">
      <button
        type="button"
        onClick={() => void signIn("microsoft-entra-id", { callbackUrl })}
        className="inline-flex items-center gap-2 rounded-[var(--radius-data)] bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity [transition-timing-function:var(--ease-out)] hover:opacity-90"
      >
        Entrar con Microsoft
      </button>
      <Hint />
    </div>
  );
}

function Hint() {
  return <p className="text-xs text-muted-foreground">Redirigiendo a Microsoft…</p>;
}
