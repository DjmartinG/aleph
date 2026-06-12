# docs — decisiones de arquitectura (ADRs)

Registro de las decisiones de arquitectura de **ALEPH** (Architecture Decision Records). Cada ADR
captura UNA decisión: su contexto, la opción elegida y sus consecuencias. Son inmutables: si una
decisión cambia, se escribe un ADR nuevo que **supersede** al anterior (no se reescribe el viejo).

> La **constitución gobernante** del producto vive en `../CLAUDE.md` (§ALEPH). Los ADRs no la
> reemplazan: explican el *por qué* de decisiones concretas tomadas durante la migración.

## Índice
| ADR | Decisión | Estado |
|---|---|---|
| [0001](adr/0001-estrangulamiento-progresivo.md) | Migrar por estrangulamiento progresivo (no big-bang) | Aceptado |
| [0002](adr/0002-monorepo-un-solo-repo.md) | Monorepo en UN solo repositorio (`aleph`) | Aceptado |
| [0003](adr/0003-snapshot-dorado.md) | Snapshot dorado como red de seguridad de la migración | Aceptado |
| [0004](adr/0004-version-heredada-del-motor.md) | `aleph_engine` hereda la versión del motor (2.39.0) | Aceptado |
| [0005](adr/0005-deploy-por-sha-imagen-bundle.md) | Deploy por SHA; la imagen empaqueta el motor | Aceptado |
