console.log('salons.js');

const sidebarToggle = document.getElementById('sidebarToggle');

if (sidebarToggle) {
	sidebarToggle.addEventListener('click', () => {
		const isCollapsed = document.body.classList.toggle('sidebar-collapsed');
		sidebarToggle.setAttribute('aria-expanded', String(!isCollapsed));
	});
}

// slots
class SalonScheduler {
    constructor(salonName) {
        this.salonName = salonName;
        this.selectedDate = new Date();
        this.selectedDate.setHours(12, 0, 0, 0);
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.bindModal();
        this.loadSlotsForToday();
        // this.initCalendar(); // Kada dodaš kalendar biblioteku
    }
    
    setupEventListeners() {
        const calendarElement = document.getElementById('calendar');
        if (calendarElement && window.FullCalendar) {
            this.calendar = new window.FullCalendar.Calendar(calendarElement, {
                initialView: 'dayGridMonth',
                initialDate: this.formatDate(this.selectedDate),
                locale: 'sr',
                customButtons: {
                    todayCustom: {
                        text: 'today',
                        click: () => {
                            const today = new Date();
                            today.setHours(12, 0, 0, 0);
                            this.selectedDate = today;
                            this.calendar.gotoDate(today);
                            this.loadSlots(this.selectedDate);
                            this.calendar.render();
                        }
                    }
                },
                headerToolbar: {
                    left: 'prev,next todayCustom',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek'
                },
                dateClick: (info) => {
                    const nextDate = new Date(info.dateStr);
                    nextDate.setHours(12, 0, 0, 0);
                    this.selectedDate = nextDate;
                    this.loadSlots(this.selectedDate);
                    this.calendar.render();
                },
                dayCellClassNames: (arg) => {
                    const activeDate = this.formatDate(this.selectedDate);
                    const cellDate = this.formatDate(arg.date);
                    return cellDate === activeDate ? ['fc-day-selected'] : [];
                }
            });

            this.calendar.render();
            return;
        }

        const datePicker = document.getElementById('date-picker');
        if (datePicker) {
            datePicker.value = this.formatDate(this.selectedDate);

            datePicker.addEventListener('change', (event) => {
                const value = event.target.value;
                if (!value) {
                    return;
                }

                const [year, month, day] = value.split('-').map(Number);
                this.selectedDate = new Date(year, month - 1, day);
                this.selectedDate.setHours(12, 0, 0, 0);
                this.loadSlots(this.selectedDate);
            });
        }
    }
    
    // Učitaj slotove za određeni datum
    async loadSlots(date) {
        const dateStr = this.formatDate(date);
        
        try {
            const response = await fetch(`/salons/${this.salonName}/slots/?date=${dateStr}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch slots');
            }
            
            const data = await response.json();
            this.renderSlots(data.slots);
            this.updateSelectedDateDisplay(date);
            this.updateDatePicker(date);
            
        } catch (error) {
            console.error('Error loading slots:', error);
            this.showError('Greška pri učitavanju termina');
        }
    }
    
    loadSlotsForToday() {
        this.loadSlots(this.selectedDate);
    }
    
    // Renderuj slotove u DOM
    renderSlots(slots) {
        const container = document.getElementById('time-slots-container');
        
        if (!container) {
            console.error('Time slots container not found');
            return;
        }
        
        // Očisti kontejner
        container.innerHTML = '';
        
        if (slots.length === 0) {
            container.innerHTML = '<p class="no-slots">Salon ne radi ovog dana</p>';
            return;
        }
        
        slots.forEach(slot => {
            const slotElement = this.createSlotElement(slot);
            container.appendChild(slotElement);
        });
    }
    
    // Kreiraj HTML element za jedan slot
    createSlotElement(slot) {
        const slotDiv = document.createElement('div');
        slotDiv.className = `time-slot time-slot-${slot.status}`;
        slotDiv.dataset.slotId = slot.id;
        
        slotDiv.innerHTML = `
            <span class="time">${slot.begin_time} - ${slot.end_time}</span>
            <span class="status-badge">${this.getStatusLabel(slot.status)}</span>
        `;
        
        // Dodaj event listener
        slotDiv.addEventListener('click', () => this.handleSlotClick(slot));
        
        return slotDiv;
    }
    
    // Klik na slot
    handleSlotClick(slot) {
        console.log('Clicked slot:', slot);
        
        // Proveri status i prikaži odgovarajuće opcije
        switch(slot.status) {
            case 'dostupan':
                this.showSlotActions(slot, ['block', 'manual_book']);
                break;
            case 'zauzet':
                this.showAppointmentDetails(slot);
                break;
            case 'blokiran':
                this.showSlotActions(slot, ['unblock']);
                break;
        }
    }
    
    // Prikaži akcije za slot (kasnije ćeš implementirati modal)
    showSlotActions(slot, actions) {
        // TODO: Otvori modal sa opcijama
        console.log('Available actions:', actions);
        
        if (actions.includes('block')) {
            if (confirm('Želite da blokirate ovaj termin?')) {
                this.blockSlot(slot.id);
            }
        }

        if (actions.includes('unblock')) {
            if (confirm('Želite da odblokirate ovaj termin?')) {
                this.unblockSlot(slot.id);
            }
        }
    }
    
    // Prikaži detalje rezervacije
    showAppointmentDetails(slot) {
        if (!slot.id) {
            this.showError('Termin nema ID');
            return;
        }

        this.fetchAppointmentDetails(slot.id);
    }

    async fetchAppointmentDetails(slotId) {
        try {
            const response = await fetch(`/salons/${this.salonName}/slots/${slotId}/appointment/`);

            if (!response.ok) {
                throw new Error('Failed to fetch appointment details');
            }

            const data = await response.json();
            if (this.modalElement) {
                this.modalElement.dataset.slotId = slotId;
            }
            this.fillAppointmentModal(data);
            this.openModal();
        } catch (error) {
            console.error('Error loading appointment details:', error);
            this.showError('Greška pri učitavanju detalja termina');
        }
    }

    fillAppointmentModal(data) {
        const safeValue = (value) => value || '-';

        const customer = document.getElementById('appointment-customer');
        const service = document.getElementById('appointment-service');
        const status = document.getElementById('appointment-status');
        const date = document.getElementById('appointment-date');
        const time = document.getElementById('appointment-time');
        const notes = document.getElementById('appointment-notes');
        const cancelButton = document.getElementById('appointment-cancel');

        if (customer) {
            customer.textContent = safeValue(data.customer);
        }
        if (service) {
            service.textContent = safeValue(data.service);
        }
        if (status) {
            status.textContent = safeValue(data.status);
        }
        if (date) {
            date.textContent = safeValue(data.date);
        }
        if (time) {
            time.textContent = safeValue(data.time);
        }
        if (notes) {
            notes.textContent = data.notes ? data.notes : '-';
        }

        if (cancelButton) {
            const isCancelled = data.status === 'otkazano';
            cancelButton.disabled = isCancelled;
            cancelButton.textContent = isCancelled ? 'Termin otkazan' : 'Otkaži termin';
        }
    }

    bindModal() {
        this.modalElement = document.getElementById('appointment-modal');
        if (!this.modalElement) {
            return;
        }

        const cancelButton = document.getElementById('appointment-cancel');
        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                if (cancelButton.disabled) {
                    return;
                }

                const slotId = this.modalElement?.dataset.slotId;
                if (!slotId) {
                    this.showError('Termin nema ID');
                    return;
                }

                if (confirm('Da li ste sigurni da želite da otkažete termin?')) {
                    this.cancelAppointment(slotId);
                }
            });
        }

        this.modalElement.addEventListener('click', (event) => {
            if (event.target.matches('[data-modal-close]')) {
                this.closeModal();
            }
        });
    }

    async cancelAppointment(slotId) {
        try {
            const response = await fetch(`/salons/${this.salonName}/slots/${slotId}/appointment/cancel/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to cancel appointment');
            }

            this.closeModal();
            this.loadSlots(this.selectedDate);
            this.showSuccess('Termin je otkazan');
        } catch (error) {
            console.error('Error cancelling appointment:', error);
            this.showError('Greška pri otkazivanju termina');
        }
    }

    openModal() {
        if (!this.modalElement) {
            return;
        }

        this.modalElement.classList.add('is-open');
        this.modalElement.setAttribute('aria-hidden', 'false');
    }

    closeModal() {
        if (!this.modalElement) {
            return;
        }

        this.modalElement.classList.remove('is-open');
        this.modalElement.setAttribute('aria-hidden', 'true');
    }
    
    // Blokiraj slot
    async blockSlot(slotId) {
        if (!slotId) {
            this.showError('Termin nema ID');
            return;
        }
        try {
            const response = await fetch(`/salons/${this.salonName}/slots/${slotId}/block/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to block slot');
            }
            
            // Refresh slotove
            this.loadSlots(this.selectedDate);
            this.showSuccess('Termin je blokiran');
            
        } catch (error) {
            console.error('Error blocking slot:', error);
            this.showError('Greška pri blokiranju termina');
        }
    }
    
    // Odblokiraj slot
    async unblockSlot(slotId) {
        if (!slotId) {
            this.showError('Termin nema ID');
            return;
        }
        try {
            const response = await fetch(`/salons/${this.salonName}/slots/${slotId}/unblock/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to unblock slot');
            }
            
            this.loadSlots(this.selectedDate);
            this.showSuccess('Termin je odblokiran');
            
        } catch (error) {
            console.error('Error unblocking slot:', error);
            this.showError('Greška pri odblokiranju termina');
        }
    }
    
    // Helper funkcije
    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    updateSelectedDateDisplay(date) {
        const displayElement = document.getElementById('selected-date');
        if (displayElement) {
            const options = { weekday: 'long' };
            displayElement.textContent = date.toLocaleDateString('sr-Latn-RS', options);
        }
    }

    updateDatePicker(date) {
        if (this.calendar) {
            this.calendar.gotoDate(this.formatDate(date));
            return;
        }

        const datePicker = document.getElementById('date-picker');
        if (datePicker) {
            const formattedDate = this.formatDate(date);
            datePicker.value = formattedDate;
        }
    }
    
    getStatusLabel(status) {
        const labels = {
            'dostupan': 'Slobodan',
            'zauzet': 'Zauzet',
            'blokiran': 'Blokiran'
        };
        return labels[status] || status;
    }
    
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    showSuccess(message) {
        // TODO: Implementiraj toast notification
        alert(message);
    }
    
    showError(message) {
        // TODO: Implementiraj toast notification
        alert(message);
    }
}

// Inicijalizuj kada se DOM učita
document.addEventListener('DOMContentLoaded', () => {
    const salonIdElement = document.getElementById('salon-id');
    
    if (salonIdElement) {
        const salonName = salonIdElement.dataset.salonName;
        window.salonScheduler = new SalonScheduler(salonName);
    }
});

// ADD NEW SERVICE
const addNewService = document.querySelector('#addNewService');
if (addNewService) {
    addNewService.addEventListener('click', () => {
        const targetUrl = addNewService.dataset.url;
        if (targetUrl) {
            window.location.href = targetUrl;
        }
    });
}

// EDIT SERVICE
const editBtns = document.querySelectorAll('.card-btn');
if (editBtns) {
    editBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetUrl = e.target.dataset.url;
            if (targetUrl) {
                window.location.href = targetUrl;
            }
        });
    });
}

// DELETE SERVICE
const deleteBtns = document.querySelectorAll('.delete-btn');
if (deleteBtns) {
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (confirm('Da li ste sigurni da želite da obrišete ovu uslugu?')) {
                const targetUrl = e.target.dataset.url;
                if (targetUrl) {
                    window.location.href = targetUrl;
                }
            }
        });
    });
}

/**
 * ============================================
 * IMAGE UPLOAD - PREVIEW
 * ============================================
 * Prikazuje preview slike pre upload-a
 */

document.addEventListener('DOMContentLoaded', function() {
    // Pozovi funkcije samo ako postoje
    if (typeof initWorkingHoursToggle === 'function') {
        initWorkingHoursToggle();
    }
    if (typeof initImageUpload === 'function') {
        initImageUpload();
    }
});


function initWorkingHoursToggle() {
    const checkboxes = document.querySelectorAll('.working-day-checkbox');

    if (!checkboxes.length) {
        return;
    }

    const toggleDayInputs = (checkbox) => {
        const row = checkbox.closest('.working-day-row');
        if (!row) {
            return;
        }

        const timeInputs = row.querySelectorAll('.working-time-input');
        const isEnabled = checkbox.checked;

        timeInputs.forEach((input) => {
            input.disabled = !isEnabled;
        });
    };

    checkboxes.forEach((checkbox) => {
        toggleDayInputs(checkbox);
        checkbox.addEventListener('change', () => toggleDayInputs(checkbox));
    });
}


/**
 * Inicijalizuje image upload funkcionalnost
 */
function initImageUpload() {
    const imageInput = document.getElementById('id_image');
    const previewContainer = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    const changeImageBtn = document.getElementById('change-image-btn');
    const cropModal = document.getElementById('crop-modal');
    const cropImage = document.getElementById('crop-image');
    const cropApplyBtn = document.getElementById('crop-apply-btn');
    const cropCancelBtn = document.getElementById('crop-cancel-btn');
    
    if (!imageInput || !previewContainer || !previewImg) {
        return;
    }

    let cropperInstance = null;
    let sourceFile = null;
    let modalImageUrl = null;

    const destroyCropper = () => {
        if (cropperInstance) {
            cropperInstance.destroy();
            cropperInstance = null;
        }
    };

    const closeCropModal = () => {
        destroyCropper();
        if (modalImageUrl) {
            URL.revokeObjectURL(modalImageUrl);
            modalImageUrl = null;
        }
        if (cropModal) {
            cropModal.classList.remove('is-open');
            cropModal.setAttribute('aria-hidden', 'true');
        }
    };

    const updatePreview = (imageUrl) => {
        previewImg.src = imageUrl;
        previewImg.style.opacity = '0';
        setTimeout(() => {
            previewImg.style.transition = 'opacity 0.3s ease';
            previewImg.style.opacity = '1';
        }, 50);
    };

    const assignFileToInput = (file) => {
        const transfer = new DataTransfer();
        transfer.items.add(file);
        imageInput.files = transfer.files;
    };

    const getOutputMimeType = (fileType) => {
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        return allowedTypes.includes(fileType) ? fileType : 'image/jpeg';
    };

    const fileToCroppedFile = (canvas, originalFile) => {
        return new Promise((resolve, reject) => {
            const mimeType = getOutputMimeType(originalFile.type);
            canvas.toBlob(
                (blob) => {
                    if (!blob) {
                        reject(new Error('Nije moguće obraditi sliku.'));
                        return;
                    }

                    const baseName = originalFile.name.replace(/\.[^/.]+$/, '');
                    const extension = mimeType === 'image/png' ? 'png' : mimeType === 'image/webp' ? 'webp' : 'jpg';
                    const croppedFile = new File([blob], `${baseName}.${extension}`, { type: mimeType });
                    resolve(croppedFile);
                },
                mimeType,
                0.92
            );
        });
    };

    const openCropModal = (file) => {
        if (!cropModal || !cropImage || !window.Cropper) {
            alert('Crop nije dostupan. Pokušajte ponovo.');
            return;
        }

        sourceFile = file;
        closeCropModal();

        modalImageUrl = URL.createObjectURL(file);
        cropImage.src = modalImageUrl;

        cropImage.onload = () => {
            cropperInstance = new window.Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 1,
                responsive: true,
                background: false
            });
            cropModal.classList.add('is-open');
            cropModal.setAttribute('aria-hidden', 'false');
        };
    };

    const processSelectedFile = (file) => {
        if (!file) {
            return;
        }

        if (!validateImageFile(file)) {
            imageInput.value = '';
            return;
        }

        openCropModal(file);
    };
    
    /**
     * Klik na preview ili dugme otvara file picker
     */
    previewContainer.addEventListener('click', function(e) {
        if (e.target !== changeImageBtn && !changeImageBtn?.contains(e.target)) {
            imageInput.click();
        }
    });
    
    if (changeImageBtn) {
        changeImageBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            imageInput.click();
        });
    }
    
    /**
     * Kada korisnik izabere fajl, prikaži preview
     */
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        processSelectedFile(file);
    });
    
    /**
     * Drag & Drop support (bonus)
     */
    previewContainer.addEventListener('dragover', function(e) {
        e.preventDefault();
        previewContainer.style.borderColor = '#6366F1';
        previewContainer.style.background = 'rgba(99, 102, 241, 0.05)';
    });
    
    previewContainer.addEventListener('dragleave', function(e) {
        e.preventDefault();
        previewContainer.style.borderColor = '#cbd5e0';
        previewContainer.style.background = '#f0f0f0';
    });
    
    previewContainer.addEventListener('drop', function(e) {
        e.preventDefault();
        previewContainer.style.borderColor = '#cbd5e0';
        previewContainer.style.background = '#f0f0f0';
        
        const file = e.dataTransfer.files[0];

        processSelectedFile(file);
    });

    if (cropCancelBtn) {
        cropCancelBtn.addEventListener('click', () => {
            imageInput.value = '';
            sourceFile = null;
            closeCropModal();
        });
    }

    if (cropApplyBtn) {
        cropApplyBtn.addEventListener('click', async () => {
            if (!cropperInstance || !sourceFile) {
                closeCropModal();
                return;
            }

            const outputSize = 500;

            try {
                const canvas = cropperInstance.getCroppedCanvas({
                    width: outputSize,
                    height: outputSize,
                    imageSmoothingEnabled: true,
                    imageSmoothingQuality: 'high'
                });

                const croppedFile = await fileToCroppedFile(canvas, sourceFile);

                if (!validateImageFile(croppedFile)) {
                    imageInput.value = '';
                    closeCropModal();
                    return;
                }

                assignFileToInput(croppedFile);
                updatePreview(URL.createObjectURL(croppedFile));
                closeCropModal();
            } catch (error) {
                console.error(error);
                alert('Greška pri crop-u slike.');
                imageInput.value = '';
                closeCropModal();
            }
        });
    }

    if (cropModal) {
        cropModal.addEventListener('click', (event) => {
            if (event.target === cropModal) {
                imageInput.value = '';
                sourceFile = null;
                closeCropModal();
            }
        });
    }
}


/**
 * Validacija image fajla
 */
function validateImageFile(file) {
    // Proveri tip fajla
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        alert('Molimo odaberite sliku (JPG, PNG ili WebP)');
        return false;
    }
    
    // Proveri veličinu (5MB max)
    const maxSize = 5 * 1024 * 1024; // 5MB u bajtovima
    if (file.size > maxSize) {
        alert('Slika je prevelika! Maksimalna veličina je 5MB.');
        return false;
    }
    
    return true;
}


/**
 * Format file size za prikaz
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}