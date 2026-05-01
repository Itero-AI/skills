# Manually Installing the Itero Skills — Step by Step

> **Most people don't need this guide.** The fastest way to install is the [auto-install prompt in the README](README.md#install-in-30-seconds-automatic) — copy one block of text, paste it into your AI assistant, answer one question. This manual guide is for anyone who hits a problem with the auto-install or who'd rather do it themselves.

This guide walks you through installing the Itero skills into your AI assistant by hand. It's written for people who have never opened a terminal and have no idea what a "hidden folder" is. If that's you, you're in the right place.

There are 6 steps. Plan for 5–10 minutes the first time.

> **Step 1** — Download the skills folder
> **Step 2** — Open your AI assistant's skills folder
> **Step 3** — Drag the four skills into place
> **Step 4** — Save your Itero API key
> **Step 5** — Install Python (one time only)
> **Step 6** — Restart your AI assistant and test

---

## Step 1 — Download the skills folder

You're going to download all four Itero skills as a single zipped folder.

1. Go to **https://github.com/Itero-AI/skills** in your web browser.
2. Click the green **Code** button (it's near the top-right of the file list).
3. In the menu that opens, click **Download ZIP**.

> *Screenshot: GitHub "Code → Download ZIP" button.*

A file called `skills-main.zip` will land in your **Downloads** folder.

### Unzip it

- **On a Mac:** Double-click `skills-main.zip` in your Downloads folder. It will create a folder named `skills-main` next to the zip file.
- **On a Windows PC:** Right-click `skills-main.zip` → click **Extract All…** → click **Extract**. It will create a folder named `skills-main`.

### Open the unzipped folder

Open `skills-main`. Inside, you'll see a folder called `skills`. Open that too.

You should now see four folders side by side:

- `personas`
- `scenarios`
- `scorecards`
- `upload-users`

> *Screenshot: Finder/File Explorer showing the four skill folders side by side.*

**Leave this window open** — you'll come back to it in Step 3.

---

## Step 2 — Open your AI assistant's skills folder

Your AI assistant looks for skills in a specific folder on your computer. You need to open that folder so you can drop the four skill folders into it.

The folder path depends on which assistant you use. Find your assistant below.

---

<a id="claude-code"></a>
### If you use Claude Code

#### On a Mac

1. Open **Finder**.
2. Press **Cmd + Shift + G** on your keyboard. A small window will pop up that says "Go to Folder."
3. Type (or paste) this exact path: `~/.claude/skills`
4. Press **Enter**.

> *Screenshot: macOS "Go to Folder" dialog with `~/.claude/skills` typed in.*

If a window opens showing an empty (or near-empty) folder, you're done with Step 2 — leave it open and skip to Step 3.

If Finder says **"The folder can't be found"** — that's fine, the folder doesn't exist yet. Create it:

1. Press **Cmd + Shift + H** to open your home folder.
2. Look for a folder called `.claude`. If it's not there, create it: right-click in an empty area → **New Folder** → name it `.claude` (with the dot at the start, exactly like that).
3. Open the `.claude` folder.
4. Inside it, create another new folder named `skills`.
5. You're now inside the `skills` folder. Continue to Step 3.

#### On a Windows PC

1. Open **File Explorer**.
2. Click in the address bar at the top (where the path is shown).
3. Type (or paste) this exact path: `%USERPROFILE%\.claude\skills`
4. Press **Enter**.

> *Screenshot: Windows File Explorer with `%USERPROFILE%\.claude\skills` in the address bar.*

If a window opens showing an empty (or near-empty) folder, you're done with Step 2 — skip to Step 3.

If Windows says the folder can't be found, create it:

1. Type `%USERPROFILE%` in the address bar and press Enter. This opens your user folder (something like `C:\Users\YourName`).
2. Right-click in the window → **New** → **Folder** → name it `.claude` (with the dot at the start).
3. Open the `.claude` folder.
4. Inside it, create another folder named `skills`.

---

<a id="openai-codex-and-cursor"></a>
### If you use OpenAI Codex CLI **or** Cursor (or both)

Codex and Cursor read skills from the same folder, so this single install covers both.

#### On a Mac

1. Open **Finder**.
2. Press **Cmd + Shift + G**.
3. Type (or paste): `~/.agents/skills`
4. Press **Enter**.

If the folder opens, you're done with Step 2.

If Finder says it can't be found, create it the same way as the Claude Code instructions above: home folder (Cmd+Shift+H) → create `.agents` → inside it create `skills`.

#### On a Windows PC

1. Open **File Explorer**.
2. Address bar → paste: `%USERPROFILE%\.agents\skills`
3. Press **Enter**.

If missing, create the path: `%USERPROFILE%` → create `.agents` → create `skills` inside it.

> **Cursor users:** Cursor also reads from `~/.cursor/skills/` (or `%USERPROFILE%\.cursor\skills\` on Windows). We recommend `~/.agents/skills/` because it covers Codex too — but `~/.cursor/skills/` works fine if you'd rather use that. Just don't put it in both places, or you'll see duplicate skills.

---

<a id="google-antigravity"></a>
### If you use Google Antigravity

#### On a Mac

1. Open **Finder**.
2. Press **Cmd + Shift + G**.
3. Type (or paste): `~/.gemini/antigravity/skills`
4. Press **Enter**.

If missing, create the nested path: home folder (Cmd+Shift+H) → create `.gemini` → inside it create `antigravity` → inside that create `skills`.

#### On a Windows PC

1. Open **File Explorer**.
2. Address bar → paste: `%USERPROFILE%\.gemini\antigravity\skills`
3. Press **Enter**.

If missing, create the path: `%USERPROFILE%` → create `.gemini` → create `antigravity` inside it → create `skills` inside that.

---

## Step 3 — Drag the four skills into place

You should now have **two windows open**:

- **Window A:** the unzipped `skills` folder from Step 1, showing `personas`, `scenarios`, `scorecards`, `upload-users`.
- **Window B:** your AI assistant's empty (or near-empty) `skills` folder from Step 2.

Now:

1. In Window A, click `personas`, hold the Shift key, and click `upload-users`. All four folders should now be highlighted.
2. Drag them from Window A into Window B.
3. If your computer asks "Copy or Move?", choose **Copy**.

> *Screenshot: dragging the four skill folders from one window to another.*

When the copy finishes, Window B should now contain four folders: `personas`, `scenarios`, `scorecards`, `upload-users`.

You can close Window A.

---

## Step 4 — Save your Itero API key

The skills need your Itero API key to talk to your account. You'll put it in a small text file called `.env` inside the project folder you'll use the AI assistant from.

### Get the key

If you don't have one yet:

1. Sign in to [your Itero account](https://app.iteroapp.ai).
2. Go to **Settings → API Keys**.
3. Click **Create new key** and copy the long string of letters and numbers.

### Create the `.env` file in your IDE (recommended)

If you're using Cursor, VS Code, or Antigravity (any IDE built on VS Code), this is the easiest way:

1. In your IDE, open the project folder where you'll be using the AI assistant.
2. In the file explorer panel on the left, right-click in the empty space and choose **New File**.
3. Name the file exactly `.env` — with the leading dot, no extension. The file will appear at the top of the file list (dotfiles are visible by default in modern IDEs).
4. The file will open in the editor. Type:

   ```
   ITERO_API_KEY=
   ```

5. Click immediately after the equals sign. Paste your Itero API key. Save with **Cmd + S** (Mac) or **Ctrl + S** (Windows).

> *Screenshot: VS Code / Cursor file explorer with `.env` open in the editor, `ITERO_API_KEY=` typed, and the cursor positioned right after the equals sign ready for the customer to paste their key.*

It should look like this when saved:

```
ITERO_API_KEY=k_abcdef123456…your-actual-key-here
```

No spaces around `=`. No quotes around the key. Just the key, directly after the equals sign.

### Alternative: TextEdit (Mac) or Notepad (Windows)

Only use this if you're not in an IDE for some reason.

#### On a Mac

1. Open **TextEdit**.
2. Click **Format → Make Plain Text** (`.env` has to be plain text, not rich text).
3. Type `ITERO_API_KEY=` followed by your key.
4. Save (**Cmd + S**) → name it `.env` (with the leading dot) → save in your project folder.
   - When TextEdit warns about names starting with a dot, click **Use "."**.
   - When it asks about appending `.txt`, click **Don't append**.

> *Screenshot: macOS TextEdit save dialog with "Use '.'" prompt.*

#### On a Windows PC

1. Open **Notepad**.
2. Type `ITERO_API_KEY=` followed by your key.
3. **File → Save As** → name `.env` → in the **Save as type** dropdown, choose **All Files (\*.\*)** (otherwise Windows saves it as `.env.txt`, which won't work).
4. Save in your project folder.

> *Screenshot: Windows Notepad save dialog with "All Files" selected.*

### Multiple Itero accounts (optional)

If you manage more than one Itero tenant from the same project, you can add extra keys with names. For example:

```
ITERO_API_KEY=your-default-key
ITERO_API_KEY_PROD=your-production-key
ITERO_API_KEY_STAGING=your-staging-key
```

Then in your AI assistant you can say things like *"list scorecards on the staging tenant"* and it'll use the right one.

---

## Step 5 — Install Python (one time only)

The skills are written in Python. You probably don't have to think about this once it's set up — but you do need it installed.

### Check if you already have it

#### On a Mac

1. Open the **Terminal** app (you can find it via Spotlight: Cmd + Space, type "Terminal", press Enter).
2. Type: `pip3 install requests python-dotenv`
3. Press Enter.

If it succeeds (you'll see "Successfully installed…"), you're done. Skip to Step 6.

If it says **"command not found: pip3"**, you need to install Python first. Go to https://python.org → **Downloads** → click the big yellow button to download the macOS installer → run it → accept the defaults. Then come back and try `pip3 install requests python-dotenv` again.

#### On a Windows PC

1. Open **PowerShell** (Start menu → type "PowerShell" → press Enter).
2. Type: `pip3 install requests python-dotenv`
3. Press Enter.

If it succeeds, skip to Step 6.

If it says `pip3` is not recognized, install Python first. Go to https://python.org → **Downloads** → click the big yellow button → run the installer.

> **Important on Windows:** during install, check the box that says **"Add Python to PATH"** at the bottom of the first installer screen. Without this, the next steps won't work.

After Python is installed, open a fresh PowerShell window and try `pip3 install requests python-dotenv` again.

---

## Step 6 — Restart your AI assistant and test

1. Quit your AI assistant completely (don't just close the window — quit the app from the menu bar).
2. Re-open it.
3. Open the folder where you saved the `.env` file in Step 4 (the same folder you'd normally work in).
4. In the chat, type:

   > *list my scorecards*

5. Press Enter.

If you see your Itero scorecards (or a polite "no scorecards yet" message), **you're done. Welcome aboard.**

If something else happens, go to Troubleshooting below.

---

<a id="troubleshooting"></a>
## Troubleshooting

### "Nothing happens when I send the message"

Quit your AI assistant fully and reopen it. The skills only get loaded when the assistant starts up.

### "It says it can't find my API key"

Three things to check:

1. The `.env` file is in the same folder you have open in your AI assistant.
2. The file is literally named `.env` — not `.env.txt`, not `env`, not `.env.rtf`. Hidden files in Finder: press Cmd + Shift + . (period) to toggle visibility. In Windows File Explorer: View → Show → File name extensions.
3. The line in the file is exactly `ITERO_API_KEY=yourkey` with no spaces around the `=` and no quotation marks.

### "It says `pip3 not found` or `python not found`"

Install Python from https://python.org. On Windows, during install, check the box that says **"Add Python to PATH"**.

After installing, fully close any open Terminal/PowerShell windows and open a fresh one before retrying.

### "Hidden folders don't show up in Finder"

That's normal — folders starting with a dot (like `.claude` or `.agents`) are hidden by default on Mac. Always use **Cmd + Shift + G** ("Go to Folder") and type the path. Don't try to navigate to them by clicking through Finder.

You can also press **Cmd + Shift + .** (period) in any Finder window to temporarily show hidden folders.

### "Cursor isn't picking up the skills"

Confirm the folders are in `~/.agents/skills/` (or `~/.cursor/skills/` if you used that one). On Windows: `%USERPROFILE%\.agents\skills\`.

If you'd rather scope skills to a single project (so only that project sees them), create `<project-folder>/.cursor/skills/` and put the four folders there instead. Cursor reads from both global and project locations.

### "I get an error mentioning `requests` or `dotenv`"

You missed Step 5. Open Terminal (Mac) or PowerShell (Windows) and run:

```
pip3 install requests python-dotenv
```

### Still stuck?

Email **support@iteroapp.ai** and include:

- Which AI assistant you use (Claude Code / Codex / Cursor / Antigravity)
- Which OS (Mac or Windows)
- Which step of this guide you got stuck on
- The exact error message you saw, if any (a screenshot is great)

We'll get back to you the same business day.

---

## Advanced: install via plugin marketplace (Claude Code only)

If you're comfortable typing slash commands inside your AI assistant, Claude Code has a one-step install path that skips Steps 1–3 above:

1. Open Claude Code.
2. In the chat, type: `/plugin marketplace add Itero-AI/skills` and press Enter.
3. Then type: `/plugin install itero@itero-skills` and press Enter.
4. Continue with **Step 4** (the API key) and **Step 5** (Python) above. The plugin install handles the rest.

This path doesn't yet exist for Cursor, Codex, or Antigravity — those still use the manual download in Steps 1–3.
