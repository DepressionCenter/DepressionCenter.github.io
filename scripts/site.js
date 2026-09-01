/*
This file is part of Eisenberg Family Depression Center Open Source Hub (DepressionCenter.github.io repository).
site.js - Interactive behavior for the Open Source Hub landing page.
Author(s): Gabriel Mongefranco.
Created: 2026-09-01
Last Modified: 2026-09-01
Summary: Adds search filtering, tag filtering, and the slide-in repository panel on top of
         content that is already present in the HTML. Every feature here is an enhancement:
         with scripting unavailable the page still lists every repository and each card links
         to a full repository page.
Notes: See README file for documentation and full license information.
Website: https://code.depressioncenter.org/

Copyright (c) 2026 The Regents of the University of Michigan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.
*/
(function () {
  'use strict';

  /* ### Load Configuration ### */

  // Panel bodies are written at build time, one file per repository.
  var FRAGMENT_BASE = 'data/readme/';

  // Opening the panel pushes a /repos/<name>/ URL into the address bar, and that changes the
  // base every later relative URL resolves against. Capture the site root once, now, before
  // any of that happens, so panel URLs stay correct however deep the address bar looks.
  var SITE_ROOT = new URL('.', window.location.href).href;

  /**
   * Resolve a path against the site root rather than the current address bar.
   *
   * @param {string} path Path relative to the site root, such as 'repos/MiNap/'.
   * @returns {string} An absolute URL.
   */
  function siteUrl(path) {
    return new URL(path, SITE_ROOT).href;
  }

  /**
   * Rewrite relative links and images inside injected markup so they resolve from the site
   * root.
   *
   * The panel is filled after the address bar has already been changed to /repos/<name>/, and
   * the browser resolves a relative src or href against whatever the address bar says at that
   * moment. Without this, a preview image asks for /repos/<name>/images/... and gets nothing.
   *
   * @param {Element} container Element whose descendants should be re-anchored.
   * @returns {void}
   */
  function anchorRelativeUrls(container) {
    var elements = container.querySelectorAll('[src], [href]');
    Array.prototype.forEach.call(elements, function (element) {
      ['src', 'href'].forEach(function (attribute) {
        var value = element.getAttribute(attribute);
        // Leave absolute URLs, protocol-relative URLs, and in-page anchors as they are.
        if (!value || /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(value)) {
          return;
        }
        element.setAttribute(attribute, siteUrl(value));
      });
    });
  }

  /* ### Search and tag filtering ### */

  /**
   * Show only the repository cards matching a search term.
   *
   * Cards carry their searchable text in a data-search attribute written at build time, so
   * filtering needs no index and no network request.
   *
   * @param {string} query Raw text from the search box.
   * @returns {void}
   */
  function applySearch(query) {
    var grid = document.getElementById('repo-grid');
    var counter = document.getElementById('repo-count');
    if (!grid) { return; }

    var term = query.toLowerCase().trim();
    var cards = grid.querySelectorAll('.repo-card');
    var visible = 0;

    cards.forEach(function (card) {
      var haystack = card.getAttribute('data-search') || '';
      var matches = !term || haystack.indexOf(term) !== -1;
      card.hidden = !matches;
      if (matches) { visible += 1; }
    });

    var empty = document.getElementById('repo-empty');
    if (empty) { empty.hidden = visible !== 0; }
    if (counter) {
      counter.textContent = visible + ' repo' + (visible === 1 ? '' : 's');
    }
  }

  /**
   * Put a tag into the search box and filter by it.
   *
   * @param {string} tag The tag text that was activated.
   * @param {boolean} scrollIntoView True when the tag was clicked in the featured section,
   *   which sits above the grid the filter applies to.
   * @returns {void}
   */
  function filterByTag(tag, scrollIntoView) {
    var input = document.getElementById('repo-search');
    if (!input) { return; }
    input.value = tag;
    applySearch(tag);
    if (scrollIntoView) {
      input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    input.focus();
  }

  /**
   * Wire up the search box and both sets of tag buttons.
   *
   * @returns {void}
   */
  function initSearch() {
    var input = document.getElementById('repo-search');
    if (input) {
      input.addEventListener('input', function () { applySearch(this.value); });
    }

    [['repo-grid', false], ['featured-grid', true]].forEach(function (pair) {
      var container = document.getElementById(pair[0]);
      if (!container) { return; }
      container.addEventListener('click', function (event) {
        var tag = event.target.closest('.lang-tag[data-tag]');
        if (tag) { filterByTag(tag.dataset.tag, pair[1]); }
      });
    });
  }

  /* ### Repository detail panel ### */

  var panelReturnFocus = null;
  var panelIsOpen = false;

  /**
   * Stop the page behind the panel from scrolling, without shifting it sideways.
   *
   * @returns {void}
   */
  function lockBodyScroll() {
    var scrollbar = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.paddingRight = scrollbar > 0 ? scrollbar + 'px' : '';
    document.body.style.overflow = 'hidden';
  }

  /**
   * Restore normal page scrolling.
   *
   * @returns {void}
   */
  function unlockBodyScroll() {
    document.body.style.paddingRight = '';
    document.body.style.overflow = '';
  }

  /**
   * Keep Tab and Shift+Tab inside the open panel, and close it on Escape.
   *
   * @param {KeyboardEvent} event The key event.
   * @returns {void}
   */
  function handlePanelKeydown(event) {
    if (event.key === 'Escape') {
      event.preventDefault();
      closePanel();
      return;
    }
    if (event.key !== 'Tab') { return; }

    var panel = document.getElementById('repo-panel');
    var focusable = Array.prototype.slice.call(panel.querySelectorAll(
      'a[href], button:not([disabled]), input, [tabindex]:not([tabindex="-1"])'
    )).filter(function (element) { return element.offsetParent !== null; });
    if (focusable.length < 2) { return; }

    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  /**
   * Open the slide-in panel for one repository and load its pre-rendered content.
   *
   * @param {string} slug Repository name, used to locate the fragment file.
   * @param {string} title Repository name to show as the panel heading.
   * @param {Element} trigger Element that opened the panel, so focus can return to it.
   * @param {boolean} pushHistory True to give the panel its own history entry, so the browser
   *   Back button closes it and the address bar shows a link worth copying.
   * @param {string} repoUrl The project's GitHub URL, offered if the content cannot be loaded.
   * @returns {void}
   */
  function openPanel(slug, title, trigger, pushHistory, repoUrl) {
    var panel = document.getElementById('repo-panel');
    var overlay = document.getElementById('panel-overlay');
    var body = document.getElementById('panel-body');
    if (!panel || !overlay || !body) { return; }

    panelReturnFocus = trigger || null;
    document.getElementById('panel-title').textContent = title;
    body.innerHTML =
      '<div class="loading-state" style="padding:20px 0">' +
      '<div class="spinner" aria-hidden="true"></div>Loading details…</div>';

    lockBodyScroll();
    panel.classList.add('is-open');
    panel.removeAttribute('inert');
    panel.setAttribute('aria-hidden', 'false');
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.getElementById('panel-close').focus();
    document.addEventListener('keydown', handlePanelKeydown);
    panelIsOpen = true;

    if (pushHistory) {
      history.pushState(
        { slug: slug, title: title, repoUrl: repoUrl || '' },
        '',
        siteUrl('repos/' + encodeURIComponent(slug) + '/')
      );
    }

    // The fragment is generated by the build, so it is same-origin, already sanitized, and
    // identical to the repository page a visitor would reach without scripting.
    fetch(siteUrl(FRAGMENT_BASE + encodeURIComponent(slug) + '.html'))
      .then(function (response) {
        if (!response.ok) { throw new Error('HTTP ' + response.status); }
        return response.text();
      })
      .then(function (markup) {
        // Parse into an inert document first. Images there do not start loading, so the
        // relative paths are corrected before the browser ever requests a wrong URL. The
        // result still goes in through innerHTML, which never runs script elements.
        var parsed = new DOMParser().parseFromString(markup, 'text/html');
        anchorRelativeUrls(parsed.body);
        body.innerHTML = parsed.body.innerHTML;
      })
      .catch(function () {
        // Reaching here means this site failed to serve its own content, so the fallback
        // deliberately leaves it: GitHub always has the project, whatever state a build is in.
        var fallback = repoUrl
          ? '<a href="' + repoUrl + '" target="_blank" rel="noopener">' +
            'View this project on GitHub.</a>'
          : '<a href="' + siteUrl('repos/' + encodeURIComponent(slug) + '/') + '">' +
            'Open the full page instead.</a>';
        body.innerHTML = '<p class="error-state">Details could not be loaded. ' + fallback + '</p>';
      });
  }

  /**
   * Close the panel and return focus to whatever opened it.
   *
   * @param {boolean} skipHistory True when the browser already moved back, so no further
   *   history change is needed.
   * @returns {void}
   */
  function closePanel(skipHistory) {
    var panel = document.getElementById('repo-panel');
    var overlay = document.getElementById('panel-overlay');
    if (!panel || !panelIsOpen) { return; }

    panel.classList.remove('is-open');
    panel.setAttribute('inert', '');
    panel.setAttribute('aria-hidden', 'true');
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    unlockBodyScroll();
    document.removeEventListener('keydown', handlePanelKeydown);
    panelIsOpen = false;

    // Focus returns before any history change, because going back fires popstate and this
    // function runs again with nothing left to restore.
    var shouldGoBack = !skipHistory && history.state && history.state.slug;
    if (panelReturnFocus) {
      panelReturnFocus.focus();
      panelReturnFocus = null;
    }
    if (shouldGoBack) {
      history.back();
    }
  }

  /**
   * Decide whether a click should be left to the browser.
   *
   * Middle-click, Ctrl-click, and Cmd-click all mean "open this somewhere else". Intercepting
   * them would break the ordinary behavior of a link.
   *
   * @param {MouseEvent} event The click event.
   * @returns {boolean} True when the browser should handle the click itself.
   */
  function isModifiedClick(event) {
    return event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;
  }

  /**
   * Turn clicks on repository cards into panel openings, and keep links working otherwise.
   *
   * @returns {void}
   */
  function initPanel() {
    var closeButton = document.getElementById('panel-close');
    var overlay = document.getElementById('panel-overlay');
    if (!closeButton || !overlay) { return; }

    closeButton.addEventListener('click', function () { closePanel(false); });
    overlay.addEventListener('click', function () { closePanel(false); });

    document.addEventListener('click', function (event) {
      if (isModifiedClick(event)) { return; }
      var trigger = event.target.closest('.card-panel-trigger[data-slug]');
      if (!trigger) { return; }
      // A tag inside a card filters the grid; it must not also open the panel.
      if (event.target.closest('.lang-tag')) { return; }
      // The links row points at other sites and is not a way into the panel.
      if (event.target.closest('.repo-links')) { return; }

      var card = trigger.closest('article');
      var titleElement = card ? card.querySelector('.card-title-link') : null;
      var slug = trigger.dataset.slug;
      event.preventDefault();
      openPanel(
        slug,
        titleElement ? titleElement.textContent : slug,
        titleElement || trigger,
        true,
        card ? card.dataset.repoUrl : ''
      );
    });

    // The Back button leaves the panel URL, so the panel itself has to close with it.
    window.addEventListener('popstate', function (event) {
      if (panelIsOpen) {
        closePanel(true);
      } else if (event.state && event.state.slug) {
        openPanel(
          event.state.slug,
          event.state.title || event.state.slug,
          null,
          false,
          event.state.repoUrl || ''
        );
      }
    });
  }

  /* ### Community open source table ### */

  /**
   * Render one comma-separated cell as a row of tag chips.
   *
   * @param {object} cell Tabulator cell component.
   * @returns {string} HTML for the cell.
   */
  function tagFormatter(cell) {
    var value = cell.getValue() || '';
    return value.split(',').map(function (tag) {
      tag = tag.trim();
      if (!tag) { return ''; }
      var safe = tag.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
      return '<button type="button" class="oss-tag" data-tag="' + safe + '">' + safe + '</button>';
    }).join('');
  }

  /**
   * Render the project name as a link to the project's own site.
   *
   * @param {object} cell Tabulator cell component.
   * @returns {string} HTML for the cell.
   */
  function linkFormatter(cell) {
    var row = cell.getRow().getData();
    var name = (cell.getValue() || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
    var url = (row.url || '#').replace(/"/g, '&quot;');
    return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + name + '</a>';
  }

  /**
   * Build the curated table of open source tools from other organizations.
   *
   * @returns {void}
   */
  function initCommunityTable() {
    var container = document.getElementById('oss-table');
    if (!container || typeof Tabulator === 'undefined') { return; }

    var table = new Tabulator('#oss-table', {
      ajaxURL: 'data/research-open-source.json',
      layout: 'fitColumns',
      pagination: 'local',
      paginationSize: 50,
      paginationSizeSelector: [25, 50, 100],
      sortMode: 'local',
      initialSort: [{ column: 'project', dir: 'asc' }],
      columns: [
        { title: 'Project', field: 'project', formatter: linkFormatter, sorter: 'string', widthGrow: 1.5 },
        { title: 'Author(s)', field: 'authors', sorter: 'string', widthGrow: 1 },
        { title: 'Summary', field: 'summary', sorter: 'string', widthGrow: 3 },
        { title: 'Keywords', field: 'keywords', formatter: tagFormatter, headerSort: false, widthGrow: 1.5 },
        { title: 'Research Stage', field: 'research_stage', formatter: tagFormatter, headerSort: false, widthGrow: 1.5 }
      ]
    });

    var search = document.getElementById('oss-search');
    if (!search) { return; }

    search.addEventListener('input', function () {
      var query = this.value.trim();
      if (!query) { table.clearFilter(); return; }
      table.setFilter([[
        { field: 'project', type: 'like', value: query },
        { field: 'authors', type: 'like', value: query },
        { field: 'summary', type: 'like', value: query },
        { field: 'keywords', type: 'like', value: query },
        { field: 'research_stage', type: 'like', value: query }
      ]]);
    });

    container.addEventListener('click', function (event) {
      var tag = event.target.closest('.oss-tag[data-tag]');
      if (!tag) { return; }
      search.value = tag.dataset.tag;
      search.dispatchEvent(new Event('input'));
      search.focus();
    });
  }

  /* ### Start ### */

  initSearch();
  initPanel();
  initCommunityTable();
})();
