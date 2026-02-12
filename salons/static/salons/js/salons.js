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
    constructor(salonId) {
        this.salonId = salonId;
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
            const response = await fetch(`/${this.salonId}/slots/?date=${dateStr}`);
            
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
            const response = await fetch(`/${this.salonId}/slots/${slotId}/appointment/`);

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
            const response = await fetch(`/${this.salonId}/slots/${slotId}/appointment/cancel/`, {
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
            const response = await fetch(`/${this.salonId}/slots/${slotId}/block/`, {
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
            const response = await fetch(`/${this.salonId}/slots/${slotId}/unblock/`, {
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
        const salonId = parseInt(salonIdElement.dataset.salonId);
        window.salonScheduler = new SalonScheduler(salonId);
    }
});