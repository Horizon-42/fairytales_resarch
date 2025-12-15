# Fairytales/Folktales across cultures

## Work Plan
30-Day Distributed Research Plan_ The Digital Silk Road

## Researchs
Resources.md

## Data tools

Download (at least) 30 Chinese tale texts into `datasets/ChineseTales/texts` in the CSV order:

```bash
python3 scripts/download_chinese_tales.py --target 30
```

If you want to re-download and overwrite existing files:

```bash
python3 scripts/download_chinese_tales.py --target 30 --force
```