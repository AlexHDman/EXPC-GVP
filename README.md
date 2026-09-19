# EXPC-GVP — EXPC Global Vocabulary Pack

<p align="center">
  <img src="assets/github-header.png" alt="EXPC-GVP — Global Vocabulary Pack" width="100%">
</p>

## Status

**Early development / Phase 00.** A vocabulary entity schema
(`schema/gvp.schema.json`) and a small curated fixture dataset
(`data/curated/`) exist as of Phase 00.2, for validating the data model
itself. No builder, no compiled data package, no updater, and no releases
exist yet. This README describes the intended purpose and shape of the
project, not features that are currently implemented.

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

- a builder/pipeline
- a SQLite (or any other) compiled data pack
- an updater/manifest mechanism
- GitHub Actions / CI
- GitHub Releases
- any Wikidata import or other bulk external dataset

The schema and fixture data that do exist (`schema/`, `data/curated/`) are
for validating the data model, not a production dataset — see
`docs/01_DATA_SCHEMA.md` and `SOURCES.md`.

## Related documents

- `docs/00_ARCHITECTURE.md` — conceptual pipeline and versioning model
- `docs/01_DATA_SCHEMA.md` — the entity schema, field by field
- `docs/02_VOCABULARY_LAYERS.md` — Global / Domain / Organization / Personal
- `docs/03_COLLISION_POLICY.md` — ambiguity levels and collision handling
- `SOURCES.md` — source policy foundation (no data formally reviewed/imported yet)
- `THIRD_PARTY_NOTICES.md` — third-party notices (none yet)
- `CONTRIBUTING.md` — contribution flow
- `SECURITY.md` — security and privacy reporting
- `LICENSE` — licensing status and open decisions

---

# EXPC-GVP — EXPC Global Vocabulary Pack (Русский)

## Статус

**Ранняя разработка / Phase 00.** По состоянию на Phase 00.2 существуют схема
словарной сущности (`schema/gvp.schema.json`) и небольшой curated fixture
датасет (`data/curated/`) — для проверки самой модели данных. Builder,
скомпилированный пакет данных, updater и релизы пока не существуют. Этот
README описывает назначение и планируемую форму проекта, а не уже
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

- builder/pipeline
- скомпилированный пакет данных (SQLite или любой другой)
- механизм updater/manifest
- GitHub Actions / CI
- GitHub Releases
- импорт Wikidata или любого другого массового внешнего датасета

Существующие схема и fixture-данные (`schema/`, `data/curated/`) служат для
проверки модели данных, а не являются production-датасетом — см.
`docs/01_DATA_SCHEMA.md` и `SOURCES.md`.

## Связанные документы

- `docs/00_ARCHITECTURE.md` — концептуальный pipeline и модель версионирования
- `docs/01_DATA_SCHEMA.md` — схема сущности, поле за полем
- `docs/02_VOCABULARY_LAYERS.md` — Global / Domain / Organization / Personal
- `docs/03_COLLISION_POLICY.md` — уровни неоднозначности и обработка коллизий
- `SOURCES.md` — основа source policy (данные пока не прошли формальную проверку/импорт)
- `THIRD_PARTY_NOTICES.md` — уведомления о сторонних данных (пока нет)
- `CONTRIBUTING.md` — процесс участия в проекте
- `SECURITY.md` — безопасность и приватность
- `LICENSE` — статус лицензирования и открытые решения
