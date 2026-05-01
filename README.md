# Itero Skills

Talk to your AI assistant about your Itero account — and have it do the work.

Once installed, you can chat with Claude Code, Cursor, OpenAI Codex, or Google Antigravity in plain English to build practice scenarios, design scorecards, create personas, or import a CSV of users — without opening the Itero app.

## What's included

Four skills, each triggered by everyday language:

- **Scenarios** — Create roleplay scenarios from a playbook, transcript, or just a description.
  *Try saying:* "Build me three cold-call scenarios from this playbook."

- **Scorecards** — Design evaluation rubrics from training materials or a methodology doc.
  *Try saying:* "Build a scorecard for our discovery calls based on this guide."

- **Personas** — Create the AI counterparties (CFOs, members, prospects) used in practice calls.
  *Try saying:* "Create a SaaS CFO persona from our buyer profile doc."

- **Upload Users** — Bulk-import a CSV of new users into your Itero tenant.
  *Try saying:* "Upload these users from this spreadsheet."

Every skill walks you through the steps, previews changes before saving, and only writes to your Itero account after you say yes.

## Install in 30 seconds (automatic)

The fastest way: copy the prompt below, paste it into your AI assistant (Claude Code, Cursor, OpenAI Codex, or Google Antigravity), and press Enter. The assistant does the install for you. **You'll add your API key yourself in a text file at the end — your key never gets typed into chat.**

````
Please install the Itero skills for me. Do these steps in order, asking me to confirm before any step that needs my input:

1. Tell me which AI assistant you are (Claude Code, Cursor, OpenAI Codex, or Google Antigravity) and which OS I'm on (Mac or Windows). Confirm with me before continuing.

2. Download https://github.com/Itero-AI/skills/archive/refs/heads/main.zip and unzip it to a temporary location.

3. Copy the four folders inside the unzipped `skills/` directory (`scenarios`, `scorecards`, `personas`, `upload-users`) into the correct global skills folder for your agent on my OS, creating the destination folder if it doesn't exist:
   - Claude Code: `~/.claude/skills/` on Mac, `%USERPROFILE%\.claude\skills\` on Windows
   - Cursor or Codex: `~/.agents/skills/` on Mac, `%USERPROFILE%\.agents\skills\` on Windows
   - Antigravity: `~/.gemini/antigravity/skills/` on Mac, `%USERPROFILE%\.gemini\antigravity\skills\` on Windows

4. Run `pip3 install requests python-dotenv` and confirm both installed successfully. If `pip3` isn't installed, tell me to install Python from https://python.org first and pause.

5. Create a file called `.env` in my current working directory containing exactly this single line — leave the value blank, do NOT ask me for my API key in chat:

   ```
   ITERO_API_KEY=
   ```

   Then tell me the full path to the `.env` file you just created and instruct me to (a) open that file in my IDE's file explorer, (b) click after the equals sign, (c) paste my Itero API key, and (d) save the file.

6. After I confirm I've added my key, list the contents of the destination skills folder to verify all four skill folders are there. Then tell me to fully restart you and try the message: list my scorecards.
````

That's it. If the assistant asks anything along the way, answer in plain English.

### Adding your API key in your IDE

After step 5, your AI assistant will tell you it created a `.env` file. Open it in the file explorer panel of your IDE (Cursor, VS Code, Antigravity all show dotfiles by default), click after the equals sign, paste your key, save.

> *Screenshot: VS Code / Cursor file explorer showing the `.env` file open with `ITERO_API_KEY=` and the cursor positioned right after the equals sign, ready for the customer to paste.*

It should look like this when you're done:

```
ITERO_API_KEY=k_abcdef123456…your-actual-key-here
```

No spaces, no quotes — just your key directly after the equals sign.

## Install manually (if the automatic path didn't work)

If the auto-install hits an error or you'd rather do it yourself, follow the painfully-detailed step-by-step guide below for your agent:

| AI assistant | Manual install guide |
|---|---|
| **Claude Code** | [INSTALL.md → Claude Code](INSTALL.md#claude-code) |
| **OpenAI Codex** | [INSTALL.md → OpenAI Codex and Cursor](INSTALL.md#openai-codex-and-cursor) |
| **Cursor** | [INSTALL.md → OpenAI Codex and Cursor](INSTALL.md#openai-codex-and-cursor) |
| **Google Antigravity** | [INSTALL.md → Google Antigravity](INSTALL.md#google-antigravity) |

The manual path is: download a folder, drag it into the right spot on your computer, paste your Itero API key into a small text file. No coding, no terminal commands required.

## Developer install (terminal, no hand-holding)

If you're comfortable with a shell, here's the whole install in five commands. Replace the destination path with the one for your agent (see the path matrix in [INSTALL.md](INSTALL.md)).

```bash
# 1. Clone (or download + unzip the tarball if you don't want a working tree)
git clone https://github.com/Itero-AI/skills.git /tmp/itero-skills

# 2. Copy the four skill folders to your agent's global skills directory
mkdir -p ~/.claude/skills          # Claude Code
# OR: mkdir -p ~/.agents/skills    # Cursor or Codex
# OR: mkdir -p ~/.gemini/antigravity/skills  # Antigravity
cp -r /tmp/itero-skills/skills/* ~/.claude/skills/

# 3. Install Python deps
pip3 install requests python-dotenv

# 4. Drop your API key into a project .env (use your secret manager of choice)
echo "ITERO_API_KEY=$ITERO_API_KEY" > .env   # if it's already in your shell env
# or just edit .env directly with your editor

# 5. Restart your agent and try: list my scorecards
```

For multi-tenant setups, add `ITERO_API_KEY_<NAME>=...` lines to `.env` and pass `--tenant <NAME>` to the skills.

## Before you install — get your API key

You'll need an Itero API key. To get one:

1. Sign in to [your Itero account](https://app.iteroapp.ai).
2. Go to **Settings → API Keys**.
3. Click **Create new key** and copy the long string of letters and numbers.
4. Keep it in a safe place — you'll paste it in during step 4 of the install.

The key for the **Upload Users** skill needs to belong to a Manager-role user. The other three skills work with any role.

## First thing to try

Once installed, open your AI assistant and type:

> *list my scorecards*

If you see your scorecards (or a polite "no scorecards yet"), the install worked. If something else happens, jump to [INSTALL.md → Troubleshooting](INSTALL.md#troubleshooting).

## Common questions

**Do I need to know how to code?**
No. The install is dragging folders and pasting one line of text. The skills themselves work entirely through conversation.

**Will this change anything in my Itero account?**
Only when you tell it to. Every skill shows you exactly what it's about to do and waits for your confirmation before saving anything.

**Can I use this with a free Itero account?**
You need an API key, which is available on paid Itero plans. Talk to your Itero account manager if you're not sure.

**My company uses Cursor *and* Codex.**
Lucky you — one install covers both, since they share the same skills folder. See [INSTALL.md → OpenAI Codex and Cursor](INSTALL.md#openai-codex-and-cursor).

## Help

Stuck? Email **support@iteroapp.ai** with:
- Which AI assistant you're using
- Which step of [INSTALL.md](INSTALL.md) you're on
- What happened (or didn't)

We'll get back to you the same business day.

## License

MIT — see [LICENSE](LICENSE). You're free to use, modify, and redistribute these skills.
