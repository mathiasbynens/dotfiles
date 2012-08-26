import sublime, sublime_plugin


def expand_to_line(view, region):
    """
    As view.full_line, but doesn't expand to the next line if a full line is
    already selected
    """
    if not (region.a == region.b) and view.substr(region.end() - 1) == '\n':
        return sublime.Region(view.line(region).begin(), region.end())
    else:
        return view.full_line(region)


def extract_line_blocks(view):
    blocks = [expand_to_line(view, s) for s in view.sel()]
    if len(blocks) == 0:
        return blocks

    # merge any adjacent blocks
    merged_blocks = [blocks[0]]
    for block in blocks[1:]:
        last_block = merged_blocks[-1]
        if block.begin() <= last_block.end():
            merged_blocks[-1] = sublime.Region(last_block.begin(), block.end())
        else:
            merged_blocks.append(block)

    return merged_blocks

class SwapLineUpCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        blocks = extract_line_blocks(self.view)

        # No selection
        if len(blocks) == 0:
            return

        # Already at BOF
        if blocks[0].begin() == 0:
            return

        # Add a trailing newline if required, the logic is simpler if every line
        # ends with a newline
        add_trailing_newline = (self.view.substr(self.view.size() - 1) != '\n') and blocks[-1].b == self.view.size()
        if add_trailing_newline:
            # The insert can cause the selection to move. This isn't wanted, so
            # reset the selection if it has moved to EOF
            sel = [r for r in self.view.sel()]
            self.view.insert(edit, self.view.size(), '\n')
            if self.view.sel()[-1].end() == self.view.size():
                # Selection has moved, restore the previous selection
                self.view.sel().clear()
                for r in sel:
                    self.view.sel().add(r)

            # Fix up any block that should now include this newline
            blocks[-1] = sublime.Region(blocks[-1].a, blocks[-1].b + 1)

        # Process in reverse order
        blocks.reverse()
        for b in blocks:
            prev_line = self.view.full_line(b.begin() - 1)
            self.view.insert(edit, b.end(), self.view.substr(prev_line))
            self.view.erase(edit, prev_line)

        if add_trailing_newline:
            # Remove the added newline
            self.view.erase(edit, sublime.Region(self.view.size() - 1, self.view.size()))

        # Ensure the selection is visible
        self.view.show(self.view.sel(), False)

class SwapLineDownCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        blocks = extract_line_blocks(self.view)

        # No selection
        if len(blocks) == 0:
            return

        # Already at EOF
        if blocks[-1].end() == self.view.size():
            return

        # Add a trailing newline if required, the logic is simpler if every line
        # ends with a newline
        add_trailing_newline = (self.view.substr(self.view.size() - 1) != '\n')
        if add_trailing_newline:
            # No block can be at EOF (checked above), so no need to fix up the
            # blocks
            self.view.insert(edit, self.view.size(), '\n')

        # Process in reverse order
        blocks.reverse()
        for b in blocks:
            next_line = self.view.full_line(b.end())
            contents = self.view.substr(next_line)

            self.view.erase(edit, next_line)
            self.view.insert(edit, b.begin(), contents)

        if add_trailing_newline:
            # Remove the added newline
            self.view.erase(edit, sublime.Region(self.view.size() - 1, self.view.size()))

        # Ensure the selection is visible
        self.view.show(self.view.sel(), False)
