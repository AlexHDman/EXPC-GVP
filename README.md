# EXPC-GVP — EXPC Global Vocabulary Pack

<p align="center">
  <img src="assets/github-header.png" alt="EXPC-GVP — Global Vocabulary Pack" width="100%">
</p>

## Status

**Early development / Phase 01.0.** A vocabulary entity schema
(`schema/gvp.schema.json`), a small curated fixture dataset
(`data/curated/`), and an early Builder MVP (`tools/builder/`, see
`docs/04_BUILDER.md`) exist. The Builder validates the fixture data and
produces an intermediate `dist/gvp.json` artifact — it is not a compiled
data package, and there is no updater, manifest, or release yet. This
README describes the intended purpose and shape of the project, not
features that are not yet implemented.

## What this is

EXPC-GVP (EXPC Global Vocabulary Pack) is a **standalone public data project**.
It is not an application and does not depend on any single consumer. Its goal
is to become a canonical, versioned vocabulary — names, terms, aliases, and
spoken forms — that other systems can consume as a shared source of truth.

## Purpose

EXPC-GVP is intended to serve as a **global canonical vocabulary**: a single
place where entity names (brands, software, AI systems, hardware, standards,
networking terms, and similar categories) are recorded once, with their
canonical original spelling, so that multiple independent consumers do not
each maintain their own divergent copy.

## Intended consumers

The vocabulary pack is designed to be consumed by, among others:

- **EXPC-WLK**
- **AI Switcher**
- **EXPC NewsBot**
- future third-party consumers not yet identified

## Canonical spelling and aliases

- The **canonical original spelling** of a term or name always has priority.
- **Aliases and spoken forms** are supported *conceptually* as part of the
  intended design — how a term is written, spoken, abbreviated, or referred
  to informally.
- Some aliases are inherently **ambiguous** (they may map to more than one
  canonical entity). Resolving these requires **context-aware logic** in
  consuming systems; EXPC-GVP does not claim to resolve ambiguity by itself.

## Layers

The vocabulary is intended to be organized in layers:

1. **Global** — universally applicable entries.
2. **Domain** — entries specific to a subject-matter domain.
3. **Organization** — entries scoped to a particular organization.
4. **Personal** — entries scoped to an individual user or context.

## Privacy boundary

EXPC-GVP is a **public** project. Only public, non-personal vocabulary data
is in scope for this repository. Personal, private, or organization-internal
data is explicitly out of scope for the public pack (see `SECURITY.md`).

## Builder (Phase 01.0 MVP)

A minimal, working Builder exists at `tools/builder/`. Run from the
repository root:

```
py -3.12 -m tools.builder build
```

It loads `data/curated/*.json`, validates each entity against
`schema/gvp.schema.json`, runs semantic and collision checks, and writes a
deterministic `dist/gvp.json`. See `docs/04_BUILDER.md` for the full
pipeline, output format, and — importantly — what it does *not* do yet
(no SQLite, no manifest, no updater, no CI, no external source ingestion).

## Planned distribution model

Data is intended to be distributed as versioned packages, roughly as:

```
GitHub Releases -> manifest.json -> versioned data package -> SHA-256 -> atomic update
```

This distribution mechanism is **not implemented yet**. It describes the
intended direction, not current behavior.

## Explicitly not implemented yet

The following do not exist in the repository at this stage and should not be
assumed to work:

- a SQLite (or any other) compiled data pack
- an updater/manifest mechanism
- GitHub Actions / CI
- GitHub Releases
- any Wikidata import or other bulk external dataset
- ingestion from any source other than `data/curated/*.json`

The schema, fixture data, and Builder that do exist (`schema/`,
`data/curated/`, `tools/builder/`) validate and build from that fixture
data — they are not a production dataset or pipeline — see
`docs/01_DATA_SCHEMA.md`, `docs/04_BUILDER.md`, and `SOURCES.md`.

## Related documents

- `docs/00_ARCHITECTURE.md` — conceptual pipeline and versioning model
- `docs/01_DATA_SCHEMA.md` — the entity schema, field by field
- `docs/02_VOCABULARY_LAYERS.md` — Global / Domain / Organization / Personal
- `docs/03_COLLISION_POLICY.md` — ambiguity levels and collision handling
- `docs/04_BUILDER.md` — the Phase 01.0 Builder MVP
- `SOURCES.md` — source policy foundation (no data formally reviewed/imported yet)
- `THIRD_PARTY_NOTICES.md` — third-party notices (none yet)
- `CONTRIBUTING.md` — contribution flow
- `SECURITY.md` — security and privacy reporting
- `LICENSE` — licensing status and open decisions

---

# EXPC-GVP — EXPC Global Vocabulary Pack (Русский)

## Статус

**Ранняя разработка / Phase 01.0.** Существуют схема словарной сущности
(`schema/gvp.schema.json`), небольшой curated fixture датасет
(`data/curated/`) и ранний Builder MVP (`tools/builder/`, см.
`docs/04_BUILDER.md`). Builder валидирует fixture-данные и создаёт
промежуточный артефакт `dist/gvp.json` — это не скомпилированный пакет
данных, updater, manifest или релиз пока не существуют. Этот README
описывает назначение и планируемую форму проекта, а не только уже
реализованные функции.

## Что это

EXPC-GVP (EXPC Global Vocabulary Pack) — это **самостоятельный публичный
data-проект**. Это не приложение, и он не зависит от какого-либо одного
потребителя. Цель проекта — стать каноническим, версионируемым словарём
(названия, термины, алиасы и произносимые формы), который другие системы
могут использовать как общий источник истины.

## Назначение

EXPC-GVP задуман как **глобальный канонический словарь**: единое место, где
названия сущностей (бренды, программное обеспечение, AI-системы, hardware,
стандарты, сетевые термины и подобные категории) фиксируются один раз, с их
канонической оригинальной орфографией, чтобы несколько независимых
потребителей не вели каждый свою расходящуюся копию.

## Предполагаемые потребители

Vocabulary pack предназначен, среди прочего, для:

- **EXPC-WLK**
- **AI Switcher**
- **EXPC NewsBot**
- будущих сторонних потребителей, ещё не определённых

## Каноническое написание и алиасы

- **Каноническое оригинальное написание** термина или имени всегда имеет
  приоритет.
- **Алиасы и произносимые формы** поддерживаются *концептуально* как часть
  задуманного дизайна — как термин пишется, произносится, сокращается или
  упоминается неформально.
- Некоторые алиасы по своей природе **неоднозначны** (могут соответствовать
  более чем одной канонической сущности). Разрешение такой неоднозначности
  требует **context-aware логики** в потребляющих системах; сам EXPC-GVP не
  заявляет, что разрешает неоднозначность самостоятельно.

## Слои

Словарь задуман как организованный по слоям:

1. **Global** — универсально применимые записи.
2. **Domain** — записи, специфичные для предметной области.
3. **Organization** — записи, ограниченные конкретной организацией.
4. **Personal** — записи, ограниченные конкретным пользователем или контекстом.

## Граница приватности

EXPC-GVP — **публичный** проект. В область этого репозитория входят только
публичные, неперсональные данные словаря. Личные, приватные или
внутриорганизационные данные явно исключены из публичного пакета (см.
`SECURITY.md`).

## Builder (Phase 01.0 MVP)

Минимальный рабочий Builder существует в `tools/builder/`. Запуск из
корня репозитория:

```
py -3.12 -m tools.builder build
```

Он загружает `data/curated/*.json`, валидирует каждую сущность против
`schema/gvp.schema.json`, выполняет semantic- и collision-проверки и
записывает детерминированный `dist/gvp.json`. Полное описание pipeline,
формата output и — что важно — того, чего Builder пока НЕ делает (нет
SQLite, manifest, updater, CI, импорта внешних источников) — см.
`docs/04_BUILDER.md`.

## Планируемая модель доставки

Данные предполагается распространять как версионируемые пакеты, примерно
по схеме:

```
GitHub Releases -> manifest.json -> versioned data package -> SHA-256 -> atomic update
```

Этот механизм доставки **пока не реализован**. Он описывает планируемое
направление, а не текущее поведение.

## Явно не реализовано на этом этапе

Следующее не существует в репозитории на данном этапе и не должно
считаться работающим:

- скомпилированный пакет данных (SQLite или любой другой)
- механизм updater/manifest
- GitHub Actions / CI
- GitHub Releases
- импорт Wikidata или любого другого массового внешнего датасета
- загрузка данных из чего-либо, кроме `data/curated/*.json`

Существующие схема, fixture-данные и Builder (`schema/`, `data/curated/`,
`tools/builder/`) валидируют и собирают именно эти fixture-данные — это не
production-датасет и не готовый pipeline — см. `docs/01_DATA_SCHEMA.md`,
`docs/04_BUILDER.md` и `SOURCES.md`.

## Связанные документы

- `docs/00_ARCHITECTURE.md` — концептуальный pipeline и модель версионирования
- `docs/01_DATA_SCHEMA.md` — схема сущности, поле за полем
- `docs/02_VOCABULARY_LAYERS.md` — Global / Domain / Organization / Personal
- `docs/03_COLLISION_POLICY.md` — уровни неоднозначности и обработка коллизий
- `docs/04_BUILDER.md` — Phase 01.0 Builder MVP
- `SOURCES.md` — основа source policy (данные пока не прошли формальную проверку/импорт)
- `THIRD_PARTY_NOTICES.md` — уведомления о сторонних данных (пока нет)
- `CONTRIBUTING.md` — процесс участия в проекте
- `SECURITY.md` — безопасность и приватность
- `LICENSE` — статус лицензирования и открытые решения
