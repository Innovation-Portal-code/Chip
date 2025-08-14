---
title: Chip the Alabama Tech Community AI Agent

This project uses uv as its package manager.

to install the dependencies, run the following command:

```bash
uv sync
```

to add a new dependency, run the following command:

```bash
uv add <dependency>
```

to remove a dependency, run the following command:

```bash
uv remove <dependency>
```

to update a dependency, run the following command:

```bash
uv update <dependency>
```

to export the requirements.txt file, run the following command:

```bash
uv export --no-hashes -o requirements.txt
```

to run the debugger ro this project you need to run the following command:

```bash
python -m debugpy --listen 5678 --wait-for-client \
-m hypercorn main:app --reload --log-level debug
```
and to use the launch.json provided in this project.