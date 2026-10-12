# Nova Caelum plugins

One marketplace for Nova Caelum's Claude Code plugins.

| Plugin | What it is |
|---|---|
| `technical-cofounder` | A senior technical team: a technical cofounder, an engineer, a DevOps lead and a forward-deployed engineer. |
| `technical-cofounder-setup` | The front door. It finds what your computer is missing, installs it, creates your project and walks you through setup. |
| `hyperspace-engine` | The working loop, the task graph and the verifier the team runs on. It installs with the team. |
| `super-novacaelum` | Optional research extras, on your own accounts. |

## Install

Paste this into Claude Code (in the desktop app, the Code tab, not Chat):

```text
I found this plugin and want to try it - it's supposed to be a team of agents that helps with building and technical AI knowledge. Here is the github link: https://github.com/Nova-Caelum/technical-cofounder

Can you check it out to make sure it's safe, and if so, download it and help me get it installed
```

## Already know your way around?

From your project folder:

    claude plugin marketplace add https://github.com/Nova-Caelum/plugins.git
    claude plugin install technical-cofounder@nova-caelum --scope project

Hyperspace Engine installs with the team. It needs Python 3.11 or newer; the setup plugin installs one for you if you use the message above.

## How this repository works

It holds no plugin code. Each entry in `.claude-plugin/marketplace.json` points at the repository where that plugin lives and pins the exact commit that was tested, so you get that version and nothing newer. Every source is fetched over HTTPS.

- Technical Cofounder: https://github.com/Nova-Caelum/technical-cofounder
- Hyperspace Engine: https://github.com/Nova-Caelum/hyperspace-engine

## License

Apache-2.0. See [LICENSE](LICENSE). Each plugin carries its own license in its own repository.
