#!/usr/bin/env python3
"""
Generate Sublime Text color scheme from pywal colors.

This script reads pywal's generated colors.json and creates a Sublime Text
.sublime-color-scheme file that matches the current terminal color scheme.

Usage:
    Run after pywal completes, typically via `wal -o` hook.
    It automatically writes to the Sublime Text User package directory.
"""

import json
import os
import sys


def make_element(name: str, scope: str, **kwargs) -> dict:
    """Helper function for generating color scheme entries."""
    result = {"name": name, "scope": scope}
    result.update(kwargs)
    return result


def generate_sublime_color_scheme() -> dict:
    """
    Generate a Sublime Text color scheme from pywal colors.

    Reads ~/.cache/wal/colors.json and maps pywal colors to appropriate
    syntax highlighting scopes for a cohesive theme.
    """
    wal_path = os.path.join(os.environ["HOME"], ".cache/wal/colors.json")

    if not os.path.exists(wal_path):
        print(f"Error: {wal_path} not found. Run pywal first.", file=sys.stderr)
        sys.exit(1)

    with open(wal_path, encoding="utf-8") as file:
        wal_scheme = json.load(file)

    # Extract colors from pywal output
    wal_colors = [wal_scheme["colors"][f"color{i}"] for i in range(16)]
    bg = wal_scheme["special"]["background"]
    fg = wal_scheme["special"]["foreground"]
    cursor = wal_scheme["special"]["cursor"]

    # Build the color scheme
    result_scheme = {"name": "PyWal"}

    # Global settings (UI colors)
    global_settings = {
        "background": bg,
        "foreground": fg,
        "caret": cursor,
        "invisibles": wal_colors[2],
        "line_highlight": wal_colors[0] + "40",  # Add alpha transparency
        "selection": wal_colors[6] + "60",  # Semi-transparent selection
        "selection_border": wal_colors[6],
        "active_guide": wal_colors[3] + "50",
        "find_highlight": wal_colors[4] + "60",
        "find_highlight_foreground": fg,
        "highlight": wal_colors[3],
        "popup_css": f"html {{ background-color: {bg}; color: {fg}; }}",
        "phantom_css": f"html {{ background-color: {bg}; color: {fg}; }}",
        "bracket_contents_foreground": wal_colors[3],
        "bracket_contents_options": "underline",
        "brackets_foreground": wal_colors[3],
        "brackets_options": "underline",
        "tags_options": "stippled_underline",
    }

    # Syntax highlighting rules
    rules = [
        # Comments
        make_element("Comment", "comment", foreground=wal_colors[8], font_style="italic"),
        make_element("Comment Line", "comment.line", foreground=wal_colors[8], font_style="italic"),
        make_element("Comment Block", "comment.block", foreground=wal_colors[8], font_style="italic"),
        make_element("Comment Documentation", "comment.documentation", foreground=wal_colors[9]),
        make_element("Comment Block Documentation", "comment.block.documentation", foreground=wal_colors[9]),
        make_element("Comment Punctuation", "punctuation.definition.comment", foreground=wal_colors[8]),
        make_element("Shebang", "comment.line.shebang, constant.language.shebang", foreground=wal_colors[5], font_style="italic"),

        # Python docstrings (scoped as comments in many syntax definitions)
        make_element("Python Docstring", "source.python comment.block.documentation", foreground=wal_colors[11]),
        make_element("Python Docstring Raw", "source.python string.quoted.docstring", foreground=wal_colors[11]),
        make_element("Docstring General", "string.quoted.docstring, string.quoted.double.block, string.quoted.single.block", foreground=wal_colors[11]),

        # Strings
        make_element("String", "string", foreground=wal_colors[10]),
        make_element("String Quoted", "string.quoted", foreground=wal_colors[10]),
        make_element("String Quoted Single", "string.quoted.single", foreground=wal_colors[10]),
        make_element("String Quoted Double", "string.quoted.double", foreground=wal_colors[10]),
        make_element("String Docstring", "string.quoted.docstring", foreground=wal_colors[11]),
        make_element("String Block", "string.quoted.double.block", foreground=wal_colors[11]),
        make_element("String Single Block", "string.quoted.single.block", foreground=wal_colors[11]),
        make_element("String Template", "string.template", foreground=wal_colors[14]),
        make_element("String Interpolated", "string.interpolated", foreground=wal_colors[14]),
        make_element("String Regex", "string.regexp", foreground=wal_colors[5]),
        make_element("String Escape", "constant.character.escape", foreground=wal_colors[5]),
        make_element("String Punctuation", "punctuation.definition.string", foreground=wal_colors[10]),
        make_element("String Interpolation Punctuation", "punctuation.section.interpolation", foreground=wal_colors[5]),

        # Constants and literals
        make_element("Number", "constant.numeric", foreground=wal_colors[13]),
        make_element("Number Suffix", "constant.numeric.suffix", foreground=wal_colors[13], font_style="italic"),
        make_element("Built-in constant", "constant.language", foreground=wal_colors[13], font_style="italic"),
        make_element("Boolean", "constant.language.boolean", foreground=wal_colors[13], font_style="bold italic"),
        make_element("User-defined constant", "variable.other.constant, entity.name.constant, constant.character, constant.other", foreground=wal_colors[13]),
        make_element("Symbol", "constant.other.symbol", foreground=wal_colors[1]),

        # Variables and identifiers
        make_element("Variable", "variable", foreground=fg),
        make_element("Variable Language", "variable.language", foreground=wal_colors[5]),
        make_element("Variable Parameter", "variable.parameter, variable.parameter.function", foreground=wal_colors[12], font_style="italic"),
        make_element("Variable Function", "variable.function", foreground=wal_colors[4]),
        make_element("Variable Member", "variable.other.member", foreground=fg),
        make_element("Variable Other Constant", "variable.other.constant", foreground=wal_colors[13]),
        make_element("Variable Other Alias", "variable.other.alias", foreground=wal_colors[3]),
        make_element("Variable Annotation", "variable.annotation", foreground=wal_colors[6]),

        # Keywords and storage
        # Exclude operator words so they get their own color later
        make_element("Keyword", "keyword - keyword.operator.word", foreground=wal_colors[5], font_style="italic"),
        make_element("Keyword Control", "keyword.control - keyword.control.flow.return", foreground=wal_colors[5], font_style="italic"),
        make_element("Keyword Control Conditional", "keyword.control.conditional", foreground=wal_colors[5], font_style="bold"),
        make_element("Keyword Control Loop", "keyword.control.loop", foreground=wal_colors[5], font_style="bold"),
        make_element("Keyword Control Flow", "keyword.control.flow", foreground=wal_colors[5]),
        make_element("Keyword Control Return", "keyword.control.return", foreground=wal_colors[5], font_style="bold"),
        make_element("Keyword Declaration", "keyword.declaration", foreground=wal_colors[5], font_style="italic"),
        make_element("Keyword Declaration Class", "keyword.declaration.class", foreground=wal_colors[5], font_style="italic"),
        make_element("Keyword Declaration Function", "keyword.declaration.function", foreground=wal_colors[5], font_style="italic"),
        make_element("Keyword Operator", "keyword.operator", foreground=wal_colors[5]),
        make_element("Keyword Operator Assignment", "keyword.operator.assignment", foreground=wal_colors[5]),
        make_element("Keyword Other", "keyword.other", foreground=wal_colors[5]),
        make_element("Keyword Import", "keyword.control.import, keyword.control.import.include", foreground=wal_colors[5], font_style="italic"),

        # Shell keywords
        make_element("Shell Conditional", "keyword.control.shell.conditional, keyword.control.conditional.shell", foreground=wal_colors[5], font_style="bold"),
        make_element("Shell Loop", "keyword.control.shell.loop, keyword.control.loop.shell", foreground=wal_colors[5], font_style="bold"),
        make_element("Shell Keyword", "keyword.other.shell, keyword.control.shell", foreground=wal_colors[5]),
        make_element("Storage", "storage", foreground=wal_colors[5]),
        make_element("Storage Type", "storage.type", foreground=wal_colors[6], font_style="italic"),
        make_element("Storage Modifier", "storage.modifier", foreground=wal_colors[5]),
        make_element("Storage Type Class", "storage.type.class", foreground=wal_colors[6], font_style="italic"),
        make_element("Storage Type Primitive", "storage.type.primitive, support.type.primitive, support.type.builtin", foreground=wal_colors[5]),

        # Classes and functions
        make_element("Entity Name", "entity.name", foreground=wal_colors[3]),
        make_element("Class name", "entity.name.class, meta.toc-list.full-identifier", foreground=wal_colors[3]),
        make_element("Inherited class", "entity.other.inherited-class", foreground=wal_colors[3], font_style="italic"),
        make_element("Function name", "entity.name.function, variable.function", foreground=wal_colors[4], font_style="italic"),
        make_element("Method name", "entity.name.function.member", foreground=wal_colors[4], font_style="italic"),
        make_element("Function Constructor", "entity.name.function.constructor", foreground=wal_colors[4]),
        make_element("Function Destructor", "entity.name.function.destructor", foreground=wal_colors[4]),
        make_element("Function Macro", "entity.name.function.preprocessor, support.macro", foreground=wal_colors[1]),
        make_element("Function Magic", "support.function.magic", foreground=wal_colors[6], font_style="italic"),
        make_element("Function Builtin", "support.function.builtin", foreground=wal_colors[6], font_style="italic"),
        make_element("Entity Name Module", "entity.name.module", foreground=wal_colors[3]),
        make_element("Entity Name Namespace", "entity.name.namespace", foreground=wal_colors[3]),
        make_element("Entity Name Section", "entity.name.section", foreground=wal_colors[5]),
        make_element("Entity Other", "entity.other", foreground=wal_colors[3]),
        make_element("Entity Other Attribute Name", "entity.other.attribute-name", foreground=wal_colors[3]),
        make_element("Entity Other Attribute Name Class", "entity.other.attribute-name.class", foreground=wal_colors[3]),
        make_element("Entity Other Attribute Name Id", "entity.other.attribute-name.id", foreground=wal_colors[3]),
        make_element("Entity Other Attribute Name Pseudo", "entity.other.attribute-name.pseudo-class", foreground=wal_colors[6]),
        make_element("Entity Other Pseudo Element", "entity.other.pseudo-element", foreground=wal_colors[6]),

        # Decorators and annotations
        make_element("Decorator", "entity.name.function.decorator", foreground=wal_colors[6]),
        make_element("Decorator Punctuation", "punctuation.definition.decorator, punctuation.definition.annotation", foreground=wal_colors[6]),
        make_element("Annotation", "storage.type.annotation", foreground=wal_colors[6]),
        make_element("Annotation Attribute", "variable.annotation", foreground=wal_colors[6]),

        # YAML keys
        make_element("YAML Unquoted Key", "source.yaml meta.mapping.key string.unquoted", foreground=wal_colors[4]),
        make_element("YAML Anchor", "variable.other.alias, entity.name.other.anchor", foreground=wal_colors[3]),

        # TOML
        make_element("TOML DateTime", "constant.other.datetime.toml", foreground=wal_colors[5]),
        make_element("TOML Table", "entity.name.table.toml", foreground=wal_colors[3]),

        # CSS
        make_element("CSS Property", "support.type.property-name.css, meta.property-name.css", foreground=wal_colors[4], font_style="italic"),
        make_element("CSS Vendor Prefix", "support.type.vendor-prefix.css", foreground=wal_colors[6], font_style="italic"),
        make_element("CSS Variable", "variable.other.custom-property.css", foreground=wal_colors[12], font_style="italic"),
        make_element("CSS Constant", "support.constant.property-value.css", foreground=fg),
        make_element("CSS Unit", "constant.numeric.suffix.css, keyword.other.unit.css", foreground=wal_colors[5], font_style="italic"),
        make_element("SCSS Tag", "entity.name.tag.css", foreground=wal_colors[6]),
        make_element("SCSS Variable", "variable.other.sass, variable.other.scss", foreground=wal_colors[12]),

        # Tags and attributes (HTML/XML)
        make_element("Tag name", "entity.name.tag", foreground=wal_colors[5]),
        make_element("Tag attribute", "entity.other.attribute-name", foreground=wal_colors[3]),
        make_element("Tag Punctuation", "punctuation.definition.tag", foreground=wal_colors[5]),
        make_element("Tag Inline Source", "source.js.embedded.html", foreground=fg),

        # Support (library functions/types)
        make_element("Library function", "support.function", foreground=wal_colors[4], font_style="italic"),
        make_element("Library constant", "support.constant", foreground=wal_colors[6]),
        make_element("Library class/type", "support.class, support.type, entity.name.type, entity.name.struct, entity.name.trait", foreground=wal_colors[6], font_style="italic"),
        make_element("Library variable", "support.other.variable", foreground=fg),
        make_element("Support Type Exception", "support.type.exception", foreground=wal_colors[6], font_style="italic"),

        # Markup - Headings (h1-h6 with different colors)
        make_element("Markup Heading", "markup.heading", foreground=wal_colors[5], font_style="bold"),
        make_element("Markup Heading 1", "markup.heading.1", foreground=wal_colors[1]),
        make_element("Markup Heading 2", "markup.heading.2", foreground=wal_colors[2]),
        make_element("Markup Heading 3", "markup.heading.3", foreground=wal_colors[3]),
        make_element("Markup Heading 4", "markup.heading.4", foreground=wal_colors[4]),
        make_element("Markup Heading 5", "markup.heading.5", foreground=wal_colors[5]),
        make_element("Markup Heading 6", "markup.heading.6", foreground=wal_colors[6]),
        make_element("Markup Link", "markup.underline.link", foreground=wal_colors[4], font_style="italic underline"),
        make_element("Markdown Link Description", "meta.link.inline.description, meta.image.inline.description", foreground=wal_colors[4]),
        make_element("Markdown Code Fence", "markup.raw.code-fence", foreground=fg),
        make_element("Markdown Inline Code", "markup.raw.inline", foreground=wal_colors[10]),
        make_element("Markdown Code Language", "meta.code-fence.definition, constant.other.language-name.markdown", foreground=wal_colors[6], font_style="italic"),
        make_element("Markup Bold", "markup.bold", font_style="bold"),
        make_element("Markup Italic", "markup.italic", font_style="italic"),
        make_element("Markup Quote", "markup.quote", foreground=wal_colors[7]),
        make_element("Markup List", "markup.list", foreground=wal_colors[3]),
        make_element("Markup Raw", "markup.raw", foreground=wal_colors[10]),

        # Javadoc/JSDoc documentation tags
        make_element("Documentation Tag", "entity.name.tag.documentation, entity.other.attribute-name.documentation", foreground=wal_colors[5]),

        # Diff
        make_element("Diff Header", "meta.diff, meta.diff.header", foreground=wal_colors[8]),
        make_element("Diff Added", "markup.inserted", foreground=wal_colors[2]),
        make_element("Diff Deleted", "markup.deleted", foreground=wal_colors[1]),
        make_element("Diff Changed", "markup.changed", foreground=wal_colors[3]),

        # Messages
        make_element("Message Error", "message.error", foreground=wal_colors[1]),

        # Shell-specific - builtins should be different from keywords
        make_element("Shell Builtin", "meta.function-call.identifier.shell support.function, support.function.builtin.shell", foreground=wal_colors[4]),  # Blue - function color
        make_element("Shell Parameter", "variable.language.shell", foreground=wal_colors[1], font_style="italic"),
        make_element("Shell Command", "meta.function-call.shell, meta.command.shell", foreground=wal_colors[4]),

        # Invalid/error states
        make_element("Invalid", "invalid", foreground=fg, background=wal_colors[1] + "40"),
        make_element("Invalid deprecated", "invalid.deprecated", foreground=bg, background=wal_colors[13]),

        # Source and text
        make_element("Source", "source", foreground=fg),
        make_element("Text", "text", foreground=fg),
        make_element("Text Plain", "text.plain", foreground=fg),

        # Operators and punctuation
        make_element("Operator Symbol", "keyword.operator - keyword.operator.word", foreground=wal_colors[5]),
        # Word-based operators (and, or, not, in, is) - distinct from keywords
        make_element("Operator Word", "keyword.operator.word", foreground=wal_colors[6]),
        make_element("Operator Word Python", "keyword.operator.word.python, keyword.operator.logical.python", foreground=wal_colors[6]),
        make_element("Shell Operator", "keyword.operator.logical.shell, keyword.operator.negation.shell, keyword.operator.test.shell", foreground=wal_colors[6]),
        make_element("Punctuation", "punctuation", foreground=wal_colors[8]),
        make_element("Punctuation Definition", "punctuation.definition", foreground=fg),
        make_element("Punctuation Definition Tag", "punctuation.definition.tag", foreground=wal_colors[5]),
        make_element("Punctuation Definition Tag Begin", "punctuation.definition.tag.begin", foreground=wal_colors[5]),
        make_element("Punctuation Definition Tag End", "punctuation.definition.tag.end", foreground=wal_colors[5]),
        make_element("Punctuation Definition Keyword", "punctuation.definition.keyword", foreground=wal_colors[5]),
        make_element("Punctuation Separator", "punctuation.separator", foreground=wal_colors[8]),
        make_element("Punctuation Separator Continuation", "punctuation.separator.continuation", foreground=wal_colors[8]),
        make_element("Punctuation Section", "punctuation.section", foreground=wal_colors[8]),
        make_element("Punctuation Section Group", "punctuation.section.group", foreground=wal_colors[8]),
        make_element("Punctuation Section Block", "punctuation.section.block", foreground=wal_colors[8]),
        make_element("Punctuation Section Brackets", "punctuation.section.brackets", foreground=wal_colors[8]),
        make_element("Punctuation Section Braces", "punctuation.section.braces", foreground=wal_colors[8]),
        make_element("Punctuation Section Parens", "punctuation.section.parens", foreground=wal_colors[8]),
        make_element("Punctuation Terminator", "punctuation.terminator", foreground=wal_colors[8]),
        make_element("Punctuation Accessor", "punctuation.accessor", foreground=wal_colors[8]),

        # JSON keys (blue) and values (green) - distinct colors for readability
        make_element("JSON Key", "source.json meta.mapping.key.json string.quoted.double.json", foreground=wal_colors[4]),
        make_element("JSON Key Quotes", "source.json meta.mapping.key.json punctuation.definition.string", foreground=wal_colors[4]),
        make_element("JSON Value", "source.json meta.string.json string.quoted.double.json", foreground=wal_colors[10]),
    ]

    result_scheme["globals"] = global_settings
    result_scheme["rules"] = rules

    return result_scheme


def main():
    """Generate and write the Sublime Text color scheme."""
    scheme = generate_sublime_color_scheme()

    # Determine Sublime Text config path (ST3 vs ST4)
    home = os.environ["HOME"]
    st3_path = os.path.join(home, ".config/sublime-text-3/Packages/User")
    st4_path = os.path.join(home, ".config/sublime-text/Packages/User")

    # Use ST4 path if it exists or ST3 doesn't exist, otherwise ST3
    if os.path.exists(st4_path):
        sublime_user_path = st4_path
    elif os.path.exists(st3_path):
        sublime_user_path = st3_path
    else:
        # Default to ST4 path (newer installations)
        sublime_user_path = st4_path
        # Create directory if needed
        os.makedirs(sublime_user_path, exist_ok=True)

    theme_path = os.path.join(sublime_user_path, "PyWal.sublime-color-scheme")

    with open(theme_path, "w", encoding="utf-8") as file:
        json.dump(scheme, file, indent=4)

    print(f"Generated Sublime Text color scheme: {theme_path}")


if __name__ == "__main__":
    main()
