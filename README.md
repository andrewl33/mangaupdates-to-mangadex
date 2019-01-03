# Manga Updates List -> MangaDex List

Imports all lists on manga updates to mangadex. Uses python 3.

### Requires python packages

- beautifulsoup4
- chromedriver-binary (to be installed in python3 directory)
- PyYAML
- selenium

## credentials.yaml

A credentials.yaml needs to be created, with the values

```yaml
mu_username: <manga updates username>
mu_password: <manga updates password>
md_username: <mangadex usernames>
md_password: <mangadex password>
```

## Usage

`python index.py`

### Reading Progress

By default, reading progress is not imported. To change this, set `OVERWRITE_PROGRESS` to `True` at the top of the file. It overwrites all progress saved on MangaDex.
