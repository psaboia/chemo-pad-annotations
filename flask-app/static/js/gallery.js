// Gallery JavaScript - Client-side filtering and image management

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    setupLazyLoading();

    // Add event listeners for real-time filtering
    setupFilterListeners();

    // Check if we have a preselected API filter
    if (typeof preselectedAPI !== 'undefined' && preselectedAPI !== null) {
        // Wait a moment for DOM to settle, then apply filters
        setTimeout(function() {
            applyFilters();
        }, 100);
    } else {
        // Apply default filters to ensure correct initial state
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
        // Fallback for browsers without IntersectionObserver
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            img.classList.add('loaded');
        });
    }
}

// Setup filter event listeners
function setupFilterListeners() {
    // Remove auto-apply on change - only apply when button is clicked
    // This prevents confusing partial filter states

    // Search input still gets real-time updates for better UX
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(applyFilters, 300));
    }
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Apply filters to gallery items
function applyFilters() {
    const filters = getActiveFilters();
    const galleryItems = document.querySelectorAll('.gallery-item');

    let visibleCount = 0;

    galleryItems.forEach(item => {
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

// Make applyFilters globally accessible for onclick
window.applyFilters = applyFilters;

// Get active filters
function getActiveFilters() {
    const filters = {
        lighting: [],
        camera: [],
        background: [],
        match_status: [],
        api: 'all',
        search: ''
    };

    // Get checked lighting filters
    document.querySelectorAll('input[name="lighting"]:checked').forEach(input => {
        filters.lighting.push(input.value);
    });

    // Get checked camera filters
    document.querySelectorAll('input[name="camera"]:checked').forEach(input => {
        filters.camera.push(input.value);
    });

    // Get checked background filters
    document.querySelectorAll('input[name="background"]:checked').forEach(input => {
        filters.background.push(input.value);
    });

    // Get checked match status filters
    document.querySelectorAll('input[name="match_status"]:checked').forEach(input => {
        filters.match_status.push(input.value);
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
    // Check lighting
    if (filters.lighting.length > 0) {
        const itemLighting = item.dataset.lighting;
        if (!filters.lighting.includes(itemLighting)) {
            return false;
        }
    }

    // Check camera
    if (filters.camera.length > 0) {
        const itemCamera = item.dataset.camera;
        if (!filters.camera.includes(itemCamera)) {
            return false;
        }
    }

    // Check background
    if (filters.background.length > 0) {
        const itemBackground = item.dataset.background;
        if (!filters.background.includes(itemBackground)) {
            return false;
        }
    }

    // Check match status
    if (filters.match_status.length > 0) {
        const itemStatus = item.dataset.status;
        if (!filters.match_status.includes(itemStatus)) {
            return false;
        }
    }

    // Check API
    if (filters.api !== 'all') {
        const itemApi = item.dataset.api;
        if (itemApi !== filters.api) {
            return false;
        }
    }

    // Check search (case-insensitive)
    if (filters.search) {
        const padNumStr = item.dataset.pad.toString().toLowerCase();
        const sample = item.dataset.sample || '';

        if (!padNumStr.includes(filters.search) && !sample.includes(filters.search)) {
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

// Make resetFilters globally accessible for onclick
window.resetFilters = resetFilters;

// Toggle section visibility
function toggleSection(lighting) {
    const section = document.querySelector(`.lighting-section[data-lighting="${lighting}"]`);
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

// Update section counts after filtering
function updateSectionCounts() {
    const sections = document.querySelectorAll('.lighting-section');

    sections.forEach(section => {
        const visibleItems = section.querySelectorAll('.gallery-item:not(.hidden)');
        const countBadge = section.querySelector('.count-badge');

        if (countBadge) {
            countBadge.textContent = `${visibleItems.length} images`;
        }

        // Hide section if no visible items
        if (visibleItems.length === 0) {
            section.style.display = 'none';
        } else {
            section.style.display = 'block';
        }
    });
}

// Update visible count
function updateVisibleCount() {
    const totalItems = document.querySelectorAll('.gallery-item').length;
    const visibleItems = document.querySelectorAll('.gallery-item:not(.hidden)').length;

    document.getElementById('total-count').textContent = totalItems;
    document.getElementById('visible-count').textContent = visibleItems;
}

// Open image modal
function openImageModal(imageUrl, padNum, lighting) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');

    modal.style.display = 'block';
    modalImg.src = imageUrl;
    modalCaption.innerHTML = `PAD# ${padNum} - ${lighting}`;

    // Add keyboard listener for ESC
    document.addEventListener('keydown', handleModalKeyPress);
}

// Close image modal
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.style.display = 'none';

    // Remove keyboard listener
    document.removeEventListener('keydown', handleModalKeyPress);
}

// Make modal functions globally accessible
window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
window.toggleSection = toggleSection;

// Handle keyboard events for modal
function handleModalKeyPress(event) {
    if (event.key === 'Escape' || event.key === 'Esc') {
        closeImageModal();
    }
}

// Click outside modal to close
window.onclick = function(event) {
    const modal = document.getElementById('imageModal');
    if (event.target == modal) {
        closeImageModal();
    }
}

// Export filtered results to CSV
function exportFilteredGallery() {
    const visibleItems = document.querySelectorAll('.gallery-item:not(.hidden)');
    const data = [];

    visibleItems.forEach(item => {
        data.push({
            annot_id: item.dataset.annotId,  // HTML: data-annot-id -> JS: annotId (camelCase)
            pad_num: item.dataset.pad,
            lighting: item.dataset.lighting,
            camera: item.dataset.camera,
            background: item.dataset.background,
            api: item.dataset.api,
            sample: item.dataset.sample,
            status: item.dataset.status
        });
    });

    // Convert to CSV
    const csv = convertToCSV(data);

    // Download
    downloadCSV(csv, 'gallery_filtered_export.csv');
}

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