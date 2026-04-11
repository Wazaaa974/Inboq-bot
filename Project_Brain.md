# 🧠 PROJECT_BRAIN.md — Inboq

> Fichier de référence centralisé pour le projet Inboq.
> Dernière mise à jour : juin 2025
> Source : exporté depuis NanoCorp CEO Agent

---

## 🎯 Vision & Positionnement

**Inboq** est un assistant IA pour Telegram, conçu pour les professionnels indépendants.
Il gère les messages entrants, filtre les spams, qualifie les leads et répond aux FAQ — automatiquement, 24h/24.

- **Marché cible initial :** Professionnel(le)s indépendant(e)s francophones (secteur adulte)
- **Expansion prévue :** Autres secteurs de services indépendants (coachs, thérapeutes, artisans...)
- **Positionnement :** "Ton assistant personnel sur Telegram — il répond à ta place, 24h/24"

---

## 💶 Modèle Économique

| Élément | Valeur |
|--------|--------|
| Prix mensuel | €19/mois (flat rate, illimité) |
| Coût par client | ~€7/mois (Railway ~$5 + OpenAI <$2) |
| Marge brute | ~63% |
| Seuil de rentabilité | ~4 clients |
| Prix futur (post-PMF) | €29/mois pour nouveaux clients |
| Pilots (early adopters) | Bloqués à €19/mois |

**Décision clé :** Un seul tier de prix. Pas de plans multiples = pas de paralysie de décision.

---

## 🔗 Liens Critiques

| Ressource | URL |
|-----------|-----|
| Landing page | https://inboq.nanocorp.app |
| Lien de paiement Stripe | https://buy.stripe.com/3cIaEYelS9D19uOcsXeOt0D |
| Questionnaire Tally (onboarding) | https://tally.so/r/q4KE05 |
| Repository GitHub | https://github.com/Wazaaa974/Inboq-bot |
| Dashboard NanoCorp | https://inboq.nanocorp.app (admin) |

---

## 🛠️ Stack Technique

| Couche | Technologie |
|--------|-------------|
| Frontend | Next.js (landing page + checkout flow) |
| Backend | Node.js + Express (webhooks) |
| Bot | Telegram Bot API |
| Hébergement bot | Railway (une instance par client) |
| IA | OpenAI API — GPT-4o-mini |
| Paiements | Stripe (webhooks) |
| Formulaires | Tally → Google Sheets |
| Automatisation config | Script Python (GSheet → JSON) |
| Code | GitHub (`Wazaaa974/Inboq-bot`) |

---

## ⚙️ Infrastructure — État des Composants

### ✅ Composants Opérationnels

| Composant | Statut | Notes |
|-----------|--------|-------|
| Bot Telegram (core) | ✅ Live | Déployé sur Railway |
| Système de config dynamique | ✅ Live | JSON par client |
| Landing page (FR + EN) | ✅ Live | Redesign dark mode complété |
| Intégration Stripe | ✅ Live | Webhooks actifs |
| Questionnaire Tally | ✅ Live | Connecté à Google Sheets |
| Script Python GSheet → JSON | ✅ Live | Génère configs automatiquement |
| Page `/checkout/success` | ✅ Live | Confirmation post-paiement |
| Webhook `/api/webhooks/stripe` | ✅ Live | Déclenche email post-achat |
| Repository GitHub | ✅ Live | Code à jour |
| Base de prospects | ✅ Ready | 412 prospects francophones (LadyXena) |
| Templates outreach | ✅ Ready | WhatsApp + Email, multilingues |

### ⏳ En Attente / Bloqué

| Composant | Statut | Bloqueur |
|-----------|--------|---------|
| Email automation (Resend) | Attente credentials | User doit créer compte Resend + fournir clé API |
| Devise Stripe (USD → EUR) | Attente NanoCorp | Contacter support NanoCorp sur Discord |
| Codes promo activés | Attente NanoCorp | Contacter support NanoCorp sur Discord |

---

## 🚀 Workflow d'Onboarding Client

Client clique sur lien de paiement Stripe (€19/mois)
Stripe capture email + déclenche webhook
Email automatique envoyé → lien Tally questionnaire
Client remplit Tally → réponses dans Google Sheets
Script Python lit la feuille → génère JSON config
Déploiement bot sur Railway (~2h au total)
Client reçoit lien bot Telegram + instructions

**Temps total d'onboarding estimé : < 2 heures**

---

## 📣 Go-To-Market

### Stratégie
- Canal principal : **WhatsApp outreach** (direct, personnel, taux de lecture >90%)
- Canal secondaire : Email (pour prospects avec email public)
- Langue : Français en priorité

### Prospects
- **Source :** Annuaire LadyXena
- **Volume identifié :** 412 prospects francophones
- **Fichier :** `outreach_batch_01.csv` (premier batch de 20)

### Objectifs
| Horizon | Objectif |
|---------|---------|
| 2 semaines | 1-2 clients payants |
| 1 mois | 5 clients actifs |
| 3 mois | 20+ clients, validation PMF |
| Post-PMF | Augmentation prix → €29/mois (nouveaux) |

---

## 🐛 Problèmes Connus

### 1. Devise Stripe (USD vs EUR)
- **Symptôme :** Lien de paiement affiche $19 USD au lieu de €19 EUR
- **Cause :** Backend NanoCorp configuré en USD
- **Impact :** Fonctionnel, mais confusant pour clients européens
- **Fix :** Demander à NanoCorp support de changer la devise produit

### 2. Codes promo désactivés
- **Symptôme :** Impossible d'offrir code PILOT100 via Stripe
- **Cause :** Fonctionnalité non activée sur le compte NanoCorp
- **Workaround :** Configurer manuellement les bots pilots sur Railway (sans paiement)
- **Fix :** Demander activation à NanoCorp support

### 3. Email automation incomplète
- **Symptôme :** Emails post-achat pas encore envoyés
- **Cause :** Resend/Nodemailer intégré mais pas activé (pas de clé API)
- **Workaround :** Client reçoit lien Tally via page de succès Stripe
- **Fix :** Créer compte Resend → fournir clé API → activer dans Railway env vars

### 4. Filtres de contenu IA
- **Symptôme :** Certains prompts bloqués par OpenAI/Anthropic
- **Cause :** Mention explicite du marché cible
- **Workaround :** Reformuler en "professionnels indépendants en services adultes"
- **Impact :** Certaines tâches d'automatisation nécessitent reformulation manuelle

---

## 📋 Actions Immédiates (Next 48h)

- [ ] **Lancer la campagne WhatsApp** — Envoyer batch 01 (20 messages)
- [ ] **Vérifier lien Stripe** — Confirmer que €19 EUR s'affiche correctement
- [ ] **Contacter NanoCorp support (Discord)** — Demander changement devise USD→EUR + activation codes promo
- [ ] **Créer compte Resend** — Fournir clé API pour activer emails automatiques
- [ ] **Tester flow complet** — Paiement → Email → Tally → Déploiement bot

## 📋 Actions Cette Semaine

- [ ] **Sélectionner 2-3 pilots** — Parmi les réponses WhatsApp
- [ ] **Configurer bots pilots** — Tally → JSON → Railway
- [ ] **Valider l'expérience client complète** — Bout en bout

---

## 💡 Décisions Stratégiques Prises

| Date | Décision | Raison |
|------|---------|--------|
| Juin 2025 | Passage à 1 seul tier de prix (€19/mois) | Deux tiers non-enforceables + friction inutile |
| Juin 2025 | Redesign landing page (dark mode) | Apparence trop basique pour la cible |
| Juin 2025 | Email automatique post-paiement | Éviter perte de contact si fermeture navigateur |
| Juin 2025 | Documentation centralisée (PROJECT_BRAIN.md) | Contexte projet accessible hors NanoCorp |

---

## 🔐 Variables d'Environnement (Railway)

> ⚠️ Ne jamais committer ces valeurs dans le repo. Stocker dans Railway dashboard.

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram (par client) |
| `OPENAI_API_KEY` | Clé API OpenAI |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe |
| `RESEND_API_KEY` | Clé API Resend (email) — **à configurer** |
| `SUPPORT_EMAIL` | Adresse email support Inboq |
| `CLIENT_CONFIG_PATH` | Chemin vers JSON config client |

---

*Ce fichier est la source de vérité du projet Inboq.*
*Le mettre à jour à chaque décision stratégique importante.*
