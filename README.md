![Depression Center Logo](images/EFDCLogo_375w.png "depressioncenter.org")

# Eisenberg Family Depression Center: Open Source Projects

## About
This repository contains the code for the landing webpage for the Eisenberg Family Depression Center's code repository: [https://code.depressioncenter.org](https://code.depressioncenter.org).

A nightly GitHub Action reads all our public repos through the GitHub API, including custom properties such as lab name and URL, documentation URL, and whether a repo is featured. It writes finished HTML into this repository, so search engines and visitors without JavaScript see every repository description and README. Each repo also gets its own page under `/repos/`. When users click a tile, a side panel opens with the same content, loaded from a file built ahead of time.

## Quick Start Guide
+ **index.html is generated. Do not edit it.** Edit `templates/index.html`, `templates/repo.html`, `styles/site.css`, or `scripts/site.js` instead, then run the build.
+ To build the site yourself: `pip install -r requirements.txt`, then `python scripts/build_site.py`. No GitHub account or token is needed. See [how to run the build locally](docs/how-to/run-the-build-locally.md).
+ To re-use this for your own organization, [fork](https://github.com/DepressionCenter/DepressionCenter.github.io/fork) the repo and change `ORG` and `SITE_BASE_URL` at the top of `scripts/build_site.py`. Keep the ".nojekyll" file.
+ Preview images can live in the repo they describe, as `images/Repo-preview.png` (912x513) and `images/Repo-preview-thumb.png` (360x202). If a repo has none, add them here under `/images/repo-previews/`, named to match the repo exactly, including capital letters. Both must be 16:9. See [how to add a repository preview image](docs/how-to/add-a-repo-preview-image.md).
+ Please remove the copyright notice in the code, especially if you are not affiliated with University of Michigan. However, the license notice at the top of the file (in HTML comments) must remain there, as the code is licensed under the GPLv3.0 or later license.

## Where are the repos located?
Please see our GitHub site at:  [https://github.com/DepressionCenter](https://github.com/DepressionCenter)



## Documentation
Please see our Knowledge Base at:  [https://michmed.org/efdc-kb](https://michmed.org/efdc-kb)

Technical documentation lives in [/docs](docs/README.md): [architecture](docs/architecture.md), [data flow](docs/data-flow.md), [how-to guides](docs/how-to/run-the-build-locally.md), [troubleshooting](docs/troubleshooting.md), and [compliance](docs/compliance.md).



## Additional Resources
+ [Eisenberg Family Depression Center](https://depressioncenter.org)
+ [Michigan Medicine](https://michiganmedicine.org)
+ [University of Michigan](https://umich.edu)



## Credits

#### Contributors:
+ Eisenberg Family Depression Center [(@DepressionCenter)](https://github.com/DepressionCenter/)
+ Gabriel Mongefranco [(@gabrielmongefranco)](https://github.com/gabrielmongefranco)

#### This work is based in part on the following projects, libraries and/or studies:
+ [GitHub REST API](https://docs.github.com/rest/about-the-rest-api/about-the-rest-api). Provides the repository list and renders each README to HTML.
+ [nh3](https://github.com/messense/nh3). An HTML sanitizer library, used here to help prevent XSS attacks from rendered markdown.
+ [Pillow](https://python-pillow.github.io/). An imaging library, used here to crop and resize repository preview images.
+ [Tabulator](https://www.tabulator.info/). A lightweight library for creating JavaScript tables and grids, featuring full support for digital accessibility standards.


## License
### Copyright Notice
Copyright © 2024-2026 The Regents of the University of Michigan


### Software and Library License Notice
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0-standalone.html>.


### Documentation License Notice
Permission is granted to copy, distribute and/or modify this document 
under the terms of the GNU Free Documentation License, Version 1.3 
or any later version published by the Free Software Foundation; 
with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts. 
You should have received a copy of the license included in the section entitled "GNU 
Free Documentation License". If not, see <https://www.gnu.org/licenses/fdl-1.3-standalone.html>



## Citation
If you find this repository, code or paper useful for your research, please cite it.

----

Copyright © 2024-2026 The Regents of the University of Michigan
