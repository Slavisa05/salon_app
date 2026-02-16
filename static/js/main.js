console.log('main.js');

// static/js/main.js

// ==============================================
// UTILITY FUNCTIONS
// ==============================================

// Delegate event listener (za dinamički kreirane elemente)
function delegate(parent, type, selector, handler) {
    parent.addEventListener(type, function(event) {
        if (event.target.matches(selector)) {
            handler.call(event.target, event);
        }
    });
}

// ==============================================
// CLICKABLE CARDS (Landing page)
// ==============================================

function initClickableCards() {
    const cards = document.querySelectorAll('.clickable-card[data-url]');
    
    cards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Ignoriši ako je kliknut link ili button
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                return;
            }
            
            const url = this.dataset.url;
            if (url) {
                window.location.href = url;
            }
        });
    });
}

// ==============================================
// BOOKING FORM
// ==============================================

class BookingForm {
    constructor(formElement) {
        this.form = formElement;
        this.salonId = formElement.dataset.salonId;
        this.salonName = formElement.dataset.salonName;
        this.apiUrl = formElement.dataset.apiUrl;
        
        this.selectedService = null;
        this.selectedDate = null;
        this.selectedTimeslot = null;
        this.selectedPrice = 0;
        
        this.init();
    }
    
    init() {
        this.setupServiceSelection();
        this.setupDateSelection();
        this.setupFormValidation();
    }
    
    // Step 1: Service selection
    setupServiceSelection() {
        const serviceRadios = this.form.querySelectorAll('input[name="service"]');
        
        serviceRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                const target = e.target;
                
                this.selectedService = {
                    id: target.value,
                    name: target.dataset.serviceName,
                    price: parseFloat(target.dataset.price),
                    duration: target.dataset.duration
                };
                
                // Show next step
                document.getElementById('step2').style.display = 'block';
                
                // Visual feedback (dodaj/ukloni CSS klasu)
                document.querySelectorAll('.service-card').forEach(card => {
                    card.classList.remove('selected');
                });
                target.closest('.service-card').classList.add('selected');
                
                // Scroll to next step
                this.scrollToElement('step2');
                
                // Update summary
                this.updateSummary();
            });
        });
    }
    
    // Step 2: Date selection
    setupDateSelection() {
        const dateInput = this.form.querySelector('input[name="date"]');
        
        if (dateInput) {
            dateInput.addEventListener('change', (e) => {
                this.selectedDate = e.target.value;
                
                // Show next step
                document.getElementById('step3').style.display = 'block';
                
                // Fetch timeslots
                if (this.selectedService) {
                    this.fetchAvailableTimeslots(this.selectedDate, this.selectedService.id);
                }
                
                // Scroll to next step
                this.scrollToElement('step3');
                
                // Update summary
                this.updateSummary();
            });
        }
    }
    
    // Step 3: Fetch timeslots
    async fetchAvailableTimeslots(date, serviceId) {
        const loading = document.getElementById('timeslotsLoading');
        const list = document.getElementById('timeslotsList');
        
        loading.style.display = 'flex';
        list.innerHTML = '';
        
        try {
            const response = await fetch(
                `${this.apiUrl}?salon=${this.salonId}&date=${date}&service=${serviceId}`
            );
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            loading.style.display = 'none';
            
            if (data.timeslots && data.timeslots.length > 0) {
                data.timeslots.forEach(ts => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'timeslot-btn';
                    btn.textContent = `${ts.start_time} - ${ts.end_time}`;
                    btn.dataset.timeslotId = ts.id;
                    btn.dataset.startTime = ts.start_time;
                    
                    btn.addEventListener('click', () => {
                        this.selectTimeslot(ts.id, ts.start_time, btn);
                    });
                    
                    list.appendChild(btn);
                });
            } else {
                list.innerHTML = '<p class="no-slots">Nema dostupnih termina za ovaj dan. Pokušajte drugi datum.</p>';
            }
        } catch (error) {
            loading.style.display = 'none';
            list.innerHTML = '<p class="error-message">Greška pri učitavanju termina. Pokušajte ponovo.</p>';
            console.error('Error fetching timeslots:', error);
        }
    }
    
    // Select timeslot
    selectTimeslot(timeslotId, startTime, button) {
        // Remove active from all
        document.querySelectorAll('.timeslot-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active to clicked
        button.classList.add('active');
        
        // Set hidden input
        this.form.querySelector('input[name="time_slot"]').value = timeslotId;
        this.selectedTimeslot = startTime;
        
        // Show next step
        document.getElementById('step4').style.display = 'block';
        
        // Scroll to next step
        this.scrollToElement('step4');
        
        // Check form completion
        this.checkFormCompletion();
        
        // Update summary
        this.updateSummary();
    }
    
    // Step 4: Form validation
    setupFormValidation() {
        const requiredFields = ['guest_name', 'guest_email', 'guest_phone'];
        
        requiredFields.forEach(fieldName => {
            const field = this.form.querySelector(`input[name="${fieldName}"]`);
            if (field) {
                field.addEventListener('input', () => {
                    this.checkFormCompletion();
                });
            }
        });
    }
    
    checkFormCompletion() {
        const name = this.form.querySelector('input[name="guest_name"]').value.trim();
        const email = this.form.querySelector('input[name="guest_email"]').value.trim();
        const phone = this.form.querySelector('input[name="guest_phone"]').value.trim();
        const timeslot = this.form.querySelector('input[name="time_slot"]').value;
        
        const submitBtn = this.form.querySelector('#submitBtn');
        submitBtn.disabled = !(name && email && phone && timeslot);
    }
    
    // Update summary sidebar
    updateSummary() {
        const content = document.getElementById('summaryContent');
        const totalDiv = document.getElementById('summaryTotal');
        const totalPrice = document.getElementById('totalPrice');
        
        let html = '<ul class="summary-list">';
        
        if (this.selectedService) {
            html += `<li><strong>Usluga:</strong><br>${this.selectedService.name}</li>`;
            this.selectedPrice = this.selectedService.price;
        }
        
        if (this.selectedDate) {
            html += `<li><strong>Datum:</strong><br>${this.selectedDate}</li>`;
        }
        
        if (this.selectedTimeslot) {
            html += `<li><strong>Vreme:</strong><br>${this.selectedTimeslot}</li>`;
        }
        
        html += '</ul>';
        content.innerHTML = html;
        
        if (this.selectedService) {
            totalDiv.style.display = 'flex';
            totalPrice.textContent = `${this.selectedPrice} RSD`;
        }
    }
    
    // Smooth scroll helper
    scrollToElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            setTimeout(() => {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }
}

// ==============================================
// INITIALIZATION
// ==============================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize clickable cards (landing page)
    initClickableCards();
    
    // Initialize booking form if exists
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        new BookingForm(bookingForm);
    }
});