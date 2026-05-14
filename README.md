![Depression Center Logo](images/EFDCLogo_375w.png "depressioncenter.org")

# Eisenberg Family Depression Center: Open Source Projects

## About
This repository contains the code for the landing webpage for the Eisnberg Family Depression Center's code repository: [https://code.depressioncenter.org](https://code.depressioncenter.org). This site creates a grid of all our public repos through the GitHub API, including custom properties such as lab name and URL, DOI#, documentation URL, etc. When users click on a tile, a side panel opens, wich gets the README.md file for that repository in real time and renders it inside the side panel.

## Quick Start Guide
+ To re-use the code, you will need to either [fork](https://github.com/DepressionCenter/DepressionCenter.github.io/fork) the repo or download and edit index.html and upload to your web server.
+ If you would like to use GitHub Pages for free web hosting, simply [fork](https://github.com/DepressionCenter/DepressionCenter.github.io/fork) this repo and make your changes to index.html there. Keep the ".nojekyll" file to avoid having to run GitHub Actions.
+ In the "index.html" file, change "DepressionCenter" to your GitHub organization (or user ID). You can also change the "fallback" data at the bottom of the script to use in case a browser is unable to reach the GitHub API.
+ Images must be stored under /images/repo-previews. Each file needs to match the name of the repo exactly (including upper case and lower case letters) plus ".png" for the larger image, or "-thumb.png" for the thumbnail image (400x125px). Both images must have a 16:9 aspect ratio.
+ Please remove the copyright notice in the code, especially if you are not affiliated with University of Michigan. However, the license notice at the top of the file (in HTML comments) must remain there, as the code is licensed under the GPLv3.0 or later license.

## Where are the repos located?
Please see our GitHub site at:  [https://github.com/DepressionCenter](https://github.com/DepressionCenter)



## Documentation
Please see our Knowledge Base at:  [https://michmed.org/efdc-kb](https://michmed.org/efdc-kb)



## Additional Resources
+ [Eisenberg Family Depression Center](https://depressioncenter.org)
+ [Michigan Medicine](https://michiganmedicine.org)
+ [University of Michigan](https://umich.edu)



## Credits

#### Contributors:
+ Eisenberg Family Depression Center [(@DepressionCenter)](https://github.com/DepressionCenter/)
+ Gabriel Mongefranco [(@gabrielmongefranco)](https://github.com/gabrielmongefranco)

#### This work is based in part on the following projects, libraries and/or studies:
+ [Marked](https://github.com/markedjs/marked). A markdown parser library, used here to render README.md files.
+ [DOMPurify](https://github.com/cure53/DOMPurify). An HTML sanitizer library, used here to help prevent XSS attacks from rendered markdown.
+ [GitHub REST API](https://docs.github.com/rest/about-the-rest-api/about-the-rest-api).


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
