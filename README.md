# ✨ ANNIST — AI Hairstyle Recommendation System

ANNIST is a premium AI-powered hairstyle recommendation application built with **Streamlit 1.37.1**.

Using semantic search powered by **Sentence Transformers (BAAI/bge-small-en-v1.5)**, ANNIST recommends hairstyles based on:

- Occasion
- Hair Length
- Skill Level
- Natural Language Search

---

# Features

✓ AI semantic search

✓ Modern luxury UI

✓ Fully responsive

✓ Glassmorphism

✓ Beautiful editorial typography

✓ Smart filtering

✓ AI ranking

✓ Automatic fallback matching

✓ Local image support

✓ Streamlit 1.37.1 compatible

✓ Python 3.11 compatible

---

# Project Structure

```
ANNIST/

│
├── app.py
├── components.py
├── semantic_search.py
├── utils.py
├── generate_embeddings.py
├── styles.css
├── requirements.txt
│
├── assets/
│   ├── logo.png
│   └── hero.png
│
├── images/
│   ├── hairstyle1.jpg
│   ├── hairstyle2.jpg
│   └── ...
│
├── data/
│   └── annist_dataset.csv
│
└── embeddings/
    └── annist_embeddings.npy
```

---

# Python Version

Python 3.11

---

# Streamlit Version

```
1.37.1
```

---

# Installation

Create a virtual environment

```bash
python3.11 -m venv venv
```

Activate

macOS

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

Install packages

```bash
pip install -r requirements.txt
```

---

# Generate Embeddings

Run only if

- the dataset changes
- embeddings are deleted
- new hairstyles are added

```bash
python generate_embeddings.py
```

This creates

```
embeddings/annist_embeddings.npy
```

---

# Start ANNIST

```bash
streamlit run app.py
```

---

# Dataset Requirements

The CSV must contain the following columns

```
filename
hairstyle_label
category
difficulty
hair_length
description
keywords
search_profile
```

---

# Semantic Search

ANNIST uses

```
BAAI/bge-small-en-v1.5
```

through Sentence Transformers.

Search is performed using

- semantic similarity
- occasion filtering
- hair length filtering
- difficulty filtering
- weighted AI ranking

---

# Matching

The final recommendation score is calculated using

```
40% Semantic Similarity

30% Occasion

20% Hair Length

10% Skill Level
```

---

# Supported Skill Levels

```
Easy

Intermediate

Advanced
```

Internally

Easy

and

Beginner

are treated as the same value.

---

# Supported Hair Length

```
Short

Medium

Long
```

---

# Supported Occasions

```
Wedding

Party

Everyday
```

---

# Technologies

- Streamlit 1.37.1
- Python 3.11
- Sentence Transformers
- HuggingFace
- PyTorch
- NumPy
- Pandas

---

# Author

ANNIST

AI Hairstyle Recommendation System