// Global variables and utilities
const API_BASE = '/api';
let currentEditingItem = null;

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification transform transition-all duration-300 ease-in-out translate-x-full opacity-0 max-w-xs bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden`;
    
    const bgColor = type === 'success' ? 'bg-green-50' : type === 'error' ? 'bg-red-50' : 'bg-blue-50';
    const iconColor = type === 'success' ? 'text-green-400' : type === 'error' ? 'text-red-400' : 'text-blue-400';
    const textColor = type === 'success' ? 'text-green-800' : type === 'error' ? 'text-red-800' : 'text-blue-800';
    
    toast.innerHTML = `
        <div class="p-4">
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <svg class="h-6 w-6 ${iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        ${type === 'success' ? 
                            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />' :
                            type === 'error' ? 
                            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />' :
                            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
                        }
                    </svg>
                </div>
                <div class="ml-3 w-0 flex-1 pt-0.5">
                    <p class="text-sm font-medium ${textColor}">${message}</p>
                </div>
                <div class="ml-4 flex-shrink-0 flex">
                    <button onclick="this.closest('.toast-notification').remove()" class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                        <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    }, 100);
    
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Modal utilities
function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
    
    // Reset forms when closing modals
    const form = document.querySelector(`#${modalId} form`);
    if (form) form.reset();
    
    currentEditingItem = null;
}

// API utilities
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(API_BASE + endpoint, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        showToast(error.message || 'An error occurred', 'error');
        throw error;
    }
}

// Users management
function viewUserDetails(userId) {
    // Load user details via API
    apiCall(`/users/${userId}`)
        .then(data => {
            const content = document.getElementById('user-details-content');
            content.innerHTML = `
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="text-sm font-medium text-gray-500">Name</label>
                            <p class="text-sm text-gray-900">${data.user.name || 'Not provided'}</p>
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-500">Phone</label>
                            <p class="text-sm text-gray-900">${data.user.phone}</p>
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-500">Email</label>
                            <p class="text-sm text-gray-900">${data.user.email || 'Not provided'}</p>
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-500">Status</label>
                            <p class="text-sm">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${data.user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                    ${data.user.is_verified ? 'Verified' : 'Pending Verification'}
                                </span>
                            </p>
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-500">Loyalty Points</label>
                            <p class="text-sm text-gray-900">${data.user.loyalty_points}</p>
                        </div>
                        <div>
                            <label class="text-sm font-medium text-gray-500">Joined</label>
                            <p class="text-sm text-gray-900">${new Date(data.user.created_at).toLocaleDateString()}</p>
                        </div>
                    </div>
                    <div>
                        <label class="text-sm font-medium text-gray-500">Recent Orders</label>
                        <p class="text-sm text-gray-900">${data.orders_count || 0} orders placed</p>
                    </div>
                </div>
            `;
            openModal('user-modal');
        })
        .catch(error => {
            showToast('Failed to load user details', 'error');
        });
}

function updateLoyaltyPoints(userId, currentPoints) {
    document.getElementById('user-id').value = userId;
    document.getElementById('loyalty-points').value = currentPoints;
    openModal('loyalty-modal');
}

function verifyUser(userId) {
    if (confirm('Are you sure you want to verify this user?')) {
        apiCall(`/users/${userId}/verify`, { method: 'POST' })
            .then(() => {
                showToast('User verified successfully', 'success');
                setTimeout(() => location.reload(), 1000);
            });
    }
}

// Enhanced Menu management
let selectedImage = null;

function filterByCategory(categoryId) {
    const items = document.querySelectorAll('.menu-item');
    const tabs = document.querySelectorAll('.category-tab');
    
    // Update tab styles
    tabs.forEach(tab => {
        tab.classList.remove('active', 'border-primary-500', 'text-primary-600');
        tab.classList.add('border-transparent', 'text-gray-500');
    });
    
    event.target.classList.add('active', 'border-primary-500', 'text-primary-600');
    event.target.classList.remove('border-transparent', 'text-gray-500');
    
    // Filter items
    items.forEach(item => {
        if (categoryId === 'all' || item.dataset.category == categoryId) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function openAddItemModal() {
    currentEditingItem = null;
    document.getElementById('item-modal-title').textContent = 'Add Menu Item';
    document.getElementById('item-form').reset();
    document.getElementById('item-id').value = '';
    resetImageUpload();
    updatePricePreview();
    openModal('item-modal');
}

function editItem(itemId) {
    currentEditingItem = itemId;
    document.getElementById('item-modal-title').textContent = 'Edit Menu Item';
    
    // Load item details
    apiCall(`/menu-items/${itemId}`)
        .then(data => {
            const item = data.item;
            document.getElementById('item-id').value = item.id;
            document.getElementById('item-name').value = item.name;
            document.getElementById('item-description').value = item.description || '';
            document.getElementById('item-price').value = item.price;
            document.getElementById('item-discount').value = item.discount_percentage || 0;
            document.getElementById('item-category').value = item.category_id;
            document.getElementById('item-available').checked = item.is_available;
            document.getElementById('current-image').value = item.image || '';
            
            // Set existing image if available
            if (item.image) {
                const imagePreview = document.getElementById('image-preview');
                const imagePlaceholder = document.getElementById('image-placeholder');
                const removeButton = document.getElementById('remove-image');
                
                imagePreview.src = `/uploads/images/${item.image}`;
                imagePreview.classList.remove('hidden');
                imagePlaceholder.classList.add('hidden');
                removeButton.classList.remove('hidden');
            } else {
                resetImageUpload();
            }
            
            updatePricePreview();
            openModal('item-modal');
        });
}

// Image upload functionality
function resetImageUpload() {
    const imagePreview = document.getElementById('image-preview');
    const imagePlaceholder = document.getElementById('image-placeholder');
    const removeButton = document.getElementById('remove-image');
    const fileInput = document.getElementById('item-image');
    
    imagePreview.classList.add('hidden');
    imagePlaceholder.classList.remove('hidden');
    removeButton.classList.add('hidden');
    fileInput.value = '';
    selectedImage = null;
}

function removeImage() {
    resetImageUpload();
    document.getElementById('current-image').value = '';
}

function handleImageUpload(file) {
    if (!file || !file.type.startsWith('image/')) {
        showToast('Please select a valid image file', 'error');
        return;
    }
    
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showToast('Image size must be less than 5MB', 'error');
        return;
    }
    
    const imagePreview = document.getElementById('image-preview');
    const imagePlaceholder = document.getElementById('image-placeholder');
    const removeButton = document.getElementById('remove-image');
    
    // Create preview
    const reader = new FileReader();
    reader.onload = function(e) {
        imagePreview.src = e.target.result;
        imagePreview.classList.remove('hidden');
        imagePlaceholder.classList.add('hidden');
        removeButton.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
    
    selectedImage = file;
}

// Price preview functionality
function updatePricePreview() {
    const priceInput = document.getElementById('item-price');
    const discountInput = document.getElementById('item-discount');
    const pricePreview = document.getElementById('price-preview');
    const finalPrice = document.getElementById('final-price');
    const originalPrice = document.getElementById('original-price');
    const discountBadge = document.getElementById('discount-badge');
    
    const price = parseFloat(priceInput.value) || 0;
    const discount = parseFloat(discountInput.value) || 0;
    
    if (price > 0) {
        const discountedPrice = price * (1 - discount / 100);
        finalPrice.textContent = `$${discountedPrice.toFixed(2)}`;
        
        if (discount > 0) {
            originalPrice.textContent = `$${price.toFixed(2)}`;
            originalPrice.classList.remove('hidden');
            discountBadge.textContent = `${discount}% OFF`;
            discountBadge.classList.remove('hidden');
        } else {
            originalPrice.classList.add('hidden');
            discountBadge.classList.add('hidden');
        }
        
        pricePreview.classList.remove('hidden');
    } else {
        pricePreview.classList.add('hidden');
    }
}

function toggleAvailability(itemId, currentStatus) {
    const newStatus = !currentStatus;
    apiCall(`/menu-items/${itemId}/availability`, {
        method: 'PUT',
        body: JSON.stringify({ is_available: newStatus })
    })
    .then(() => {
        showToast(`Item ${newStatus ? 'enabled' : 'disabled'} successfully`, 'success');
        setTimeout(() => location.reload(), 1000);
    });
}

function deleteItem(itemId) {
    if (confirm('Are you sure you want to delete this item?')) {
        apiCall(`/menu-items/${itemId}`, { method: 'DELETE' })
            .then(() => {
                showToast('Item deleted successfully', 'success');
                setTimeout(() => location.reload(), 1000);
            });
    }
}

// Order management
function updateOrderStatus(orderId, newStatus) {
    apiCall(`/orders/${orderId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus })
    })
    .then(() => {
        showToast('Order status updated successfully', 'success');
        setTimeout(() => location.reload(), 1000);
    });
}

function viewOrderDetails(orderId) {
    // Load order details via API
    apiCall(`/orders/${orderId}`)
        .then(data => {
            const order = data.order;
            const content = document.getElementById('order-details-content');
            
            // Format order date
            const orderDate = order.created_at ? new Date(order.created_at).toLocaleString() : 'Unknown';
            
            // Generate status badge
            const statusColors = {
                'pending': 'bg-yellow-100 text-yellow-800',
                'confirmed': 'bg-blue-100 text-blue-800',
                'preparing': 'bg-orange-100 text-orange-800',
                'ready': 'bg-green-100 text-green-800',
                'delivered': 'bg-gray-100 text-gray-800'
            };
            
            const statusBadge = `
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[order.status] || 'bg-gray-100 text-gray-800'}">
                    ${order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                </span>
            `;
            
            // Generate items list
            const itemsHtml = order.items.map(item => {
                const itemImage = item.menu_item && item.menu_item.image 
                    ? `/uploads/images/${item.menu_item.image}` 
                    : null;
                
                return `
                    <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        ${itemImage ? 
                            `<img src="${itemImage}" alt="${item.name}" class="w-12 h-12 object-cover rounded-lg">` :
                            `<div class="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                                <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 110 2h-1v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6H3a1 1 0 110-2h4zM9 6h6v10H9V6z"/>
                                </svg>
                            </div>`
                        }
                        <div class="flex-1">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="text-sm font-medium text-gray-900">${item.name}</h4>
                                    ${item.menu_item && item.menu_item.category_name ? 
                                        `<p class="text-xs text-gray-500">${item.menu_item.category_name}</p>` : ''
                                    }
                                </div>
                                <div class="text-right">
                                    <p class="text-sm font-medium text-gray-900">$${parseFloat(item.total || 0).toFixed(2)}</p>
                                    <p class="text-xs text-gray-500">${item.quantity}x $${parseFloat(item.price || 0).toFixed(2)}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            content.innerHTML = `
                <div class="space-y-6">
                    <!-- Order Header -->
                    <div class="flex justify-between items-start pb-4 border-b border-gray-200">
                        <div>
                            <h4 class="text-lg font-semibold text-gray-900">Order #${order.id}</h4>
                            <p class="text-sm text-gray-500">${orderDate}</p>
                        </div>
                        <div class="text-right">
                            ${statusBadge}
                            <p class="text-lg font-bold text-gray-900 mt-1">$${parseFloat(order.total_amount || 0).toFixed(2)}</p>
                        </div>
                    </div>
                    
                    <!-- Customer Information -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h5 class="text-sm font-medium text-gray-900 mb-2">Customer Information</h5>
                            <div class="space-y-1">
                                <p class="text-sm text-gray-700">
                                    <span class="font-medium">Name:</span> ${order.user ? order.user.name || 'Not provided' : 'Unknown'}
                                </p>
                                <p class="text-sm text-gray-700">
                                    <span class="font-medium">Phone:</span> ${order.phone || (order.user ? order.user.phone : 'Not provided')}
                                </p>
                                <p class="text-sm text-gray-700">
                                    <span class="font-medium">Email:</span> ${order.user && order.user.email ? order.user.email : 'Not provided'}
                                </p>
                                <p class="text-sm text-gray-700">
                                    <span class="font-medium">Loyalty Points:</span> ${order.user ? order.user.loyalty_points || 0 : 0}
                                </p>
                            </div>
                        </div>
                        
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h5 class="text-sm font-medium text-gray-900 mb-2">Delivery Information</h5>
                            <div class="space-y-1">
                                <p class="text-sm text-gray-700">
                                    <span class="font-medium">Address:</span> ${order.delivery_address || 'Not provided'}
                                </p>
                                <p class="text-sm text-gray-700">
                                    <span class="font-medium">Order Type:</span> ${order.delivery_address ? 'Delivery' : 'Pickup'}
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Order Items -->
                    <div>
                        <h5 class="text-sm font-medium text-gray-900 mb-3">Order Items (${order.items.length})</h5>
                        <div class="space-y-2">
                            ${itemsHtml}
                        </div>
                    </div>
                    
                    <!-- Order Summary -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h5 class="text-sm font-medium text-gray-900 mb-3">Order Summary</h5>
                        <div class="space-y-2">
                            <div class="flex justify-between text-sm">
                                <span class="text-gray-600">Subtotal</span>
                                <span class="text-gray-900">$${parseFloat(order.total_amount || 0).toFixed(2)}</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span class="text-gray-600">Delivery Fee</span>
                                <span class="text-green-600 font-medium">FREE</span>
                            </div>
                            <div class="border-t border-gray-300 pt-2 mt-2">
                                <div class="flex justify-between text-base font-semibold">
                                    <span class="text-gray-900">Total</span>
                                    <span class="text-gray-900">$${parseFloat(order.total_amount || 0).toFixed(2)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Status Update -->
                    <div class="bg-primary-50 p-4 rounded-lg">
                        <h5 class="text-sm font-medium text-gray-900 mb-2">Update Order Status</h5>
                        <select onchange="updateOrderStatusFromModal(${order.id}, this.value)" class="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md">
                            <option value="pending" ${order.status === 'pending' ? 'selected' : ''}>Pending</option>
                            <option value="confirmed" ${order.status === 'confirmed' ? 'selected' : ''}>Confirmed</option>
                            <option value="preparing" ${order.status === 'preparing' ? 'selected' : ''}>Preparing</option>
                            <option value="ready" ${order.status === 'ready' ? 'selected' : ''}>Ready</option>
                            <option value="delivered" ${order.status === 'delivered' ? 'selected' : ''}>Delivered</option>
                        </select>
                    </div>
                </div>
            `;
            openModal('order-modal');
        })
        .catch(error => {
            showToast('Failed to load order details', 'error');
        });
}

function updateOrderStatusFromModal(orderId, newStatus) {
    apiCall(`/orders/${orderId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus })
    })
    .then(() => {
        showToast('Order status updated successfully', 'success');
        closeModal('order-modal');
        setTimeout(() => location.reload(), 1000);
    });
}

// Form submissions
document.addEventListener('DOMContentLoaded', function() {
    // Loyalty points form
    const loyaltyForm = document.getElementById('loyalty-form');
    if (loyaltyForm) {
        loyaltyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const userId = formData.get('user_id');
            const points = formData.get('loyalty_points');
            
            apiCall(`/users/${userId}/loyalty-points`, {
                method: 'PUT',
                body: JSON.stringify({ loyalty_points: parseInt(points) })
            })
            .then(() => {
                showToast('Loyalty points updated successfully', 'success');
                closeModal('loyalty-modal');
                setTimeout(() => location.reload(), 1000);
            });
        });
    }
    
    // Enhanced Menu item form
    const itemForm = document.getElementById('item-form');
    if (itemForm) {
        itemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const saveBtn = document.getElementById('save-item-btn');
            const saveLoading = document.getElementById('save-loading');
            
            // Disable submit button and show loading
            saveBtn.disabled = true;
            saveLoading.classList.remove('hidden');
            
            const formData = new FormData(this);
            const itemId = formData.get('item_id');
            
            // Handle boolean conversion for availability
            formData.set('is_available', formData.get('is_available') ? 'true' : 'false');
            
            // Add selected image if any
            if (selectedImage) {
                formData.set('image', selectedImage);
            }
            
            const method = itemId ? 'PUT' : 'POST';
            const endpoint = itemId ? `/menu-items/${itemId}` : '/menu-items';
            
            fetch(API_BASE + endpoint, {
                method: method,
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(`Menu item ${itemId ? 'updated' : 'created'} successfully`, 'success');
                    closeModal('item-modal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    throw new Error(data.message || 'Operation failed');
                }
            })
            .catch(error => {
                showToast(error.message || 'An error occurred', 'error');
            })
            .finally(() => {
                // Re-enable submit button and hide loading
                saveBtn.disabled = false;
                saveLoading.classList.add('hidden');
            });
        });
    }
    
    // Search functionality
    const searchInput = document.getElementById('search-users');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const userRows = document.querySelectorAll('#users-tbody tr');
            
            userRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
    
    // Close modals on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('[id$="-modal"]:not(.hidden)');
            openModals.forEach(modal => {
                modal.classList.add('hidden');
            });
            document.body.classList.remove('overflow-hidden');
        }
    });
    
    // Close modals when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.matches('[id$="-modal"]')) {
            e.target.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    });
    
    // Image upload event listeners
    const imageInput = document.getElementById('item-image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                handleImageUpload(file);
            }
        });
        
        // Drag and drop functionality
        const imageContainer = document.getElementById('image-preview-container');
        if (imageContainer) {
            imageContainer.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.classList.add('border-primary-400', 'bg-primary-50');
            });
            
            imageContainer.addEventListener('dragleave', function(e) {
                e.preventDefault();
                this.classList.remove('border-primary-400', 'bg-primary-50');
            });
            
            imageContainer.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('border-primary-400', 'bg-primary-50');
                
                const file = e.dataTransfer.files[0];
                if (file) {
                    // Update the file input
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    imageInput.files = dt.files;
                    
                    handleImageUpload(file);
                }
            });
        }
    }
    
    // Price preview event listeners
    const priceInput = document.getElementById('item-price');
    const discountInput = document.getElementById('item-discount');
    
    if (priceInput) {
        priceInput.addEventListener('input', updatePricePreview);
    }
    
    if (discountInput) {
        discountInput.addEventListener('input', updatePricePreview);
    }
});