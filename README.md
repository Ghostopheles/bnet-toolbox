# bnet-toolbox
A collection of command-line tools written in Python that allow you to interact with the Battle.net client and Agent

```
pip install bnet-toolbox
```

## Usage
To install the current WoW beta client:
```
bnet install wow_beta
```

Current Commands:
- `install <agent_uid>`: Installs a product
- `uninstall <agent_uid>`: Uninstalls a product
- `update <agent_uid>`: Updates a product
- `products`: Lists the currently installed products
- `sessions`: Lists active game sessions

> [!TIP]
> The product IDs that Agent uses (agent_uids) are not the same as those that TACT uses. Most of the IDs will end up being the same, but some won't match.
> You can find a list of products and their Agent UIDs on the [TACT](https://wowdev.wiki/TACT#Product_Information) wiki page.