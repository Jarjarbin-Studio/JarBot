import asyncio
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import discord
import jardiscordengine as JDE

from jarbot_modulable.constants import REQUEST_TIMEOUT, MAX_WORKERS, MANKIER_WEB_URL, PAGE_LIMIT
from jarbot_modulable.services.generic import log_info


_MONTHS = (
    "January|February|March|April|May|June|"
    "July|August|September|October|November|December"
)

# Footer ManKier appends to every section ("November 2026 GNU coreutils 9.12"
# followed by a link back to the section).
_FOOTER_DATE_RE = re.compile(
    rf"^(?:(?:{_MONTHS})\s+\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}})\b.*$"
)
_FOOTER_URL_RE = re.compile(r"^<?https?://(?:www\.)?mankier\.com/\S*>?$")

# Pandoc-style definition list entry (": definition").
_DEFINITION_RE = re.compile(r"^\s*:\s+(.*)$")

# Exactly two backticks: ManKier leaks these around highlighted arguments.
_DOUBLE_BACKTICK_RE = re.compile(r"(?<!`)``(?!`)")


class ManKierError(Exception):
    pass


class ManKierNotFound(ManKierError):
    pass


# --------------------------------------------------------------------------- #
# Discord view
# --------------------------------------------------------------------------- #


class ManPaginationView(discord.ui.View):

    def __init__(
            self,
            pages: list[str],
            owner_id: int,
            timeout: float = 300,
        ) -> None:
        super().__init__(timeout=timeout)

        self.pages = pages
        self.owner_id = owner_id
        self.current_page = 0
        self.message: discord.Message | None = None

        self._update_buttons()

    def get_content(self) -> str:
        return (
            f"{self.pages[self.current_page]}\n\n"
            f"-# Page {self.current_page + 1}/{len(self.pages)}"
        )

    def _update_buttons(self) -> None:
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue

            if item.custom_id == "mankier:previous":
                item.disabled = self.current_page <= 0

            elif item.custom_id == "mankier:next":
                item.disabled = self.current_page >= len(self.pages) - 1

    async def _show_page(
            self,
            interaction: discord.Interaction,
            offset: int,
        ) -> None:
        self.current_page += offset
        self._update_buttons()

        await interaction.response.edit_message(
            content=self.get_content(),
            view=self,
        )

    async def interaction_check(
            self,
            interaction: discord.Interaction,
        ) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "These manual controls do not belong to you.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.secondary,
        custom_id="mankier:previous",
    )
    async def previous_page(
            self,
            button: discord.ui.Button,
            interaction: discord.Interaction,
        ) -> None:
        await self._show_page(interaction, -1)

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.primary,
        custom_id="mankier:next",
    )
    async def next_page(
            self,
            button: discord.ui.Button,
            interaction: discord.Interaction,
        ) -> None:
        await self._show_page(interaction, 1)

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #


def _get_api_url() -> str:
    api_url = JDE.Systems.JDEEnv("MANKIER_API_URL")

    if not api_url:
        raise ManKierError("MANKIER_API_URL is not configured.")

    return api_url.rstrip("/")


def _request(
        url: str,
        accept: str = "application/json",
    ) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "JarBotModulable/1.0",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            return response.read().decode("utf-8")

    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ManKierNotFound(
                "No matching manual or section was found."
            ) from error

        raise ManKierError(
            f"HTTP {error.code}: {error.reason}"
        ) from error

    except urllib.error.URLError as error:
        raise ManKierError(
            f"Unable to reach ManKier: {error.reason}"
        ) from error

    except TimeoutError as error:
        raise ManKierError("ManKier request timed out.") from error

    except UnicodeDecodeError as error:
        raise ManKierError(
            "ManKier returned an invalid UTF-8 response."
        ) from error


def _request_json(url: str) -> dict:
    try:
        data = json.loads(_request(url))

    except json.JSONDecodeError as error:
        raise ManKierError(
            "ManKier returned an invalid JSON response."
        ) from error

    if not isinstance(data, dict):
        raise ManKierError("Unexpected response from ManKier.")

    return data


def _search_mans(query: str) -> dict:
    encoded_query = urllib.parse.urlencode({"q": query})

    log_info("ManKier", f"Searching manuals: {query}")

    return _request_json(f"{_get_api_url()}/v3/mans/?{encoded_query}")


def _get_man_page(name: str, section: str) -> dict:
    manual = f"{name}.{section}"
    encoded_manual = urllib.parse.quote(manual, safe=".")

    log_info("ManKier", f"Retrieving manual: {manual}")

    return _request_json(f"{_get_api_url()}/v3/mans/{encoded_manual}")


def _get_man_section(name: str, section: str, section_id: str) -> str:
    manual = f"{name}.{section}"
    encoded_manual = urllib.parse.quote(manual, safe=".")
    encoded_section = urllib.parse.quote(section_id, safe="")

    log_info("ManKier", f"Retrieving section: {manual}/{section_id}")

    return _request(
        f"{_get_api_url()}/v3/mans/{encoded_manual}"
        f"/sections/{encoded_section}",
        accept="text/markdown",
    )


def _fetch_sections(
        name: str,
        section: str,
        sections: list,
    ) -> list[tuple[str, str]]:
    """Download every section concurrently, keeping the original order."""
    targets = []

    for manual_section in sections:
        if not isinstance(manual_section, dict):
            continue

        section_id = manual_section.get("id")

        if section_id:
            targets.append((
                manual_section.get("title") or "Unknown section",
                section_id,
            ))

    def fetch(target: tuple[str, str]) -> tuple[str, str]:
        title, section_id = target

        try:
            return title, _get_man_section(name, section, section_id)
        except ManKierNotFound:
            return title, ""

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        return list(pool.map(fetch, targets))


# --------------------------------------------------------------------------- #
# Markdown helpers
# --------------------------------------------------------------------------- #


def _inline_code(text: str) -> str:
    text = text.strip()

    if "`" in text:
        return f"`` {text} ``"

    return f"`{text}`"


def _strip_heading(lines: list[str], title: str) -> list[str]:
    """Drop the heading(s) ManKier repeats at the top of each section."""
    lines = list(lines)

    def skip_blanks() -> None:
        while lines and not lines[0].strip():
            lines.pop(0)

    skip_blanks()

    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
        skip_blanks()

    if lines and lines[0].strip().lower() == title.strip().lower():
        lines.pop(0)
        skip_blanks()

    return lines


def _strip_footer(lines: list[str]) -> list[str]:
    """Remove the trailing date / back-link ManKier adds to each section."""
    lines = list(lines)

    while lines:
        last = lines[-1].strip()

        if (
            not last
            or _FOOTER_URL_RE.match(last)
            or _FOOTER_DATE_RE.match(last)
        ):
            lines.pop()
            continue

        break

    return lines


def _strip_backticks(lines: list[str], everything: bool) -> list[str]:
    """Remove stray backticks outside code fences."""
    result = []
    in_fence = False

    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            result.append(line)
            continue

        if in_fence:
            result.append(line)
            continue

        if everything:
            line = line.replace("`", "")
        else:
            line = _DOUBLE_BACKTICK_RE.sub("", line)

        result.append(line)

    return result


def _format_tldr_lines(lines: list[str], command: str) -> list[str]:
    """Turn 'Label: command ...' lines into bullets with a code span."""
    pattern = re.compile(
        rf"^(?P<label>.+?):\s*(?P<command>{re.escape(command)}\b.*)$"
    )

    result = []

    for line in lines:
        line = re.sub(r"^[-*•]\s+", "", line.strip())

        if not line:
            result.append("")
            continue

        match = pattern.match(line)

        if match:
            result.append(
                f"- {match['label'].strip()}: "
                f"{_inline_code(match['command'])}"
            )
        else:
            result.append(line)

    return result


def _synopsis_block(lines: list[str]) -> str:
    """Render the synopsis as a code block, like the original man page."""
    cleaned = []

    for line in lines:
        line = re.sub(r"\\$", "", line.rstrip())
        line = re.sub(r"\\([\[\]*_`<>#|\\])", r"\1", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", line)

        if line.strip() or (cleaned and cleaned[-1]):
            cleaned.append(line)

    body = "\n".join(cleaned).strip()

    return f"```\n{body}\n```" if body else ""


def _read_definition(lines: list[str], start: int) -> tuple[str, int]:
    """Read one or more ': definition' entries and their continuations."""
    parts = []
    index = start
    total = len(lines)

    while index < total:
        line = lines[index]
        match = _DEFINITION_RE.match(line)

        if match:
            parts.append(match.group(1).strip())
            index += 1
            continue

        if line.startswith("    "):
            parts.append(line.strip())
            index += 1
            continue

        if not line.strip():
            peek = index + 1

            while peek < total and not lines[peek].strip():
                peek += 1

            if peek < total and (
                _DEFINITION_RE.match(lines[peek])
                or lines[peek].startswith("    ")
            ):
                index = peek
                continue

        break

    return "\n  ".join(part for part in parts if part), index


def _tighten_bullets(lines: list[str]) -> list[str]:
    """Remove blank lines sitting between two bullets."""
    result = []

    for index, line in enumerate(lines):
        if not line.strip() and result and index + 1 < len(lines):
            previous = result[-1]
            following = lines[index + 1]

            if previous.startswith(("- ", "  ")) and following.startswith("- "):
                continue

        result.append(line)

    return result


def _format_blocks(lines: list[str]) -> list[str]:
    """Convert definition lists and indented blocks to Discord markdown."""
    output: list[str] = []
    total = len(lines)
    index = 0

    while index < total:
        line = lines[index]

        if not line.strip():
            if output and output[-1] != "":
                output.append("")
            index += 1
            continue

        # Existing fenced block: copy untouched.
        if line.lstrip().startswith("```"):
            output.append(line)
            index += 1

            while index < total:
                output.append(lines[index])
                closing = lines[index].lstrip().startswith("```")
                index += 1

                if closing:
                    break

            continue

        # Definition list: "term" / ": definition".
        if not _DEFINITION_RE.match(line) and not line.startswith("- "):
            lookahead = index + 1

            while lookahead < total and not lines[lookahead].strip():
                lookahead += 1

            if lookahead < total and _DEFINITION_RE.match(lines[lookahead]):
                definition, index = _read_definition(lines, lookahead)
                output.append(f"- {_inline_code(line)}: {definition}")
                continue

        # Indented block -> fenced code block.
        if line.startswith("    "):
            block = []

            while index < total:
                current = lines[index]

                if current.startswith("    "):
                    block.append(current[4:])
                    index += 1
                    continue

                if not current.strip():
                    peek = index + 1

                    while peek < total and not lines[peek].strip():
                        peek += 1

                    if peek < total and lines[peek].startswith("    "):
                        block.append("")
                        index += 1
                        continue

                break

            output.extend(["```", *block, "```"])
            continue

        output.append(line.rstrip())
        index += 1

    return _tighten_bullets(output)


def _normalize_links(text: str) -> str:
    """Make links absolute and suppress Discord embeds."""
    text = re.sub(
        r"\]\((/[^)\s]*)\)",
        rf"](<{MANKIER_WEB_URL}\1>)",
        text,
    )

    return re.sub(
        r"\]\((?!<)(https?://[^)\s]+)\)",
        r"](<\1>)",
        text,
    )


def _prepare_section(raw: str, title: str, command: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"</?div[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\\(?=https?://)", "", text)

    lines = [line.rstrip() for line in text.split("\n")]
    lines = _strip_heading(lines, title)
    lines = _strip_footer(lines)

    if not lines:
        return ""

    normalized_title = title.strip().lower()

    if normalized_title == "synopsis":
        return _synopsis_block(lines)

    is_tldr = "tl;dr" in normalized_title
    lines = _strip_backticks(lines, everything=is_tldr)

    if is_tldr:
        lines = _tighten_bullets(_format_tldr_lines(lines, command))

    lines = _format_blocks(lines)

    return _normalize_links("\n".join(lines).strip())


# --------------------------------------------------------------------------- #
# Message splitting
# --------------------------------------------------------------------------- #


def _split_blocks(content: str) -> list[str]:
    """Split on blank lines, never inside a code fence."""
    blocks = []
    current: list[str] = []
    in_fence = False

    for line in content.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence

        if not line.strip() and not in_fence:
            if current:
                blocks.append("\n".join(current))
                current = []
            continue

        current.append(line)

    if current:
        blocks.append("\n".join(current))

    return blocks


def _split_oversized_block(block: str, limit: int) -> list[str]:
    """Split a block longer than the limit, keeping code fences balanced."""
    fence = "```"
    max_line = limit - 2 * len(fence) - 4

    parts = []
    current: list[str] = []
    size = 0
    in_fence = False

    for raw_line in block.split("\n"):
        pieces = [
            raw_line[i:i + max_line]
            for i in range(0, len(raw_line), max_line)
        ] or [""]

        for line in pieces:
            is_fence = line.lstrip().startswith(fence)

            if (
                current
                and size + len(line) + 1 > limit - len(fence) - 1
                and not (in_fence and is_fence)
            ):
                if in_fence:
                    current.append(fence)

                parts.append("\n".join(current))

                current = [fence] if in_fence else []
                size = len(fence) + 1 if in_fence else 0

            current.append(line)
            size += len(line) + 1

            if is_fence:
                in_fence = not in_fence

    if current:
        parts.append("\n".join(current))

    return parts


def _split_message(content: str, limit: int = PAGE_LIMIT) -> list[str]:
    pages = []
    current = ""

    for block in _split_blocks(content):
        if len(block) > limit:
            if current:
                pages.append(current)
                current = ""

            pages.extend(_split_oversized_block(block, limit))
            continue

        candidate = f"{current}\n\n{block}" if current else block

        if len(candidate) <= limit:
            current = candidate
        else:
            pages.append(current)
            current = block

    if current:
        pages.append(current)

    return pages


# --------------------------------------------------------------------------- #
# Response builders
# --------------------------------------------------------------------------- #


def _format_manual(
        name: str,
        section: str,
        description: str = "",
    ) -> list[str]:
    data = _get_man_page(name, section)

    if not data:
        raise ManKierNotFound(
            f"No content was found for `{name}({section})`."
        )

    name = data.get("name", name)
    section = data.get("section", section)
    description = data.get("description", description)
    manual_url = data.get("url", f"{MANKIER_WEB_URL}/{section}/{name}")

    sections = data.get("sections", [])

    if not isinstance(sections, list) or not sections:
        raise ManKierNotFound(
            f"No sections were found for `{name}({section})`."
        )

    header = [f"# `{name}({section})`"]

    if description:
        header.append(f"**{description}**")

    header.append(f"[Open complete manual](<{manual_url}>)")

    parts = ["\n".join(header)]

    for title, raw in _fetch_sections(name, section, sections):
        content = _prepare_section(raw, title, name)

        if content:
            parts.append(f"## {title}\n{content}")

    if len(parts) == 1:
        raise ManKierNotFound(
            f"No section content was available for `{name}({section})`."
        )

    parts.append("-# Source: ManKier API")

    return _split_message("\n\n".join(parts))


def _format_search_results(query: str, data: dict) -> list[str]:
    results = data.get("results", [])

    if not isinstance(results, list) or not results:
        return [
            f"**No manual entries found for `{query}`.**\n"
            "Check the spelling or try another search term.\n"
            f"[Search directly on ManKier](<{MANKIER_WEB_URL}/>)"
        ]

    if len(results) == 1:
        name = results[0].get("name")
        section = results[0].get("section")

        if name and section:
            try:
                return _format_manual(
                    name,
                    section,
                    results[0].get("description", ""),
                )
            except ManKierNotFound:
                pass

    lines = [f"**Search results for `{query}`** ({len(results)} entries)", ""]

    for index, result in enumerate(results, start=1):
        name = result.get("name", "Unknown")
        section = result.get("section", "?")
        description = result.get("description", "No description available.")
        url = result.get("url", f"{MANKIER_WEB_URL}/{section}/{name}")
        alias = " · Alias" if result.get("is_alias") else ""

        lines.append(f"**{index}. [{name}({section})](<{url}>)**{alias}")
        lines.append(f"↳ {description}")
        lines.append("")

    lines.append("-# Source: ManKier API")

    if data.get("truncated", False):
        lines.append(
            "*Results truncated by ManKier. "
            "Try a more specific search term.*"
        )

    return _split_message("\n".join(lines))


def _get_man_response(query: str) -> list[str]:
    query = query.strip()

    if not query:
        return ["Please provide a manual name or search term."]

    match = re.fullmatch(
        r"([a-zA-Z0-9_.+-]+)\.([0-9][a-zA-Z]*)",
        query,
    )

    if match:
        name, section = match.groups()

        try:
            return _format_manual(name, section)
        except ManKierNotFound:
            # Not a "name.section" pair after all (e.g. "python3.11"):
            # fall back to a regular search.
            pass

    return _format_search_results(query, _search_mans(query))


async def get_man_response(query: str) -> list[str]:
    return await asyncio.to_thread(_get_man_response, query)


async def send_man_response(
        interaction: discord.Interaction,
        pages: list[str],
        ephemeral: bool = False,
    ) -> None:
    if not pages:
        pages = ["No manual content was returned."]

    view = ManPaginationView(
        pages=pages,
        owner_id=interaction.user.id,
    )

    content = view.get_content()

    if interaction.response.is_done():
        view.message = await interaction.followup.send(
            content,
            view=view,
            ephemeral=ephemeral,
            wait=True,
        )
        return

    await interaction.response.send_message(
        content,
        view=view,
        ephemeral=ephemeral,
    )

    view.message = await interaction.original_response()
