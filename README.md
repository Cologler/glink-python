# glink

![GitHub](https://img.shields.io/github/license/Cologler/glink-python.svg)
[![Build Status](https://travis-ci.com/Cologler/glink-python.svg?branch=main)](https://travis-ci.com/Cologler/glink-python)
[![PyPI](https://img.shields.io/pypi/v/glink2.svg)](https://pypi.org/project/glink2/)

Sync files between gist and localhost.

## Purpose

When I clone a lot of repos and found a lot of interesting code file,
I can simplily push them to my gist via `glink`.

After I pull all the above repos,
I can simplily update all my gists via one single command (`glink sync`).

`glink` store sync states in `~/.config/Cologler/glink/...`,
which mean if you move the linked file,
it will lose the connection.

Try [gist-sync](https://github.com/Cologler/gist-sync-python) if you need move the gist files.

## Installation

``` bash
pip install glink2
```

## Login

To login a remote repo, you need to edit the `~/.config/Cologler/glink/auth.json`.
The format is like:

``` json
{
    "<USER>@<SERVICE>": ...
}
```

*The user name is required because the `glink` support multi-accounts per provider.*

### Gist

*Login is required for push only.*

To login gist, you need to create a new dev token from https://github.com/settings/tokens/new.
Ensure you checked the `gist` scope.

After you get the token, add following text into `auth.json`:

``` json
{
    "<USER>@gist": "<TOKEN>"
}
```
