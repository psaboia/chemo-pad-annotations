// Cards Gallery JavaScript - Client-side filtering and card management

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    setupLazyLoading();
    setupFilterListeners();

    // Check if we have a preselected API filter
    if (typeof preselectedAPI !== 'undefined' && preselectedAPI !== null) {
        setTimeout(function() {
            applyFilters();
        }, 100);
    } else {
        applyFilters();
    }
});

// Lazy loading for images
function setupLazyLoading() {
    const images = document.querySelectorAll('.gallery-image.lazy');

    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        images.forEach(img => imageObserver.observe(img));
    } else {
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            img.classList.add('loaded');
        });
    }
}

// Setup filter event listeners
function setupFilterListeners() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(applyFilters, 300));
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Apply filters to cards
function applyFilters() {
    const filters = getActiveFilters();
    const cardItems = document.querySelectorAll('.card-item');

    let visibleCount = 0;

    cardItems.forEach(item => {
        const isVisible = matchesFilters(item, filters);

        if (isVisible) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });

    // Update section counts
    updateSectionCounts();

    // Update visible count
    document.getElementById('visible-count').textContent = visibleCount;
}

window.applyFilters = applyFilters;

// Get active filters
function getActiveFilters() {
    const filters = {
        camera: [],
        status: [],
        api: 'all',
        search: ''
    };

    // Get checked camera filters
    document.querySelectorAll('input[name="camera"]:checked').forEach(input => {
        filters.camera.push(input.value);
    });

    // Get checked status filters
    document.querySelectorAll('input[name="status"]:checked').forEach(input => {
        filters.status.push(input.value);
    });

    // Get API filter
    const apiFilter = document.getElementById('api-filter');
    if (apiFilter) {
        filters.api = apiFilter.value;
    }

    // Get search text
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        filters.search = searchInput.value.toLowerCase();
    }

    return filters;
}

// Check if item matches filters
function matchesFilters(item, filters) {
    // Check camera
    if (filters.camera.length > 0) {
        const itemCamera = item.dataset.camera;
        if (!filters.camera.includes(itemCamera)) {
            return false;
        }
    }

    // Check status
    if (filters.status.length > 0) {
        const itemStatus = item.dataset.status;
        if (!filters.status.includes(itemStatus)) {
            return false;
        }
    }

    // Check API
    if (filters.api !== 'all') {
        const itemApi = item.dataset.api;
        if (itemApi !== filters.api.toLowerCase()) {
            return false;
        }
    }

    // Check search
    if (filters.search) {
        const cardId = item.dataset.cardId.toString().toLowerCase();
        const sample = item.dataset.sample || '';

        if (!cardId.includes(filters.search) && !sample.includes(filters.search)) {
            return false;
        }
    }

    return true;
}

// Reset all filters
function resetFilters() {
    // Check all checkboxes
    document.querySelectorAll('.filter-sidebar input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = true;
    });

    // Reset API dropdown
    const apiFilter = document.getElementById('api-filter');
    if (apiFilter) {
        apiFilter.value = 'all';
    }

    // Clear search
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = '';
    }

    // Apply filters
    applyFilters();
}

window.resetFilters = resetFilters;

// Toggle section visibility
function toggleSection(api) {
    const section = document.querySelector(`.api-section[data-api="${api}"]`);
    if (!section) return;

    const grid = section.querySelector('.image-grid');
    const toggle = section.querySelector('.toggle-section');

    if (grid.classList.contains('collapsed')) {
        grid.classList.remove('collapsed');
        toggle.classList.remove('collapsed');
        toggle.textContent = '▼';
    } else {
        grid.classList.add('collapsed');
        toggle.classList.add('collapsed');
        toggle.textContent = '▶';
    }
}

window.toggleSection = toggleSection;

// Update section counts after filtering
function updateSectionCounts() {
    const sections = document.querySelectorAll('.api-section');

    sections.forEach(section => {
        const visibleItems = section.querySelectorAll('.card-item:not(.hidden)');
        const countBadge = section.querySelector('.count-badge');

        if (countBadge) {
            countBadge.textContent = `${visibleItems.length} cards`;
        }

        // Hide section if no visible items
        if (visibleItems.length === 0) {
            section.style.display = 'none';
        } else {
            section.style.display = 'block';
        }
    });
}

// Open image modal
function openImageModal(imageUrl, cardId, sampleName) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');

    modal.style.display = 'block';
    modalImg.src = imageUrl;
    modalCaption.innerHTML = `Card #${cardId} - ${sampleName}`;

    document.addEventListener('keydown', handleModalKeyPress);
}

// Close image modal
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.style.display = 'none';
    document.removeEventListener('keydown', handleModalKeyPress);
}

window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;

// Handle keyboard events for modal
function handleModalKeyPress(event) {
    if (event.key === 'Escape' || event.key === 'Esc') {
        closeImageModal();
        closeQuickMatchModal();
    }
}

// Click anywhere on modal to close
window.onclick = function(event) {
    const imageModal = document.getElementById('imageModal');
    const quickMatchModal = document.getElementById('quickMatchModal');

    if (event.target.id === 'imageModal' || event.target.closest('#imageModal')) {
        closeImageModal();
    }

    if (event.target.id === 'quickMatchModal') {
        closeQuickMatchModal();
    }
}

// Mark card with issue
async function markInvalid(cardId) {
    let reason = '';

    // Keep prompting until user enters a reason or cancels
    while (true) {
        reason = prompt('Describe the issue with this card (required):');

        // User cancelled
        if (reason === null) return;

        // Check if reason is not empty
        if (reason.trim() !== '') {
            break;
        }

        // Show error and prompt again
        alert('Please provide a description of the issue.');
    }

    try {
        const response = await fetch('/api/mark-card-invalid', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ card_id: cardId, reason: reason.trim() })
        });

        const data = await response.json();

        if (data.success) {
            // Reload page to reflect changes
            location.reload();
        } else {
            alert('Error flagging card: ' + data.error);
        }
    } catch (error) {
        alert('Error flagging card: ' + error);
    }
}

window.markInvalid = markInvalid;

// Remove issue flag from card
async function unmarkInvalid(cardId) {
    if (!confirm('Remove issue flag from this card?')) return;

    try {
        const response = await fetch('/api/unmark-card-invalid', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ card_id: cardId })
        });

        const data = await response.json();

        if (data.success) {
            location.reload();
        } else {
            alert('Error removing issue flag: ' + data.error);
        }
    } catch (error) {
        alert('Error removing issue flag: ' + error);
    }
}

window.unmarkInvalid = unmarkInvalid;

// Quick match modal
let currentCardIdForMatch = null;

function openQuickMatchModal(cardId, sampleName) {
    currentCardIdForMatch = cardId;
    const modal = document.getElementById('quickMatchModal');
    const cardIdSpan = document.getElementById('matchCardId');
    const sampleSpan = document.getElementById('matchCardSample');

    cardIdSpan.textContent = cardId;
    sampleSpan.textContent = sampleName;

    modal.style.display = 'block';

    // Focus search input
    const searchInput = document.getElementById('annotationSearch');
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
        searchInput.addEventListener('input', searchAnnotations);
    }
}

window.openQuickMatchModal = openQuickMatchModal;

function closeQuickMatchModal() {
    const modal = document.getElementById('quickMatchModal');
    modal.style.display = 'none';
    currentCardIdForMatch = null;
}

window.closeQuickMatchModal = closeQuickMatchModal;

// Search annotations for matching
async function searchAnnotations() {
    const searchTerm = document.getElementById('annotationSearch').value.toLowerCase();
    const resultsDiv = document.getElementById('annotationResults');

    if (searchTerm.length < 2) {
        resultsDiv.innerHTML = '<p class="no-results">Enter at least 2 characters to search...</p>';
        return;
    }

    // Search through annotations data from the main matching page
    // For now, provide a link to the main matching page
    resultsDiv.innerHTML = `
        <p class="info-message">
            To match this card to an annotation, please use the main matching interface:
        </p>
        <a href="/match/${currentCardIdForMatch}" class="btn-primary" style="display: inline-block; margin-top: 10px;">
            Go to Matching Page →
        </a>
    `;
}

// Export filtered cards to CSV
function exportFilteredCards() {
    const visibleItems = document.querySelectorAll('.card-item:not(.hidden)');
    const data = [];

    visibleItems.forEach(item => {
        data.push({
            card_id: item.dataset.cardId,
            api: item.dataset.api,
            sample: item.dataset.sample,
            camera: item.dataset.camera,
            status: item.dataset.status
        });
    });

    // Convert to CSV
    const csv = convertToCSV(data);

    // Download
    downloadCSV(csv, 'unmatched_cards_export.csv');
}

window.exportFilteredCards = exportFilteredCards;

// Convert data to CSV format
function convertToCSV(data) {
    if (data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');

    const csvRows = data.map(row => {
        return headers.map(header => {
            const value = row[header] || '';
            return `"${value}"`;
        }).join(',');
    });

    return csvHeaders + '\n' + csvRows.join('\n');
}

// Download CSV file
function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}
