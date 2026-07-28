#MenuTitle: Inherit Kerning From Selected Glyphs
# -*- coding: utf-8 -*-
__doc__ = """
Pick a donor glyph from your Font View selection and let the rest inherit
its kerning groups/classes. Dry run previews everything with no changes.
"""

# Workflow:
#   1. In Font View, select the donor glyph (already has correct kerning)
#      plus every glyph that should inherit it.
#   2. Run this script and pick the donor from the dropdown.
#   3. Leave "Dry run" checked and hit Run to preview. Uncheck and run
#      again once the preview looks right.
#
# Per side (left / right), independently:
#   - Donor already has a kerning GROUP on that side -> every other
#     selected glyph joins that same existing group.
#   - Donor has NO group but DOES have glyph-level (exception) kerning
#     on that side -> a new group is created (named UC_<name> / lc_<name>
#     depending on case), donor + targets join it, and the donor's old
#     exception pairs are converted into class pairs under it.
#   - Neither a group nor exceptions on that side -> nothing happens there.
#
# BACK UP YOUR .glyphs FILE FIRST — non-dry-run mode rewrites kerning
# data and group assignments.

from GlyphsApp import *
import vanilla

Glyphs.clearLog()
Glyphs.showMacroWindow()


class InheritKerningController:

    def __init__(self):
        self.font = Glyphs.font
        if self.font is None:
            Message("No font open", "Open a font first.", OKButton=None)
            return

        self.selectedGlyphs = list(self.font.selection)

        if len(self.selectedGlyphs) < 2:
            Message(
                "Select at least two glyphs",
                "Select the donor glyph plus at least one glyph that should "
                "inherit its kerning in Font View, then run this again.",
                OKButton=None,
            )
            return

        names = [g.name for g in self.selectedGlyphs]

        self.dryRunPrefKey = "com.inheritKerningFromSelected.dryRun"
        savedDryRun = Glyphs.defaults[self.dryRunPrefKey]
        if savedDryRun is None:
            savedDryRun = True  # default to safe/preview mode the very first time

        self.w = vanilla.Window((460, 380), "Inherit Kerning From Selected Glyphs")

        self.w.text1 = vanilla.TextBox((15, 15, -15, 20), f"{len(names)} glyph(s) selected.")
        self.w.text2 = vanilla.TextBox((15, 40, -15, 20), "Inherit kerning from (donor):")
        self.w.donorPopup = vanilla.PopUpButton((15, 62, -15, 22), names)

        self.w.dryRun = vanilla.CheckBox(
            (15, 95, -15, 20),
            "Dry run (preview only, no changes)",
            value=savedDryRun,
            callback=self.dryRunCallback,
        )

        self.w.runButton = vanilla.Button((15, 125, -15, 30), "Run", callback=self.runCallback)

        self.w.output = vanilla.TextEditor((15, 165, -15, -15), text="", readOnly=True)

        self.w.open()

    # -------------------------------------------------------------------
    def dryRunCallback(self, sender):
        Glyphs.defaults[self.dryRunPrefKey] = sender.get()

    # -------------------------------------------------------------------
    def log(self, line=""):
        current = self.w.output.get()
        self.w.output.set(current + ("\n" if current else "") + str(line))
        print(line)

    # -------------------------------------------------------------------
    def runCallback(self, sender):
        self.w.output.set("")
        font = self.font
        dryRun = self.w.dryRun.get()
        donorIndex = self.w.donorPopup.get()
        donor = self.selectedGlyphs[donorIndex]
        others = [g for g in self.selectedGlyphs if g is not donor]

        if not others:
            self.log("Need at least one other selected glyph besides the donor.")
            return

        prefix = "[DRY RUN] " if dryRun else ""
        self.log(f"{prefix}Donor: {donor.name}   Targets: {', '.join(g.name for g in others)}")
        self.log("")

        # ---- helpers -----------------------------------------------------
        def is_uppercase(glyph_name):
            root = glyph_name.split(".")[0]
            for ch in root:
                if ch.isalpha():
                    return ch.isupper()
            return True

        def group_name_for(glyph_name):
            return ("UC_" if is_uppercase(glyph_name) else "lc_") + glyph_name

        def get_left_exceptions(master_id, glyph_id):
            kerning = font.kerning.get(master_id, {})
            return dict(kerning.get(glyph_id, {}))

        def get_right_exceptions(master_id, glyph_id):
            result = {}
            kerning = font.kerning.get(master_id, {})
            for left_key, right_dict in kerning.items():
                if glyph_id in right_dict:
                    result[left_key] = right_dict[glyph_id]
            return result

        def resolve_key(key):
            """kerningForPair / setKerningForPair / removeKerningForPair need either
            a '@group' reference or the glyph's current NAME — not its raw id, even
            though font.kerning itself is keyed by id internally. Returns the usable
            string, or None if the id genuinely doesn't match any glyph anymore."""
            if key.startswith("@"):
                return key
            g = font.glyphForId_(key)
            return g.name if g else None

        has_left_group = bool(donor.leftKerningGroup)
        has_right_group = bool(donor.rightKerningGroup)

        left_has_exceptions = False
        right_has_exceptions = False
        if not has_left_group:
            for master in font.masters:
                if get_left_exceptions(master.id, donor.id):
                    left_has_exceptions = True
                    break
        if not has_right_group:
            for master in font.masters:
                if get_right_exceptions(master.id, donor.id):
                    right_has_exceptions = True
                    break

        if not (has_left_group or left_has_exceptions or has_right_group or right_has_exceptions):
            self.log(f"{donor.name} has no kerning groups and no kerning exceptions on either side — nothing to inherit.")
            return

        # ===================================================================
        # LEFT SIDE
        # ===================================================================
        if has_left_group:
            group = donor.leftKerningGroup
            self.log(f"LEFT — existing group '{group}':")
            for g in others:
                if g.leftKerningGroup and g.leftKerningGroup != group:
                    self.log(f"  SKIP {g.name}: already in a different left group '{g.leftKerningGroup}'")
                    continue
                if not dryRun:
                    g.leftKerningGroup = group
                self.log(f"  {prefix}{g.name}: joined left group '{group}'")

        elif left_has_exceptions:
            new_group = group_name_for(donor.name)
            self.log(f"LEFT — {prefix}creating new group '{new_group}':")
            if not dryRun:
                donor.leftKerningGroup = new_group
            for g in others:
                if g.leftKerningGroup and g.leftKerningGroup != new_group:
                    self.log(f"  SKIP {g.name}: already in a different left group '{g.leftKerningGroup}'")
                    continue
                if not dryRun:
                    g.leftKerningGroup = new_group
                self.log(f"  {prefix}{g.name}: joined new left group '{new_group}'")

            orphan_count = 0
            conflict_count = 0
            for master in font.masters:
                mid = master.id
                for right_key, value in get_left_exceptions(mid, donor.id).items():
                    resolved_right = resolve_key(right_key)
                    if resolved_right is None:
                        orphan_count += 1
                        self.log(f"  STALE [{master.name}] {donor.name}/{right_key} (value {value}): id does not match any glyph currently in the font (likely renamed/deleted)")
                        continue
                    new_left = f"@MMK_L_{new_group}"
                    try:
                        existing = font.kerningForPair(mid, new_left, resolved_right)
                    except Exception as e:
                        orphan_count += 1
                        self.log(f"  STALE [{master.name}] {donor.name}/{resolved_right} (value {value}): kerningForPair failed even after resolving to a name ({e})")
                        continue
                    if existing is None or existing == NSNotFound:
                        if not dryRun:
                            try:
                                font.setKerningForPair(mid, new_left, resolved_right, value)
                                font.removeKerningForPair(mid, donor.name, resolved_right)
                            except Exception as e:
                                orphan_count += 1
                                self.log(f"  STALE [{master.name}] {donor.name}/{resolved_right}: write/remove failed ({e})")
                                continue
                        self.log(f"  {prefix}[{master.name}] {donor.name}/{resolved_right} -> {new_left}/{resolved_right} = {value}")
                    elif existing == value:
                        if not dryRun:
                            try:
                                font.removeKerningForPair(mid, donor.name, resolved_right)
                            except Exception:
                                pass
                        self.log(f"  {prefix}[{master.name}] {donor.name}/{resolved_right} matches existing class value ({value}) — {'removing' if not dryRun else 'would remove'} redundant exception")
                    else:
                        conflict_count += 1
                        self.log(f"  CONFLICT [{master.name}] {donor.name}/{resolved_right}: donor exception = {value}, existing class '{new_left}' = {existing} — left untouched, please review manually")
            if orphan_count:
                self.log(f"  ({orphan_count} left-side exception pair(s) skipped — see STALE lines above for detail)")
            if conflict_count:
                self.log(f"  ({conflict_count} left-side value conflict(s) — see CONFLICT lines above)")
        else:
            self.log("LEFT — no group and no exceptions on the donor. Nothing to do.")

        self.log("")

        # ===================================================================
        # RIGHT SIDE
        # ===================================================================
        if has_right_group:
            group = donor.rightKerningGroup
            self.log(f"RIGHT — existing group '{group}':")
            for g in others:
                if g.rightKerningGroup and g.rightKerningGroup != group:
                    self.log(f"  SKIP {g.name}: already in a different right group '{g.rightKerningGroup}'")
                    continue
                if not dryRun:
                    g.rightKerningGroup = group
                self.log(f"  {prefix}{g.name}: joined right group '{group}'")

        elif right_has_exceptions:
            new_group = group_name_for(donor.name)
            self.log(f"RIGHT — {prefix}creating new group '{new_group}':")
            if not dryRun:
                donor.rightKerningGroup = new_group
            for g in others:
                if g.rightKerningGroup and g.rightKerningGroup != new_group:
                    self.log(f"  SKIP {g.name}: already in a different right group '{g.rightKerningGroup}'")
                    continue
                if not dryRun:
                    g.rightKerningGroup = new_group
                self.log(f"  {prefix}{g.name}: joined new right group '{new_group}'")

            orphan_count = 0
            conflict_count = 0
            for master in font.masters:
                mid = master.id
                for left_key, value in get_right_exceptions(mid, donor.id).items():
                    resolved_left = resolve_key(left_key)
                    if resolved_left is None:
                        orphan_count += 1
                        self.log(f"  STALE [{master.name}] {left_key}/{donor.name} (value {value}): id does not match any glyph currently in the font (likely renamed/deleted)")
                        continue
                    new_right = f"@MMK_R_{new_group}"
                    try:
                        existing = font.kerningForPair(mid, resolved_left, new_right)
                    except Exception as e:
                        orphan_count += 1
                        self.log(f"  STALE [{master.name}] {resolved_left}/{donor.name} (value {value}): kerningForPair failed even after resolving to a name ({e})")
                        continue
                    if existing is None or existing == NSNotFound:
                        if not dryRun:
                            try:
                                font.setKerningForPair(mid, resolved_left, new_right, value)
                                font.removeKerningForPair(mid, resolved_left, donor.name)
                            except Exception as e:
                                orphan_count += 1
                                self.log(f"  STALE [{master.name}] {resolved_left}/{donor.name}: write/remove failed ({e})")
                                continue
                        self.log(f"  {prefix}[{master.name}] {resolved_left}/{donor.name} -> {resolved_left}/{new_right} = {value}")
                    elif existing == value:
                        if not dryRun:
                            try:
                                font.removeKerningForPair(mid, resolved_left, donor.name)
                            except Exception:
                                pass
                        self.log(f"  {prefix}[{master.name}] {resolved_left}/{donor.name} matches existing class value ({value}) — {'removing' if not dryRun else 'would remove'} redundant exception")
                    else:
                        conflict_count += 1
                        self.log(f"  CONFLICT [{master.name}] {resolved_left}/{donor.name}: donor exception = {value}, existing class '{new_right}' = {existing} — left untouched, please review manually")
            if orphan_count:
                self.log(f"  ({orphan_count} right-side exception pair(s) skipped — see STALE lines above for detail)")
            if conflict_count:
                self.log(f"  ({conflict_count} right-side value conflict(s) — see CONFLICT lines above)")
        else:
            self.log("RIGHT — no group and no exceptions on the donor. Nothing to do.")

        self.log("")
        self.log(f"{'DRY RUN complete — nothing was changed.' if dryRun else 'Done — file has been modified.'}")


InheritKerningController()
