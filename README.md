# Nova Caelum plugins

One marketplace for Nova Caelum's Claude Code plugins.

| Plugin | What it is |
|---|---|
| `technical-cofounder` | A senior technical team: a technical cofounder, an engineer, a DevOps lead and a forward-deployed engineer. |
| `technical-cofounder-setup` | The front door. It finds what your computer is missing, installs it, creates your project and walks you through setup. |
| `hyperspace-engine` | The working loop, the task graph and the verifier the team runs on. It installs with the team. |
| `super-novacaelum` | Optional research extras, on your own accounts. |

## Install

Paste this one message into Claude Code:

```text
Set up Technical Cofounder for me, from https://github.com/Nova-Caelum/plugins

1. If `claude --version` does not work here, install Claude Code's command line first (macOS or Linux: curl -fsSL https://claude.ai/install.sh | bash   Windows PowerShell: irm https://claude.ai/install.ps1 | iex).
2. If I am on Windows and `git --version` does not work, run this in PowerShell, then tell me to close Claude Code completely, open it again and paste this same message:
   winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
3. Run these two commands:
   claude plugin marketplace add Nova-Caelum/plugins
   claude plugin install technical-cofounder-setup@nova-caelum
4. Run `claude plugin list --json`, find the installPath of technical-cofounder-setup, read skills/setup/SKILL.md inside it, and follow it from the top. Tell me what each step is for before you run it, and go one step at a time.
```

## Already know your way around?

From your project folder:

    claude plugin marketplace add Nova-Caelum/plugins
    claude plugin install technical-cofounder@nova-caelum --scope project

Hyperspace Engine installs with the team. It needs Python 3.11 or newer; the setup plugin installs one for you if you use the message above.

## How this repository works

It holds no plugin code. Each entry in `.claude-plugin/marketplace.json` points at the repository where that plugin lives and pins the exact commit that was tested, so you get that version and nothing newer. Every source is fetched over HTTPS.

- Technical Cofounder: https://github.com/Nova-Caelum/technical-cofounder
- Hyperspace Engine: https://github.com/Nova-Caelum/hyperspace-engine

## License

Apache-2.0. See [LICENSE](LICENSE). Each plugin carries its own license in its own repository.
