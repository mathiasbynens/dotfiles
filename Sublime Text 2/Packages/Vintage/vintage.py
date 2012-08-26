import sublime, sublime_plugin
import os.path

# Normal: Motions apply to all the characters they select
MOTION_MODE_NORMAL = 0
# Used in visual line mode: Motions are extended to BOL and EOL.
MOTION_MODE_LINE = 2

# Registers are used for clipboards and macro storage
g_registers = {}

# Represents the current input state. The primary commands that interact with
# this are:
# * set_action
# * set_motion
# * push_repeat_digit
class InputState:
    prefix_repeat_digits = []
    action_command = None
    action_command_args = None
    action_description = None
    motion_repeat_digits = []
    motion_command = None
    motion_command_args = None
    motion_mode = MOTION_MODE_NORMAL
    motion_mode_overridden = False
    motion_inclusive = False
    motion_clip_to_line = False
    register = None

g_input_state = InputState()

# Updates the status bar to reflect the current mode and input state
def update_status_line(view):
    desc = []

    if view.settings().get('command_mode'):
        if g_input_state.motion_mode == MOTION_MODE_LINE:
            desc = ['VISUAL LINE MODE']
        elif view.has_non_empty_selection_region():
            desc = ['VISUAL MODE']
        else:
            desc = ['COMMAND MODE']
            if g_input_state.action_command is not None:
                if g_input_state.action_description:
                    desc.append(g_input_state.action_description)
                else:
                    desc.append(g_input_state.action_command)

            repeat = (digits_to_number(g_input_state.prefix_repeat_digits)
                * digits_to_number(g_input_state.motion_repeat_digits))
            if repeat != 1:
                if g_input_state.action_command is not None:
                    desc[-1] += " * " + str(repeat)
                else:
                    desc.append("* " + str(repeat))

        if g_input_state.register is not None:
            desc.insert(1, 'Register "' + g_input_state.register + '"')
    else:
        desc = ['INSERT MODE']

    view.set_status('mode', ' - '.join(desc))

def set_motion_mode(view, mode):
    g_input_state.motion_mode = mode
    update_status_line(view)

def reset_input_state(view, reset_motion_mode = True):
    global g_input_state
    g_input_state.prefix_repeat_digits = []
    g_input_state.action_command = None
    g_input_state.action_command_args = None
    g_input_state.action_description = None
    g_input_state.motion_repeat_digits = []
    g_input_state.motion_command = None
    g_input_state.motion_mode_overridden = False
    g_input_state.motion_command_args = None
    g_input_state.motion_inclusive = False
    g_input_state.motion_clip_to_line = False
    g_input_state.register = None
    if reset_motion_mode:
        set_motion_mode(view, MOTION_MODE_NORMAL)

class ViCancelCurrentAction(sublime_plugin.TextCommand):
    def run(self, action, action_args = {}, motion_mode = None, description = None):
        reset_input_state(self.view, True)

def string_to_motion_mode(mode):
    if mode == 'normal':
        return MOTION_MODE_NORMAL
    elif mode == 'line':
        return MOTION_MODE_LINE
    else:
        return -1

# Called when the plugin is unloaded (e.g., perhaps it just got added to
# ignored_packages). Ensure files aren't left in command mode.
def unload_handler():
    for w in sublime.windows():
        for v in w.views():
            v.settings().set('command_mode', False)
            v.settings().set('inverse_caret_state', False)
            v.erase_status('mode')

# Ensures the input state is reset when the view changes, or the user selects
# with the mouse or non-vintage key bindings
class InputStateTracker(sublime_plugin.EventListener):
    def __init__(self):
        for w in sublime.windows():
            for v in w.views():
                if v.settings().get("vintage_start_in_command_mode"):
                    v.settings().set('command_mode', True)
                    v.settings().set('inverse_caret_state', True)
                update_status_line(v)

    def on_activated(self, view):
        reset_input_state(view)

    def on_deactivated(self, view):
        reset_input_state(view)

        # Ensure that insert mode actions will no longer be grouped, otherwise
        # it can lead to the impression that too much is undone at once
        view.run_command('unmark_undo_groups_for_gluing')

    def on_post_save(self, view):
        # Ensure that insert mode actions will no longer be grouped, so it's
        # always possible to undo back to the last saved state
        view.run_command('unmark_undo_groups_for_gluing')

    def on_selection_modified(self, view):
        reset_input_state(view, False)
        # Get out of visual line mode if the selection has changed, e.g., due
        # to clicking with the mouse
        if (g_input_state.motion_mode == MOTION_MODE_LINE and
            not view.has_non_empty_selection_region()):
            g_input_state.motion_mode = MOTION_MODE_NORMAL
        update_status_line(view)

    def on_load(self, view):
        if view.settings().get("vintage_start_in_command_mode"):
            view.run_command('exit_insert_mode')

    def on_new(self, view):
        self.on_load(view)

    def on_clone(self, view):
        self.on_load(view)

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "vi_action" and g_input_state.action_command:
            if operator == sublime.OP_EQUAL:
                return operand == g_input_state.action_command
            if operator == sublime.OP_NOT_EQUAL:
                return operand != g_input_state.action_command
        elif key == "vi_has_action":
            v = g_input_state.action_command is not None
            if operator == sublime.OP_EQUAL: return v == operand
            if operator == sublime.OP_NOT_EQUAL: return v != operand
        elif key == "vi_has_register":
            r = g_input_state.register is not None
            if operator == sublime.OP_EQUAL: return r == operand
            if operator == sublime.OP_NOT_EQUAL: return r != operand
        elif key == "vi_motion_mode":
            m = string_to_motion_mode(operand)
            if operator == sublime.OP_EQUAL:
                return m == g_input_state.motion_mode
            if operator == sublime.OP_NOT_EQUAL:
                return m != g_input_state.motion_mode
        elif key == "vi_has_repeat_digit":
            if g_input_state.action_command:
                v = len(g_input_state.motion_repeat_digits) > 0
            else:
                v = len(g_input_state.prefix_repeat_digits) > 0
            if operator == sublime.OP_EQUAL: return v == operand
            if operator == sublime.OP_NOT_EQUAL: return v != operand
        elif key == "vi_has_input_state":
            v = (len(g_input_state.motion_repeat_digits) > 0 or
                len(g_input_state.prefix_repeat_digits) > 0 or
                g_input_state.action_command is not None or
                g_input_state.register is not None)
            if operator == sublime.OP_EQUAL: return v == operand
            if operator == sublime.OP_NOT_EQUAL: return v != operand
        elif key == "vi_can_enter_text_object":
            v = (g_input_state.action_command is not None) or view.has_non_empty_selection_region()
            if operator == sublime.OP_EQUAL: return v == operand
            if operator == sublime.OP_NOT_EQUAL: return v != operand

        return None

# Called when g_input_state represents a fully formed command. Generates a
# call to vi_eval, which is what will be left on the undo/redo stack.
def eval_input(view):
    global g_input_state

    cmd_args = {
        'action_command': g_input_state.action_command,
        'action_args': g_input_state.action_command_args,
        'motion_command': g_input_state.motion_command,
        'motion_args': g_input_state.motion_command_args,
        'motion_mode': g_input_state.motion_mode,
        'motion_inclusive': g_input_state.motion_inclusive,
        'motion_clip_to_line': g_input_state.motion_clip_to_line }

    if len(g_input_state.prefix_repeat_digits) > 0:
        cmd_args['prefix_repeat'] = digits_to_number(g_input_state.prefix_repeat_digits)

    if len(g_input_state.motion_repeat_digits) > 0:
        cmd_args['motion_repeat'] = digits_to_number(g_input_state.motion_repeat_digits)

    if g_input_state.register is not None:
        if not cmd_args['action_args']:
            cmd_args['action_args'] = {}
        cmd_args['action_args']['register'] = g_input_state.register

    reset_motion_mode = (g_input_state.action_command is not None)

    reset_input_state(view, reset_motion_mode)

    view.run_command('vi_eval', cmd_args)

# Adds a repeat digit to the input state.
# Repeat digits may come before the action, after the action, or both. For
# example:
#   4dw
#   d4w
#   2d2w
# These commands will all delete 4 words.
class PushRepeatDigit(sublime_plugin.TextCommand):
    def run(self, edit, digit):
        global g_input_state
        if g_input_state.action_command:
            g_input_state.motion_repeat_digits.append(digit)
        else:
            g_input_state.prefix_repeat_digits.append(digit)
        update_status_line(self.view)

# Set the current action in the input state. Note that this won't create an
# entry on the undo stack: only eval_input does this.
class SetAction(sublime_plugin.TextCommand):
    # Custom version of run_, so an edit object isn't created. This allows
    # eval_input() to add the desired command to the undo stack
    def run_(self, args):
        if 'event' in args:
            del args['event']

        return self.run(**args)

    def run(self, action, action_args = {}, description = None):
        global g_input_state
        g_input_state.action_command = action
        g_input_state.action_command_args = action_args
        g_input_state.action_description = description

        if self.view.has_non_empty_selection_region():
            # Currently in visual mode, so no following motion is expected:
            # eval the current input
            eval_input(self.view)
        else:
            update_status_line(self.view)

def digits_to_number(digits):
    if len(digits) == 0:
        return 1

    number = 0
    place = 1
    for d in reversed(digits):
        number += place * int(d)
        place *= 10
    return number

# Set the current motion in the input state. Note that this won't create an
# entry on the undo stack: only eval_input does this.
class SetMotion(sublime_plugin.TextCommand):
    # Custom version of run_, so an edit object isn't created. This allows
    # eval_input() to add the desired command to the undo stack
    def run_(self, args):
        return self.run(**args)

    def run(self, motion, motion_args = {}, linewise = False, inclusive = False,
            clip_to_line = False, character = None, mode = None):

        global g_input_state

        # Pass the character, if any, onto the motion command.
        # This is required for 'f', 't', etc
        if character is not None:
            motion_args['character'] = character

        g_input_state.motion_command = motion
        g_input_state.motion_command_args = motion_args
        g_input_state.motion_inclusive = inclusive
        g_input_state.motion_clip_to_line = clip_to_line
        if not g_input_state.motion_mode_overridden \
                and g_input_state.action_command \
                and linewise:
            g_input_state.motion_mode = MOTION_MODE_LINE

        if mode is not None:
            m = string_to_motion_mode(mode)
            if m != -1:
                set_motion_mode(self.view, m)
            else:
                print "invalid motion mode:", mode

        eval_input(self.view)

# Run a single, combined action and motion. Examples are 'D' (delete to EOL)
# and 'C' (change to EOL).
class SetActionMotion(sublime_plugin.TextCommand):
    # Custom version of run_, so an edit object isn't created. This allows
    # eval_input() to add the desired command to the undo stack
    def run_(self, args):
        return self.run(**args)

    def run(self, motion, action, motion_args = {}, motion_clip_to_line = False,
            motion_inclusive = False, motion_linewise = False, action_args = {}):

        global g_input_state

        g_input_state.motion_command = motion
        g_input_state.motion_command_args = motion_args
        g_input_state.motion_inclusive = motion_inclusive
        g_input_state.motion_clip_to_line = motion_clip_to_line
        g_input_state.action_command = action
        g_input_state.action_command_args = action_args
        if motion_linewise:
            g_input_state.motion_mode = MOTION_MODE_LINE

        eval_input(self.view)

# Update the current motion mode. e.g., 'dvj'
class SetMotionMode(sublime_plugin.TextCommand):
    def run_(self, args):
        if 'event' in args:
            del args['event']

        return self.run(**args)

    def run(self, mode):
        global g_input_state
        m = string_to_motion_mode(mode)

        if m != -1:
            set_motion_mode(self.view, m)
            g_input_state.motion_mode_overridden = True
        else:
            print "invalid motion mode"

class SetRegister(sublime_plugin.TextCommand):
    def run_(self, args):
        return self.run(**args)

    def run(self, character):
        g_input_state.register = character
        update_status_line(self.view)

def clip_point_to_line(view, f, pt):
    l = view.line(pt)
    if l.a == l.b:
        return l.a

    new_pt = f(pt)
    if new_pt < l.a:
        return l.a
    elif new_pt >= l.b:
        return l.b
    else:
        return new_pt

def transform_selection(view, f, extend = False, clip_to_line = False):
    new_sel = []
    sel = view.sel()
    size = view.size()

    for r in sel:
        if clip_to_line:
            new_pt = clip_point_to_line(view, f, r.b)
        else:
            new_pt = f(r.b)

        if new_pt < 0: new_pt = 0
        elif new_pt > size: new_pt = size

        if extend:
            new_sel.append(sublime.Region(r.a, new_pt))
        else:
            new_sel.append(sublime.Region(new_pt))

    sel.clear()
    for r in new_sel:
        sel.add(r)

def transform_selection_regions(view, f):
    new_sel = []
    sel = view.sel()

    for r in sel:
        nr = f(r)
        if nr is not None:
            new_sel.append(nr)

    sel.clear()
    for r in new_sel:
        sel.add(r)

def expand_to_full_line(view, ignore_trailing_newline = True):
    new_sel = []
    for s in view.sel():
        if s.a == s.b:
            new_sel.append(view.full_line(s.a))
        else:
            la = view.full_line(s.begin())
            lb = view.full_line(s.end())

            a = la.a

            if ignore_trailing_newline and s.end() == lb.a:
                # s.end() is already at EOL, don't go down to the next line
                b = s.end()
            else:
                b = lb.b

            if s.a < s.b:
                new_sel.append(sublime.Region(a, b, 0))
            else:
                new_sel.append(sublime.Region(b, a, 0))

    view.sel().clear()
    for s in new_sel:
        view.sel().add(s)

def orient_single_line_region(view, forward, r):
    l = view.full_line(r.begin())
    if l.a == r.begin() and l.end() == r.end():
        if forward:
            return l
        else:
            return sublime.Region(l.b, l.a)
    else:
        return r

def set_single_line_selection_direction(view, forward):
    transform_selection_regions(view,
        lambda r: orient_single_line_region(view, forward, r))

def orient_single_character_region(view, forward, r):
    if r.begin() + 1 == r.end():
        if forward:
            return sublime.Region(r.begin(), r.end())
        else:
            return sublime.Region(r.end(), r.begin())
    else:
        return r

def set_single_character_selection_direction(view, forward):
    transform_selection_regions(view,
        lambda r: orient_single_character_region(view, forward, r))

def clip_empty_selection_to_line_contents(view):
    new_sel = []
    for s in view.sel():
        if s.empty():
            l = view.line(s.b)
            if s.b == l.b and not l.empty():
                s = sublime.Region(l.b - 1, l.b - 1, s.xpos())

        new_sel.append(s)

    view.sel().clear()
    for s in new_sel:
        view.sel().add(s)

def shrink_inclusive(r):
    if r.a < r.b:
        return sublime.Region(r.b - 1, r.b - 1, r.xpos())
    else:
        return sublime.Region(r.b, r.b, r.xpos())

def shrink_exclusive(r):
    return sublime.Region(r.b, r.b, r.xpos())

def shrink_to_first_char(r):
    if r.b < r.a:
        # If the Region is reversed, the first char is the character *before*
        # the first bound.
        return sublime.Region(r.a - 1)
    else:
        return sublime.Region(r.a)

# This is the core: it takes a motion command, action command, and repeat
# counts, and runs them all.
#
# Note that this doesn't touch g_input_state, and doesn't maintain any state
# other than what's passed on its arguments. This allows it to operate correctly
# in macros, and when running via repeat.
class ViEval(sublime_plugin.TextCommand):
    def run_(self, args):
        was_visual = self.view.has_non_empty_selection_region()

        edit = self.view.begin_edit(self.name(), args)
        try:
            self.run(edit, **args)
        finally:
            self.view.end_edit(edit)

        # Glue the marked undo groups if visual mode was exited (e.g., by
        # running an action while in visual mode). This ensures that
        # v+motions+action can be repeated as a single unit.
        if self.view.settings().get('command_mode') == True:
            is_visual = self.view.has_non_empty_selection_region()
            if was_visual and not is_visual:
                self.view.run_command('glue_marked_undo_groups')
            elif not is_visual:
                self.view.run_command('unmark_undo_groups_for_gluing')

    def run(self, edit, action_command, action_args,
            motion_command, motion_args, motion_mode,
            motion_inclusive, motion_clip_to_line,
            prefix_repeat = None, motion_repeat = None):

        explicit_repeat = (prefix_repeat is not None or motion_repeat is not None)

        if prefix_repeat is None:
            prefix_repeat = 1
        if motion_repeat is None:
            motion_repeat = 1

        # Arguments are always passed as floats (thanks to JSON encoding),
        # convert them back to integers
        prefix_repeat = int(prefix_repeat)
        motion_repeat = int(motion_repeat)
        motion_mode = int(motion_mode)

        # Combine the prefix_repeat and motion_repeat into motion_repeat, to
        # allow commands like 2yy to work by first doing the motion twice,
        # then operating once
        if motion_command and prefix_repeat > 1:
            motion_repeat *= prefix_repeat
            prefix_repeat = 1

        # Check if the motion command would like to handle the repeat itself
        if motion_args and 'repeat' in motion_args:
            motion_args['repeat'] = motion_repeat * prefix_repeat
            motion_repeat = 1
            prefix_repeat = 1

        # Some commands behave differently if a repeat is given. e.g., 1G goes
        # to line one, but G without a repeat goes to EOF. Let the command
        # know if a repeat was specified.
        if motion_args and 'explicit_repeat' in motion_args:
            motion_args['explicit_repeat'] = explicit_repeat

        visual_mode = self.view.has_non_empty_selection_region()

        # Let the motion know if we're in visual mode, if it wants to know
        if motion_args and 'visual' in motion_args:
            motion_args['visual'] = visual_mode

        for i in xrange(prefix_repeat):
            # Run the motion command, extending the selection to the range of
            # characters covered by the motion
            if motion_command:
                direction = 0
                if motion_args and 'forward' in motion_args:
                    forward = motion_args['forward']
                    if forward:
                        direction = 1
                    else:
                        direction = -1

                for j in xrange(motion_repeat):
                    if direction != 0 and motion_mode == MOTION_MODE_LINE:
                        # Ensure selections encompassing a single line are
                        # oriented in the same way as the motion, so they'll
                        # remain selected. This is needed so that Vk will work
                        # as expected
                        set_single_line_selection_direction(self.view, direction == 1)
                    elif direction != 0:
                        set_single_character_selection_direction(self.view, direction == 1)

                    if motion_mode == MOTION_MODE_LINE:
                        # Don't do either of the below things: this is
                        # important so that Vk on an empty line would select
                        # the following line.
                        pass
                    elif direction == 1 and motion_inclusive:
                        # Expand empty selections include the character
                        # they're on, and to start from the RHS of the
                        # character
                        transform_selection_regions(self.view,
                            lambda r: sublime.Region(r.b, r.b + 1, r.xpos()) if r.empty() else r)

                    self.view.run_command(motion_command, motion_args)

            # If the motion needs to be clipped to the line, remove any
            # trailing newlines from the selection. For example, with the
            # caret at the start of the last word on the line, 'dw' should
            # delete the word, but not the newline, while 'w' should advance
            # the caret to the first character of the next line.
            if motion_mode != MOTION_MODE_LINE and action_command and motion_clip_to_line:
                transform_selection_regions(self.view, lambda r: self.view.split_by_newlines(r)[0])

            reindent = False

            if motion_mode == MOTION_MODE_LINE:
                expand_to_full_line(self.view, visual_mode)
                if action_command == "enter_insert_mode":
                    # When lines are deleted before entering insert mode, the
                    # cursor should be left on an empty line. Leave the trailing
                    # newline out of the selection to allow for this.
                    transform_selection_regions(self.view,
                        lambda r: (sublime.Region(r.begin(), r.end() - 1)
                                   if not r.empty() and self.view.substr(r.end() - 1) == "\n"
                                   else r))
                    reindent = True

            if action_command:
                # Apply the action to the selection
                self.view.run_command(action_command, action_args)
                if reindent and self.view.settings().get('auto_indent'):
                    self.view.run_command('reindent', {'force_indent': False})

        if not visual_mode:
            # Shrink the selection down to a point
            if motion_inclusive:
                transform_selection_regions(self.view, shrink_inclusive)
            else:
                transform_selection_regions(self.view, shrink_exclusive)

        # Clip the selections to the line contents
        if self.view.settings().get('command_mode'):
            clip_empty_selection_to_line_contents(self.view)

        # Ensure the selection is visible
        self.view.show(self.view.sel())


class EnterInsertMode(sublime_plugin.TextCommand):
    # Ensure no undo group is created: the only entry on the undo stack should
    # be the insert_command, if any
    def run_(self, args):
        if args:
            return self.run(**args)
        else:
            return self.run()

    def run(self, insert_command = None, insert_args = {}, register = '"'):
        # mark_undo_groups_for_gluing allows all commands run while in insert
        # mode to comprise a single undo group, which is important for '.' to
        # work as desired.
        self.view.run_command('maybe_mark_undo_groups_for_gluing')
        if insert_command:
            args = insert_args.copy()
            args.update({'register': register})
            self.view.run_command(insert_command, args)

        self.view.settings().set('command_mode', False)
        self.view.settings().set('inverse_caret_state', False)
        update_status_line(self.view)

class ExitInsertMode(sublime_plugin.TextCommand):
    def run_(self, args):
        edit = self.view.begin_edit(self.name(), args)
        try:
            self.run(edit)
        finally:
            self.view.end_edit(edit)

        # Call after end_edit(), to ensure the final entry in the glued undo
        # group is 'exit_insert_mode'.
        self.view.run_command('glue_marked_undo_groups')

    def run(self, edit):
        self.view.settings().set('command_mode', True)
        self.view.settings().set('inverse_caret_state', True)

        if not self.view.has_non_empty_selection_region():
            self.view.run_command('vi_move_by_characters_in_line', {'forward': False})

        update_status_line(self.view)

class EnterVisualMode(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('mark_undo_groups_for_gluing')
        if g_input_state.motion_mode != MOTION_MODE_NORMAL:
            set_motion_mode(self.view, MOTION_MODE_NORMAL)

        transform_selection_regions(self.view, lambda r: sublime.Region(r.b, r.b + 1) if r.empty() else r)

class ExitVisualMode(sublime_plugin.TextCommand):
    def run(self, edit, toggle = False):
        if toggle:
            if g_input_state.motion_mode != MOTION_MODE_NORMAL:
                set_motion_mode(self.view, MOTION_MODE_NORMAL)
            else:
                self.view.run_command('shrink_selections')
        else:
            set_motion_mode(self.view, MOTION_MODE_NORMAL)
            self.view.run_command('shrink_selections')

        self.view.run_command('unmark_undo_groups_for_gluing')

class EnterVisualLineMode(sublime_plugin.TextCommand):
    def run(self, edit):
        set_motion_mode(self.view, MOTION_MODE_LINE)
        expand_to_full_line(self.view)
        self.view.run_command('maybe_mark_undo_groups_for_gluing')

class ShrinkSelections(sublime_plugin.TextCommand):
    def shrink(self, r):
        if r.empty():
            return r
        elif r.a < r.b:
            return sublime.Region(r.b - 1)
        else:
            return sublime.Region(r.b)

    def run(self, edit):
        transform_selection_regions(self.view, self.shrink)

class ShrinkSelectionsToBeginning(sublime_plugin.TextCommand):
    def shrink(self, r):
        return sublime.Region(r.begin())

    def run(self, edit, register = '"'):
        transform_selection_regions(self.view, self.shrink)

class ShrinkSelectionsToEnd(sublime_plugin.TextCommand):
    def shrink(self, r):
        end = r.end()
        if self.view.substr(end - 1) == u'\n':
            # For linewise selections put the cursor *before* the line break
            return sublime.Region(end - 1)
        else:
            return sublime.Region(end)

    def run(self, edit, register = '"'):
        transform_selection_regions(self.view, self.shrink)

class VisualUpperCase(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("upper_case")
        self.view.run_command("exit_visual_mode")

class VisualLowerCase(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("lower_case")
        self.view.run_command("exit_visual_mode")

# Sequence is used as part of glue_marked_undo_groups: the marked undo groups
# are rewritten into a single sequence command, that accepts all the previous
# commands
class Sequence(sublime_plugin.TextCommand):
    def run(self, edit, commands):
        for cmd, args in commands:
            self.view.run_command(cmd, args)

class ViDelete(sublime_plugin.TextCommand):
    def run(self, edit, register = '"'):
        if self.view.has_non_empty_selection_region():
            set_register(self.view, register, forward=False)
            set_register(self.view, '1', forward=False)
            self.view.run_command('left_delete')

class ViLeftDelete(sublime_plugin.TextCommand):
    def run(self, edit, register = '"'):
        set_register(self.view, register, forward=False)
        set_register(self.view, '1', forward=False)
        self.view.run_command('left_delete')
        clip_empty_selection_to_line_contents(self.view)

class ViRightDelete(sublime_plugin.TextCommand):
    def run(self, edit, register = '"'):
        set_register(self.view, register, forward=True)
        set_register(self.view, '1', forward=True)
        self.view.run_command('right_delete')
        clip_empty_selection_to_line_contents(self.view)

class ViCopy(sublime_plugin.TextCommand):
    def run(self, edit, register = '"'):
        set_register(self.view, register, forward=True)
        set_register(self.view, '0', forward=True)
        transform_selection_regions(self.view, shrink_to_first_char)

class ViPrefixableCommand(sublime_plugin.TextCommand):
    # Ensure register and repeat are picked up from g_input_state, and that
    # it'll be recorded on the undo stack
    def run_(self, args):
        if not args:
            args = {}

        if g_input_state.register:
            args['register'] = g_input_state.register
            g_input_state.register = None

        if g_input_state.prefix_repeat_digits:
            args['repeat'] = digits_to_number(g_input_state.prefix_repeat_digits)
            g_input_state.prefix_repeat_digits = []

        if 'event' in args:
            del args['event']

        edit = self.view.begin_edit(self.name(), args)
        try:
            return self.run(edit, **args)
        finally:
            self.view.end_edit(edit)

class ViPasteRight(ViPrefixableCommand):
    def advance(self, pt):
        if self.view.substr(pt) == '\n' or pt >= self.view.size():
            return pt
        else:
            return pt + 1

    def run(self, edit, register = '"', repeat = 1):
        visual_mode = self.view.has_non_empty_selection_region()
        if not visual_mode:
            transform_selection(self.view, lambda pt: self.advance(pt))
        self.view.run_command('paste_from_register', {'forward': not visual_mode,
                                                      'repeat': repeat,
                                                      'register': register})

class ViPasteLeft(ViPrefixableCommand):
    def run(self, edit, register = '"', repeat = 1):
        self.view.run_command('paste_from_register', {'forward': False,
                                                      'repeat': repeat,
                                                      'register': register})

def set_register(view, register, forward):
    delta = 1
    if not forward:
        delta = -1

    text = []
    regions = []
    for s in view.sel():
        if s.empty():
            s = sublime.Region(s.a, s.a + delta)
        text.append(view.substr(s))
        regions.append(s)

    text = '\n'.join(text)

    use_sys_clipboard = view.settings().get('vintage_use_clipboard', False) == True

    if (use_sys_clipboard and register == '"') or (register in ('*', '+')):
        sublime.set_clipboard(text)
        # If the system's clipboard is used, Vim always propagates the data to
        # the unnamed register too.
        register = '"'

    if register == '%':
        pass
    else:
        reg = register.lower()
        append = (reg != register)

        if append and reg in g_registers:
            g_registers[reg] += text
        else:
            g_registers[reg] = text

def get_register(view, register):
    use_sys_clipboard = view.settings().get('vintage_use_clipboard', False) == True
    register = register.lower()
    if register == '%':
        if view.file_name():
            return os.path.basename(view.file_name())
        else:
            return None
    elif (use_sys_clipboard and register == '"') or (register in ('*', '+')):
        return sublime.get_clipboard()
    else:
        return g_registers.get(register, None)

def has_register(register):
    if register in ['%', '*', '+']:
        return True
    else:
        return register in g_registers

class PasteFromRegisterCommand(sublime_plugin.TextCommand):
    def run(self, edit, register, repeat = 1, forward = True):
        text = get_register(self.view, register)
        if not text:
            sublime.status_message("Undefined register" + register)
            return
        text = text * int(repeat)

        self.view.run_command('vi_delete')

        regions = [r for r in self.view.sel()]
        new_sel = []

        offset = 0

        for s in regions:
            s = sublime.Region(s.a + offset, s.b + offset)

            if len(text) > 0 and text[-1] == '\n':
                # paste line-wise
                if forward:
                    start = self.view.full_line(s.end()).b
                else:
                    start = self.view.line(s.begin()).a

                num = self.view.insert(edit, start, text)
                new_sel.append(start)
            else:
                # paste character-wise
                num = self.view.insert(edit, s.begin(), text)
                self.view.erase(edit, sublime.Region(s.begin() + num,
                    s.end() + num))
                num -= s.size()
                new_sel.append(s.begin())

            offset += num

        self.view.sel().clear()
        for s in new_sel:
            self.view.sel().add(s)

    def is_enabled(self, register, repeat = 1, forward = True):
        return has_register(register)

class ReplaceCharacter(sublime_plugin.TextCommand):
    def run(self, edit, character):
        new_sel = []
        created_new_line = False
        for s in reversed(self.view.sel()):
            if s.empty():
                self.view.replace(edit, sublime.Region(s.b, s.b + 1), character)
                if character == "\n":
                    created_new_line = True
                    # selection should be in the first column of the newly
                    # created line
                    new_sel.append(sublime.Region(s.b + 1))
                else:
                    new_sel.append(s)
            else:
                # Vim replaces characters with unprintable ones when r<enter> is
                # pressed from visual mode.  Let's not make a replacement in
                # that case.
                if character != '\n':
                    # Process lines contained in the selection individually.
                    # This way we preserve newline characters.
                    lines = self.view.split_by_newlines(s)
                    for line in lines:
                        self.view.replace(edit, line, character * line.size())
                new_sel.append(sublime.Region(s.begin()))

        self.view.sel().clear()
        for s in new_sel:
            self.view.sel().add(s)

        if created_new_line and self.view.settings().get('auto_indent'):
            self.view.run_command('reindent', {'force_indent': False})

class CenterOnCursor(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.show_at_center(self.view.sel()[0])

class ScrollCursorLineToTop(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.set_viewport_position((self.view.viewport_position()[0], self.view.layout_extent()[1]))
        self.view.show(self.view.sel()[0], False)

class ScrollCursorLineToBottom(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.set_viewport_position((self.view.viewport_position()[0], 0.0))
        self.view.show(self.view.sel()[0], False)

class ViScrollLines(ViPrefixableCommand):
    def run(self, edit, forward = True, repeat = None):
        if repeat:
            line_delta = repeat * (1 if forward else -1)
        else:
            viewport_height = self.view.viewport_extent()[1]
            lines_per_page = viewport_height / self.view.line_height()
            line_delta = int(round(lines_per_page / (2 if forward else -2)))
        visual_mode = self.view.has_non_empty_selection_region()

        y_deltas = []
        def transform(pt):
            row = self.view.rowcol(pt)[0]
            new_pt = self.view.text_point(row + line_delta, 0)
            y_deltas.append(self.view.text_to_layout(new_pt)[1]
                            - self.view.text_to_layout(pt)[1])
            return new_pt

        transform_selection(self.view, transform, extend = visual_mode)

        self.view.run_command('vi_move_to_first_non_white_space_character',
                              {'extend': visual_mode})

        # Vim scrolls the viewport as far as it moves the cursor.  With multiple
        # selections the cursors could have moved different distances, due to
        # word wrapping.  Move the viewport by the average of those distances.
        avg_y_delta = sum(y_deltas) / len(y_deltas)
        vp = self.view.viewport_position()
        self.view.set_viewport_position((vp[0], vp[1] + avg_y_delta))


class ViIndent(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('indent')
        transform_selection_regions(self.view, shrink_to_first_char)

class ViUnindent(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('unindent')
        transform_selection_regions(self.view, shrink_to_first_char)

class ViSetBookmark(sublime_plugin.TextCommand):
    def run(self, edit, character):
        sublime.status_message("Set bookmark " + character)
        self.view.add_regions("bookmark_" + character, [s for s in self.view.sel()],
            "", "", sublime.PERSISTENT | sublime.HIDDEN)

class ViSelectBookmark(sublime_plugin.TextCommand):
    def run(self, edit, character, select_bol=False):
        self.view.run_command('select_all_bookmarks', {'name': "bookmark_" + character})
        if select_bol:
            sels = list(self.view.sel())
            self.view.sel().clear()
            for r in sels:
                start = self.view.line(r.a).begin()
                self.view.sel().add(sublime.Region(start, start))

g_macro_target = None

class ViBeginRecordMacro(sublime_plugin.TextCommand):
    def run(self, edit, character):
        global g_macro_target
        g_macro_target = character
        self.view.run_command('start_record_macro')

class ViEndRecordMacro(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('stop_record_macro')
        if not g_macro_target:
            return

        m = sublime.get_macro()
        # TODO: Convert the macro to a string before trying to store it in a
        # register
        g_registers[g_macro_target] = m

class ViReplayMacro(sublime_plugin.TextCommand):
    def run(self, edit, character):
        if not character in g_registers:
            return
        m = g_registers[character]
        global g_input_state

        prefix_repeat_digits, motion_repeat_digits = None, None
        if len(g_input_state.prefix_repeat_digits) > 0:
            prefix_repeat_digits = digits_to_number(g_input_state.prefix_repeat_digits)

        if len(g_input_state.motion_repeat_digits) > 0:
            motion_repeat_digits = digits_to_number(g_input_state.motion_repeat_digits)

        repetitions = 1
        if prefix_repeat_digits:
            repetitions *= prefix_repeat_digits

        if motion_repeat_digits:
            repetitions *= motion_repeat_digits

        for i in range(repetitions):
            for d in m:
                cmd = d['command']
                args = d['args']
                self.view.run_command(cmd, args)

class ShowAsciiInfo(sublime_plugin.TextCommand):
    def run(self, edit):
        c = self.view.substr(self.view.sel()[0].end())
        sublime.status_message("<%s> %d, Hex %s, Octal %s" %
                        (c, ord(c), hex(ord(c))[2:], oct(ord(c))))

class ViReverseSelectionsDirection(sublime_plugin.TextCommand):
    def run(self, edit):
        new_sels = []
        for s in self.view.sel():
            new_sels.append(sublime.Region(s.b, s.a))
        self.view.sel().clear()
        for s in new_sels:
            self.view.sel().add(s)

class MoveGroupFocus(sublime_plugin.WindowCommand):
    def run(self, direction):
        cells = self.window.get_layout()['cells']
        active_group = self.window.active_group()
        x1, y1, x2, y2 = cells[active_group]

        idxs = range(len(cells))
        del idxs[active_group]

        # Matches are any group that shares a border with the active group in the
        # specified direction.
        if direction == "up":
            matches = (i for i in idxs if cells[i][3] == y1 and cells[i][0] < x2 and cells[i][2] > x1)
        elif direction == "down":
            matches = (i for i in idxs if cells[i][1] == y2 and cells[i][0] < x2 and cells[i][2] > x1)
        elif direction == "right":
            matches = (i for i in idxs if cells[i][0] == x2 and cells[i][1] < y2 and cells[i][3] > y1)
        elif direction == "left":
            matches = (i for i in idxs if cells[i][2] == x1 and cells[i][1] < y2 and cells[i][3] > y1)

        # Focus the first group found in the specified direction, if there is one.
        try:
            self.window.focus_group(matches.next())
        except StopIteration:
            return
