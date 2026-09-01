#!/usr/bin/env python3
# This file is part of Eisenberg Family Depression Center Open Source Hub (DepressionCenter.github.io repository).
# resources.py - The Center's public resources, grouped into categories for display.
# Author(s): Gabriel Mongefranco.
# Created: 2026-09-01
# Last Modified: 2026-09-01
# Summary: One list of the Eisenberg Family Depression Center's public resources, rendered by
#          build_site.py into both llms.txt and the Related Resources section of the landing
#          page, so the two can never disagree.
# Notes: See README file for documentation and full license information.
# Website: https://code.depressioncenter.org/
#
# Copyright (c) 2026 The Regents of the University of Michigan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.
"""The Center's public resources, and the categories they are shown under.

To add a resource, append an entry to RESOURCE_LIBRARY in any position: each category is
sorted by name when rendered. Its "category" must match one named in RESOURCE_CATEGORIES.

Every entry carries two lengths of text on purpose:

- "summary" is one line. It appears on the landing page, where brevity helps a reader scan.
- "description" is fuller. It appears in llms.txt, where an agent benefits from the context.

Neither is hidden behind a hover. The page shows its summary at all times, because content
revealed only on hover cannot be reached by touch or keyboard users and would fail the
project's accessibility standard.
"""

### Category Icons ###

# Path data from Bootstrap Icons (https://icons.getbootstrap.com/), MIT licensed. Only the
# paths are stored; build_site.py writes the surrounding <svg> element. Each icon is marked
# decorative and hidden from assistive technology, because the category name printed beside it
# already carries the meaning. An icon is never the only signal of anything.
CATEGORY_ICON_PATHS = {
    "building": (
        '<path d="M4 2.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5zm3 0a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5zm3.5-.5a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5zM4 5.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5zM7.5 5a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5zm2.5.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5zM4.5 8a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5zm2.5.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5zm3.5-.5a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5z"/>'
        '<path d="M2 1a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1zm11 0H3v14h3v-2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V15h3z"/>'
    ),
    "code-slash": (
        '<path d="M10.478 1.647a.5.5 0 1 0-.956-.294l-4 13a.5.5 0 0 0 .956.294zM4.854 4.146a.5.5 0 0 1 0 .708L1.707 8l3.147 3.146a.5.5 0 0 1-.708.708l-3.5-3.5a.5.5 0 0 1 0-.708l3.5-3.5a.5.5 0 0 1 .708 0m6.292 0a.5.5 0 0 0 0 .708L14.293 8l-3.147 3.146a.5.5 0 0 0 .708.708l3.5-3.5a.5.5 0 0 0 0-.708l-3.5-3.5a.5.5 0 0 0-.708 0"/>'
    ),
    "journal-text": (
        '<path d="M5 10.5a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5m0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5m0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5m0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5"/>'
        '<path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2v-1h1v1a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v1H1V2a2 2 0 0 1 2-2"/>'
        '<path d="M1 5v-.5a.5.5 0 0 1 1 0V5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1zm0 3v-.5a.5.5 0 0 1 1 0V8h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1zm0 3v-.5a.5.5 0 0 1 1 0v.5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1z"/>'
    ),
    "mortarboard": (
        '<path d="M8.211 2.047a.5.5 0 0 0-.422 0l-7.5 3.5a.5.5 0 0 0 .025.917l7.5 3a.5.5 0 0 0 .372 0L14 7.14V13a1 1 0 0 0-1 1v2h3v-2a1 1 0 0 0-1-1V6.739l.686-.275a.5.5 0 0 0 .025-.917zM8 8.46 1.758 5.965 8 3.052l6.242 2.913z"/>'
        '<path d="M4.176 9.032a.5.5 0 0 0-.656.327l-.5 1.7a.5.5 0 0 0 .294.605l4.5 1.8a.5.5 0 0 0 .372 0l4.5-1.8a.5.5 0 0 0 .294-.605l-.5-1.7a.5.5 0 0 0-.656-.327L8 10.466zm-.068 1.873.22-.748 3.496 1.311a.5.5 0 0 0 .352 0l3.496-1.311.22.748L8 12.46z"/>'
    ),
}

### Categories ###

# Shown in this order on the landing page. Each pairs a heading with one of the icons above.
RESOURCE_CATEGORIES = (
    ("About the Center", "building"),
    ("Documentation and code", "code-slash"),
    ("Research and publications", "journal-text"),
    ("Outreach and Education", "mortarboard"),
)

### Resources ###

RESOURCE_LIBRARY = (
    {
        "name": "Campus Mind Works",
        "url": "https://campusmindworks.org/",
        "category": "Outreach and Education",
        "summary": "Mental health and academic support for U-M students.",
        "description": "Mental health and academic support for University of Michigan students "
        "managing a mental health condition, plus guidance on staying well through college "
        "life.",
    },
    {
        "name": "Depression Center Toolkit",
        "url": "https://depressioncenter.org/outreach-education/depression-center-toolkit",
        "category": "Outreach and Education",
        "summary": "Self-assessments, practical tools, and strategies for managing symptoms.",
        "description": "An online resource guiding individuals and families through their "
        "mental health journey. Brings together trusted information, self-assessments, "
        "practical tools, and evidence-based strategies for understanding mental health "
        "disorders, exploring treatment options, and managing symptoms.",
    },
    {
        "name": "Eisenberg Family Depression Center Open Source Hub",
        "url": "https://code.depressioncenter.org/",
        "category": "Documentation and code",
        "summary": "This site. Research code, automations, and reusable workflows.",
        "description": "This site. Open source tools, automations, and research workflows "
        "built to accelerate mental health discoveries while remaining reusable across any "
        "research discipline. The repositories themselves are at "
        "[github.com/DepressionCenter](https://github.com/depressioncenter?view_as=public).",
    },
    {
        "name": "Eisenberg Family Depression Center Website",
        "url": "https://depressioncenter.org/",
        "category": "About the Center",
        "summary": "Research programs, services, staff, events, and news.",
        "description": "The Center itself: research programs, services, staff, events, and "
        "news.",
    },
    {
        "name": "Eisenberg Family Depression Center YouTube Channel",
        "url": "https://www.youtube.com/@DepressionCenter",
        "category": "About the Center",
        "summary": "Recorded talks, demonstrations, symposia, and training.",
        "description": "Recorded talks, demonstrations, symposia, and training sessions.",
    },
    {
        "name": "Peer-to-Peer Depression Awareness Program Resource Center",
        "url": "https://p2p.depressioncenter.org/",
        "category": "Outreach and Education",
        "summary": "Training and campaign materials for schools running the P2P program.",
        "description": "Resources, training materials, tools, and campaign examples for "
        "partners, schools, students, and educators launching the Peer-to-Peer program at "
        "their own school.",
    },
    {
        "name": "U-M Health Research Resource Library",
        "url": "https://teamdynamix.umich.edu/TDClient/210/DepressionCenter/Home/",
        "category": "Documentation and code",
        "summary": "Articles, tutorials, and code documentation for health research.",
        "description": "Articles, best practices, tutorials, code documentation, and "
        "discussions that foster collaboration and accelerate health research. Maintained by "
        "the Center, and the canonical documentation for most projects listed below. Short "
        "link: [michmed.org/efdc-kb](https://michmed.org/efdc-kb).",
    },
    {
        "name": "U-M Library Deep Blue Documents Collection: Eisenberg Family Depression Center",
        "url": "https://hdl.handle.net/2027.42/195355",
        "category": "Research and publications",
        "summary": "Articles, guides, and digital media in the U-M Library repository.",
        "description": "Articles, guides, and digital media from researchers and technical "
        "experts at the Center, members of the Mobile Technologies Research Innovation "
        "Collaborative (MeTRIC), and other University of Michigan partners.",
    },
    {
        "name": "U-M Library Deep Blue Documents Collection: MeTRIC (Mobile Technologies "
        "Research Innovation Collaborative)",
        "url": "https://hdl.handle.net/2027.42/195645",
        "category": "Research and publications",
        "summary": "Symposium posters and scholarly works from the mobile technologies "
        "community.",
        "description": "MeTRIC Symposium posters and other scholarly works from the University "
        "of Michigan mobile technologies community.",
    },
)
