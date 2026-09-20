# EXPC-GVP — EXPC Global Vocabulary Pack

<p align="center">
  <img src="assets/github-header.png" alt="EXPC-GVP — Global Vocabulary Pack" width="100%">
</p>

## Status

**Early development / Phase 02.1.** A vocabulary entity schema
(`schema/gvp.schema.json`), a small curated fixture dataset
(`data/curated/`), and an early Builder MVP (`tools/builder/`, see
`docs/04_BUILDER.md`) exist. The Builder validates the fixture data and
produces an intermediate `dist/gvp.json` artifact. It can also package
that artifact into a versioned, checksummed local Data Pack, verify one
standalone, and validate one as a release candidate for a `gvp-<CalVer>`
Git tag (`docs/05_DISTRIBUTION.md`, `docs/06_RELEASE_CONTRACT.md`) — but
only locally: there is still no GitHub Release publishing, no GitHub API
client, no updater, no network downloader, no consumer integration, and
no CI/CD. This README describes the intended purpose and shape of the
project, not features that are not yet implemented.

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

## Builder (Phase 01.0-02.1)

A minimal, working Builder exists at `tools/builder/`. Run from the
repository root:

```
py -3.12 -m tools.builder build
py -3.12 -m tools.builder package --version 2026.09.20.1
py -3.12 -m tools.builder verify dist/2026.09.20.1
py -3.12 -m tools.builder release-check --tag gvp-2026.09.20.1 dist/2026.09.20.1
```

`build` loads `data/curated/*.json`, validates each entity against
`schema/gvp.schema.json`, runs semantic and collision checks, and writes a
deterministic `dist/gvp.json`. `package` wraps that same artifact into a
versioned, checksummed local Data Pack (`manifest.json` +
`checksums.sha256`), `verify` checks one standalone, and `release-check`
validates one against a `gvp-<CalVer>` Git tag — all entirely local, no
GitHub API or network access. See `docs/04_BUILDER.md`,
`docs/05_DISTRIBUTION.md`, and `docs/06_RELEASE_CONTRACT.md` for the full
pipeline, output format, and — importantly — what none of this does yet
(no SQLite, no actual GitHub Release, no updater, no network downloader,
no consumer integration, no CI).

## Planned distribution model

Data is intended to be distributed as versioned packages, roughly as:

```
local package (implemented) -> GitHub Releases -> updater -> atomic update
```

Local, versioned packaging with a manifest and SHA-256 checksums now
exists (`docs/05_DISTRIBUTION.md`). Publishing that package as a GitHub
Release, and any updater/downloader that consumes it, is **not
implemented yet**.

## Explicitly not implemented yet

The following do not exist in the repository at this stage and should not be
assumed to work:

- a SQLite (or any other) compiled data pack
- GitHub Release publishing
- an updater or network downloader
- GitHub Actions / CI
- consumer integration (EXPC-WLK or any other consumer)
- any Wikidata import or other bulk external dataset
- ingestion from any source other than `data/curated/*.json`

The schema, fixture data, and Builder that do exist (`schema/`,
`data/curated/`, `tools/builder/`) validate and build from that fixture
data, and can package/verify a local Data Pack — they are not a
production dataset, pipeline, or release process — see
`docs/01_DATA_SCHEMA.md`, `docs/04_BUILDER.md`, `docs/05_DISTRIBUTION.md`,
and `SOURCES.md`.

## Related documents

- `docs/00_ARCHITECTURE.md` — conceptual pipeline and versioning model
- `docs/01_DATA_SCHEMA.md` — the entity schema, field by field
- `docs/02_VOCABULARY_LAYERS.md` — Global / Domain / Organization / Personal
- `docs/03_COLLISION_POLICY.md` — ambiguity levels and collision handling
- `docs/04_BUILDER.md` — the Phase 01.0 Builder MVP
- `docs/05_DISTRIBUTION.md` — Phase 02.0: local Data Pack packaging, manifest, checksums, verification
- `docs/06_RELEASE_CONTRACT.md` — Phase 02.1: GitHub Release tag/asset contract, local release-candidate check
- `SOURCES.md` — source policy foundation (no data formally reviewed/imported yet)
- `THIRD_PARTY_NOTICES.md` — third-party notices (none yet)
- `CONTRIBUTING.md` — contribution flow
- `SECURITY.md` — security and privacy reporting
- `LICENSE` — licensing status and open decisions

---

# EXPC-GVP — EXPC Global Vocabulary Pack (Русский)

## Статус

**Ранняя разработка / Phase 02.1.** Существуют схема словарной сущности
(`schema/gvp.schema.json`), небольшой curated fixture датасет
(`data/curated/`) и ранний Builder MVP (`tools/builder/`, см.
`docs/04_BUILDER.md`). Builder валидирует fixture-данные и создаёт
промежуточный артефакт `dist/gvp.json`. Он также умеет собирать этот
артефакт в версионированный локальный Data Pack с контрольными суммами,
проверять его отдельно и проверять его как кандидата релиза для Git-тега
`gvp-<CalVer>` (`docs/05_DISTRIBUTION.md`, `docs/06_RELEASE_CONTRACT.md`)
— но только локально: публикации GitHub Release, GitHub API, updater,
сетевого загрузчика, интеграции с потребителями и CI/CD пока не
существует. Этот README описывает назначение и планируемую форму
проекта, а не только уже реализованные функции.

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

## Builder (Phase 01.0-02.1)

Минимальный рабочий Builder существует в `tools/builder/`. Запуск из
корня репозитория:

```
py -3.12 -m tools.builder build
py -3.12 -m tools.builder package --version 2026.09.20.1
py -3.12 -m tools.builder verify dist/2026.09.20.1
py -3.12 -m tools.builder release-check --tag gvp-2026.09.20.1 dist/2026.09.20.1
```

`build` загружает `data/curated/*.json`, валидирует каждую сущность
против `schema/gvp.schema.json`, выполняет semantic- и collision-проверки
и записывает детерминированный `dist/gvp.json`. `package` оборачивает
этот же артефакт в версионированный локальный Data Pack (`manifest.json`
+ `checksums.sha256`), `verify` проверяет такой пакет отдельно, а
`release-check` проверяет его против Git-тега `gvp-<CalVer>` — всё
полностью локально, без GitHub API и сети. Полное описание pipeline,
формата output и — что важно — того, чего это пока НЕ делает (нет
SQLite, реального GitHub Release, updater, сетевого загрузчика,
интеграции с потребителями, CI) — см. `docs/04_BUILDER.md`,
`docs/05_DISTRIBUTION.md` и `docs/06_RELEASE_CONTRACT.md`.

## Планируемая модель доставки

Данные предполагается распространять как версионируемые пакеты, примерно
по схеме:

```
локальный пакет (реализовано) -> GitHub Releases -> updater -> atomic update
```

Локальная версионированная упаковка с manifest и SHA-256 контрольными
суммами уже реализована (`docs/05_DISTRIBUTION.md`). Публикация этого
пакета как GitHub Release и любой updater/загрузчик, использующий его,
**пока не реализованы**.

## Явно не реализовано на этом этапе

Следующее не существует в репозитории на данном этапе и не должно
считаться работающим:

- скомпилированный пакет данных (SQLite или любой другой)
- публикация GitHub Release
- updater или сетевой загрузчик
- GitHub Actions / CI
- интеграция с потребителями (EXPC-WLK или любым другим)
- импорт Wikidata или любого другого массового внешнего датасета
- загрузка данных из чего-либо, кроме `data/curated/*.json`

Существующие схема, fixture-данные и Builder (`schema/`, `data/curated/`,
`tools/builder/`) валидируют и собирают именно эти fixture-данные, а
также умеют собирать/проверять локальный Data Pack — это не
production-датасет, pipeline или процесс релиза — см.
`docs/01_DATA_SCHEMA.md`, `docs/04_BUILDER.md`, `docs/05_DISTRIBUTION.md`
и `SOURCES.md`.

## Связанные документы

- `docs/00_ARCHITECTURE.md` — концептуальный pipeline и модель версионирования
- `docs/01_DATA_SCHEMA.md` — схема сущности, поле за полем
- `docs/02_VOCABULARY_LAYERS.md` — Global / Domain / Organization / Personal
- `docs/03_COLLISION_POLICY.md` — уровни неоднозначности и обработка коллизий
- `docs/04_BUILDER.md` — Phase 01.0 Builder MVP
- `docs/05_DISTRIBUTION.md` — Phase 02.0: локальная упаковка Data Pack, manifest, контрольные суммы, verification
- `docs/06_RELEASE_CONTRACT.md` — Phase 02.1: контракт тега/ассетов GitHub Release, локальная проверка кандидата релиза
- `SOURCES.md` — основа source policy (данные пока не прошли формальную проверку/импорт)
- `THIRD_PARTY_NOTICES.md` — уведомления о сторонних данных (пока нет)
- `CONTRIBUTING.md` — процесс участия в проекте
- `SECURITY.md` — безопасность и приватность
- `LICENSE` — статус лицензирования и открытые решения
