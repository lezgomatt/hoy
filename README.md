Hoy!  [![PyPI - Version](https://img.shields.io/pypi/v/hoy?style=flat-square)](https://pypi.org/project/hoy/)
====

A dead simple notifier.

Be informed when your scripts finish running!


Installation
------------

```bash
pipx install hoy
```


Usage
-----

Simply run `hoy` after a long-running process (example: `sleep 5`):

```bash
sleep 5; hoy
```

Or if you want different messages for success and failure:

```bash
sleep 5 && hoy Success! || hoy Fail!
```
