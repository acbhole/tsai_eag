def load_prompt(path, **kwargs):
    with open(path, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(**kwargs)