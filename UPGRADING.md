# Upgrading Itero Skills from v1 to v2

Do not copy v2 over an existing v1 install. A folder merge can leave the six old HTTP-client copies active. The commands below first move exactly the six v1 API-skill folders to reversible backups, then copy clean v2 replacements plus the new `conversations` skill. The two document-preparation skills are unchanged and stay in place.

Open a Bash or Zsh shell in your current v2 clone. Set `ITERO_SKILLS_DEST` to the absolute skills-directory path for your assistant before running the block.

```bash
set -eu
ITERO_SKILLS_SOURCE="$(git rev-parse --show-toplevel)"
ITERO_SKILLS_DEST="/absolute/path/to/your/agent/skills"

test -f "$ITERO_SKILLS_SOURCE/README.md"
test -d "$ITERO_SKILLS_DEST"
test "$ITERO_SKILLS_DEST" != "/"
test ! -e "$ITERO_SKILLS_DEST/personas.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/scenarios.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/scorecards.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/learning-paths.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/manage-users.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/upload-users.v1.bak"
test ! -e "$ITERO_SKILLS_DEST/conversations"

# All six v1 folders must exist before anything moves — a partial install
# would otherwise stop mid-upgrade with some skills moved and some not.
test -d "$ITERO_SKILLS_DEST/personas"
test -d "$ITERO_SKILLS_DEST/scenarios"
test -d "$ITERO_SKILLS_DEST/scorecards"
test -d "$ITERO_SKILLS_DEST/learning-paths"
test -d "$ITERO_SKILLS_DEST/manage-users"
test -d "$ITERO_SKILLS_DEST/upload-users"

mv "$ITERO_SKILLS_DEST/personas" "$ITERO_SKILLS_DEST/personas.v1.bak"
mv "$ITERO_SKILLS_DEST/scenarios" "$ITERO_SKILLS_DEST/scenarios.v1.bak"
mv "$ITERO_SKILLS_DEST/scorecards" "$ITERO_SKILLS_DEST/scorecards.v1.bak"
mv "$ITERO_SKILLS_DEST/learning-paths" "$ITERO_SKILLS_DEST/learning-paths.v1.bak"
mv "$ITERO_SKILLS_DEST/manage-users" "$ITERO_SKILLS_DEST/manage-users.v1.bak"
mv "$ITERO_SKILLS_DEST/upload-users" "$ITERO_SKILLS_DEST/upload-users.v1.bak"

cp -R "$ITERO_SKILLS_SOURCE/skills/personas" "$ITERO_SKILLS_DEST/personas"
cp -R "$ITERO_SKILLS_SOURCE/skills/scenarios" "$ITERO_SKILLS_DEST/scenarios"
cp -R "$ITERO_SKILLS_SOURCE/skills/scorecards" "$ITERO_SKILLS_DEST/scorecards"
cp -R "$ITERO_SKILLS_SOURCE/skills/learning-paths" "$ITERO_SKILLS_DEST/learning-paths"
cp -R "$ITERO_SKILLS_SOURCE/skills/manage-users" "$ITERO_SKILLS_DEST/manage-users"
cp -R "$ITERO_SKILLS_SOURCE/skills/upload-users" "$ITERO_SKILLS_DEST/upload-users"
cp -R "$ITERO_SKILLS_SOURCE/skills/conversations" "$ITERO_SKILLS_DEST/conversations"
```

Confirm that the six backups exist before removing or replacing anything else:

```bash
ls -d "$ITERO_SKILLS_DEST"/*.v1.bak
```

To restore v1, first print and inspect `ITERO_SKILLS_DEST`, verify that it is the intended skills directory, and verify all six backup folders exist. Then run these exact restore commands:

```bash
set -eu
printf '%s\n' "$ITERO_SKILLS_DEST"
test -n "$ITERO_SKILLS_DEST" && test "$ITERO_SKILLS_DEST" != "/"
test -d "$ITERO_SKILLS_DEST/personas.v1.bak"
test -d "$ITERO_SKILLS_DEST/scenarios.v1.bak"
test -d "$ITERO_SKILLS_DEST/scorecards.v1.bak"
test -d "$ITERO_SKILLS_DEST/learning-paths.v1.bak"
test -d "$ITERO_SKILLS_DEST/manage-users.v1.bak"
test -d "$ITERO_SKILLS_DEST/upload-users.v1.bak"

rm -rf "$ITERO_SKILLS_DEST/personas" && mv "$ITERO_SKILLS_DEST/personas.v1.bak" "$ITERO_SKILLS_DEST/personas"
rm -rf "$ITERO_SKILLS_DEST/scenarios" && mv "$ITERO_SKILLS_DEST/scenarios.v1.bak" "$ITERO_SKILLS_DEST/scenarios"
rm -rf "$ITERO_SKILLS_DEST/scorecards" && mv "$ITERO_SKILLS_DEST/scorecards.v1.bak" "$ITERO_SKILLS_DEST/scorecards"
rm -rf "$ITERO_SKILLS_DEST/learning-paths" && mv "$ITERO_SKILLS_DEST/learning-paths.v1.bak" "$ITERO_SKILLS_DEST/learning-paths"
rm -rf "$ITERO_SKILLS_DEST/manage-users" && mv "$ITERO_SKILLS_DEST/manage-users.v1.bak" "$ITERO_SKILLS_DEST/manage-users"
rm -rf "$ITERO_SKILLS_DEST/upload-users" && mv "$ITERO_SKILLS_DEST/upload-users.v1.bak" "$ITERO_SKILLS_DEST/upload-users"
```

The restore commands leave `conversations` installed because v1 has no folder to restore for it. Remove that folder only after verifying the destination path if you want an exact v1-only set.

