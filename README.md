# glink

sync gist with you local files.

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
