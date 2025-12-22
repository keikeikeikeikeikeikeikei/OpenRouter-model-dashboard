const validTabs = ['text', 'image', 'embedding'];
let currentTab = 'text';
let sortKey = 'price';
let sortAsc = true;
let activeFilters = new Set();

// --- Configuration ---
const filters = {
    text: [
        { id: 'isFree', label: 'Free' },
        { id: 'excludeFree', label: 'Paid Only' },
        { id: 'supportsFunctionCalling', label: 'Function Calling' },
        { id: 'supportsJSON', label: 'JSON Mode' }
    ],
    image: [
        { id: 'isFree', label: 'Free' }
    ],
    embedding: [
        { id: 'isFree', label: 'Free' }
    ]
};

const headers = {
    text: [
        { key: 'name', label: 'Model Name', class: '' },
        { key: 'price', label: 'Price (per 1M)', class: '' },
        { key: 'context', label: 'Context', class: '' },
        { key: 'caps', label: 'Capabilities', class: '' }
    ],
    image: [
        { key: 'name', label: 'Model Name', class: '' },
        { key: 'price', label: 'Price (per Image)', class: '' },
        { key: 'context', label: 'Context', class: '' },
        { key: 'caps', label: 'Capabilities', class: '' }
    ],
    embedding: [
        { key: 'name', label: 'Model Name', class: '' },
        { key: 'price', label: 'Price (per 1M)', class: '' },
        { key: 'context', label: 'Context', class: '' },
        { key: 'caps', label: 'Capabilities', class: '' }
    ]
};

// --- Utils ---
const get = (obj, path, def) => {
    return path.split('.').reduce((acc, part) => acc && acc[part] !== undefined ? acc[part] : def, obj);
};

const formatPrice = (p) => {
    if (p === 0) return 'Free';
    if (p < 0.01) return '$' + p.toFixed(6);
    return '$' + p.toFixed(3);
}

const strategies = {
    text: {
        getPrice: (m) => {
            const p = m.pricing;
            const prompt = parseFloat(p.prompt);
            const comp = parseFloat(p.completion);
            if (prompt < 0) return -1; // Special/Beta
            // Per 1M tokens
            return ((prompt + comp) / 2) * 1000000;
        },
        renderPrice: (m, max) => {
            const p = m.pricing;

            if (p.prompt === "-1") return '<div class="price-cell"><div class="price-val">Special Pricing</div></div>';

            const prompt = parseFloat(p.prompt) * 1000000;
            const comp = parseFloat(p.completion) * 1000000;
            const avg = (prompt + comp) / 2;

            // Handle very small numbers or zero
            const pStr = formatPrice(prompt);
            const cStr = formatPrice(comp);
            const aStr = formatPrice(avg);

            const pct = max > 0 ? (avg / max) * 100 : 0;

            return `
            <div class="price-cell">
                <div class="price-val">${pStr} (in) / ${cStr} (out)</div>
                <div class="rel-bar-container" title="Relative Cost: ${Math.round(pct)}%">
                    <div class="rel-bar-bg"><div class="rel-bar-fill ${getBarColor(pct)}" style="width:${pct}%"></div></div>
                    <span>Avg ${aStr}</span>
                </div>
            </div>
        `;
        },
        renderCaps: (m) => {
            const p = m.supported_parameters || [];
            const arch = m.architecture || {};
            const modal = arch.input_modalities || [];

            const caps = [
                { k: 'reasoning', label: 'Reasoning', cls: 'feat-reasoning', check: () => p.includes('reasoning') || m.id.includes('reasoning') },
                { k: 'vision', label: 'Vision', cls: 'feat-vision', check: () => modal.includes('image') || m.id.includes('vision') },
                { k: 'func', label: 'Function Call', cls: 'feat-func', check: () => p.includes('tools') || p.includes('tool_choice') },
                { k: 'web', label: 'Web Search', cls: 'feat-search', check: () => m.pricing && parseFloat(m.pricing.web_search) > 0 },
                { k: 'json', label: 'JSON Mode', cls: 'feat-json', check: () => p.includes('json_schema') || p.includes('structured_outputs') }
            ];
            return `<div class="feature-tags">
            ${caps.filter(cap => cap.check()).map(cap => `<span class="feature-badge ${cap.cls}">${cap.label}</span>`).join('')}
        </div>`;
        },
        renderCtx: (m) => {
            const t = m.context_length || 0;
            return Math.round(t / 1024) + 'k';
        },
        checkFilter: (m, fid) => {
            const p = m.supported_parameters || [];
            const arch = m.architecture || {};
            const modal = arch.input_modalities || [];

            if (fid === 'isFree') {
                return parseFloat(m.pricing.prompt) === 0 && parseFloat(m.pricing.completion) === 0;
            }
            if (fid === 'excludeFree') {
                return parseFloat(m.pricing.prompt) > 0 || parseFloat(m.pricing.completion) > 0;
            }
            if (fid === 'supportsReasoning') return p.includes('reasoning') || m.id.includes('reasoning');
            if (fid === 'supportsVision') return modal.includes('image');
            if (fid === 'supportsFunctionCalling') return p.includes('tools');
            if (fid === 'supportsJSON') return p.includes('json_schema') || p.includes('structured_outputs');
            return false;
        }
    },
    image: {
        getPrice: (m) => {
            // Try to get per-image price first, otherwise per request
            return parseFloat(m.pricing.image) || parseFloat(m.pricing.request) || 0;
        },
        renderPrice: (m, max) => {
            const p = parseFloat(m.pricing.image) || parseFloat(m.pricing.request) || 0;
            const pStr = formatPrice(p);
            const pct = max > 0 ? (p / max) * 100 : 0;

            return `
             <div class="price-cell">
                <div class="price-val">${pStr} / image</div>
                <div class="rel-bar-container" title="Relative Cost: ${Math.round(pct)}%">
                    <div class="rel-bar-bg"><div class="rel-bar-fill ${getBarColor(pct)}" style="width:${pct}%"></div></div>
                </div>
             </div>`;
        },
        renderCaps: (m) => {
            return `<div class="cap-icons"><span class="cap-icon cap-active" title="Image Generation">🎨</span></div>`;
        },
        renderCtx: (m) => {
            const t = m.context_length || 0;
            return t > 0 ? Math.round(t / 1024) + 'k' : '-';
        },
        checkFilter: (m, fid) => {
            if (fid === 'isFree') {
                const p = parseFloat(m.pricing.image) || parseFloat(m.pricing.request) || 0;
                return p === 0;
            }
            return true;
        }
    },
    embedding: {
        getPrice: (m) => {
            const p = m.pricing;
            const prompt = parseFloat(p.prompt);
            // Embeddings usually just have prompt price
            return prompt * 1000000;
        },
        renderPrice: (m, max) => {
            const p = m.pricing;
            const prompt = parseFloat(p.prompt) * 1000000;
            const pStr = formatPrice(prompt);

            const pct = max > 0 ? (prompt / max) * 100 : 0;

            return `
            <div class="price-cell">
                <div class="price-val">${pStr} (per 1M)</div>
                 <div class="rel-bar-container" title="Relative Cost: ${Math.round(pct)}%">
                    <div class="rel-bar-bg"><div class="rel-bar-fill ${getBarColor(pct)}" style="width:${pct}%"></div></div>
                </div>
            </div>`;
        },
        renderCaps: (m) => '',
        renderCtx: (m) => {
            const t = m.context_length || 0;
            return Math.round(t / 1024) + 'k';
        },
        checkFilter: (m, fid) => {
            if (fid === 'isFree') {
                return parseFloat(m.pricing.prompt) === 0;
            }
            return true;
        }
    }
};

function getBarColor(p) {
    if (p < 33) return 'bar-low';
    if (p < 66) return 'bar-med';
    return 'bar-high';
}

// --- Main Logic ---

function handleSort(key) {
    if (sortKey === key) {
        sortAsc = !sortAsc;
    } else {
        sortKey = key;
        sortAsc = true;
        if (key === 'created') sortAsc = false;
    }
    renderTable();
}

function renderTable() {
    const thead = document.getElementById('tableHead');
    const tbody = document.getElementById('tableBody');
    const cols = headers[currentTab];

    // Safety check for data
    if (!window.openRouterModels || !window.openRouterModels[currentTab]) {
        console.warn(`No models found for tab: ${currentTab}`);
        if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="loading-text">No data available for this category.</td></tr>';
        return;
    }

    const models = window.openRouterModels[currentTab] || [];
    const term = document.getElementById('searchInput') ? document.getElementById('searchInput').value.toLowerCase() : '';

    // 1. Render Headers
    if (!cols) return;
    thead.innerHTML = `<tr class="table-header">
    ${cols.map(c => `<th class="${c.class}" onclick="handleSort('${c.key}')">${c.label} ${sortKey === c.key ? (sortAsc ? '▲' : '▼') : ''}</th>`).join('')}
</tr>`;

    // 2. Filter
    let data = models.filter(m => {
        // Text Search
        const n = get(m, 'name', '').toLowerCase();
        const i = m.id.toLowerCase();
        if (!(n.includes(term) || i.includes(term))) return false;

        // Capability Filters
        const strat = strategies[currentTab];
        for (let fid of activeFilters) {
            if (!strat.checkFilter(m, fid)) return false;
        }

        return true;
    });

    // 3. Prepare Sort Data & Max Price
    // Calculate max price for relative bars (exclude special pricing -1)
    const validPrices = data.map(m => strategies[currentTab].getPrice(m)).filter(p => p >= 0);
    const maxPrice = validPrices.length > 0 ? Math.max(...validPrices) : 0;

    data.forEach(m => {
        m._sort_price = strategies[currentTab].getPrice(m);
        // If price is -1 (unknown/special), treat as very high for sorting desc, or specific place
        if (m._sort_price < 0) m._sort_price = 999999;
    });

    // 4. Sort
    data.sort((a, b) => {
        let valA, valB;

        if (sortKey === 'price') {
            valA = a._sort_price;
            valB = b._sort_price;
        } else if (sortKey === 'context') {
            valA = a.context_length || 0;
            valB = b.context_length || 0;
        } else if (sortKey === 'name') {
            valA = a.name.toLowerCase();
            valB = b.name.toLowerCase();
        } else {
            valA = get(a, sortKey, 0);
            valB = get(b, sortKey, 0);
        }

        if (valA < valB) return sortAsc ? -1 : 1;
        if (valA > valB) return sortAsc ? 1 : -1;
        return 0;
    });

    // 5. Render Rows
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading-text">No models match your criteria.</td></tr>';
        return;
    }

    const strat = strategies[currentTab];
    const rows = data.map(m => {
        return `
        <tr class="table-row" onclick="toggleDetails(this, '${m.id}')">
            <td>
                <a href="https://openrouter.ai/models/${m.id}" target="_blank" class="model-name" onclick="event.stopPropagation()">${m.name}</a>
                <div class="model-id">${m.id}</div>
            </td>
            <td>${strat.renderPrice(m, maxPrice)}</td>
            <td>${strat.renderCtx(m)}</td>
            <td>${strat.renderCaps(m)}</td>
        </tr>
        <tr>
             <td colspan="4" style="padding: 0; border: none;">
                <div class="row-details" id="details-${m.id.replace(/[^a-zA-Z0-9-_]/g, '_')}">
                    <!-- Content loaded on demand -->
                </div>
             </td>
        </tr>
    `;
    }).join('');

    tbody.innerHTML = rows;
}

function renderFilters() {
    const bar = document.getElementById('filterBar');
    const available = filters[currentTab] || [];

    if (available.length === 0) {
        bar.style.display = 'none';
        bar.innerHTML = '';
        return;
    }

    bar.style.display = 'flex';
    bar.innerHTML = available.map(f => {
        const active = activeFilters.has(f.id);
        return `
    <label class="filter-item">
        <input type="checkbox" ${active ? 'checked' : ''} onchange="toggleFilter('${f.id}')" style="display:none">
        <span>${active ? '✓ ' : ''}${f.label}</span>
    </label>
    `;
    }).join('');
}

async function switchTab(tab) {
    if (!validTabs.includes(tab)) return;
    currentTab = tab;
    activeFilters.clear(); // Clear filters when switching tabs

    // Reset sort defaults
    sortKey = 'price';
    sortAsc = true;

    // Update UI
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => {
        if (b.getAttribute('onclick').includes(`'${tab}'`)) {
            b.classList.add('active');
        }
    });

    // Reset Search
    if (document.getElementById('searchInput')) {
        document.getElementById('searchInput').value = '';
    }

    // Set View Mode class for grid layout
    const listEl = document.getElementById('model-list'); // Keeping for legacy if element exists
    if (listEl) {
        listEl.className = 'model-list'; // Reset
        listEl.classList.add(`view-mode-${tab}`);
    }

    // Re-render
    filterAndRender();
}

function filterAndRender() {
    renderFilters();
    renderTable();
}

function toggleFilter(fid) {
    if (activeFilters.has(fid)) {
        activeFilters.delete(fid);
    } else {
        activeFilters.add(fid);
    }
    renderTable();
}

// Check for DOM readiness and initialize
document.addEventListener('DOMContentLoaded', function () {
    // Initial Render
    switchTab('text');
});


// Provider Fetching Logic (Same as before)
async function toggleDetails(rowGroup, modelId) {
    // rowGroup is the TR element clicked. The details TR is the next sibling.
    const detailsRow = rowGroup.nextElementSibling;
    const detailsDiv = detailsRow.querySelector('.row-details');

    if (!detailsDiv) return;

    // Toggle expansion
    const isExpanded = detailsDiv.classList.contains('expanded');

    // Collapse all others (optional - keeps UI clean)
    document.querySelectorAll('.row-details.expanded').forEach(el => {
        if (el !== detailsDiv) el.classList.remove('expanded');
    });

    if (isExpanded) {
        detailsDiv.classList.remove('expanded');
    } else {
        detailsDiv.classList.add('expanded');

        // Load data if empty
        if (!detailsDiv.hasAttribute('data-loaded')) {
            detailsDiv.innerHTML = '<div class="loading-text">Fetching live provider data...</div>';

            try {
                // Fetch endpoints
                const res = await fetch(`https://openrouter.ai/api/v1/models/${modelId}/endpoints`);
                if (!res.ok) throw new Error('Failed to load');
                const json = await res.json();
                const endpoints = json.data;

                if (!endpoints || endpoints.length === 0) {
                    detailsDiv.innerHTML = '<div class="loading-text">No active provider details available.</div>';
                } else {
                    // Render Table
                    let html = `
                        <table class="provider-table">
                            <thead>
                                <tr>
                                    <th>Provider</th>
                                    <th>Price (1M in/out)</th>
                                    <th>Context</th>
                                    <th>Quantization</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    endpoints.forEach(ep => {
                        const p = ep.pricing;
                        const pIn = formatPrice(parseFloat(p.prompt) * 1000000);
                        const pOut = formatPrice(parseFloat(p.completion) * 1000000);
                        const q = ep.quantization || 'Unknown';
                        const ctx = Math.round(ep.context_length / 1024) + 'k';

                        html += `
                            <tr>
                                <td>${ep.provider_name}</td>
                                <td>${pIn} / ${pOut}</td>
                                <td>${ctx}</td>
                                <td>${q}</td>
                            </tr>
                        `;
                    });

                    html += '</tbody></table>';
                    detailsDiv.innerHTML = html;
                }

                detailsDiv.setAttribute('data-loaded', 'true');

            } catch (e) {
                console.error(e);
                detailsDiv.innerHTML = '<div class="loading-text">Error loading provider details.</div>';
            }
        }
    }
}
