# Embeddings

[< Retour a l'index](index.md)

---

Les embeddings sont des representations vectorielles du texte qui permettent la [recherche semantique](recherche-hybride.md#canal-1--semantique-knn). Fougasse utilise un modele local pour generer ces vecteurs.

## Modele par defaut

| Propriete | Valeur |
|-----------|--------|
| Modele | `BAAI/bge-base-en-v1.5` |
| Dimensions | 768 |
| Parametres | ~110M |
| Taille | ~450 Mo |
| Latence | ~22ms par texte (M1 Pro) |
| Normalisation | L2 (activee a l'encodage) |

Le modele est [configurable](configuration.md#embeddings) via `model_name` dans le TOML.

## Chargement du modele

Le modele est charge **une seule fois** au demarrage du serveur MCP (via le mecanisme lifespan) et reutilise pour toutes les requetes.

- **Premier demarrage** : telecharge depuis HuggingFace (~30s)
- **Demarrages suivants** : charge depuis le cache local `~/.fougasse/models/` (~3s)
- **Mode offline** : avec `TRANSFORMERS_OFFLINE=1`, aucune requete reseau. Voir [Installation](installation.md#configurer-comme-serveur-mcp)

## Detection automatique du device

Fougasse detecte automatiquement le meilleur device disponible :

| Priorite | Device | Contexte |
|----------|--------|----------|
| 1 | MPS | Mac Apple Silicon (M1/M2/M3) |
| 2 | CUDA | GPU NVIDIA |
| 3 | CPU | Fallback universel |

## Fonctions disponibles

### `encode(text)`

Encode un texte en vecteur normalise de 768 dimensions.

```python
from fougasse.embeddings import encode
vector = encode("Python is great for ML")
# -> [0.023, -0.041, 0.087, ...] (768 floats)
```

### `encode_batch(texts)`

Encode plusieurs textes en parallele (batch_size=32).

```python
from fougasse.embeddings import encode_batch
vectors = encode_batch(["Text 1", "Text 2", "Text 3"])
# -> [[...768...], [...768...], [...768...]]
```

### `serialize_vector(vector)`

Convertit un vecteur float en bytes pour stockage dans [sqlite-vec](modele-donnees.md#recherche-vectorielle).

```python
from fougasse.embeddings import serialize_vector
binary = serialize_vector([0.1, 0.2, 0.3])
# -> b'\xcd\xcc\xcc=...' (struct.pack)
```

### `deserialize_vector(data, dim)`

Reconstruit un vecteur depuis les bytes.

```python
from fougasse.embeddings import deserialize_vector
vector = deserialize_vector(binary, dim=768)
```

## Normalisation

Les vecteurs sont **normalises L2 a l'encodage** (`normalize_embeddings=True`). Cela signifie que la distance L2 entre deux vecteurs normalises est equivalente a `2 * (1 - cosine_similarity)`.

sqlite-vec utilise la distance L2 par defaut — pas besoin de configurer la distance cosinus separement.

## Changement de modele

Si vous changez de modele (ex: passer a `nomic-embed-text-v1.5`), vous devez **re-indexer** toutes les memoires existantes car les dimensions et l'espace vectoriel changent.

> **Attention** : la re-indexation de 100K memoires prend ~37 minutes sur M1 Pro. Planifiez a l'avance.

---

**Voir aussi** : [Recherche hybride](recherche-hybride.md) | [Configuration](configuration.md#embeddings) | [Modele de donnees](modele-donnees.md#recherche-vectorielle)
